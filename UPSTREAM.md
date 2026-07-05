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
| `sembench/src/eval_scripts/eval_blendsql.py` | **Edited.** Import `make_model`; `model=VLLM(...)` → `model=make_model()`. Backend defaults to `vllm`, so upstream Gemma runs are unaffected. |
| `sembench/run_gemini.sh` | **New.** Drives the Gemini runs through the eval script without a vLLM server. |
| `sembench/costs.py` | **New.** Converts the raw token/latency logs into USD (upstream logs neither). |
| `sembench/decide.py` | **New.** Applies our Flash-Lite → 3-Flash escalation rule to results. |

We do **not** fork `blendsql` — it stays a pinned pip dependency
(`blendsql==0.1.26`). If the Option-C Gemini structured-output parity work needs
changes inside the library, fork `blendsql` separately at that point.

## Attribution
Per Apache-2.0, the upstream `LICENSE` and `NOTICE` (if any) are retained. Cite
the upstream paper and repository in any write-up of results produced here.
