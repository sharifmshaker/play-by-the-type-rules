#!/usr/bin/env python3
"""
glue.py — fold SemBench's aggregated results into decide.py's input format.

SemBench's aggregate_results.py writes, per split (and per model dir), an
`all_results_with_runs.csv` with columns including:
    system_name, query_name, run, quality, latency, input_tokens, output_tokens
One such file can contain SEVERAL configs (system_name distinguishes them, e.g.
the CD-on and CD-off runs from run.sh land in the same file).

This normalizes one such file into decide.py's long format
    config, scenario, query, run, quality
and appends to a shared probe_long.csv (dedup on config/scenario/query/run).
Run it once per (file, config) you want in the comparison.

Examples
--------
# Gemma side (pick the CD-OFF variant out of the combined file, label it cleanly):
python glue.py --file results/feature_ablations/movie/gemma_e4b/all_results_with_runs.csv \
    --scenario movie --filter-system cdfalse --config gemma_e4b_nocd

# Gemini Flash-Lite side (its own dir; single config):
python glue.py --file results/gemini/gemini-3.1-flash-lite/movie/all_results_with_runs.csv \
    --scenario movie --config flash_lite_nocd

Repeat per scenario (movie/mmqa/ecomm). Then:
    python decide.py --gemma gemma_e4b_nocd --flashlite flash_lite_nocd
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, help="path to an all_results_with_runs.csv")
    ap.add_argument("--scenario", required=True, help="movie | mmqa | ecomm | cars | wildlife")
    ap.add_argument("--config", default=None,
                    help="clean config label for decide.py; default = the system_name value")
    ap.add_argument("--filter-system", default=None,
                    help="keep only rows whose system_name CONTAINS this substring "
                         "(e.g. 'cdfalse' to pick the CD-off variant)")
    ap.add_argument("--out", default="results/probe_long.csv")
    a = ap.parse_args()

    df = pd.read_csv(a.file)
    need = {"system_name", "query_name", "run", "quality"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"{a.file} missing columns {missing}; has {list(df.columns)}")

    if a.filter_system:
        df = df[df["system_name"].astype(str).str.contains(a.filter_system, na=False)]
        if df.empty:
            raise SystemExit(f"no rows with system_name containing {a.filter_system!r}. "
                             f"Available: {sorted(pd.read_csv(a.file)['system_name'].unique())}")

    df = df.dropna(subset=["quality"]).copy()
    df["scenario"] = a.scenario
    df["config"] = a.config if a.config else df["system_name"]
    tidy = df.rename(columns={"query_name": "query"})[
        ["config", "scenario", "query", "run", "quality"]]

    out = Path(a.out)
    added = len(tidy)
    if out.exists():
        tidy = pd.concat([pd.read_csv(out), tidy], ignore_index=True)
        tidy = tidy.drop_duplicates(subset=["config", "scenario", "query", "run"], keep="last")
    out.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(out, index=False)
    print(f"+{added} rows from {a.file}  ->  {out} (now {len(tidy)} rows, "
          f"configs={sorted(tidy['config'].unique())})")


if __name__ == "__main__":
    main()
