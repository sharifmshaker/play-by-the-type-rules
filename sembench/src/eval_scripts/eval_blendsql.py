#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = "==3.12"
# dependencies = ["blendsql==0.1.12"]
# ///

import os
import pandas as pd
import time
import duckdb
from contextlib import nullcontext

from blendsql import BlendSQL
from blendsql.models import VLLM
from blendsql.db import DuckDB
from blendsql.common.logger import Color, logger
from blendsql import config

from sembench.config import N_PARALLEL, DUCKDB_SEED, MODEL_PARAMS
from sembench.database_utils import iter_queries, fetch_from_hub
from sembench.gpu_util_tracker import track_gpu

config.set_deterministic(True)
config.set_async_limit(N_PARALLEL)
config.set_default_max_tokens(MODEL_PARAMS["max_tokens"])

if __name__ == "__main__":
    model_name_or_path = os.environ["MODEL_NAME_OR_PATH"]
    base_url = os.environ["BASE_URL"]
    has_gpu = os.environ.get("HAS_GPU", "false") == "true"
    output_path = os.environ["OUTPUT_PATH"]
    dataset_hub_path = os.environ["DATASET_HUB_PATH"]

    print(f"{output_path=}, {model_name_or_path=}, {base_url=}, {has_gpu=}, {dataset_hub_path=}")

    with duckdb.connect(fetch_from_hub(dataset_hub_path), read_only=True) as con:
        con.execute(f"SELECT setseed({DUCKDB_SEED})")
        logger.debug(Color.horizontal_line())
        logger.debug(
            Color.model_or_data_update("~~~~~ Running blendsql eval ~~~~~")
        )
        Color.in_block = True

        # Initialize BlendSQL
        bsql = BlendSQL(
            DuckDB(con),
            model=VLLM(
                model_name_or_path=model_name_or_path,
                base_url=base_url,
            ),
            verbose=False,
        )
        bsql._warmup()

        # Run queries
        results = []
        for query_file, query_name in iter_queries("blendsql"):
            query = open(query_file).read()
            with (track_gpu() if has_gpu else nullcontext()) as gpu_data:
                start = time.perf_counter()
                smoothie = bsql.execute(query)
                result = (
                    smoothie.df
                )  # Count this, since conversion to pd from pl takes a small bit of latency
                latency = time.perf_counter() - start
            results.append(
                {
                    "system_name": "blendsql",
                    "query_name": query_name,
                    "latency": latency,
                    "gpu_usage": gpu_data,
                    "prediction": result.to_json(orient="split", index=False),
                    "num_generation_calls": smoothie.meta.num_generation_calls,
                    "output_tokens": smoothie.meta.completion_tokens,
                    "input_tokens": smoothie.meta.prompt_tokens,
                }
            )
    Color.in_block = False
    pd.DataFrame(results).to_csv(output_path)