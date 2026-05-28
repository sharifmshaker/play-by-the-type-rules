SELECT City AS city, StationID AS stationID
FROM image_data
WHERE {{LLMMap('Does this image contain a zebra?', ImagePath)}}
GROUP BY city, stationID
ORDER BY COUNT(*) DESC
LIMIT 1