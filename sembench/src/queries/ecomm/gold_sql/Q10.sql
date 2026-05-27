WITH shoes AS (
  SELECT id, baseColour as color, price, brandName
  FROM styles_details
  WHERE masterCategory.typeName = 'Footwear'
    AND price <= 1000
),
lower AS (
  SELECT id, baseColour as color, price, brandName
  FROM styles_details
  WHERE masterCategory.typeName = 'Apparel' AND subCategory.typeName = 'Bottomwear'
    AND price <= 1000
),
upper AS (
  SELECT id, baseColour as color, price, brandName
  FROM styles_details
  WHERE masterCategory.typeName = 'Apparel' AND subCategory.typeName = 'Topwear'
    AND price <= 1000
)
SELECT
  shoes.id || '-' || lower.id || '-' || upper.id AS id
FROM shoes
JOIN lower ON shoes.color = lower.color AND shoes.brandName = lower.brandName
JOIN upper ON lower.color = upper.color AND lower.brandName = upper.brandName
WHERE true
  AND shoes.color IN ('Black', 'Blue', 'Red', 'White')
;