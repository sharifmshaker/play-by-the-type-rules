SELECT 2026 - AVG(cars.year) AS average_age
FROM cars, car_complaints
WHERE cars.car_id = car_complaints.car_id
AND {{
    LLMMap(
        'In the complaint, does the car have engine-related problems?', summary
    )
}} = TRUE