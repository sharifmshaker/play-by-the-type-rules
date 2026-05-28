import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    text_df = con.execute("SELECT * FROM lizzy_caplan_text_data").df()
    target_values = [
        "Love Is the Drug",
        "Crashing",
        "Cloverfield",
        "My Best Friend's Girl",
        "Hot Tub Time Machine",
        "The Last Rites of Ransom Pride",
        "Save the Date",
        "Bachelorette",
        "3, 2, 1... Frankie Go Boom",
        "Queens of Country",
        "Item 47",
        "The Night Before",
        "Now You See Me 2",
        "Allied",
        "Extinction",
        "Cobweb",
    ]
    text_df = text_df[text_df["title"].isin(target_values)]
    pz_text = pz.MemoryDataset(id="lizzy_caplan_text", vals=text_df)

    prompt = "Who has played a role in all the movies listed in the table given their descriptions? Simply give the name of the actor."  # noqa: E501
    pz_text = pz_text.sem_agg(
        col={
            "name": "actor",
            "type": str,
            "description": "The name of the actor",
        },
        agg=prompt,
        depends_on=["title", "text"],
    )
    output = pz_text.run(pz_config)

    return output