import os
import pandas as pd


def run(con):
    # Load data
    styles_details = con.execute("SELECT * FROM styles_details").df()

    # Apply map
    # TODO: productDescriptors contains sub-columns and should only access 'productDescriptors.description.value'
    processed = styles_details.sem_extract(
        input_cols=["productDisplayName", "productDescriptors"],
        output_cols={
            "category": "Extract the brand name from the following product description."
        },
    )

    return processed[["id", "category"]]