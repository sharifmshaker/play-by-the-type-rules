WITH elephant_subset AS (
    SELECT City FROM image_data
    WHERE {{LLMMap('Does this image contain an elephant?', ImagePath)}}
    UNION
    SELECT City FROM audio_data
    WHERE {{LLMMap('The audio contains an animal sound. Does the audio contain elephant sounds?', AudioPath)}}
), monkey_subset AS (
    SELECT City FROM image_data
    WHERE {{LLMMap('Does this image contain a monkey?', ImagePath)}}
    UNION
    SELECT City FROM audio_data
    WHERE {{LLMMap('The audio contains an animal sound. Does the audio contain monkey sounds?', AudioPath)}}
) SELECT DISTINCT City FROM elephant_subset INTERSECT SELECT DISTINCT City FROM monkey_subset