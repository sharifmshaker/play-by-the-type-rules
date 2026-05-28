WITH filtered_pairs AS (
    SELECT DISTINCT
        s1.id AS id1,
        img1.local_image_path AS image1,
        s2.id AS id2,
        img2.local_image_path AS image2
    FROM styles_details s1
    JOIN image_mapping img1 ON s1.id = img1.id
    JOIN styles_details s2 ON s1.id < s2.id
    JOIN image_mapping img2 ON s2.id = img2.id
    WHERE s1.baseColour IN ('Black', 'Blue', 'Red', 'White', 'Orange', 'Green')
      AND s1.colour1 = ''
      AND s1.colour2 = ''
      AND s1.price < 800
      AND s2.baseColour IN ('Black', 'Blue', 'Red', 'White', 'Orange', 'Green')
      AND s2.colour1 = ''
      AND s2.colour2 = ''
      AND s2.price < 800
)
SELECT id1 || '-' || id2 AS id
FROM filtered_pairs
WHERE {{
    LLMMap(
        'Do both images display objects of the same category (e.g., both are shoes, both are bags, etc.) and and have the same dominant surface color? Disregard any logos, text, or printed graphics on the objects. Only focus on the main object. Base your comparison solely on object type and overall surface color.',
        image1,
        image2
    )
}} AND id1 <> id2