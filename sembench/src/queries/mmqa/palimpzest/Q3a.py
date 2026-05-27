import palimpzest as pz

def run(con, pz_config: pz.QueryProcessorConfig):
    # Load data
    text_df = con.execute("SELECT * FROM lizzy_caplan_text_data").df()
    pz_text = pz.MemoryDataset(id="lizzy_caplan_text", vals=text_df)

    prompt = (
        "Determine if a movie is a comedy movie given their description."
    )
    pz_text = pz_text.sem_filter(prompt, depends_on=["title", "text"])
    pz_text = pz_text.project(["title"])
    output = pz_text.run(pz_config)
    return output