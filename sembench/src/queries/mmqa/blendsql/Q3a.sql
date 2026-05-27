SELECT title FROM lizzy_caplan_text_data
WHERE {{LLMMap('Given the description, is this movie a comedy movie?', text)}}