SELECT COUNT(DISTINCT cars.car_id) AS count
FROM cars, car_images, car_audio
WHERE cars.car_id = car_images.car_id
AND cars.car_id = car_audio.car_id
AND cars.transmission = 'Automatic'
AND {{LLMMap('You are given an audio recording of car diagnostics. Does the recording capture audio of a damaged car?', audio_path)}}
AND {{LLMMap('You will be given an image of a car or its parts. Is the vehicle damaged?', image_path)}}