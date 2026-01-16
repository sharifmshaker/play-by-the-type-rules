import typing as t 
import evaluate 
import pandas as pd 
from pandarallel import pandarallel

pandarallel.initialize(progress_bar=False)

def calculate_metrics(
    predictions: t.List[dict], metric: evaluate.EvaluationModule
) -> t.Tuple[dict, pd.DataFrame]:

    def _calculate_single(prediction, reference, question):
        metric_dict = {}
        if isinstance(prediction, list):
            p = prediction[0] if len(prediction) > 0 else ""
        else:
            p = prediction if prediction is not None else ""
        metric_name_to_results: t.Dict[str, float] = metric.compute(
            references=[
                {
                    "answer_text": reference,
                    "id": "",
                    "question": question,
                }
            ],
            predictions=[p],
        )  # type: ignore
        for metric_name, result in metric_name_to_results.items():
            if p == "":
                metric_dict[f"metric_{metric_name}"] = 0.0
                continue
            metric_dict[f"metric_{metric_name}"] = result
        return pd.Series(metric_dict)

    metric_df = pd.DataFrame(predictions)
    new_metric_columns = metric_df.parallel_apply(
        lambda row: _calculate_single(
            prediction=row["prediction"],
            reference=row["answer_text"],
            question=row["question"],
        ),
        axis=1,
    )  # type: ignore
    metric_df = pd.concat([metric_df, new_metric_columns], axis=1)
    executed_predictions = metric_df[pd.isna(metric_df["error"])]

    print(
        f"Total executed: {len(executed_predictions)}/{len(predictions)} (aka {len(executed_predictions) / len(predictions) * 100}%)"
    )
    print()
    aggregated_results = {}
    for exp_name, exp_df in {
        "All Predictions": metric_df,
        "Executed Predictions": executed_predictions,
    }.items():
        aggregated_results[exp_name] = {}
        aggregated_results[exp_name]["num_examples"] = len(exp_df)
        for column in metric_df.columns:
            if column.startswith("metric_"):
                avg_metric = exp_df[column].mean()
                aggregated_results[exp_name][column] = avg_metric

    return (aggregated_results, metric_df)
