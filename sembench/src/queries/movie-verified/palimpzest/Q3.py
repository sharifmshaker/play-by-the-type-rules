import palimpzest as pz
import pandas as pd

def run(con, pz_config: pz.QueryProcessorConfig):
    reviews = con.execute("SELECT * FROM Reviews").df()

    def is_valid_fraction_not_half(score):
        if pd.isna(score) or "/" not in str(score):
            return False
        try:
            parts = str(score).split("/")
            numerator = float(parts[0])
            denominator = float(parts[1])
            return denominator != 0 and (numerator / denominator) != 0.5
        except (ValueError, IndexError):
            return False

    mask = reviews["originalScore"].apply(is_valid_fraction_not_half)
    reviews = reviews[mask]

    reviews = pz.MemoryDataset(
        id="reviews",
        vals=reviews.rename(columns={"id": "movieId"}),
    )
    reviews = reviews.filter(lambda r: r["movieId"] == "taken_3")
    reviews = reviews.sem_filter(
        "Determine if the score, as a fraction, is greater than 0.5.",
        depends_on=["originalScore"],
    )
    reviews = reviews.count()

    return reviews.run(config=pz_config)
