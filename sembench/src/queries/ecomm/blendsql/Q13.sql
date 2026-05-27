WITH joined AS (
    SELECT *
    FROM styles_details s
    JOIN image_mapping i on s.id = i.id
) SELECT id FROM joined
WHERE {{
    LLMMap(
        '
        You will receive a description of what a customer is looking for together with an image and a textual description of the product.
        Determine if they both match.

        I am looking for a running shirt for men with a round neck and short sleeves,
        preferably in blue or black, but not bright colors like white.
        Also definitely not green.
        It should be suitable for outdoor running in warm weather.
        If the t-shirt is not green, it should at least feature a striped design.
        ',
        productDisplayName,
        productDescriptors,
        local_image_path
    )
}}