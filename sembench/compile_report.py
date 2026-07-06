#!/usr/bin/env python3
"""
compile_report.py — roll up every run into one quality / latency / cost report.

Auto-discovers all aggregated outputs the harness produced:
  * Gemini (API):  results/gemini/<model>/<scenario>/all_results_with_runs.csv
  * Gemma (local): results/feature_ablations/<scenario>/<model>/all_results_with_runs.csv

For each (model, CD-config, scenario) it reports, averaged over runs:
  - quality       (the [0,1] score aggregate_results.py computed)
  - latency/query (mean wall-clock per query)
  - $ cost/run    (API: token pricing via costs.py; local: GPU-hours x rate)
  - errored-query count (rate-limit / other failures — flags compromised data)

Then prints a quality pivot (scenario x model/config) and a per-config rollup,
and writes a tidy long-format CSV. Run from the sembench/ directory.

Usage:  python compile_report.py [--gpu-rate 0.31] [--out results/report.csv]
"""
from __future__ import annotations
import argparse
import glob
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from costs import api_cost, gemma_cost, PRICING  # noqa: E402


def _cd(system_name: str) -> str:
    """CD-on / CD-off, parsed from either side's config label."""
    m = re.search(r"cd(true|false)", str(system_name))
    return {"true": "CD-on", "false": "CD-off"}.get(m.group(1)) if m else "?"


def discover():
    """Yield (side, model, scenario, path) for every results file present."""
    for f in glob.glob("results/gemini/*/*/all_results_with_runs.csv"):
        p = f.split(os.sep)
        yield ("api", p[-3], p[-2], f)       # results/gemini/<model>/<scenario>/...
    for f in glob.glob("results/feature_ablations/*/*/all_results_with_runs.csv"):
        p = f.split(os.sep)
        yield ("local", p[-2], p[-3], f)     # results/feature_ablations/<scenario>/<model>/...


def summarize(side, model, scenario, path, gpu_rate):
    df = pd.read_csv(path)
    if "quality" not in df.columns or "system_name" not in df.columns:
        return []
    df["quality"] = pd.to_numeric(df["quality"], errors="coerce")
    df["latency"] = pd.to_numeric(df.get("latency"), errors="coerce")
    rows = []
    for sysname, g in df.groupby("system_name"):
        n_runs = g["run"].nunique() if "run" in g.columns else 1
        n_runs = max(n_runs, 1)
        errs = int(g["error"].notna().sum()) if "error" in g.columns else 0
        tin = pd.to_numeric(g.get("input_tokens"), errors="coerce").fillna(0).sum()
        tout = pd.to_numeric(g.get("output_tokens"), errors="coerce").fillna(0).sum()
        if side == "api":
            cost_run = (api_cost(model, tin, tout).total / n_runs
                        if model in PRICING else float("nan"))
        else:  # local: GPU wall-time cost
            cost_run = gemma_cost(g["latency"].fillna(0).sum(), gpu_rate) / n_runs
        rows.append(dict(
            side=side, model=model, cd=_cd(sysname), scenario=scenario,
            n_runs=n_runs, n_q=g["query_name"].nunique(), errors=errs,
            quality=g["quality"].mean(), latency_s=g["latency"].mean(),
            in_tok=int(tin), out_tok=int(tout), cost_run=cost_run,
        ))
    return rows


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gpu-rate", type=float, default=0.31,
                    help="USD/hr for local GPU cost (default 0.31 ~ spot RTX 4090)")
    ap.add_argument("--out", default="results/report.csv")
    args = ap.parse_args()

    recs = []
    for side, model, scenario, path in discover():
        recs += summarize(side, model, scenario, path, args.gpu_rate)
    if not recs:
        sys.exit("No results found under results/. Run at least one scenario first.")
    rep = pd.DataFrame(recs).sort_values(["side", "model", "cd", "scenario"])
    rep["cfg"] = rep["model"] + " / " + rep["cd"]

    line = "=" * 92
    print(line + "\nPER model / CD-config / scenario\n" + line)
    det = rep.copy()
    for c, r in (("quality", 3), ("latency_s", 1), ("cost_run", 4)):
        det[c] = det[c].round(r)
    print(det[["model", "cd", "scenario", "n_runs", "n_q", "errors",
               "quality", "latency_s", "cost_run"]].to_string(index=False))

    bad = rep[rep["errors"] > 0]
    if len(bad):
        print("\n⚠️  COMPROMISED configs (errored queries — re-run with RESUME=1 before trusting):")
        print(bad[["model", "cd", "scenario", "errors"]].to_string(index=False))

    print("\n" + line + "\nQUALITY  (scenario x model/config), equal-weighted overall\n" + line)
    piv = rep.pivot_table(index="scenario", columns="cfg", values="quality")
    piv.loc["** overall **"] = piv.mean()
    print(piv.round(3).to_string())

    print("\n" + line + "\nROLLUP per model/config (across scenarios present)\n" + line)
    roll = rep.groupby("cfg").agg(
        scenarios=("scenario", "nunique"),
        mean_quality=("quality", "mean"),
        cost_per_full_run=("cost_run", "sum"),  # $ for one pass over all scenarios present
    ).round({"mean_quality": 3, "cost_per_full_run": 4})
    print(roll.to_string())

    rep.drop(columns=["cfg"]).to_csv(args.out, index=False)
    print(f"\nSaved tidy long-format report to {args.out}")


if __name__ == "__main__":
    main()
