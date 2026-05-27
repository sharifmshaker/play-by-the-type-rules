import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    styles_details = pz.MemoryDataset(
        id="styles_details", vals=con.execute("SELECT * FROM styles_details").df()
    )

    # Filter data
    styles_details = styles_details.sem_filter(
        "The product is a backpack from Reebok",
        depends_on=["productDisplayName", "productDescriptors"],
    )
    styles_details = styles_details.project(["id"])

    output = styles_details.run(pz_config)
    return output