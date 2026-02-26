import duckdb
import pandas as pd
from typing import Generator
import logging

from src.config import (
    SKIP_QUERIES,
    ONLY_USE,
    QUERIES_DIR,
)

HF_REPO_ID = "parkervg/blendsql-test-dbs"

def fetch_from_hub(filename: str):
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ImportError(
            f"You need huggingface_hub to run this!\n`pip install huggingface_hub`"
        ) from None
    return hf_hub_download(
        repo_id=HF_REPO_ID, filename=filename, repo_type="dataset", force_download=False
    )

def iter_queries(system_name: str) -> Generator:
    """
    Iterate through query files for a given system.

    Args:
        system_name: Name of the system directory containing queries

    Yields:
        Tuples of (query_file_path, query_name)
    """
    queries_path = QUERIES_DIR / system_name
    sorted_query_files = sorted(
        (f for f in queries_path.iterdir() if not f.name.startswith("_")),
        key=lambda x: x.stem,
    )

    for query_file in sorted_query_files:
        query_name = query_file.stem
        if query_name in SKIP_QUERIES:
            continue
        if ONLY_USE and query_name not in ONLY_USE:
            continue
        print(f"Running {system_name} {query_name}...")
        yield (query_file, query_name)
