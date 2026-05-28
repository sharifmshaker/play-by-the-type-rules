SELECT DISTINCT City FROM image_data
WHERE {{LLMMap('Does this image contain a zebra?', ImagePath)}}
INTERSECT
SELECT DISTINCT City FROM image_data
WHERE {{LLMMap('Does this image contain an impala?', ImagePath)}}