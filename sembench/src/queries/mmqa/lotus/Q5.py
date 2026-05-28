import pandas as pd

def run(con):
    # Load data
    text_df = con.execute("SELECT * FROM lizzy_caplan_text_data").df()
    target_values = [
        "Love Is the Drug",
        "Crashing",
        "Cloverfield",
        "My Best Friend's Girl",
        "Hot Tub Time Machine",
        "The Last Rites of Ransom Pride",
        "Save the Date",
        "Bachelorette",
        "3, 2, 1... Frankie Go Boom",
        "Queens of Country",
        "Item 47",
        "The Night Before",
        "Now You See Me 2",
        "Allied",
        "Extinction",
        "Cobweb",
    ]
    text_df = text_df[text_df["title"].isin(target_values)]

    prompt = "Who has played a role in all the movies {title} listed in the table given their descriptions {text}? Simply give the name of the actor."  # noqa: E501
    result_df = text_df.sem_agg(prompt)

    return result_df[["_output"]]