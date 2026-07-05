# Setup & run — Gemini vs. local Gemma on SemBench (fork workflow)

## 0. Prerequisites
- **`uv`** — the eval scripts run via a `uv run --script` shebang. Install it (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- **Gemma side:** a CUDA GPU (paper: 16GB RTX 5080; a 24GB 4090 or rented A100 works), `vllm`.
- **Gemini side:** `GEMINI_API_KEY`, network, no GPU. Use a **paid tier** (free tier's ~250–1000 req/day is too small); prefer the **Batch API** for full passes.
- The **aggregate** step uses plain `python`, so run inside the env from `uv pip install -r requirements.txt` (pandas/duckdb/scipy/huggingface_hub available).

## 1. Fork & clone (once)
```bash
# Fork CapitalOne-Research/play-by-the-type-rules on GitHub (button in the UI), then:
git clone https://github.com/<you>/play-by-the-type-rules
cd play-by-the-type-rules/sembench
uv pip install -r requirements.txt      # BlendSQL + deps; DuckDB data auto-downloads on first run
```

## 2. Install our enhancements into the fork (once)
From this `harness/` directory:
```bash
bash install_into_fork.sh /path/to/play-by-the-type-rules
```
This copies `costs.py`, `decide.py`, `run_gemini.sh`, and `model_factory.py` to
their real paths and applies the backend switch to `eval_blendsql.py`. Then
commit inside the fork:
```bash
cd /path/to/play-by-the-type-rules
git checkout -b gemini-vs-gemma
git add -A && git commit -m "Add Gemini backend, cost accounting, and decision harness"
```
From here everything lives in the fork — no more copying.

## 3. The fair-comparison knob (the crux — don't skip)
BlendSQL only enforces its grammar-constrained decoding on the **vLLM** backend;
the Gemini path drops it. Since constrained decoding is a large quality lever for
small models, run the **primary comparison with CD OFF on both sides**:
- Gemma: in `run.sh`, use a `SYSTEMS` entry `blendsql:64:false:false:false` (4th
  field = `constrained_decoding`). Also run `...:true` to measure CD's lift.
- Gemini: `run_gemini.sh` already sets `CONSTRAINED=false`.

## 4. Phase 1 — cheap probe (text+image; ~hours; a few $)
```bash
cd sembench
# Gemma side (stock harness): MODELS=("gemma_e4b"),
#   SYSTEMS=("blendsql:64:false:false:false" "blendsql:64:false:false:true"),
#   SCENARIO_SCALE_ENTRIES=(movie:2000 mmqa:200 ecomm:500), N_RUNS=3
./run.sh
# Gemini Flash-Lite side:
MODEL=gemini-3.1-flash-lite N_RUNS=3 CONSTRAINED=false OUTDIR=results/flash_lite \
  bash run_gemini.sh
```

## 5. Decide
Both sides auto-aggregate to `all_results_with_runs.csv` (the Gemma side via
`run.sh`'s aggregate step; the Gemini side inside `run_gemini.sh`). Fold the
relevant configs into one `results/probe_long.csv` with `glue.py` — once per
scenario per side:
```bash
# Gemma side: pick the CD-off variant out of the combined file
for s in movie mmqa ecomm; do
  python glue.py --scenario $s --config gemma_e4b_nocd --filter-system cdfalse \
    --file results/feature_ablations/$s/gemma_e4b/all_results_with_runs.csv
done
# Gemini Flash-Lite side:
for s in movie mmqa ecomm; do
  python glue.py --scenario $s --config flash_lite_nocd \
    --file results/gemini/gemini-3.1-flash-lite/$s/all_results_with_runs.csv
done
```
Then run the decision rule:
```bash
python decide.py --csv results/probe_long.csv \
    --gemma gemma_e4b_nocd --flashlite flash_lite_nocd
```
Output is one of: **ESCALATE** (run 3 Flash), **run 3 Flash at least once**
(close), or **may skip 3 Flash** (Flash-Lite consistently better).

## 6. Phase 2 — escalate if directed
```bash
MODEL=gemini-3-flash-preview N_RUNS=3 CONSTRAINED=false OUTDIR=results/three_flash \
  bash run_gemini.sh
```

## 7. Phase 3 — optional
Add audio scenarios (`cars:19672`, `wildlife:200`) — expect multimodal-compat
debugging and a Gemma quality gap on audio — and/or the Option-C Gemini
structured-output parity run.

## Cost accounting
```python
from costs import api_cost, gemma_cost
api_cost("gemini-3.1-flash-lite", input_tokens, output_tokens, batch=True)
gemma_cost(total_latency_seconds, gpu_hourly_rate=0.31)
```
Full 5-run pass, rough: Gemma **~$1–5**; Flash-Lite **~$80 batched**; 3 Flash
**~$160 batched**. Watch thinking-token billing (use Flash-Lite / `thinking_level=low`)
and audio input tokens (`audio_fraction` for cars/wildlife).

## Verify-first caveats
- `run_gemini.sh` env-var names were reconstructed from a source read of upstream
  `run.sh`/`eval_blendsql.py` — smoke-test `movie`, 1 run, before a full sweep.
- 55 queries are noisy; keep `N_RUNS≥3`. Re-check `costs.py::PRICING` vs. the live page.
