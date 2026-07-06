# Setup & run — Gemini vs. local Gemma on SemBench (fork workflow)

**Scope:** `movie`, `mmqa`, `ecomm`. Audio (`cars`, `wildlife`) is out of scope.
**Image queries are also not runnable** — the HF database repo ships only the
`.duckdb` files, not the image binaries they reference (paths like
`files/mmqa/data/sf_200/images/*.jpg`), so multimodal queries hit `FileNotFoundError`.
Use **`--text-only`** on both runners to skip them; that leaves **22 text queries**
(movie ×10, mmqa ×8, ecomm ×4) — also where the paper's open-weight advantage is
strongest. See `CONSIDERATIONS.md` for the full risk register.

## 0. Prerequisites
- **`uv`** — eval scripts run via a `uv run --script` shebang: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- **Gemma side:** a CUDA GPU (24GB 4090 or rented A100 is comfortable; E4B is small), plus **`vllm`** installed (`uv pip install vllm`; **not** in `requirements.txt`). Needs a working `nvidia-smi`.
- **Gemini side:** `GEMINI_API_KEY`, network, no GPU. **Tier 1 is enough to start** — the text pass at `N_PARALLEL=16` completed clean (0 rate-limit errors); watch the `error` column and move to Tier 2 only if you see 429s. No Batch discount (BlendSQL makes live streaming calls → sync pricing). Set a project spend cap at aistudio.google.com/spend.
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
Both runners have a `--smoke` flag: **1 run, movie+mmqa, only `Q1` (text) + `Q2a`
(image)** — the cheapest queries that still exercise both modalities (it avoids the
pricey mmqa `Q7`), writing to `results/smoke/`. Run the **Gemini side on your laptop
first** (off the GPU clock) — it validates HF download, DB open, image handling,
token accounting, and quality computation for pennies.
```bash
MODEL=gemini-3.1-flash-lite bash run_gemini.sh --smoke    # laptop, no GPU
```
**Check before scaling up:** the output CSV has **non-zero `input_tokens`/`output_tokens`**
(else Gemini isn't returning usage and cost can't be computed from data), the `Q2a`
image query didn't error, and `all_results_with_runs.csv` has a non-null `quality`.
Then confirm the GPU side serves and loads the model:
```bash
bash run.sh --smoke                                        # GPU box: gemma_e4b via vLLM
```
No config to revert — `--smoke` sets everything via env and leaves your real config untouched.

## 4. Phase 1 — the probe (text only; ~30–45 min/side; ~$16 Gemini)
```bash
cd sembench
# Gemma side (stock run.sh) — edit its config block:
#   SCENARIO_SCALE_ENTRIES=("movie:2000" "mmqa:200" "ecomm:500")
#   N_RUNS=3
#   MODELS=("gemma_e4b")
#   SYSTEMS=("blendsql:64:true:true:false" "blendsql:64:true:true:true")
bash run.sh --text-only
# Gemini Flash-Lite side (laptop is fine):
MODEL=gemini-3.1-flash-lite N_RUNS=3 CONSTRAINED=false bash run_gemini.sh --text-only
```
**Do `N_RUNS=1` first** and confirm the `error` column is empty (no 429s) before the
3-run pass — latency is only trustworthy from an un-throttled run.
Runs are **resilient**: a failing query is logged (`error` column) and scored 0 instead
of crashing, and each query is checkpointed to CSV. If a run is interrupted or some
queries hit a rate limit, re-invoke with `RESUME=1` — it re-runs the **failed** queries
(not just missing ones) and keeps the successful ones.

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

## Compile the report (anytime)
`decide.py` answers the one pairwise question; `compile_report.py` rolls up **everything**
into the final report. It auto-discovers every `all_results_with_runs.csv` in both trees:
```bash
python compile_report.py            # prints tables + writes results/report.csv
```
It prints a per-`model × CD-config × scenario` table (with an **`errors` column** that
flags rate-limited / compromised configs), a **scenario × config quality pivot** (your
Gemma-vs-Gemini head-to-head, which fills out as configs accumulate), and a per-config
cost rollup. API cost comes from `costs.py` token pricing; local (Gemma) cost from
GPU-hours × `--gpu-rate` (default $0.31/hr). Re-run it after each pass — it picks up
whatever exists. **First copy the GPU box's `results/feature_ablations/` back here**
(results are gitignored / local-only, and the Gemma runs happen on a different machine).

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
**Measured** (text-only, Flash-Lite): **~$5.3 per run** — driven by ~21M input tokens
(long review/product text × many rows), so a **3-run Gemini side ≈ ~$16**. 3 Flash is
~2× the token price plus thinking tokens (≈ $32+ for 3 runs). Gemma side is GPU-time only
(~$1–5). Adding image scenarios later would increase all of these. `compile_report.py`
reports the real per-run cost from the logged tokens.

## Caveats
- **After the Gemma run, run `python gpu_check.py`** — it reads the logged GPU
  utilization and tells you (latency-weighted) whether the heavy queries were
  **GPU-bound** (latency trustworthy) or **client/CPU-bound** (latency reflects
  BlendSQL orchestration, not the GPU → use a stronger CPU or lower `N_PARALLEL`).
  Report CPU **and** GPU specs with any latency claim. See `CONSIDERATIONS.md`.
- `run_gemini.sh` is reconciled against the real `run.sh`/`eval_blendsql.py`, but
  still **smoke-test one scenario** before a full sweep.
- 55 queries are noisy → keep `N_RUNS≥3`; `decide.py` treats ±0.02 as a tie.
- Re-check `costs.py::PRICING` against the live pricing page — Gemini pricing drifts.
