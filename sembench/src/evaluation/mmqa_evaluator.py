"""Evaluator for the MMQA dataset."""

import json
import shutil
from typing import Union

import pandas as pd

from .generic_evaluator import (
    GenericEvaluator,
    QueryMetricAggregation,
    QueryMetricRetrieval,
    QueryMetricRank,
)


def compute_metrics(results: list, ground_truth: Union[set, list]):
    tp = 0
    fp = 0

    for item in results:
        if item in ground_truth:
            tp += 1
        else:
            fp += 1

    assert tp + fp == len(
        results
    ), "True Positives and False Positives do not match the results length."
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / len(ground_truth) if len(ground_truth) > 0 else 0.0
    f1_score = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return QueryMetricRetrieval(precision, recall, f1_score)


class MMQAEvaluator(GenericEvaluator):

    def evaluate_single_query(
        self, query_id: int, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> "QueryMetricRetrieval | QueryMetricAggregation | QueryMetricRank":
        """Evaluate a single query based on its type."""
        evaluate_fn = self._discover_evaluate_impl(query_id)
        return evaluate_fn(system_results, ground_truth)

    def _evaluate_q1(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        pred_results = [i.strip().lower() for i in system_results['director'].tolist()]
        gt_results = [i.strip().lower() for i in ground_truth['director'].tolist()]
        return compute_metrics(pred_results, gt_results)

    def _evaluate_q2(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if "uri" in system_results.columns:  # for BigQuery
            system_results.rename(columns={"uri": "image_id"}, inplace=True)
        if "filename" in system_results.columns:  # for Palimpzest
            system_results.rename(
                columns={"filename": "image_id"}, inplace=True
            )
        elif "local_image_path" in system_results.columns:
            system_results.rename(columns={"local_image_path": "image_id"}, inplace=True)

        pred_results = set()
        for _, row in system_results.iterrows():
            image_id = row["image_id"].split("/")[-1]
            image_id = image_id.replace("%2e", ".")

            if len(row) == 2:
                pred_results.add((row["ID"], image_id))
            elif len(row) == 3:
                pred_results.add(
                    (
                        row["ID"],
                        image_id,
                        str(row["color"]).strip().lower(),
                    )
                )
            else:
                raise ValueError(
                    f"Unexpected number of columns: {len(row)} in the results."
                )
        gt_results = ground_truth.to_records(index=False).tolist()
        return compute_metrics(pred_results, gt_results)

    def _evaluate_q3(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        pred_results = system_results["title"].tolist()
        gt_results = ground_truth["title"].tolist()

        return compute_metrics(pred_results, gt_results)

    def _evaluate_q4(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        pred_results = []
        for _, row in system_results.iterrows():
            genre = row["genre"].strip().lower()

            for movie in row["movies_in_genre"].split(","):
                pred_results.append((genre, movie.strip().lower()))

        gt_results = set()
        for _, row in ground_truth.iterrows():
            genre = row["genre"].strip().lower()
            for movie in row['movies']:
                gt_results.add((genre.strip().lower(), movie.strip().lower()))

        return compute_metrics(pred_results, gt_results)

    def _evaluate_q5(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        pred_results = []
        for _, row in system_results.iterrows():
            if "_output" in row:
                pred_results.append(row["_output"].strip().lower())
            elif "actor" in row:
                pred_results.append(row["actor"].strip().lower())
            else:
                raise ValueError(
                    "Expected either '_output' or 'actor' column in the results."  # noqa: E501
                )
        gt_results = [i.strip().lower() for i in ground_truth['actor'].tolist()]

        return compute_metrics(pred_results, gt_results)

    def _evaluate_q6(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        pred_results = [i.strip().lower() for i in system_results.get("Airlines", [])]
        gt_results = [i.strip().lower() for i in ground_truth['Airlines'].tolist()]

        return compute_metrics(pred_results, gt_results)

    def _evaluate_q7(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if "uri" in system_results.columns:  # for BigQuery
            system_results.rename(columns={"uri": "image_id"}, inplace=True)
        if "filename" in system_results.columns:  # for Palimpzest
            system_results.rename(
                columns={"filename": "image_id"}, inplace=True
            )
        elif 'local_image_path' in system_results.columns:
            system_results.rename(columns={"local_image_path": "image_id"}, inplace=True)

        pred_results = set()
        for _, row in system_results.iterrows():
            image_id = row["image_id"].split("/")[-1]
            image_id = image_id.replace("%2e", ".")
            pred_results.add((row["Airlines"], image_id))

        gt_results = ground_truth.to_records(index=False).tolist()
        return compute_metrics(pred_results, gt_results)