WITH self_joined_details AS (
    SELECT
    s1.id AS id1,
    s1.productDisplayName AS productName1,
    s1.productDescriptors AS productDescriptors1,
    s2.id AS id2,
    s2.productDisplayName AS productName2,
    s2.productDescriptors AS productDescriptors2,
    FROM styles_details s1
    CROSS JOIN styles_details s2
    WHERE s1.price <= 500 AND s2.price <= 500
)
SELECT id1 || '-' || id2 AS id
FROM self_joined_details
WHERE {{
    LLMMap(
        'You will be given two product descriptions. Do both product descriptions describe products of the same category from the same brand, e.g., both are t-shirts from Adidas?',
        productName1,
        productDescriptors1,
        productName2,
        productDescriptors2
    )
}}