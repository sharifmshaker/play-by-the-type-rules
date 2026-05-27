WITH images AS (
    SELECT
        sd.id,
        sd.productDisplayName AS title,
        sd.productDescriptors.description.value AS descr,
        sd.price,
        img.local_image_path AS image_path
    FROM styles_details sd
    JOIN image_mapping img ON CAST(sd.id AS VARCHAR) = img.id
),
img_classifications AS (
    SELECT *,
    {{
        LLMMap(
            'Classify the clothing item given the description and image.
            ''shoes'' and things like sandals, flip-flops, or other shoes.
            ''bottoms'' are pieces of apparel that can be worn on the lower part of the body, like pants, shorts, and skirts, but NOT swimwear.
            ''tops'' are pieces of apparel that can be worn on the upper part of the body, like t-shirts, shirts, pullovers, hoodies, but still requires some sort of clothing on the lower body (i.e., not a dress).
            ''accessories'' are things like jewelry or a bag, including handbags or a (gym) backpacks',
            title, descr, image_path,
            options=('shoes', 'bottoms', 'tops', 'accessories', 'N.A.')
        )
    }} AS category,
    {{
        LLMMap(
            'What is the brand name of this product? Return just the brand name.',
            title, descr
        )
    }} AS brand
    FROM images
    WHERE category != 'N.A.'
),
black_clothes AS (
    SELECT * FROM img_classifications
    WHERE category <> 'accessories'
    AND {{LLMMap('Is the predominant color of the product black?', title, descr)}} = TRUE
),
pairings AS (
    SELECT
        s.id AS id1, s.title AS title1, s.image_path AS image1,
        b.id AS id2, b.title AS title2, b.image_path AS image2,
        t.id AS id3, t.title AS title3, t.image_path AS image3,
        a.id AS id4, a.title AS title4, a.image_path AS image4
    FROM black_clothes s
    JOIN black_clothes b ON LOWER(TRIM(s.brand)) = LOWER(TRIM(b.brand))
    JOIN black_clothes t ON LOWER(TRIM(s.brand)) = LOWER(TRIM(t.brand))
    JOIN img_classifications a ON LOWER(TRIM(s.brand)) = LOWER(TRIM(a.brand))
    WHERE s.category = 'shoes'
      AND b.category = 'bottoms'
      AND t.category = 'tops'
      AND a.category = 'accessories'
      AND a.price <= 500
)
SELECT id1 || '-' || id2 || '-' || id3 || '-' || id4 AS id
FROM pairings