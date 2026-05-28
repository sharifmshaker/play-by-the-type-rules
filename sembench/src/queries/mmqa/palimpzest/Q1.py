import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    table_df = con.execute("SELECT * FROM ben_piazza").df()
    text_df = con.execute("SELECT * FROM ben_piazza_text_data").df()

    joined_df = table_df.merge(
        text_df,
        left_on="Title",
        right_on="title",
        how="left",
    )
    joined_df = joined_df.fillna("")
    pz_dataset = pz.MemoryDataset(id="ben_piazza_joined", vals=joined_df)

    prompt = "Extract the director name from the movie description."
    pz_dataset = pz_dataset.sem_map(
        [
            {
                "name": "director",
                "type": str,
                "desc": prompt,
            }
        ],
        depends_on=["text"],
    )
    pz_dataset = pz_dataset.filter(
        lambda row: row["Role"] == "Bob Whitewood"
    )
    pz_dataset = pz_dataset.project(["director"])
    output = pz_dataset.run(pz_config)

    return output