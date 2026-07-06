# Relationship to upstream

This repository is a **fork of
[CapitalOne-Research/play-by-the-type-rules](https://github.com/CapitalOne-Research/play-by-the-type-rules)**
(the SemBench harness from *"Large Databases Need Small, Open-Weight Language
Models"*, Glenn & Samuel), used under its **Apache-2.0** license.

## Why the fork
The upstream paper compares `BlendSQL + local Gemma` against *other* LM-DB
systems running Gemini 2.5 Flash — it never runs BlendSQL itself with a closed
API model. This fork holds **BlendSQL constant** and varies only the model
(Gemini vs. Gemma), isolating the model effect on quality, latency, and cost.

We inherit upstream's queries, ground-truth SQL, per-scenario evaluators, and
quality normalization unchanged, so our numbers stay directly comparable to the
paper's.

## What we changed vs. upstream
| Path | Change |
|------|--------|
| `sembench/src/eval_scripts/model_factory.py` | **New.** Chooses the BlendSQL model backend (vLLM or Gemini) from a `BACKEND` env var. |
| `sembench/src/eval_scripts/eval_blendsql.py` | **Edited.** Backend switch (`model=make_model()`, defaults to vLLM); plus per-query try/except + incremental CSV checkpoint + `RESUME=1` so one failing query can't destroy a run. |
| `sembench/run_gemini.sh` | **New.** Drives the Gemini runs through the eval script without a vLLM server (`--smoke` for cheap validation). |
| `sembench/costs.py` | **New.** Converts the raw token/latency logs into USD (upstream logs neither). |
| `sembench/glue.py` | **New.** Folds `all_results_with_runs.csv` into `decide.py`'s long format. |
| `sembench/decide.py` | **New.** Applies our Flash-Lite → 3-Flash escalation rule to results. |
| `sembench/src/aggregate_results.py` | **Edited.** Guard per-query metric computation so an empty/failed prediction scores 0 instead of aborting aggregation. |
| `sembench/src/config.py` | **Edited.** `SKIP_QUERIES`/`ONLY_USE` are now env-overridable (comma-separated); empty = original behavior. Powers `run_gemini.sh --smoke`. |

We do **not** fork `blendsql` — it stays a pinned pip dependency
(`blendsql==0.1.26`). If the Option-C Gemini structured-output parity work needs
changes inside the library, fork `blendsql` separately at that point.

## Attribution
Per Apache-2.0, the upstream `LICENSE` and `NOTICE` (if any) are retained. Cite
the upstream paper and repository in any write-up of results produced here.
