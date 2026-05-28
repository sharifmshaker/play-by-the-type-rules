WITH product_selection AS (
  SELECT *
  FROM styles_details
  WHERE true
    AND baseColour IN ('Black', 'Blue', 'Red', 'White', 'Orange', 'Green')
    AND colour1 = ''
    AND colour2 = ''
    AND price < 800
)
SELECT p1.id || '-' || p2.id AS id
FROM product_selection p1
JOIN product_selection p2
  ON p1.id != p2.id
  AND p1.baseColour = p2.baseColour
  AND p1.articleType.typeName = p2.articleType.typeName;