WITH sick_audio AS (
    SELECT DISTINCT cars.car_id
    FROM cars, car_audio
    WHERE cars.car_id = car_audio.car_id
    AND {{LLMMap('You will be given an audio recording of car diagnostics. Does the car from the recording have worn out brakes?', audio_path)}}
),
sick_text AS (
    SELECT DISTINCT cars.car_id
    FROM cars, car_complaints
    WHERE cars.car_id = car_complaints.car_id
    AND {{LLMMap('Does the car in the complaint have problems related to its electrical system?', summary)}}
),
sick_image AS (
    SELECT DISTINCT cars.car_id
    FROM cars, car_images
    WHERE cars.car_id = car_images.car_id
    AND {{LLMMap('You will be given an image of a car or its parts. Is the car dented?', image_path)}}
)
SELECT car_id FROM sick_audio
UNION DISTINCT
SELECT car_id FROM sick_text
UNION DISTINCT
SELECT car_id FROM sick_image