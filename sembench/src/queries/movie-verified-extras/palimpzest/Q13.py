import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    reviews = pz.MemoryDataset(
        id="reviews",
        vals=con.execute("SELECT * FROM Reviews").df()
    )
    reviews = reviews.sem_filter(
        "This review starts with the letter 'T'.",
        depends_on=["reviewText"],
    )
    reviews = reviews.project(["reviewId"])
    return reviews.run(config=pz_config)
