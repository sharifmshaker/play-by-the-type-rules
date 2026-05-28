import pandas as pd

def run(con):
    # Load data
    text_df = con.execute("SELECT * FROM lizzy_caplan_text_data").df()
    target_values = [
        "Orange County",
        "Mean Girls",
        "Love Is the Drug",
        "Crashing",
        "Cloverfield",
        "My Best Friend's Girl",
        "Crossing Over",
        "Hot Tub Time Machine",
        "The Last Rites of Ransom Pride",
        "127 Hours",
        "High Road",
        "Save the Date",
        "Bachelorette",
        "3, 2, 1... Frankie Go Boom",
        "Queens of Country",
        "Item 47",
        "The Interview",
        "The Night Before",
        "Now You See Me 2",
        "Allied",
        "The Disaster Artist",
        "Extinction",
        "The People We Hate at the Wedding",
        "Cobweb",
    ]
    text_df = text_df[text_df["title"].isin(target_values)]

    text_input_cols = ["text"]
    text_output_cols = {
        "genres": "The genres of the movie, separated by commas",
    }
    new_text_df = text_df.sem_extract(
        text_input_cols,
        text_output_cols,
        extract_quotes=False,
        return_raw_outputs=False,
    )

    expanded_data = []
    for _, row in new_text_df.iterrows():
        movie_title = row["title"]
        genres = [genre.strip() for genre in row["genres"].split(",")]
        for genre in genres:
            expanded_data.append({"genre": genre, "title": movie_title})

    df_expanded = pd.DataFrame(expanded_data)
    genre_movies_table = (
        df_expanded.groupby("genre")["title"]
        .apply(lambda x: ", ".join(x))
        .reset_index()
    )
    genre_movies_table.rename(
        columns={"title": "movies_in_genre"}, inplace=True
    )

    return genre_movies_table[["genre", "movies_in_genre"]]