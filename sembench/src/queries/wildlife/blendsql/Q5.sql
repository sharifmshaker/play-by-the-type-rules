WITH image_cities AS (
    SELECT City AS city
    FROM image_data
    WHERE {{LLMMap('Does this image contain an elephant?', ImagePath)}}
), audio_cities AS (
    SELECT City AS city
    FROM audio_data
    WHERE {{LLMMap('The audio contains an animal sound. Does the audio contain elephant sounds?', AudioPath)}}
) SELECT DISTINCT city FROM (
    SELECT city FROM image_cities
    UNION ALL
    SELECT city FROM audio_cities
)