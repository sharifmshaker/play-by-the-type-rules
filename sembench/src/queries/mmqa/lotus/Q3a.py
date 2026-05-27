import pandas as pd

def run(con):
    # Load data
    text_df = con.execute("SELECT * FROM lizzy_caplan_text_data").df()
    prompt = "{title} is a comedy movie given their description: {text}"
    result_df = text_df.sem_filter(prompt)

    return result_df[["title"]]