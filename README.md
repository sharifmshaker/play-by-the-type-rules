# play-by-the-type-rules

Experiment code for the paper [Play by the Type Rules: Inferring Constraints for Small Language Models in Declarative Programs](https://openreview.net/pdf?id=Nv7zctYGYj). Query language implementation can be found in the [blendsql](https://github.com/parkervg/blendsql) library. 

For the HybridQA ablations with type constraints, see [hybridqa](./hybridqa).

For the SemBench benchmark, see [sembench](./sembench).

---

## This branch — `gemini-vs-gemma`: a model-isolation study

This fork extends the **SemBench** harness to hold **BlendSQL constant** and vary
**only the model** — a cheap closed API model (Gemini 3.1 Flash-Lite) vs. a local
open-weight model (Gemma E4B) — isolating the model's effect on quality, latency,
and cost. (The upstream paper never runs BlendSQL itself with a closed API model.)

| Doc | What's in it |
|-----|--------------|
| **[FINDINGS.md](./FINDINGS.md)** | Results — the headline tradeoff, the decision, and the hosted report. |
| **[EXPERIMENT_SETUP.md](./EXPERIMENT_SETUP.md)** | Runbook — how to reproduce, end to end. |
| **[UPSTREAM.md](./UPSTREAM.md)** | Exactly what this fork changes vs. upstream, and why. |
| **[CONSIDERATIONS.md](./CONSIDERATIONS.md)** | Methodology notes / risk register. |

Based on the SemBench paper *"Large Databases Need Small, Open-Weight Language
Models"* (Parker Glenn & Alfy Samuel, [arXiv:2606.31808](https://arxiv.org/abs/2606.31808)).
New code lives under [`sembench/`](./sembench): `costs.py`, `decide.py`, `glue.py`,
`compile_report.py`, `gpu_check.py`, `run_gemini.sh`, and
`src/eval_scripts/model_factory.py`.