SELECT DISTINCT cars.car_id
FROM cars, car_images, car_audio
WHERE cars.car_id = car_images.car_id
AND cars.car_id = car_audio.car_id
AND {{
    LLMMap(
        'You will be given an image of a car. Is the car torn?', image_path
    )
}}
AND {{
    LLMMap(
        'You will be given an audio recording of car diagnostics. Does it sound like the car has bad ignition?', audio_path
    )
}}