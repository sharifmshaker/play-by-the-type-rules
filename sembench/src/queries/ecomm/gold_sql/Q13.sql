WITH mapped_attributes AS (
    SELECT *,
    MAP_FROM_ENTRIES(list_transform(articleAttributes, x -> struct_pack(key := x[1], value := x[2]))) AS attributes
    FROM styles_details
) SELECT id
FROM mapped_attributes
WHERE gender = 'Men'
  AND usage = 'Sports'
  AND articleType.typeName = 'Tshirts'
  AND (baseColour = 'Blue' OR baseColour = 'Black')
  AND 'Short Sleeves' IN attributes['Sleeve Length']
  AND 'Round Neck' IN attributes['Neck']
  AND 'Striped' IN attributes['Pattern']
  AND season <> 'Winter'