SELECT id,
{{
    LLMMap(
        'You are given a description of a product. Your task is to classify the product
        into one of the following categories:
        (1) Dress: A dress is a one-piece outer garment that is worn on the torso, hangs down over the legs, and often consist of a bodice attached to a skirt.
        (2) Bottomwear: Bottomwear refers to clothing worn on the lower part of the body, such as trousers, jeans, skirts, shorts, and leggings.
        (3) Socks: Socks are a type of clothing worn on the feet, typically made of soft fabric, designed to provide comfort and warmth.
        (4) Topwear: Topwear refers to clothing worn on the upper part of the body, such as shirts, blouses, t-shirts, and jackets
        (5) Innerwear: Innerwear refers to clothing worn beneath outer garments, typically close to the skin, such as underwear, bras, and undershirts.
        When classifying the product, only output the category name, nothing more.',
        productDisplayName,
        productDescriptors,
        options=('Dress', 'Bottomwear', 'Socks', 'Topwear', 'Innerwear')
    )
}} AS category
FROM styles_details
WHERE masterCategory.typeName = 'Apparel'
AND subCategory.typeName NOT IN ('Saree', 'Apparel Set', 'Loungewear and Nightwear')