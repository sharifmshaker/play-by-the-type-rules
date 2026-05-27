SELECT COUNT(*) AS count
FROM audio_data
WHERE {{LLMMap('The audio contains an animal sound. Does the audio contain elephant sounds?', AudioPath)}}