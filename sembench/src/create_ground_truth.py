def create_ground_truth():
    import os
    import duckdb
    import time
    import pandas as pd

    from blendsql.common.utils import fetch_from_hub

    from src.database_utils import iter_queries

    dataset_hub_path = os.environ["DATASET_HUB_PATH"]
    offline_mode = os.getenv("OFFLINE_MODE", '0') == '1'

    with duckdb.connect(dataset_hub_path if offline_mode else fetch_from_hub(dataset_hub_path), read_only=True) as con:
        # Run queries
        results = []
        for query_file, query_name in iter_queries("gold_sql"):
            query = open(query_file).read()
            start = time.time()
            result = con.execute(query).df()
            if result.empty:
                print(f"Ground truth for {query_file} is empty")
            latency = time.time() - start
            results.append(
                {
                    "system_name": "ground_truth",
                    "query_name": query_name,
                    "latency": latency,
                    "prediction": result.to_json(orient="split", index=False),
                }
            )
        return pd.DataFrame(results)
