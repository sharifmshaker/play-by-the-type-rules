WITH joined AS (
    SELECT DISTINCT s.productDisplayName, s.productDescriptors, i.local_image_path, s.id || '-' || i.id as id
    FROM styles_details s
    CROSS JOIN image_mapping i
    WHERE character_length(s.productDescriptors.description.value) >= 3000
)
SELECT id
FROM joined
WHERE {{LLMMap('Does the attached image fit the description in the context?', productDisplayName, productDescriptors, local_image_path)}}