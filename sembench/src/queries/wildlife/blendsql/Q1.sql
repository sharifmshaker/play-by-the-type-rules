SELECT COUNT(*) AS count
FROM image_data
WHERE {{LLMMap('Does this image contain a zebra?', ImagePath)}}