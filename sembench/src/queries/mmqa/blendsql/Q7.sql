WITH joined AS (
    SELECT t1.Airlines, t2.local_image_path
    FROM tampa_international_airport t1
    CROSS JOIN images t2
)
SELECT Airlines, local_image_path
FROM joined
WHERE {{
    LLMMap(
        'You will be provided with an airline name and an image. Does the image show the logo of the airline?',
        Airlines,
        local_image_path
    )
}}