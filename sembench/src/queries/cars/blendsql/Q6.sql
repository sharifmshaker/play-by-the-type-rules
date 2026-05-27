WITH two_more_modalities AS (
SELECT
    cars.car_id,
    cars.year,
    car_complaints.complaint_id,
    car_complaints.summary,
    car_images.image_id,
    car_images.image_path,
    car_audio.audio_id,
    car_audio.audio_path
FROM cars
LEFT JOIN car_images ON cars.car_id = car_images.car_id
LEFT JOIN car_audio ON cars.car_id = car_audio.car_id
LEFT JOIN car_complaints ON cars.car_id = car_complaints.car_id
WHERE (car_audio.audio_id IS NOT NULL AND car_complaints.complaint_id IS NOT NULL) OR
      (car_images.image_id IS NOT NULL AND car_complaints.complaint_id IS NOT NULL) OR
      (car_images.image_id IS NOT NULL AND car_audio.audio_id IS NOT NULL)
),
sick_audio AS (
    SELECT car_id
    FROM two_more_modalities
    WHERE audio_id IS NOT NULL
    AND {{LLMMap('You will be given an audio recording of car diagnostics. Does the recording capture audio of a damaged car?', audio_path)}}
),
sick_image AS (
    SELECT car_id
    FROM two_more_modalities
    WHERE image_id IS NOT NULL
    AND {{LLMMap('You will be given an image of a car or its parts. Is the car damaged?', image_path)}}
),
sick_text AS (
    SELECT car_id
    FROM two_more_modalities
    WHERE complaint_id IS NOT NULL
    AND {{
        LLMMap(
            'Does the complaint entail that the car was in a fire or burned?', summary
        )
    }}
)
SELECT DISTINCT car_id FROM (
    SELECT
        t.car_id,
        t.year,
        t.complaint_id,
        t.image_id,
        t.audio_id,
        CASE WHEN a.car_id IS NOT NULL THEN 1 WHEN t.audio_id IS NOT NULL THEN 0 ELSE NULL END AS is_sick_audio,
        CASE WHEN s.car_id IS NOT NULL THEN 1 WHEN t.complaint_id IS NOT NULL THEN 0 ELSE NULL END AS is_sick_text,
        CASE WHEN x.car_id IS NOT NULL THEN 1 WHEN t.image_id IS NOT NULL THEN 0 ELSE NULL END AS is_sick_image
    FROM two_more_modalities t
    LEFT JOIN sick_audio a ON t.car_id = a.car_id
    LEFT JOIN sick_text s ON t.car_id = s.car_id
    LEFT JOIN sick_image x ON t.car_id = x.car_id
)
WHERE (is_sick_audio = 1 OR is_sick_text = 1 OR is_sick_image = 1)
AND (is_sick_audio = 0 OR is_sick_text = 0 OR is_sick_image = 0)