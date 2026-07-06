# Considerations & risk register

Goal: **minimize cost and avoid failed runs.** Prioritized. Items marked ✅ are
already handled in this fork; ⚠️ require an operator decision/check before running.

## Decisions locked for this project
- **Audio is out of scope.** We run only `movie`, `mmqa`, `ecomm` (text + image).
  `cars` and `wildlife` (the audio scenarios) are dropped — they're the most
  expensive and the modality where local Gemma is weakest.
- **Matched optimizer config both sides:** cascade ON, early-exit ON, vary only CD.
- **Primary comparison is CD-off vs CD-off** (BlendSQL only enforces grammar
  constraints on vLLM; the Gemini path can't, so equalize).

## P0 — would crash a run / waste spend
1. ✅ **No per-query error handling.** `eval_blendsql.py` now wraps each query in
   try/except, checkpoints to CSV after every query, and supports `RESUME=1`. A
   failed query is scored 0 (matching the paper) instead of destroying the run.
   `aggregate_results.py` similarly guards each metric computation.
2. ⚠️ **Gemini rate limits vs. call volume.** One `LLMMap` = one call per distinct
   value → hundreds/query, thousands/phase. **Be on paid Tier 2+ (10k+ RPD).** Keep
   `N_PARALLEL≤16`. Confirm retries survive 429s during the smoke test.
3. ✅ **Optimizer-config mismatch** (early-exit off on one side) — fixed: both sides
   `cascade=true, early_exit=true`. Gemma SYSTEMS = `blendsql:64:true:true:{false,true}`.
4. ✅→note **No Batch API discount.** BlendSQL makes live streaming calls, so batch
   pricing is unreachable here — budget with **sync** rates (~2× my earlier "batched"
   figures).

## P1 — validity & measurement
5. ⚠️ **Gemini multimodal** is wired in blendsql 0.1.26 (image + audio message
   parts), but the image path on Google's OpenAI-compat endpoint is unproven —
   the `mmqa` smoke test is the gate before trusting image scenarios.
6. ⚠️ **Token accounting** — if Gemini's stream omits usage, `input_tokens`/
   `output_tokens` come back 0 and cost can't be computed from data. Verify non-zero
   in the smoke test.
7. ✅ **CD fairness** — only compare `*_nocd` labels; CD-on Gemma run is for the lift, not the head-to-head.
8. ✅ **Noise** — `N_RUNS≥3`, ±0.02 tie band in `decide.py`.
9. ⚠️ **vLLM startup has no timeout** — a model that fails to load leaves the GPU
   paid-and-idle forever. Watch `/tmp/vllm.log`; E4B FP8 is small and should load fine.
10. ⚠️ **Thinking tokens** — Flash-Lite is thinking-off (cheap probe); Gemini 3 Flash
    is thinking-on (cost/latency hit) — minimize via `EXTRA_BODY` when escalating.

## P2 — scope & housekeeping
11. ✅ **Deferred/cut the expensive audio scenarios** (see decisions).
12. **Minimize the matrix:** 1 Gemma model (`gemma_e4b`) × 3 scenarios × 3 runs ×
    {CD off, CD on}. Expand only if `decide.py` says to.
13. ⚠️ **Persistent cache** — put `HF_HOME` on a persistent volume when renting so the
    DB+weights download isn't re-paid each session; run the Gemini side off-GPU. See SETUP §7.
14. ⚠️ **Ground truth must generate** — `aggregate` runs `gold_sql` live; cars Q9 is
    skipped for empty GT (moot now). The aggregate guard (item 1) prevents a stray
    empty prediction from aborting the whole aggregation.
15. **Repro hygiene** — `results/` should be git-ignored; record exact Gemini model id
    + date (pricing/behavior drift); vLLM/blendsql versions pinned.

## De-risked sequence (cheapest first)
Smoke (laptop Gemini) → smoke (GPU Gemma) → Phase 1 probe → decide → escalate to
3 Flash only if directed. Full runbook in `EXPERIMENT_SETUP.md`.
