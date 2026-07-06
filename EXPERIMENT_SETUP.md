# Setup & run — Gemini vs. local Gemma on SemBench (fork workflow)

**Scope:** text + image scenarios only — `movie`, `mmqa`, `ecomm`. Audio (`cars`,
`wildlife`) is intentionally out of scope. See `CONSIDERATIONS.md` for the full
risk register behind the choices below.

## 0. Prerequisites
- **`uv`** — eval scripts run via a `uv run --script` shebang: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- **Gemma side:** a CUDA GPU (24GB 4090 or rented A100 is comfortable; E4B is small), plus **`vllm`** installed (`uv pip install vllm`; **not** in `requirements.txt`). Needs a working `nvidia-smi`.
- **Gemini side:** `GEMINI_API_KEY`, network, no GPU. **Use a paid Tier 2+** — one query fans out into hundreds of LM calls, so Tier 1's 1,500 requests/day will be exhausted fast (and there's no Batch discount here — BlendSQL makes live streaming calls, so you pay sync rates).
- **Ambient python env** (for the aggregate step, which uses plain `python`): `uv pip install -r requirements.txt` (pandas/duckdb/scipy/huggingface_hub).

## 1. Fork, clone, install (once — already done for this project)
```bash
git clone git@github.com:sharifmshaker/play-by-the-type-rules
cd play-by-the-type-rules && git checkout gemini-vs-gemma   # our branch
cd sembench && uv pip install -r requirements.txt && uv pip install vllm
export GEMINI_API_KEY=...
```
Our additions (`costs.py`, `decide.py`, `glue.py`, `run_gemini.sh`,
`model_factory.py`, the patched `eval_blendsql.py`) are already committed on the
branch. If re-bootstrapping a fresh clone, run `harness/install_into_fork.sh <clone>`.

## 2. The fair-comparison knob (the crux — don't skip)
BlendSQL enforces grammar-constrained decoding **only on the vLLM backend**; the
Gemini path drops it. It's a large quality lever for small models, so run the
**primary comparison with CD OFF on both sides**, and keep every *other* optimizer
setting identical so you're comparing models, not systems.

`run.sh`'s SYSTEMS field order is `system:n_parallel:cascade_filter:early_exit:constrained_decoding`.
Use **cascade ON, early-exit ON** (matches the paper and `run_gemini.sh`), varying only CD:
- Gemma: `"blendsql:64:true:true:false"` (CD off — the comparison) and `"blendsql:64:true:true:true"` (CD on — measures CD's lift).
- Gemini: `run_gemini.sh` sets `CONSTRAINED=false`, `ENABLE_CASCADE_FILTER=true`, `ENABLE_EARLY_EXIT=true` to match.

> Do **not** use `blendsql:64:false:false:false` — that also turns early-exit off, which makes Gemma far slower/costlier on LIMIT queries *and* breaks the apples-to-apples.

## 3. Smoke test FIRST (do this before any multi-hour/paid run)
Prove the plumbing on a tiny subset — cheap, and it catches the failure modes that
would otherwise waste GPU/API spend. Run the **Gemini side on your laptop first**
(off the GPU clock); it exercises HF download, DB open, image handling, token
accounting, and quality computation for free.
```bash
# In sembench/src/config.py set:  ONLY_USE = {"Q1"}   (restricts to one query per scenario)
# Temporarily trim run_gemini.sh SCENARIO_SCALE to ("movie:2000" "mmqa:200")   # 1 text, 1 image
MODEL=gemini-3.1-flash-lite N_RUNS=1 CONSTRAINED=false bash run_gemini.sh
```
**Check before scaling up:** the output CSV has **non-zero `input_tokens`/`output_tokens`**
(else Gemini isn't returning usage and cost can't be computed from data), the `mmqa`
image query didn't error, and `all_results_with_runs.csv` has a non-null `quality`.
Then repeat the same tiny subset on the GPU box for Gemma (`MODELS=("gemma_e4b")`,
one SYSTEMS entry, `N_RUNS=1`) to confirm vLLM serves and the model loads.
**Revert `ONLY_USE = {}` and the scenario list before Phase 1.**

## 4. Phase 1 — the probe (text+image; a few hours; a few $)
```bash
cd sembench
# Gemma side (stock run.sh) — edit its config block:
#   SCENARIO_SCALE_ENTRIES=("movie:2000" "mmqa:200" "ecomm:500")
#   N_RUNS=3
#   MODELS=("gemma_e4b")
#   SYSTEMS=("blendsql:64:true:true:false" "blendsql:64:true:true:true")
./run.sh
# Gemini Flash-Lite side (laptop is fine):
MODEL=gemini-3.1-flash-lite N_RUNS=3 CONSTRAINED=false bash run_gemini.sh
```
Runs are **resilient**: a failing query is logged (with an `error` column) and scored
0 instead of crashing the run, and each query is checkpointed to CSV. If a run dies
anyway (machine died, etc.), re-invoke with `RESUME=1` to skip completed queries.

## 5. Decide
Both sides auto-aggregate to `all_results_with_runs.csv`. Fold the relevant configs
into one `results/probe_long.csv` with `glue.py` (once per scenario per side), then
apply the rule:
```bash
for s in movie mmqa ecomm; do
  python glue.py --scenario $s --config gemma_e4b_nocd --filter-system cdfalse \
    --file results/feature_ablations/$s/gemma_e4b/all_results_with_runs.csv
  python glue.py --scenario $s --config flash_lite_nocd \
    --file results/gemini/gemini-3.1-flash-lite/$s/all_results_with_runs.csv
done
python decide.py --gemma gemma_e4b_nocd --flashlite flash_lite_nocd
```
Verdict: **ESCALATE** (run 3 Flash), **run 3 Flash at least once** (close), or
**may skip 3 Flash** (Flash-Lite consistently better).

## 6. Phase 2 — escalate if directed
```bash
MODEL=gemini-3-flash-preview N_RUNS=3 CONSTRAINED=false bash run_gemini.sh
# re-run the flash glue line with --config three_flash_nocd + the new path, then decide.py
```
3 Flash has **thinking on** (unlike Flash-Lite) → higher cost + latency. Try to
minimize it (e.g. a low `thinking_level` via `EXTRA_BODY`) and budget for it.

## 7. Persistent cache — don't re-pay the download each GPU session
First run pulls the scenario DuckDBs from HF **and** the Gemma weights via vLLM.
On a *rented* GPU that download is on the clock, and by default it's re-fetched
every time you spin up a fresh pod. Point the caches at storage that survives:

- **What to persist:** `HF_HOME` (covers both the HF datasets *and* the vLLM/HF model weights — vLLM downloads through the HF hub).
- **RunPod:** attach a **Network Volume** (persists across pods; mounts at `/workspace`). Then:
  ```bash
  export HF_HOME=/workspace/hf-cache      # datasets + model weights land here, reused next pod
  ```
  Put the cloned repo on `/workspace` too so you don't re-clone.
- **Vast.ai:** use a persistent volume / keep the instance's disk; set `export HF_HOME=/path/on/persistent/disk/hf-cache`.
- **Local GPU:** nothing to do — default `~/.cache/huggingface` already persists.
- **Verify it worked:** after run 1, `du -sh $HF_HOME` shows the cached weights+DBs; the next session should start without re-downloading.

Alternative (fully off the GPU clock): pre-download the `.duckdb` files on a cheap
CPU box / your laptop, copy them onto the volume, and run with `OFFLINE_MODE=1`
(then `DATASET_HUB_PATH` is treated as a local path, no fetch).

## 8. Cost accounting
```python
from costs import api_cost, gemma_cost
api_cost("gemini-3.1-flash-lite", input_tokens, output_tokens)  # sync pricing (no batch here)
gemma_cost(total_latency_seconds, gpu_hourly_rate=0.31)
```
Rough Phase-1 (text+image, 3 runs): Gemma **~$1–3** of GPU time; Flash-Lite **~$10–30**
sync. Escalating to 3 Flash and/or more runs scales up from there (sync rates, plus
3 Flash's thinking tokens). Full 5-run/all-scenario on 3 Flash would be **~$300+**.

## Caveats
- `run_gemini.sh` is reconciled against the real `run.sh`/`eval_blendsql.py`, but
  still **smoke-test one scenario** before a full sweep.
- 55 queries are noisy → keep `N_RUNS≥3`; `decide.py` treats ±0.02 as a tie.
- Re-check `costs.py::PRICING` against the live pricing page — Gemini pricing drifts.
