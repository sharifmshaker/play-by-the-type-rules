#!/bin/bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
chmod -R u+x src/eval_scripts

# With the below on, all paths point to local files as opposed to HuggingFace datasets/models.
OFFLINE_MODE=1

RESULTS_DIR="./results"
N_RUNS=5
SYSTEMS=("blendsql" "thalamusdb" "lotus")

export DATASET_HUB_PATH="./local_data/movie_database_2000.duckdb"

declare MODEL_NAME_OR_PATH
declare BASE_URL

MODEL_NAME_OR_PATH["gemma_4b"]="/home/jovyan/model-registry/google_gemma-3-4b-it"
BASE_URL["gemma_4b"]="http://127.0.0.1:8000/v1/"

MODEL_NAME_OR_PATH["gemma_12b"]="/home/jovyan/model-registry/google_gemma-3-12b-it"
BASE_URL["gemma_12b"]="http://127.0.0.1:8000/v1/"

MODEL_NAME_OR_PATH["llama_1b"]="/home/jovyan/model-registry/meta-llama_llama-3.2-1b-instruct"
BASE_URL["llama_1b"]="http://127.0.0.1:8000/v1/"

MODEL_NAME_OR_PATH["llama_3b"]="/home/jovyan/model-registry/meta-llama_llama-3.2-3b-instruct"
BASE_URL["llama_3b"]="http://127.0.0.1:8000/v1/"

set_model_config() {
    local key=$1
    model_path="${MODEL_NAME_OR_PATH[$key]}"
    base_url="${BASE_URL[$key]}"
}

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
    --max-model-len 16000 \
    --structured-outputs-config.backend guidance \
    --gpu_memory_utilization 0.8 \
    --enable-prompt-tokens-details &

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

export HAS_GPU=has_gpu

for model_name in "gemma_4b" "gemma_12b" "llama_1b" "llama_3b"; do
  set_model_config ${model_name}
  start_vllm ${model_path}
  for system in "${SYSTEMS[@]}"; do
      for run in $(seq 0 $((N_RUNS - 1))); do
          out_dir="${RESULTS_DIR}/${model_name}/${system}"
          mkdir -p "$out_dir"
          echo "Running ${system} run_${run}..."
          MODEL_NAME_OR_PATH="$model_path" \
          BASE_URL="$base_url" \
          OUTPUT_PATH="${out_dir}/run_${run}.csv" \
          OFFLINE_MODE=$OFFLINE_MODE \
          ./src/eval_scripts/eval_${system}.py
      done
  done
  pkill vllm
    while pgrep vllm > /dev/null; do 
        sleep 1
    done
  echo "Aggregating results..."
  OFFLINE_MODE=$OFFLINE_MODE python ./src/aggregate_results.py "${RESULTS_DIR}/${model_name}" 
done

echo "Creating plot..."
RESULTS_DIR="$RESULTS_DIR" OFFLINE_MODE=$OFFLINE_MODE ./src/plot.py