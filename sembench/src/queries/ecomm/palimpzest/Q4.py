import os
import pandas as pd
import palimpzest as pz


def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    images = pz.ImageFileDataset(
        id="images", path="./files/ecomm/data/sf_500/images"
    )
    styles_details = con.execute("SELECT * FROM styles_details").df()

    # Pre-filter for simple colors
    images = images.add_columns(
        udf=lambda row: {"product_id": row["filename"].split(".", 1)[0]},
        cols=[
            {
                "name": "product_id",
                "type": str,
                "description": "Product id generated from image name",
            }
        ],
    )
    styles_details = styles_details[
        styles_details["baseColour"].isin(
            ["Black", "Blue", "Red", "White", "Orange", "Green"]
        )
    ]
    images = images.filter(
        lambda row: int(row["product_id"]) in styles_details["id"].values
    )

    # Process data
    images = images.sem_add_columns(
        cols=[
            {
                "name": "category",
                "type": str,
                "description": "Extract the primary color of the product in the image. Only return the base color, nothing else.",
            }
        ],
        depends_on=["contents"],
    )
    images = images.project(["product_id", "category"])

    output = images.run(pz_config)
    return output