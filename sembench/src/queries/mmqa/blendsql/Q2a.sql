WITH joined AS (
    SELECT t1.ID, t2.local_image_path, t1.Track
    FROM ap_warrior t1
    CROSS JOIN images t2
)
SELECT ID, local_image_path
FROM joined
WHERE {{
    LLMMap(
        'You will be provided with a horse racetrack name and an image. Does the image show the logo of the racetrack?',
        Track,
        local_image_path
    )
}}