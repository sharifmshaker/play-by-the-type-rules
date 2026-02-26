#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = "==3.12"
# dependencies = ["lotus-ai==1.1.4", "huggingface_hub", "duckdb"]
# ///

import os
import pandas as pd
import time
import duckdb
import importlib

import lotus
from lotus.models import LM

import importlib.util
from contextlib import nullcontext
from sembench.config import N_PARALLEL, MODEL_PARAMS
import litellm

original_completion = litellm.completion
def patched_completion(*args, **kwargs):
    litellm.drop_params = True
    kwargs["temperature"] = MODEL_PARAMS["temperature"]
    out = original_completion(*args, **kwargs)
    print(out)

litellm.completion = patched_completion

from sembench.config import DUCKDB_SEED
from sembench.gpu_util_tracker import track_gpu
from sembench.database_utils import iter_queries, fetch_from_hub

if __name__ == "__main__":
    model_name_or_path = os.environ["MODEL_NAME_OR_PATH"]
    base_url = os.environ["BASE_URL"]
    has_gpu = os.environ.get("HAS_GPU", "false") == "true"
    output_path = os.environ["OUTPUT_PATH"]
    dataset_hub_path = os.environ["DATASET_HUB_PATH"]

    print(f"{output_path=}, {model_name_or_path=}, {base_url=}, {has_gpu=}, {dataset_hub_path=}")

    def load_module(filename):
        """Load a Python file as a module and execute its run() function."""
        spec = importlib.util.spec_from_file_location("module", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    with duckdb.connect(fetch_from_hub(dataset_hub_path)) as con:
        con.execute(f"SELECT setseed({DUCKDB_SEED})")
        print("~~~~~ Running lotus eval ~~~~~")

        lotus.settings.configure(
            lm=LM(
                model=f"hosted_vllm/{model_name_or_path}",
                api_base=base_url,
                api_key="N.A.",
                # https://docs.litellm.ai/docs/providers/openai_compatible#advanced---disable-system-messages
                supports_system_message=False,  # lotus uses system prompts. Gemma3 doesn't listen to those.
                temperature=MODEL_PARAMS["temperature"],
                max_tokens=MODEL_PARAMS["max_tokens"],
                max_batch_size=N_PARALLEL,
            )
        )

        # Run queries
        results = []
        for query_file, query_name in iter_queries("lotus"):
            lotus.settings.lm.reset_stats()
            func = load_module(query_file)
            with (track_gpu() if has_gpu else nullcontext()) as gpu_data:
                start = time.perf_counter()
                result = func.run(con)
                latency = time.perf_counter() - start
            results.append(
                {
                    "system_name": "lotus",
                    "query_name": query_name,
                    "latency": latency,
                    "gpu_usage": gpu_data,
                    "prediction": result.to_json(orient="split", index=False),
                    "num_generation_calls": "N.A.",
                    "output_tokens": lotus.settings.lm.stats.physical_usage.completion_tokens,
                    "input_tokens": lotus.settings.lm.stats.physical_usage.prompt_tokens,
                }
            )
    pd.DataFrame(results).to_csv(output_path)