SELECT {{
    LLMQA(
        'Who played a role in all of these movies? Return the name of the actor.',
        (
            SELECT text FROM lizzy_caplan_text_data
            WHERE title IN (
                'Love Is the Drug',
                'Crashing',
                'Cloverfield',
                'My Best Friend''s Girl',
                'Hot Tub Time Machine',
                'The Last Rites of Ransom Pride',
                'Save the Date',
                'Bachelorette',
                '3, 2, 1... Frankie Go Boom',
                'Queens of Country',
                'Item 47',
                'The Night Before',
                'Now You See Me 2',
                'Allied',
                'Extinction',
                'Cobweb'
                )
        )
    )
}} AS actor