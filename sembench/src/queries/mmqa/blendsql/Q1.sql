SELECT {{
    LLMMap(
        'Extract the director from the following movie description.',
        t2.text
    )
}} AS director FROM ben_piazza t1
JOIN ben_piazza_text_data t2
ON t1.Title = t2.title
WHERE t1.Role = 'Bob Whitewood';