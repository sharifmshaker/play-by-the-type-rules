import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    table_df = con.execute("SELECT * FROM tampa_international_airport").df()
    pz_table = pz.MemoryDataset(id="tampa_airport", vals=table_df)

    prompt = "Given destinations of an airline, the airline has flights to Europe."  # noqa: E501
    pz_table = pz_table.sem_filter(
        prompt, depends_on=["Airlines", "Destinations"]
    )
    pz_table = pz_table.project(["Airlines"])
    output = pz_table.run(pz_config)

    return output