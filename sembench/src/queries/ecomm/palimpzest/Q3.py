import os
import pandas as pd
import palimpzest as pz


def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    styles_details = pz.MemoryDataset(
        id="styles_details", vals=con.execute("SELECT * FROM styles_details").df()
    )

    # Perform map/extract
    styles_details = styles_details.sem_add_columns(
        cols=[
            {
                "name": "category",
                "type": str,
                "description": "Extract the brand name from the following product description. Only return the brand name, nothing else.",
            }
        ],
        depends_on=["productDisplayName", "productDescriptors"],
    )
    styles_details = styles_details.project(["id", "category"])

    output = styles_details.run(pz_config)
    return output