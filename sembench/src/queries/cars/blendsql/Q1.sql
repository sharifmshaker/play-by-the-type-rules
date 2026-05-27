SELECT DISTINCT car_id
FROM car_complaints
WHERE {{
    LLMMap(
        'You will be given a complaint. Does the complain entail that the car was in a crash/accident/collision?', summary
    )
}}