    WITH movie_genres AS (
    SELECT title, CAST({{
        LLMMap(
            'Extract all applicable genres for the move based on the description. Return a valid python list[str].',
            text
        )
    }} AS VARCHAR[]) AS genres
    FROM lizzy_caplan_text_data
    WHERE title IN (
        'Orange County',
        'Mean Girls',
        'Love Is the Drug',
        'Crashing',
        'Cloverfield',
        'My Best Friend''s Girl',
        'Crossing Over',
        'Hot Tub Time Machine',
        'The Last Rites of Ransom Pride',
        '127 Hours',
        'High Road',
        'Save the Date',
        'Bachelorette',
        '3, 2, 1... Frankie Go Boom',
        'Queens of Country',
        'Item 47',
        'The Interview',
        'The Night Before',
        'Now You See Me 2',
        'Allied',
        'The Disaster Artist',
        'Extinction',
        'The People We Hate at the Wedding',
        'Cobweb'
    )
) SELECT
  LOWER(unnested_genre) AS genre,
  STRING_AGG(title, ', ') AS movies_in_genre
FROM
  movie_genres,
  UNNEST(genres) AS t(unnested_genre)
GROUP BY
  unnested_genre
ORDER BY
  unnested_genre