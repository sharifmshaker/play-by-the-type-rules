"""
Configuration settings for model evaluation framework.
"""
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DUCKDB_SEED = 0.5

MODEL_PARAMS = {
    "temperature": 0.0,
    "repeat_penalty": 1.0,
    "max_tokens": 5,
    "num_ctx": 2048,
    "seed": 100,
    "num_predict": -1,
    "top_k": 40,
    "top_p": 0.95,
    "min_p": 0.05,
    "num_threads": 6,
    "n_gpu_layers": -1,
    "flash_attn": True,
    "n_batch": 2048,
}

# System params
N_PARALLEL = 32

# Paths
MOVIE_FILES_DIR = BASE_DIR / "data"
QUERIES_DIR = BASE_DIR / "queries/movie-verified"
THALAMUS_CONFIG_PATH = "../thalamus_db_model_config.json"

# Query Filtering
SKIP_QUERIES = {"Q9", "Q10", "Q11", "Q12"}
ONLY_USE = {}