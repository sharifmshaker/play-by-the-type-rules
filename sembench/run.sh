#!/bin/bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
chmod -R u+x src/eval_scripts

SMOKE=0
for arg in "$@"; do
  case "$arg" in
    --smoke) SMOKE=1 ;;
    -h|--help)
      echo "usage: bash run.sh [--smoke]"
      echo "  --smoke : 1 run · gemma_e4b · movie+mmqa · Q1(text)+Q2a(image) · CD off — cheap GPU-side validation"
      exit 0 ;;
    *) echo "unknown arg: $arg (try --help)" >&2; exit 2 ;;
  esac
done

#----------------------- CONFIG -----------------------#
OFFLINE_MODE=0

# Format: "split:scale_factor"
SCENARIO_SCALE_ENTRIES=(
  "movie:2000",
  "mmqa:200",
  "wildlife:200"
  "cars:19672"
  "ecomm:500"
#  "ecomm:250"
#  "ecomm:1000"
#  "ecomm:2000"
#  "ecomm:4000"
)

N_RUNS=5
# n_parallel, enable_cascade_filter, enable_early_exit, enable_constrained_decoding
SYSTEMS=(
#"blendsql"
#"blendsql:1:true:true"
#"blendsql:16:true:true"
#"blendsql:32:true:true"
#"blendsql:64:true:true"
#"blendsql:128:true:true"
"blendsql:64:true:true:true"
"blendsql:64:false:false:false"
"blendsql:64:true:false:true"
"blendsql:64:false:false:true"
)
MODELS=("gemma_e2b" "gemma_e4b")
#------------------------------------------------------#

if [[ "$SMOKE" == "1" ]]; then
  echo "### SMOKE MODE (Gemma): 1 run · gemma_e4b · movie+mmqa · Q1+Q2a · CD off ###"
  SCENARIO_SCALE_ENTRIES=("movie:2000" "mmqa:200")
  N_RUNS=1
  MODELS=("gemma_e4b")
  SYSTEMS=("blendsql:64:true:true:false")   # cascade on, early-exit on, CD off (matches run_gemini.sh)
  export ONLY_USE="Q1,Q2a"                   # movie->Q1; mmqa->Q1(text)+Q2a(image path on vLLM)
fi

source "$(dirname "$0")/model_config.sh"

start_vllm() {
  local model_path=$1
  local num_gpus=$(nvidia-smi --list-gpus | wc -l)

  if [[ "$num_gpus" -eq 0 ]]; then
    echo "Warning: No GPUs detected by nvidia-smi. Defaulting to 1."
    num_gpus=1
  fi

  echo "Starting vLLM with Tensor Parallel Size: ${num_gpus}"

  vllm serve "${model_path}" \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size "${num_gpus}" \
    --enable-prefix-caching \
    --max-model-len 32000 \
    --structured-outputs-config.backend guidance \
    --gpu_memory_utilization 0.9 \
    --mm-processor-kwargs '{"max_length": 480000}' \
    --enable-prompt-tokens-details ${extra_serve_args} > /tmp/vllm.log 2>&1 &

  echo "Waiting for vLLM to load the model..."
  while ! curl -s -f http://127.0.0.1:8000/health > /dev/null; do
    sleep 5
  done
  echo "vLLM is online and ready!"
}

if nvidia-smi &>/dev/null; then
  has_gpu=true
else
  has_gpu=false
fi
export HAS_GPU=$has_gpu

for entry in "${SCENARIO_SCALE_ENTRIES[@]}"; do
  IFS=':' read -r sembench_split scale_factor <<< "$entry"

  export DATASET_HUB_PATH="${sembench_split}/sf_${scale_factor}/${sembench_split}_database_${scale_factor}.duckdb"
  export QUERIES_DIR="src/queries/${sembench_split}"
  RESULTS_DIR="./results/feature_ablations/${sembench_split}"

  for model_name in "${MODELS[@]}"; do
    set_model_config ${model_name}
    start_vllm ${model_path}

    for system_entry in "${SYSTEMS[@]}"; do
      IFS=':' read -r system n_parallel enable_cascade_filter enable_early_exit enable_constrained_decoding <<< "$system_entry"
      n_parallel="${n_parallel:-64}"
      enable_cascade_filter="${enable_cascade_filter:-true}"
      enable_early_exit="${enable_early_exit:-true}"
      enable_constrained_decoding="${enable_constrained_decoding:-true}"
        out_label="${system}"
#        out_label+="_sf${scale_factor}"
        [[ -n "$n_parallel" ]]           && out_label+="_np${n_parallel}"
        [[ -n "$enable_cascade_filter" ]] && out_label+="_cf${enable_cascade_filter}"
        [[ -n "$enable_constrained_decoding" ]] && out_label+="_cd${enable_constrained_decoding}"
        [[ -n "$enable_early_exit" ]] && out_label+="_ee${enable_early_exit}"

      for run in $(seq 0 $((N_RUNS - 1))); do
        out_dir="${RESULTS_DIR}/${model_name}/${out_label}"
        mkdir -p "$out_dir"
        echo "Running ${system} sf${scale_factor} run_${run}..."
        MODEL_NAME_OR_PATH="$model_path" \
        BASE_URL="$base_url" \
        EXTRA_BODY="$extra_body" \
        OUTPUT_PATH="${out_dir}/run_${run}.csv" \
        OFFLINE_MODE=$OFFLINE_MODE \
        SEMBENCH_SPLIT=$sembench_split \
        N_PARALLEL="${n_parallel}" \
        ENABLE_CONSTRAINED_DECODING="${enable_constrained_decoding}" \
        ENABLE_CASCADE_FILTER="${enable_cascade_filter}" \
        ENABLE_EARLY_EXIT="${enable_early_exit}" \
        ./src/eval_scripts/eval_${system}.py
      done
    done

    pkill vllm
    while pgrep vllm > /dev/null; do
      sleep 1
    done

    echo "Aggregating results..."
    SEMBENCH_SPLIT=${sembench_split} python ./src/aggregate_results.py "${RESULTS_DIR}/${model_name}"
  done

  if [[ "$SMOKE" != "1" ]]; then   # plotting needs a full run; skip it for the 2-query smoke
    echo "Creating plot..."
    if [ "$sembench_split" = "movie" ] || [ "$sembench_split" = "ecomm" ] || [ "$sembench_split" = "mmqa" ] || [ "$sembench_split" = "wildlife" ] || [ "$sembench_split" = "cars" ]; then
      IS_COMPARABLE_TO_ORIGINAL_SEMBENCH=1
    else
      IS_COMPARABLE_TO_ORIGINAL_SEMBENCH=0
    fi

    RESULTS_DIR="$RESULTS_DIR" OFFLINE_MODE=$OFFLINE_MODE \
      IS_COMPARABLE_TO_ORIGINAL_SEMBENCH=$IS_COMPARABLE_TO_ORIGINAL_SEMBENCH \
      SEMBENCH_SPLIT=${sembench_split} \
      ./src/plot.py
  fi
done