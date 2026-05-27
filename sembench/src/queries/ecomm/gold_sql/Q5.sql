SELECT id, subCategory.typeName AS category
FROM styles_details
WHERE masterCategory.typeName = 'Apparel'
AND subCategory.typeName NOT IN ('Saree', 'Apparel Set', 'Loungewear and Nightwear')