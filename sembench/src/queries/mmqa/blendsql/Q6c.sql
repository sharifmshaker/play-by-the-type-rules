SELECT Airlines
FROM tampa_international_airport
WHERE {{LLMMap('Given destinations of the airline, does the airline have flights to Europe?', Airlines, Destinations)}}