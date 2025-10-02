# Documentation

# **Functions**

## LLMQA

The `LLMQA` is an aggregate function that returns a single scalar value. The `question` argument can contain an f-string formatted variable.

```python
def LLMQA(
    question: str,
    *context: Optional[Union[ColumnRef, Subquery] # Can be a BlendSQL subquery, or a `{tablename}.{colname}` reference
):
    ...
```

```sql
SELECT {{
    /* Use f-strings to fill result from subquery */
    LLMQA(
        'Which teams drafted {}?', 
        (
            SELECT name FROM w 
            WHERE school = 'university of georgia'
        )
    )
}}
```

```sql
SELECT name FROM w
WHERE w.state = {{
    LLMQA(
        /* No `context` argument will do a search over all documents with the raw `question`*/
        "Which state is known as 'The Golden State'?"
    )
}}
```

## LLMMap

The `LLMMap` is a unary scalar function, much like `LENGTH` or `ABS` in SQlite. The output of this function is set as a new column in a temporary table, for later use within the wider query.

```python
def LLMMap(
    question: str,
    values: ColumnRef # {tablename}.{colname}
):
    ...
```

```sql
SELECT * FROM posts p
WHERE {{
    LLMMap(
        'Is the sentiment of this post positive?',
        p.content
    )      
}} = TRUE
```

### LLMSearchMap 

If a given question requires knowledge outside of what is present in the database values, the `LLMSearchMap` function can be utilized. This will fetch relevant context for each mapped value in the database. 

```python
def LLMSearchMap(
    question: str,
    values: ColumnRef # {tablename}.{colname}
):
    ...
```

Examples:

```sql
SELECT COUNT(DISTINCT(s.CDSCode)) FROM schools s
JOIN satscores sa ON s.CDSCode = sa.cds
WHERE sa.AvgScrMath > 560
/* Generations below will be restricted to a boolean - no need to pass `options`. */
AND {{LLMSearchMap('Is {} a county in the California Bay Area?', s.County)}} = TRUE
```

### Common Mistakes

Both `LLMSearchMap` and `LLMMap` will NOT work when the `values` argument is a subquery. For example, the below query is incorrect. DO NOT do this:

```sql
SELECT {{
    /* Below will raise an error! Use LLMQA here instead. */
    LLMSearchMap(
        'How many professional leagues did {} play in?', 
        (SELECT player FROM w ORDER BY hits DESC LIMIT 1)
    )
}}
```

Remember, in your task, all database values are lowercased. Use double-quotes (e.g. `''`) to escape single-quotes in strings.