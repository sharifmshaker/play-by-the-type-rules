SELECT id,
{{
    LLMMap(
        'What is the brand name for the following product description? Only return the brand name, nothing else.',
        productDisplayName,
        productDescriptors
    )
}} AS category FROM styles_details
