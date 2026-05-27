WITH joined AS (
    SELECT *
    FROM styles_details s
    CROSS JOIN image_mapping
    WHERE s.price < 130
) SELECT id FROM joined
WHERE {{
    LLMMap(
        'Does the image depict white socks?',
        local_image_path
    )
}} AND {{
    LLMMap(
        'Does the provided image fit the description?',
        local_image_path,
        productDescriptors
    )
}}