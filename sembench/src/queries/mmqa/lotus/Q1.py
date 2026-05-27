import pandas as pd

def run(con):
    # Load data
    table_df = con.execute("SELECT * FROM ben_piazza").df()
    text_df = con.execute("SELECT * FROM ben_piazza_text_data").df()

    text_input_cols = ["text"]
    text_output_cols = {
        "director": "The director of the movie",
    }
    processed_text_df = text_df.sem_extract(
        text_input_cols,
        text_output_cols,
        extract_quotes=False,
        return_raw_outputs=False,
    )

    joined_df = pd.merge(
        table_df,
        processed_text_df,
        left_on="Title",
        right_on="title",
        how="left",
    )
    result_df = joined_df[joined_df["Role"] == "Bob Whitewood"][["director"]]

    return result_df