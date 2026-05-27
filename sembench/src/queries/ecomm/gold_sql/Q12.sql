SELECT json_object('id', id, 'brand', lower(brandName), 'category', lower(masterCategory.typeName)) as id
FROM styles_details
WHERE lower(brandName) in ('adidas', 'puma');