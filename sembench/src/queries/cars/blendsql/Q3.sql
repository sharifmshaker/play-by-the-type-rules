SELECT cars.vin
FROM cars, car_images
WHERE cars.car_id = car_images.car_id
AND cars.transmission = 'Manual'
AND {{
    LLMMap(
        'You will be given an image of a car or its parts. Is the vehicle damaged?', image_path
    )
}} = FALSE
LIMIT 10