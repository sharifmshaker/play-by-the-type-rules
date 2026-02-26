def create_ground_truth():
    import os
    import duckdb
    import time
    import pandas as pd

    from blendsql.common.utils import fetch_from_hub

    from src.database_utils import iter_queries

    dataset_hub_path = os.environ["DATASET_HUB_PATH"]

    with duckdb.connect(fetch_from_hub(dataset_hub_path), read_only=True) as con:
        print(
            f"Reviews has {con.execute('SELECT COUNT(*) FROM Reviews').fetchone()} rows"
        )
        print(
            f"Movies has {con.execute('SELECT COUNT(*) FROM Movies').fetchone()} rows"
        )

        # Run queries
        results = []
        for query_file, query_name in iter_queries("gold_sql"):
            query = open(query_file).read()
            start = time.time()
            result = con.execute(query).df()
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
