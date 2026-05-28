WITH img_classifications AS (
    SELECT sd.id,
    sd.productDisplayName AS title,
    sd.productDescriptors.description.value AS descr,
    sd.brandName,
    sd.baseColour,
    img.local_image_path AS image_path,
    {{
        LLMMap(
            'Classify the clothing item in the image. If there are multiple products in the picture, always refer to the most prominent one.
            ''shoes'' and things like sandals, flip-flops, or other shoes.
            ''bottoms'' are pieces of apparel that can be worn on the lower part of the body, like pants, shorts, and skirts.
            ''tops'' are pieces of apparel that can be worn on the upper part of the body, like t-shirts, shirts, pullovers, hoodies, but still requires some sort of clothing on the lower body (i.e., not a dress)
            ',
            image_path,
            options=('shoes', 'bottoms', 'tops', 'N.A.')
        )
    }} AS category,
    {{
        LLMMap(
            'What is the primary color of the product in this image? Only return the base color, nothing else.',
            image_path
        )
    }} AS color
    FROM styles_details sd
    JOIN image_mapping img ON CAST(sd.id AS VARCHAR) = img.id
    WHERE sd.baseColour IN ('Black', 'Blue', 'Red', 'White')
    AND sd.price <= 1000
    AND category IN ('shoes', 'bottoms', 'tops')
),
pairings AS (
    SELECT
        s.id AS id1, s.title AS title1, s.descr AS descr1, s.image_path AS image1,
        b.id AS id2, b.title AS title2, b.descr AS descr2, b.image_path AS image2,
        t.id AS id3, t.title AS title3, t.descr AS descr3, t.image_path AS image3
    FROM img_classifications s
    JOIN img_classifications b ON LOWER(s.color) = LOWER(b.color)
    JOIN img_classifications t ON LOWER(s.color) = LOWER(t.color)
    WHERE s.category = 'shoes'
    AND b.category = 'bottoms'
    AND t.category = 'tops'
)
SELECT id1 || '-' || id2 || '-' || id3  AS id
FROM pairings