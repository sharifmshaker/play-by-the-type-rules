WITH shoes AS (
  SELECT
    id,
    brandName as brand,
    price,
    productDisplayName as title,
    productDescriptors.description.value as description
  FROM styles_details
  WHERE masterCategory.typeName = 'Footwear'
    AND baseColour = 'Black'
),
lower AS (
  SELECT
    id,
    brandName as brand,
    price,
    productDisplayName as title,
    productDescriptors.description.value as description
  FROM styles_details
  WHERE masterCategory.typeName = 'Apparel'
    AND subCategory.typeName = 'Bottomwear'
    AND articleType.typeName <> 'Swimwear'
    AND baseColour = 'Black'
),
upper AS (
  SELECT
    id,
    brandName as brand,
    price,
    productDisplayName as title,
    productDescriptors.description.value as description
  FROM styles_details
  WHERE masterCategory.typeName = 'Apparel'
    AND subCategory.typeName = 'Topwear'
    AND articleType.typeName <> 'Swimwear'
    AND baseColour = 'Black'
),
accessories AS (
  SELECT
    id,
    brandName as brand,
    price,
    productDisplayName as title,
    productDescriptors.description.value as description
  FROM styles_details
  WHERE masterCategory.typeName = 'Accessories'
    AND subCategory.typeName IN ('Watches', 'Jewellery', 'Bags')
    AND price <= 500
)
SELECT
  shoes.id || '-' || lower.id || '-' || upper.id || '-' || accessories.id AS id
FROM shoes
JOIN lower ON shoes.brand = lower.brand
JOIN upper ON lower.brand = upper.brand
JOIN accessories ON upper.brand = accessories.brand