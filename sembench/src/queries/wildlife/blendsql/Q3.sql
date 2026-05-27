SELECT City AS city
FROM image_data
WHERE {{LLMMap('Does this image contain a zebra?', ImagePath)}}
GROUP BY City
ORDER BY COUNT(*) DESC
LIMIT 1;