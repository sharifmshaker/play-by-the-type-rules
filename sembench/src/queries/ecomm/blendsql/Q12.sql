WITH joined_style_details AS (
    SELECT *
    FROM styles_details s
    JOIN image_mapping i on s.id = i.id
    WHERE {{LLMMap('Does the following description describe a product from either Adidas or Puma?', s.productDisplayName, s.productDescriptors)}}
    AND masterCategory.typeName IN ('Accessories', 'Apparel', 'Footwear')
) SELECT {{
    LLMMap(
        '
        You are given a product description and an image of the product as well as the product id.
        The product contains a fashion item (clothing, shoes, accessories, etc).
        There might be multiple fashion items in the image, especially when a model is presenting them.
        If this is the case, focus only on the primary fashion item and use the description to determine which item in the image is of interest.

        For each product, generate the below json:

         {
            "id": <product id> (integer),
            "brand": <extract the brand name from the description and/or image. use lower-case letters for the brand name>",
            "category": <classify the images into ''''accessories'''', ''''apparel'''', ''''footwear''''>
        }
        ',
        id,
        productDisplayName,
        productDescriptors,
        local_image_path,
        return_type='{
          "type": "object",
          "properties": {
            "id": {
              "type": "integer",
              "description": "Product ID"
            },
            "brand": {
              "type": "string",
              "description": "Brand name extracted from description/image, in lower-case",
              "pattern": "^[a-z0-9 &._-]+$"
            },
            "category": {
              "type": "string",
              "description": "Product category classification",
              "enum": ["accessories", "apparel", "footwear"]
            }
          },
          "required": ["id", "brand", "category"],
          "additionalProperties": false
        }'
    )
}} AS id
FROM joined_style_details