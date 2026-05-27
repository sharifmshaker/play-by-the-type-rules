SELECT reviewId FROM Reviews
WHERE NLfilter(reviewText, 'Does this review starts with the letter ''T''?')