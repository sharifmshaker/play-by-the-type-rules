"""
Created on July 27, 2025

@author: Jiale Lao

MovieEvaluator Implementation based on generic_evaluator
Uses DuckDB with ground truth SQL queries to generate reference results
"""

import pandas as pd

from .generic_evaluator import (
    GenericEvaluator,
    QueryMetricRetrieval,
    QueryMetricAggregation,
    QueryMetricRank,
)

class EcommEvaluator(GenericEvaluator):

    def evaluate_single_query(
        self, query_id: int, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> "QueryMetricRetrieval | QueryMetricAggregation | QueryMetricRank":
        """Evaluate a single query based on its type."""
        evaluate_fn = self._discover_evaluate_impl(query_id)
        print(f"Query: {query_id}")
        return evaluate_fn(system_results, ground_truth)

    def _evaluate_q1(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q2(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q3(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'adjusted-rand-index', ground_truth, system_results
        )

    def _evaluate_q4(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'adjusted-rand-index', ground_truth, system_results
        )

    def _evaluate_q5(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'adjusted-rand-index', ground_truth, system_results
        )

    def _evaluate_q6(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'adjusted-rand-index', ground_truth, system_results
        )

    def _evaluate_q7(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q8(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q9(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q10(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q11(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q12(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results, as_json=True
        )

    def _evaluate_q13(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )

    def _evaluate_q14(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ):
        return GenericEvaluator.compute_accuracy_score(
            'f1-score', ground_truth, system_results
        )