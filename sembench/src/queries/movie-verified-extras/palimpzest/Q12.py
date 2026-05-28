import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    reviews = con.execute("SELECT * FROM Reviews").df()
    movies = con.execute("SELECT * FROM Movies").df()

    merged = reviews.merge(movies, on="id", how="inner")

    merged_reviews = pz.MemoryDataset(
        id="merged_reviews",
        vals=merged
    )
    merged_reviews = merged_reviews.filter(lambda r: r["originalLanguage"] == "Korean")
    merged_reviews = merged_reviews.sem_filter(
        "Determine if the score, as a fraction, is greater than 0.5.",
        depends_on=["originalScore"],
    )
    merged_reviews = merged_reviews.sem_add_columns(
        [
            {
                "name": "sentiment",
                "type": str,
                "desc": "Classify the sentiment of this movie review as either 'POSITIVE' or 'NEGATIVE'. "
                "Return 'POSITIVE' if the score as a fraction is greater than 0.5, and 'NEGATIVE' otherwise."
                "Only output the exact word 'POSITIVE' or 'NEGATIVE' with no additional text. ",
            }
        ],
        depends_on=["reviewText"],
    )
    merged_reviews = merged_reviews.project(["reviewId"])
    return merged_reviews.run(config=pz_config)
