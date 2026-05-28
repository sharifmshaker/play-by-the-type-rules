SELECT p.car_id,
{{
    LLMMap(
        'Classify the car complaint into one of the given problem categories.',
        summary,
        options=('ELECTRICAL SYSTEM', 'POWER TRAIN', 'ENGINE', 'STEERING', 'SERVICE BRAKES', 'STRUCTURE', 'AIR BAGS', 'ENGINE AND ENGINE COOLING', 'VEHICLE SPEED CONTROL', 'VISIBILITY/WIPER', 'FUEL/PROPULSION SYSTEM', 'FORWARD COLLISION AVOIDANCE', 'EXTERIOR LIGHTING', 'SUSPENSION', 'FUEL SYSTEM', 'VISIBILITY', 'WHEELS', 'SEAT BELTS', 'BACK OVER PREVENTION', 'TIRES', 'SEATS', 'LATCHES/LOCKS/LINKAGES', 'LANE DEPARTURE', 'EQUIPMENT')
    )
}} AS problem_category
FROM cars AS p
JOIN car_complaints AS c
ON p.car_id = c.car_id