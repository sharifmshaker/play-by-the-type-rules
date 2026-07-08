"""
Configuration settings for model evaluation framework.
"""
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DUCKDB_SEED = 0.5

# Paths
THALAMUS_CONFIG_PATH = "../thalamus_db_model_config.json"

# Query Filtering — env-overridable (comma-separated query names), used by e.g.
# run_gemini.sh --smoke (ONLY_USE="Q1,Q2a"). Empty = no filter (original behavior).
def _env_query_set(name: str) -> set:
    return {q.strip() for q in os.getenv(name, "").split(",") if q.strip()}

SKIP_QUERIES = _env_query_set("SKIP_QUERIES")
ONLY_USE = _env_query_set("ONLY_USE")
