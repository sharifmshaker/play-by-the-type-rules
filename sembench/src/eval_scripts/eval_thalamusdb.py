#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = "==3.12"
# dependencies = ["thalamusdb==0.1.15", "huggingface_hub"]
# ///

import tdb.operators.semantic_filter
from tdb.execution.counters import LLMCounters
import litellm
from litellm import completion


def make_llama_compatible(config):
    """
    Convert OpenAI multi-part content format to llama-cpp-server compatible format.

    Args:
        config: Dictionary containing the API configuration and messages

    Returns:
        Modified dict with compatible message format
    """
    # Create a deep copy to avoid modifying the original
    new_config = config.copy()

    if "messages" in new_config:
        new_messages = []
        for message in new_config["messages"]:
            new_message = message.copy()
            # Check if content is a list (multi-part format)
            if isinstance(new_message.get("content"), list):
                # Extract and concatenate all text parts
                text_parts = []
                for part in new_message["content"]:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                # Join with newline or space (you can adjust the separator)
                new_message["content"] = "\n".join(text_parts)
            new_messages.append(new_message)
        new_config["messages"] = new_messages
    return new_config


def _modified_filter_completion_wrapper(item_text, kwargs):
    """Invoke completion function with given keyword arguments.

    Args:
        item_text (str): Text representation of the item.
        kwargs (dict): Keyword arguments for the completion function.

    Returns:
        tuple: (item_text, kwargs, LLM response).
    """
    # Ensure parameters are dropped for logging where applicable
    litellm.drop_params = True
    kwargs["supports_system_message"] = False
    response = completion(**make_llama_compatible(kwargs))
    # ThalamusDB does this on their filter:
    # `results.append((item_text, result == '1'))`
    # Many times small models will add a leading/trailing newline, making this equality wrong.
    # We patch that here.
    model_response = response.choices[0].message.content
    response.choices[0].message.content = model_response.strip()
    return item_text, kwargs, response


tdb.operators.semantic_filter._filter_completion_wrapper = (
    _modified_filter_completion_wrapper
)

from tdb.operators.semantic_join import BatchJoin


class CustomBatchJoin(BatchJoin):
    def _find_matches(self, pairs):
        """Finds pairs satisfying the join condition.

        Args:
            pairs: List of key pairs to check for matches.

        Returns:
            list: List of key pairs that satisfy the join condition.
        """
        # Get list of unique keys from both tables
        left_keys = sorted(set(left_key for left_key, _ in pairs))
        right_keys = sorted(set(right_key for _, right_key in pairs))
        # Prepare the items for the LLM prompt
        left_items = [self._encode_item(left_key) for left_key in left_keys]
        right_items = [self._encode_item(right_key) for right_key in right_keys]
        # If there are no keys, return empty list
        nr_left_items = len(left_items)
        nr_right_items = len(right_items)
        if nr_left_items == 0 or nr_right_items == 0:
            return []
        # Construct prompt for LLM
        prompt = self._create_prompt(left_items, right_items)
        messages = [prompt]
        base = self._best_model_args(messages)["join"]
        kwargs = {**base, "messages": messages}
        litellm.drop_params = True
        kwargs["supports_system_message"] = False
        response = completion(**make_llama_compatible(kwargs))
        model = kwargs["model"]
        self.update_cost_counters(model, response)
        matching_keys = []
        try:
            matching_keys = self._extract_matches(left_keys, right_keys, response)
        except:
            print("Incorrect output format in LLM reply - continuing join.")
            # traceback.print_exc()

        return matching_keys


tdb.operators.semantic_join.BatchJoin = CustomBatchJoin

import json
import pandas as pd
import time
import duckdb
from contextlib import contextmanager, nullcontext
import os
import sys

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

from tdb.data.relational import Database
from tdb.execution.constraints import Constraints
from tdb.execution.engine import ExecutionEngine
from tdb.queries.query import Query

from src.database_utils import iter_queries, fetch_from_hub
from src.gpu_util_tracker import track_gpu
from src.config import DUCKDB_SEED, THALAMUS_CONFIG_PATH

if __name__ == "__main__":
    model_name_or_path = os.environ["MODEL_NAME_OR_PATH"]
    base_url = os.environ["BASE_URL"]
    has_gpu = os.environ.get("HAS_GPU", "false") == "true"
    output_path = os.environ["OUTPUT_PATH"]
    dataset_hub_path = os.environ["DATASET_HUB_PATH"]
    offline_mode = os.getenv("OFFLINE_MODE", '0') == '1'
    n_parallel = int(os.environ["N_PARALLEL"])

    print(f"{output_path=}, {model_name_or_path=}, {base_url=}, {has_gpu=}, {dataset_hub_path=}")

    litellm.drop_params = True

    with duckdb.connect(dataset_hub_path if offline_mode else fetch_from_hub(dataset_hub_path), read_only=True) as con:
        con.execute(f"SELECT setseed({DUCKDB_SEED})")
        print("~~~~~ Running thalamusdb eval ~~~~~")

        ########### Prepare database + model ###########
        import rich.console

        # Disable all Rich console output
        rich.console.Console.is_terminal = False

        class CustomDatabase(Database):
            def __init__(self, con):
                self.con = con
                self.db_path = "N.A."

        #################################################

        # Create model configuration file
        tdb_model_name = f"hosted_vllm/{model_name_or_path}"
        with open(THALAMUS_CONFIG_PATH, "w") as f:
            json.dump(
                {
                    "models": [
                        {
                            "modalities": ["text"],
                            "priority": 10,
                            "kwargs": {
                                "filter": {
                                    "model": tdb_model_name,
                                    "api_base": base_url,
                                    "api_key": "N.A.",
                                    "max_tokens": 1,
                                    # "reasoning_effort": "disable",
                                },
                                "join": {
                                    "model": tdb_model_name,
                                    "api_base": base_url,
                                    "api_key": "N.A.",
                                    "stop": ["."],
                                    # "reasoning_effort": "disable",
                                },
                            },
                        }
                    ]
                },
                f,
            )

        # Initialize ThalamusDB components
        db = CustomDatabase(con)
        engine = ExecutionEngine(
            db=db,
            dop=n_parallel,
            model_config_path=THALAMUS_CONFIG_PATH,
        )
        constraints = Constraints(
            max_calls=10000000000000000000000000000,
            max_seconds=10000000000000000000000000000,
            max_tokens=10000000000000000000000000000,
        )

        # Run queries
        results = []
        for query_file, query_name in iter_queries("thalamusdb"):
            query = open(query_file).read()
            start = time.time()
            with suppress_stdout():
                with (track_gpu() if has_gpu else nullcontext()) as gpu_data:
                    start = time.perf_counter()
                    query = Query(db, query)
                    result, counters = engine.run(query, constraints)
                    latency = time.perf_counter() - start
            model_counter: LLMCounters = counters.model2counters[tdb_model_name]
            results.append(
                {
                    "system_name": "thalamusdb",
                    "query_name": query_name,
                    "latency": latency,
                    "gpu_usage": gpu_data,
                    "prediction": result.to_json(orient="split", index=False),
                    "num_generation_calls": model_counter.LLM_calls,
                    "output_tokens": model_counter.output_tokens,
                    "input_tokens": model_counter.input_tokens,
                }
            )
    pd.DataFrame(results).to_csv(output_path)
