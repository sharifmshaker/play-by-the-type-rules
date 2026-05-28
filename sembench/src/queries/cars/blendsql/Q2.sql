SELECT DISTINCT cars.car_id
FROM cars, car_audio
WHERE cars.car_id = car_audio.car_id
AND cars.fuel_type = 'Electric'
AND {{
    LLMMap(
        'Does the audio sound like a car with a dead battery?',
        audio_path
    )
}}
