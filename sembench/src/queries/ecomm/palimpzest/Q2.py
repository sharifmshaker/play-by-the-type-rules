import palimpzest as pz


def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    images = pz.ImageFileDataset(
        id="images", path="./files/ecomm/data/sf_500/images"
    )

    # Filter data
    images = images.sem_filter(
        "The image shows a (pair of) sports shoe(s) that feature the colors yellow and silver",
        depends_on=["contents"],
    )
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
    images = images.project(["product_id"])

    output = images.run(pz_config)
    return output