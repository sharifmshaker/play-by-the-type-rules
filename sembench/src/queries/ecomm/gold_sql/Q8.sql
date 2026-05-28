WITH product_selection AS (
  SELECT *
  FROM styles_details
  WHERE character_length(productDescriptors.description.value) >= 3000
)
SELECT
  id || '-' || id as id
FROM product_selection;