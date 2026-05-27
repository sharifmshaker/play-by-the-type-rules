SELECT
  i.id as id
FROM styles_details s
JOIN image_mapping i on s.id = i.id
WHERE {{LLMMap('Does this image show a (pair of) sports shoe(s) that feature the colors yellow and silver?', i.local_image_path)}}