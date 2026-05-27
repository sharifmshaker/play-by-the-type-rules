#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = "==3.12"
# dependencies = ["blendsql==0.1.26"]
# ///
import json
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

from src.config import DUCKDB_SEED
from src.database_utils import iter_queries, fetch_from_hub
from src.gpu_util_tracker import track_gpu

config.set_deterministic(True)

if __name__ == "__main__":
    model_name_or_path = os.environ["MODEL_NAME_OR_PATH"]
    base_url = os.environ["BASE_URL"]
    has_gpu = os.environ.get("HAS_GPU", "false") == "true"
    output_path = os.environ["OUTPUT_PATH"]
    extra_body = os.environ["EXTRA_BODY"]
    dataset_hub_path = os.environ["DATASET_HUB_PATH"]
    offline_mode = os.getenv("OFFLINE_MODE", '0') == '1'
    sembench_split = os.environ["SEMBENCH_SPLIT"]
    n_parallel = int(os.environ["N_PARALLEL"])
    enable_constrained_decoding = os.environ.get("ENABLE_CONSTRAINED_DECODING", "").lower() == "true"
    enable_cascade_filter = os.environ.get("ENABLE_CASCADE_FILTER", "").lower() == "true"
    enable_early_exit = os.environ.get("ENABLE_EARLY_EXIT", "").lower() == "true"

    if extra_body:
        extra_body = json.loads(extra_body)
    else:
        extra_body = None

    print(f"{output_path=}, {model_name_or_path=}, {base_url=}, {has_gpu=}, {dataset_hub_path=}")
    print(f"{n_parallel=}, {enable_constrained_decoding=}, {enable_cascade_filter=}, {enable_early_exit=}")

    with duckdb.connect(dataset_hub_path if offline_mode else fetch_from_hub(dataset_hub_path), read_only=True) as con:
        con.execute(f"SELECT setseed({DUCKDB_SEED})")
        logger.debug(Color.horizontal_line())
        logger.debug(
            Color.model_or_data_update("~~~~~ Running blendsql eval ~~~~~")
        )
        Color.in_block = True

        # Initialize BlendSQL
        config.set_async_limit(n_parallel)
        bsql = BlendSQL(
            DuckDB(con),
            model=VLLM(
                model_name_or_path=model_name_or_path,
                base_url=base_url,
                extra_body=extra_body,
            ),
            verbose=False,
            enable_constrained_decoding=enable_constrained_decoding,
            enable_cascade_filter=enable_cascade_filter,
            enable_early_exit=enable_early_exit,
        )
        bsql._warmup()

        # Run queries
        results = []
        for query_file, query_name in iter_queries("blendsql"):
            if sembench_split == "cars":
                if query_name == "Q9":
                    continue # The ground truth for this query returns an empty subset
            query = open(query_file).read()
            with (track_gpu() if has_gpu else nullcontext()) as gpu_data:
                start = time.perf_counter()
                smoothie = bsql.execute(query)
                result = (
                    smoothie.df()
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