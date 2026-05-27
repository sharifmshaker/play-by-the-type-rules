SELECT id FROM styles_details
WHERE {{LLMMap('Is this product a backpack from Reebok?', productDisplayName, productDescriptors)}}