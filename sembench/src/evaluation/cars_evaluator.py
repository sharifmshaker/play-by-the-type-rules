"""
Created on Jun 28, 2025

@author: OlgaOvcharenko
"""

import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

from .generic_evaluator import (
    GenericEvaluator,
    QueryMetricRetrieval,
    QueryMetricAggregation,
)


class CarsEvaluator(GenericEvaluator):
    """Evaluator for the cars benchmark using the reusable framework."""

    def evaluate_single_query(
        self,
        query_id: int,
        system_results: pd.DataFrame,
        ground_truth: pd.DataFrame,
    ) -> "QueryMetricRetrieval | QueryMetricAggregation":
        evaluate_fn = self._discover_evaluate_impl(query_id)
        return evaluate_fn(system_results, ground_truth)

    def _evaluate_q1(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "car_id"
        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q2(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "car_id"
        system_results = system_results.drop_duplicates()
        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q3(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "vin"

        correct_ids_ix = ground_truth[id_column].isin(system_results[id_column].to_list())
        correct_ids = ground_truth.loc[correct_ids_ix, :]
        if correct_ids.empty:
            n_to_sample = min(10, len(ground_truth))
            ground_truth_sample = ground_truth.sample(n=n_to_sample, random_state=42) if n_to_sample > 0 else ground_truth
        elif correct_ids.shape[0] < 10:
            false_cases = ground_truth[~correct_ids_ix]
            n_to_sample = min(10 - correct_ids.shape[0], len(false_cases))
            ground_truth_sample = pd.concat([correct_ids, false_cases.sample(n=n_to_sample, random_state=42)]) if n_to_sample > 0 else correct_ids
        else:
            ground_truth_sample = correct_ids

        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth_sample, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth_sample, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q4(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricAggregation:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        return self._generic_aggregation_evaluation(system_results, ground_truth)

    def _evaluate_q5(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricAggregation:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        return self._generic_aggregation_evaluation(system_results, ground_truth)

    def _evaluate_q6(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "car_id"
        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q7(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "car_id"
        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q8(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "car_id"

        correct_ids_ix = ground_truth[id_column].isin(system_results[id_column].to_list())
        correct_ids = ground_truth.loc[correct_ids_ix, :]
        if correct_ids.empty:
            n_to_sample = min(100, len(ground_truth))
            ground_truth_sample = ground_truth.sample(n=n_to_sample, random_state=42) if n_to_sample > 0 else ground_truth
        elif correct_ids.shape[0] < 100:
            false_cases = ground_truth[~correct_ids_ix]
            n_to_sample = min(100 - correct_ids.shape[0], len(false_cases))
            ground_truth_sample = pd.concat([correct_ids, false_cases.sample(n=n_to_sample, random_state=42)]) if n_to_sample > 0 else correct_ids
        else:
            ground_truth_sample = correct_ids

        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth_sample, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth_sample, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q9(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        id_column = "car_id"
        precision = GenericEvaluator.compute_accuracy_score("precision", ground_truth, system_results, id_column=id_column).accuracy
        recall = GenericEvaluator.compute_accuracy_score("recall", ground_truth, system_results, id_column=id_column).accuracy
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)

    def _evaluate_q10(
        self, system_results: pd.DataFrame, ground_truth: pd.DataFrame
    ) -> QueryMetricRetrieval:
        if len(system_results.columns) > 0:
            system_results.columns = system_results.columns.str.lower()
        if "problem_category" in system_results.columns:
            system_results["problem_category"] = system_results["problem_category"].apply(
                lambda x: str(x).lower().replace("\n", ""))

        id_column = "car_id"
        result_column = "problem_category"
        gt = ground_truth.sort_values(id_column)[result_column]
        query = system_results.sort_values(id_column)[result_column]

        (precision, recall, f1, _) = precision_recall_fscore_support(gt, query, average="macro")
        return QueryMetricRetrieval(precision=precision, recall=recall, f1_score=f1)
