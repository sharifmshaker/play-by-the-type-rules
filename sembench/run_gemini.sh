#!/usr/bin/env bash
# run_gemini.sh — Gemini side of the probe, through SemBench's eval_blendsql.py,
# with NO vLLM server. Env contract reconciled against the real run.sh /
# eval_blendsql.py. Run from inside the sembench/ directory.
#
# Prereqs: `uv` installed (eval_blendsql.py uses a uv-run shebang), GEMINI_API_KEY,
# and the ambient python env from `uv pip install -r requirements.txt` (aggregate
# step uses plain `python`).
set -euo pipefail

SMOKE=0
for arg in "$@"; do
  case "$arg" in
    --smoke) SMOKE=1 ;;
    -h|--help)
      echo "usage: [MODEL=.. N_RUNS=.. CONSTRAINED=.. N_PARALLEL=.. OUTDIR=.. RESUME=1] bash run_gemini.sh [--smoke]"
      echo "  --smoke : 1 run over movie+mmqa, queries Q1 (text) + Q2a (image) only — cheap validation"
      exit 0 ;;
    *) echo "unknown arg: $arg (try --help)" >&2; exit 2 ;;
  esac
done

export PYTHONPATH="$(pwd):${PYTHONPATH:-}"   # eval + aggregate need repo root for `src.*`
chmod -R u+x src/eval_scripts

# --- config (override via env) ----------------------------------------------
MODEL="${MODEL:-gemini-3.1-flash-lite}"      # probe model; later gemini-3-flash-preview
N_RUNS="${N_RUNS:-3}"                          # >=3 so decide.py sees run-to-run noise
N_PARALLEL="${N_PARALLEL:-16}"                # concurrent async requests; watch Gemini RPM/RPD
CONSTRAINED="${CONSTRAINED:-false}"           # false = fair vs Gemma cd=false (grammar is vLLM-only)
OFFLINE_MODE="${OFFLINE_MODE:-0}"
OUTDIR="${OUTDIR:-results/gemini/${MODEL}}"
# Text+image scenarios only. Audio (cars, wildlife) is intentionally OUT OF SCOPE.
SCENARIO_SCALE=("movie:2000" "mmqa:200" "ecomm:500")

if [[ "$SMOKE" == "1" ]]; then
  echo "### SMOKE MODE: 1 run · movie+mmqa · Q1 (text) + Q2a (image) only ###"
  N_RUNS=1
  SCENARIO_SCALE=("movie:2000" "mmqa:200")
  export ONLY_USE="Q1,Q2a"      # movie->Q1; mmqa->Q1(text)+Q2a(image, the cheap image-path check)
  OUTDIR="results/smoke/${MODEL}"
fi

: "${GEMINI_API_KEY:?set GEMINI_API_KEY (or GOOGLE_API_KEY)}"
export HAS_GPU=false
CONFIG_LABEL="cd${CONSTRAINED}"

# --- drive ------------------------------------------------------------------
for entry in "${SCENARIO_SCALE[@]}"; do
  IFS=':' read -r split scale <<< "$entry"
  export DATASET_HUB_PATH="${split}/sf_${scale}/${split}_database_${scale}.duckdb"
  export QUERIES_DIR="src/queries/${split}"       # iter_queries() reads this
  out_dir="${OUTDIR}/${split}/${CONFIG_LABEL}"
  mkdir -p "$out_dir"
  for run in $(seq 0 $((N_RUNS - 1))); do
    echo ">>> $MODEL  $split (sf=$scale)  run $run  cd=$CONSTRAINED"
    BACKEND=gemini \
    MODEL_NAME_OR_PATH="$MODEL" \
    BASE_URL="unused-for-gemini" \
    EXTRA_BODY="" \
    OFFLINE_MODE="$OFFLINE_MODE" \
    SEMBENCH_SPLIT="$split" \
    N_PARALLEL="$N_PARALLEL" \
    ENABLE_CONSTRAINED_DECODING="$CONSTRAINED" \
    ENABLE_CASCADE_FILTER="true" \
    ENABLE_EARLY_EXIT="true" \
    RESUME="${RESUME:-0}" \
    OUTPUT_PATH="${out_dir}/run_${run}.csv" \
      ./src/eval_scripts/eval_blendsql.py       # uv-run shebang; do NOT prefix with python
  done
  echo ">>> aggregating $split -> quality"
  SEMBENCH_SPLIT="$split" python ./src/aggregate_results.py "${OUTDIR}/${split}"
done

echo "Done. Per-split quality at: ${OUTDIR}/<split>/all_results_with_runs.csv"
echo "Fold into decide.py's input with glue.py (see SETUP.md)."
