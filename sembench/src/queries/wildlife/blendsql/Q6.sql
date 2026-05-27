WITH image_cities AS (
    SELECT DISTINCT City
    FROM image_data
    WHERE {{LLMMap('Does this image contain a monkey?', ImagePath)}}
),
audio_cities AS (
    SELECT DISTINCT City
    FROM audio_data
    WHERE {{LLMMap('The audio contains an animal sound. Does the audio contain monkey sounds?', AudioPath)}}
)
SELECT ic.City
FROM image_cities ic
LEFT JOIN audio_cities ac ON ic.City = ac.City
WHERE ac.City IS NULL