import argparse
import pandas as pd
from io import StringIO
from dataclasses import asdict
from pathlib import Path

from evaluation.evaluate import MovieEvaluator
from create_ground_truth import create_ground_truth


def extract_quality_metric(query_data: dict) -> float:
    if "f1_score" in query_data:
        return min(1.0, max(0.0, query_data["f1_score"]))
    elif "spearman_correlation" in query_data:
        corr = query_data["spearman_correlation"]
        return (corr + 1) / 2
    elif "relative_error" in query_data:
        error = query_data["relative_error"]
        return max(0.0, 1.0 - min(1.0, error))
    else:
        print(f"Warning: No quality metric found in query data, using 0.0")
        return 0.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggregate eval results from a directory of CSVs"
    )
    parser.add_argument(
        "results_dir",
        type=Path,
        help="Directory with structure: {results_dir}/{system_name}/run_N.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Where to save aggregated results (defaults to results_dir)",
    )
    return parser.parse_args()


def load_results(results_dir: Path) -> pd.DataFrame:
    """Load all CSVs from {results_dir}/{system_name}/run_N.csv into a single DataFrame."""
    dfs = []
    for system_dir in sorted(results_dir.iterdir()):
        if not system_dir.is_dir():
            continue
        system_name = system_dir.name
        for run_csv in sorted(system_dir.glob("run_*.csv")):
            run_number = int(run_csv.stem.split("_")[1])
            df = pd.read_csv(run_csv)
            df["system_name"] = system_name
            df["run"] = run_number
            dfs.append(df)
    if not dfs:
        raise ValueError(f"No CSVs found under {results_dir}")
    return pd.concat(dfs, ignore_index=True)


def main():
    args = parse_args()
    output_dir = args.output_dir or args.results_dir

    print("Loading results...")
    all_results_df = load_results(args.results_dir)
    all_results_df["raw_metrics"] = None
    all_results_df["quality"] = None

    print("Creating ground truth...")
    evaluator = MovieEvaluator()
    ground_truth_results_df = create_ground_truth()

    for query_name in all_results_df["query_name"].unique():
        print(f"Evaluating {query_name}...")
        reference = pd.read_json(
            StringIO(
                ground_truth_results_df[
                    ground_truth_results_df["query_name"] == query_name
                ]["prediction"].item()
            ),
            orient="split",
        )

        for system_name in all_results_df["system_name"].unique():
            for run_number in all_results_df[
                all_results_df["system_name"] == system_name
            ]["run"].unique():
                mask = (
                    (all_results_df["query_name"] == query_name)
                    & (all_results_df["system_name"] == system_name)
                    & (all_results_df["run"] == run_number)
                )
                _prediction = all_results_df[mask]
                if _prediction.empty:
                    continue

                prediction = pd.read_json(
                    StringIO(_prediction["prediction"].item()), orient="split"
                )
                metric_dict = asdict(
                    evaluator.evaluate_single_query(
                        int(query_name.replace("Q", "")),
                        system_results=prediction,
                        ground_truth=reference,
                    )
                )
                all_results_df.loc[mask, "raw_metrics"] = [metric_dict]
                all_results_df.loc[mask, "quality"] = extract_quality_metric(metric_dict)
                print(f"  {system_name} (run {run_number}): {metric_dict}")

    out_path = output_dir / "all_results_with_runs.csv"
    all_results_df.to_csv(out_path, index=False)
    print(f"\nSaved combined results to {out_path}")


if __name__ == "__main__":
    main()