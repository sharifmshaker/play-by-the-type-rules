SELECT DISTINCT City FROM image_data
WHERE {{LLMMap('Does this image contain a monkey?', ImagePath)}}
INTERSECT DISTINCT
SELECT DISTINCT City FROM audio_data
WHERE {{LLMMap('The audio contains an animal sound. Does the audio contain monkey sounds?', AudioPath)}}