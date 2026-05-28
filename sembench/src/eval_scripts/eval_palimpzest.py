#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = "==3.12"
# dependencies = ["palimpzest==1.4.0", "huggingface_hub", "duckdb"]
# ///

import palimpzest as pz
import time
import duckdb
import importlib
import importlib.util
from contextlib import nullcontext
import os
import pandas as pd

from src.config import DUCKDB_SEED
from src.database_utils import iter_queries, fetch_from_hub
from src.gpu_util_tracker import track_gpu

if __name__ == "__main__":
    model_name_or_path = os.environ["MODEL_NAME_OR_PATH"]
    base_url = os.environ["BASE_URL"]
    has_gpu = os.environ.get("HAS_GPU", "false") == "true"
    output_path = os.environ["OUTPUT_PATH"]
    dataset_hub_path = os.environ["DATASET_HUB_PATH"]
    offline_mode = os.getenv("OFFLINE_MODE", '0') == '1'
    sembench_split = os.environ["SEMBENCH_SPLIT"]
    n_parallel = int(os.environ["N_PARALLEL"])

    print(f"{output_path=}, {model_name_or_path=}, {base_url=}, {has_gpu=}, {dataset_hub_path=}")

    import litellm

    original_completion = litellm.completion

    def patched_completion(*args, **kwargs):
        litellm.drop_params = True
        kwargs["supports_system_message"] = False

        return original_completion(*args, **kwargs)

    # Replace the completion function with your patched version
    litellm.completion = patched_completion

    def load_module(filename):
        """Load a Python file as a module and execute its run() function."""
        spec = importlib.util.spec_from_file_location("module", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    with duckdb.connect(dataset_hub_path if offline_mode else fetch_from_hub(dataset_hub_path), read_only=True) as con:
        print("~~~~~ Running palimpzest eval ~~~~~")

        vllm_model = pz.Model(f"hosted_vllm/{model_name_or_path}", api_base=base_url)

        # Run queries
        results = []
        for query_file, query_name in iter_queries("palimpzest"):
            if sembench_split == 'ecomm':
                if query_name in ["Q2", "Q4", "Q6", "Q8", "Q9", "Q10", "Q11", "Q12", "Q13"]:
                    print(f"Skipping {query_name}....")
                    continue
            elif sembench_split == "mmqa":
                if query_name in ["Q5"]:
                    print(f"Skipping {query_name}...")
                    continue

            pz_config = pz.QueryProcessorConfig(
                max_workers=n_parallel,
                join_parallelism=n_parallel,
                verbose=True,
                progress=False,
                available_models=[vllm_model],
                reasoning_effort='low'
            )
            func = load_module(query_file)
            with (track_gpu() if has_gpu else nullcontext()) as gpu_data:
                start = time.time()
                result = func.run(con, pz_config)
                if not isinstance(result, pd.DataFrame):
                    result = result.to_df()
                latency = time.time() - start
            results.append(
                {
                    "system_name": "palimpzest",
                    "query_name": query_name,
                    "latency": latency,
                    "gpu_usage": gpu_data,
                    "prediction": result.to_json(orient="split", index=False),
                }
            )
    pd.DataFrame(results).to_csv(output_path)