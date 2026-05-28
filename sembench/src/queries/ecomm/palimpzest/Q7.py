import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    styles_details = con.execute("SELECT * FROM styles_details").df().rename(
        columns={"id": "prod_id"}
    )  # prevent naming conflict with internal Palimpzest 'id' column
    styles_details = styles_details[styles_details["price"] <= 500]
    styles_details = pz.MemoryDataset(id="styles_details", vals=styles_details)

    # Join data
    styles_details = styles_details.sem_join(
        styles_details,
        """
        You will be given two product descriptions.
        Do both product descriptions describe products of the same category from the
        same brand, e.g., both are t-shirts from Adidas?
        """,
        depends_on=[
            "productDisplayName",
            "productDescriptors",
            "productDisplayName_right",
            "productDescriptors_right",
        ],
    )

    # Generate joined identifiers
    styles_details = styles_details.add_columns(
        udf=lambda row: {
            "id": str(row["prod_id"]) + "-" + str(row["prod_id_right"])
        },
        cols=[
            {"name": "id", "type": str, "description": "Combined ID"}
        ],
    )
    styles_details = styles_details.project(["id"])

    output = styles_details.run(pz_config)
    return output