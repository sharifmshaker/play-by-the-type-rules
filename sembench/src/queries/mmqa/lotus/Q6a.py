import pandas as pd

def run(con):
    # Load data
    table_df = con.execute("SELECT * FROM tampa_international_airport").df()

    prompt = "Given destinations '{Destinations}' of {Airlines}, the airline has flights to Frankfurt"  # noqa: E501
    result_df = table_df.sem_filter(prompt)

    return result_df[["Airlines"]]