SELECT
  i.id as id,
  {{LLMMap('What is the primary color of the product in this image? Only return the base color, nothing else.', i.local_image_path)}} AS category
FROM styles_details s
JOIN image_mapping i on s.id = i.id
WHERE s.baseColour IN ('Black', 'Blue', 'Red', 'White', 'Orange', 'Green')