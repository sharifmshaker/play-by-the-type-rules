WITH product_selection AS (
  SELECT *
  FROM styles_details
  WHERE price <= 500
)
SELECT p1.id || '-' || p2.id AS id
FROM product_selection p1
JOIN product_selection p2
  ON p1.articleType.typeName = p2.articleType.typeName
  AND p1.brandName = p2.brandName
;