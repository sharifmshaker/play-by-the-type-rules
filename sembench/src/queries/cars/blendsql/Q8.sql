SELECT car_id
FROM car_images
WHERE {{LLMMap('You will be given an image of a car or its parts. Does the car have both punctures and paint scratches?', image_path)}}
LIMIT 100