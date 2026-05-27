"""
Configuration settings for model evaluation framework.
"""
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DUCKDB_SEED = 0.5

# Paths
THALAMUS_CONFIG_PATH = "../thalamus_db_model_config.json"

# Query Filtering
SKIP_QUERIES = {}
ONLY_USE = {}