#!/usr/bin/env python3
"""
gpu_check.py — was the Gemma side GPU-bound or client/CPU-bound?

BlendSQL's per-query latency includes CPU-side orchestration (SQL parse, dedup,
prompt marshalling, output parsing, polars re-join) running on a single async
event loop. With fast local inference at high concurrency, that client work can
become the bottleneck instead of the GPU — which would make Gemma's measured
latency reflect the box's CPU, not its GPU.

The harness samples GPU utilization per query (the `gpu_usage` column, populated
only when HAS_GPU=true — i.e. the Gemma/vLLM side; the Gemini side logs None).
This reads those samples, reports mean/max GPU util per query, flags client-bound
(low-util) queries, and gives a latency-weighted verdict.

Interpretation:
  * high mean GPU util (>~70%) on the heavy queries -> GPU-bound -> latency
    reflects real inference speed; trust it.
  * low mean GPU util (<~40%) -> client/CPU-bound -> latency reflects orchestration,
    not the GPU; use a stronger CPU or lower N_PARALLEL before trusting it.

Usage:
  python gpu_check.py [--glob 'results/feature_ablations/**/run_*.csv'] [--low 40] [--high 70]
"""
from __future__ import annotations
import argparse
import glob
import re

import pandas as pd

_NUM = r"[-+]?\d*\.?\d+"


def _field(cell, key):
    """Extract a summary numeric from the stringified gpu_usage dict.

    We search only the tail so we skip the (potentially huge) per-sample list;
    the summary fields (wall_time_s, mean/max_gpu_util, mean_mem_util) sit at the
    end of the dict repr.
    """
    m = re.search(rf"'{key}':\s*({_NUM})", str(cell)[-800:])
    return float(m.group(1)) if m else float("nan")


def _np(cfg: str):
    m = re.search(r"np(\d+)", str(cfg))
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glob", default="results/feature_ablations/**/run_*.csv")
    ap.add_argument("--low", type=float, default=40.0,
                    help="mean GPU util %% below this flags a query as client-bound")
    ap.add_argument("--high", type=float, default=70.0,
                    help="latency-weighted util at/above this = GPU-bound verdict")
    args = ap.parse_args()

    files = sorted(glob.glob(args.glob, recursive=True))
    if not files:
        raise SystemExit(f"No files match {args.glob!r}. Run the Gemma side first "
                         "(gpu_usage is only logged when HAS_GPU=true).")

    rows = []
    for f in files:
        d = pd.read_csv(f)
        if "gpu_usage" not in d.columns:
            continue
        p = f.replace("\\", "/").split("/")
        # results/feature_ablations/<scenario>/<model>/<out_label>/run_N.csv
        scenario = p[2] if len(p) > 2 else "?"
        cfg = p[4] if len(p) > 4 else "?"
        for _, r in d.iterrows():
            g = r["gpu_usage"]
            if pd.isna(g) or str(g).strip() in ("", "None", "nan"):
                continue
            rows.append(dict(
                scenario=scenario, np=_np(cfg), cfg=cfg, query=r.get("query_name"),
                latency_s=pd.to_numeric(r.get("latency"), errors="coerce"),
                mean_gpu=_field(g, "mean_gpu_util"),
                max_gpu=_field(g, "max_gpu_util"),
                mean_mem=_field(g, "mean_mem_util"),
            ))
    if not rows:
        raise SystemExit("Found run CSVs but no populated gpu_usage — were these "
                         "Gemma (HAS_GPU=true) runs?")

    df = pd.DataFrame(rows)
    line = "=" * 88

    print(line + "\nPER-QUERY GPU utilization (heaviest queries first)\n" + line)
    show = df.sort_values("latency_s", ascending=False).copy()
    for c in ("latency_s", "mean_gpu", "max_gpu", "mean_mem"):
        show[c] = show[c].round(1)
    print(show[["scenario", "np", "query", "latency_s",
                "mean_gpu", "max_gpu", "mean_mem"]].to_string(index=False))

    # Latency-weighted: the latency claim rests on the heavy queries, so weight by it.
    w = df["latency_s"].fillna(0)
    wmean = (df["mean_gpu"] * w).sum() / w.sum() if w.sum() else df["mean_gpu"].mean()
    client_bound = df[df["mean_gpu"] < args.low].sort_values("latency_s", ascending=False)

    print("\n" + line + "\nVERDICT\n" + line)
    print(f"latency-weighted mean GPU util: {wmean:.1f}%")
    if len(client_bound):
        print(f"\n⚠️  {len(client_bound)} quer(y/ies) below {args.low:.0f}% GPU util "
              "(client/CPU-bound — latency reflects orchestration, not the GPU):")
        print(client_bound[["scenario", "np", "query", "latency_s", "mean_gpu"]]
              .round(1).to_string(index=False))
    if wmean >= args.high:
        print(f"\n=> GPU-BOUND (weighted util ≥ {args.high:.0f}%). Latency reflects real "
              "inference speed — trust it.")
    elif wmean < args.low:
        print(f"\n=> CLIENT/CPU-BOUND (weighted util < {args.low:.0f}%). Latency is dominated "
              "by BlendSQL orchestration, not the GPU.\n   Use a stronger CPU or lower "
              "N_PARALLEL before trusting Gemma latency.")
    else:
        print(f"\n=> MIXED ({args.low:.0f}-{args.high:.0f}%). Some heavy queries are client-bound "
              "— report CPU+GPU specs and consider a stronger CPU / lower concurrency\n   "
              "for a clean latency claim.")


if __name__ == "__main__":
    main()
