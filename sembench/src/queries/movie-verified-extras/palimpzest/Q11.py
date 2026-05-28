import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    reviews = pz.MemoryDataset(
        id="reviews",
        vals=con.execute("SELECT * FROM Reviews").df()
    )
    reviews = reviews.filter(lambda r: r["isTopCritic"] == True or r['creationDate'].startswith('2023'))
    reviews = reviews.sem_filter(
        "This review has the EXACT substring 'Marvel' in it.",
        depends_on=["reviewText"],
    )
    reviews = reviews.sem_filter(
        "This review have the EXACT substring 'movie' in it.",
        depends_on=["reviewText"],
    )
    reviews = reviews.project(["reviewId"])
    reviews = reviews.limit(5)
    return reviews.run(config=pz_config)
