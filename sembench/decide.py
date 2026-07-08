"""
decide.py — apply the Flash-Lite-vs-Gemma escalation rule to probe results.

DECISION RULE (agreed for this study)
-------------------------------------
Probe cheapest current closed model (Gemini Flash-Lite) vs. a local Gemma,
with constrained decoding CONTROLLED on both sides, across N runs. Then:

  * Flash-Lite significantly WORSE than Gemma  -> ESCALATE to Gemini 3 Flash.
  * Close                                       -> run 3 Flash AT LEAST ONCE.
  * Flash-Lite CONSISTENTLY better than Gemma   -> may SKIP 3 Flash.

"significantly worse"  = Gemma leads by > ESCALATE_THRESHOLD mean quality,
                         and that lead holds in a majority of runs.
"consistently better"  = Flash-Lite leads by > TIE_BAND in EVERY run.
TIE_BAND (0.02) matches the paper's tie definition; 55 queries are noisy, so
the per-run consistency check guards against escalating on variance.

INPUT
-----
A long-format CSV (default: results/probe_long.csv) with columns:
    config, scenario, query, run, quality
where `config` labels the model+setting, e.g.:
    gemma_e4b_cd, gemma_e4b_nocd, flash_lite_nocd, three_flash_nocd
For a fair read, compare configs with the SAME constrained-decoding setting
(e.g. gemma_e4b_nocd vs flash_lite_nocd), since Gemini can't enforce BlendSQL's
grammar by default. Pass --gemma and --flashlite to pick which labels to compare.

Build this CSV from SemBench's per-run outputs with merge_results() below, or
adapt to your column names — quality is produced by
sembench/src/aggregate_results.py::extract_quality_metric.
"""
from __future__ import annotations
import argparse
import sys
import pandas as pd

TIE_BAND = 0.02
ESCALATE_THRESHOLD = 0.05


def per_run_means(df: pd.DataFrame, config: str) -> pd.Series:
    """Mean quality per run for one config (averaged over all queries/scenarios)."""
    sub = df[df["config"] == config]
    if sub.empty:
        sys.exit(f"ERROR: no rows for config={config!r}. "
                 f"Available: {sorted(df['config'].unique())}")
    return sub.groupby("run")["quality"].mean()


def scenario_table(df: pd.DataFrame, gemma: str, flashlite: str) -> pd.DataFrame:
    """Mean quality per scenario for both configs, plus the gap."""
    piv = (df[df["config"].isin([gemma, flashlite])]
           .groupby(["scenario", "config"])["quality"].mean().unstack("config"))
    piv["gemma_minus_flashlite"] = piv[gemma] - piv[flashlite]
    return piv


def verdict(gemma_runs: pd.Series, flash_runs: pd.Series) -> str:
    runs = sorted(set(gemma_runs.index) & set(flash_runs.index))
    if not runs:
        return "ERROR: no overlapping run ids between the two configs."
    gaps = [gemma_runs[r] - flash_runs[r] for r in runs]          # +ve = Gemma ahead
    mean_gap = sum(gaps) / len(gaps)
    gemma_wins = sum(g > TIE_BAND for g in gaps)
    flash_wins = sum(-g > TIE_BAND for g in gaps)

    lines = [
        f"runs compared:            {runs}",
        f"per-run gap (Gemma-Flash):{[round(g, 3) for g in gaps]}",
        f"mean gap:                 {mean_gap:+.3f}  (+ = Gemma better)",
        f"runs Gemma clearly ahead: {gemma_wins}/{len(runs)}",
        f"runs Flash clearly ahead: {flash_wins}/{len(runs)}",
        "",
    ]
    if mean_gap > ESCALATE_THRESHOLD and gemma_wins > len(runs) / 2:
        lines.append(">> VERDICT: Flash-Lite is SIGNIFICANTLY WORSE than Gemma.")
        lines.append(">> ACTION:  ESCALATE — run Gemini 3 Flash to test if a stronger")
        lines.append(">>          closed model closes the gap.")
    elif flash_wins == len(runs):
        lines.append(">> VERDICT: Flash-Lite CONSISTENTLY beats Gemma (every run).")
        lines.append(">> ACTION:  You MAY skip Gemini 3 Flash. (Cost/latency/repro then")
        lines.append(">>          decide the open-vs-closed call, not quality.)")
    else:
        lines.append(">> VERDICT: Flash-Lite and Gemma are CLOSE (or mixed across runs).")
        lines.append(">> ACTION:  Run Gemini 3 Flash AT LEAST ONCE — the safer default;")
        lines.append(">>          3 Flash may beat Gemma where Flash-Lite only tied.")
    return "\n".join(lines)


def merge_results(paths_and_labels: list[tuple[str, str]]) -> pd.DataFrame:
    """Helper: stitch per-config SemBench result CSVs into the long format.

    Each SemBench run writes a CSV (OUTPUT_PATH) with at least
    [scenario/split, query, run, quality]. Column names vary slightly by
    harness version — adjust the rename map if needed.
    """
    frames = []
    for path, label in paths_and_labels:
        d = pd.read_csv(path)
        d = d.rename(columns={"split": "scenario"})
        keep = [c for c in ("scenario", "query", "run", "quality") if c in d.columns]
        d = d[keep].copy()
        d["config"] = label
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="results/probe_long.csv",
                    help="long-format CSV (config,scenario,query,run,quality)")
    ap.add_argument("--gemma", default="gemma_e4b_nocd",
                    help="config label for the Gemma side")
    ap.add_argument("--flashlite", default="flash_lite_nocd",
                    help="config label for the Gemini Flash-Lite side")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    missing = {"config", "scenario", "run", "quality"} - set(df.columns)
    if missing:
        sys.exit(f"CSV missing columns: {missing}. Have: {list(df.columns)}")

    print("=" * 66)
    print("Per-scenario mean quality")
    print("=" * 66)
    print(scenario_table(df, args.gemma, args.flashlite).round(3).to_string())
    print()
    print("=" * 66)
    print(f"Decision: {args.flashlite}  vs  {args.gemma}")
    print("=" * 66)
    print(verdict(per_run_means(df, args.gemma),
                  per_run_means(df, args.flashlite)))


if __name__ == "__main__":
    main()
