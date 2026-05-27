SELECT reviewId FROM Reviews
WHERE {{LLMMap('Does this review starts with the letter ''T''?', reviewText)}}