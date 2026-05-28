WITH joined AS (
    SELECT s.id, s.productDescriptors, im.local_image_path
    FROM styles_details s
    CROSS JOIN image_mapping im
    WHERE s.price < 130
),
candidates AS (
    SELECT * FROM joined
    WHERE {{LLMMap('Does the image depict white socks?', local_image_path)}} = TRUE
    AND {{LLMMap('Does the provided image fit the description?', local_image_path, productDescriptors)}} = TRUE
),
scored AS (
    SELECT id, productDescriptors, local_image_path,
        {{
            LLMMap(
                'On a scale of 1-10, how well does the image match the description?',
                local_image_path,
                productDescriptors,
                options=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
            )
        }} AS match_score
    FROM candidates
)
SELECT id
FROM scored
WHERE (productDescriptors, match_score) IN (
    SELECT productDescriptors, MAX(match_score)
    FROM scored
    GROUP BY productDescriptors
)