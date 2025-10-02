Generate BlendSQL given the question to answer the question correctly. BlendSQL is a superset of SQL, which adds external function calls for information not found within native SQL. These function calls are always wrapped in double-curly brackets ("{", "}").

# Documentation

# **General Syntax**

## `ValueArray`

A `ValueArray` is a reference to a list of values. This can be written using:

- Standard column `{tablename}.{columnname}` syntax (`tablename` can be ommitted, and standard SQL binding logic will apply)

- A BlendSQL query which returns a 1d array of values (`(SELECT value FROM table WHERE ...)`)

# **Functions**

## LLMQA

The `LLMQA` is an aggregate function that returns a single scalar value. The `question` argument can contain an f-string formatted variable.

```python
def LLMQA(
    question: str,
    values: Optional[ValueArray]
):
    ...
```

```sql
WITH player AS (
    SELECT name FROM w 
    WHERE school = 'university of georgia'
) SELECT {{LLMQA('Which teams drafted {}?', player.name)}} /* Use question f-strings to reference CTE */
```

```sql
SELECT name FROM w
WHERE w.state = {{
    LLMQA(
        /* No `values` argument will do a search over all documents with the `question`*/
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

# Parsing Examples

Note that ALL content in the database is LOWERCASED.

## Context

-- `w` is sourced from the `1999_Kyalami_Superbike_World_Championship_round` Wikipedia table
CREATE TABLE w (
  no INTEGER,
  rider TEXT,
  team TEXT,
  motorcycle TEXT
)
/*
3 example rows:
SELECT * FROM w LIMIT 3
|   no | rider          | team                 | motorcycle      |
|-----:|:---------------|:---------------------|:----------------|
|    1 | carl fogarty   | ducati performance   | ducati 996      |
|    4 | akira yanagawa | kawasaki racing team | kawasaki zx-7rr |
|    5 | colin edwards  | castrol honda        | honda rc45      |
*/

## Question

After what season did the number 7 competitor retire ?
                
## BlendSQL

```sql
SELECT {{
    LLMQA(
        'When did {} retire?', (
            SELECT rider FROM w 
            WHERE no = 7 
        ) 
    )
}}
```

---

## Context 

-- `w` is sourced from the `Marine_defense_battalions_0` Wikipedia table.
CREATE TABLE w (
	"battalion name" TEXT, 
	"location ( s )" TEXT, 
	"notable commanding officers" TEXT
)
/*
3 example rows:
SELECT * FROM "w" LIMIT 3
| battalion name        | location ( s )                                                                                         | notable commanding officers                                                            |
|:----------------------|:-------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------|
| 1st defense battalion | pearl harbor , hawaii wake island johnston island palmyra island marshall islands mariana islands guam | bertram a . bone augustus w. cockrell john h. griebel lewis a. hohn                    |
| 2nd defense battalion | hawaii american samoa tarawa guam okinawa                                                              | bertram a . bone thomas e. bourke charles i. murray raymond e. knapp                   |
| 3rd defense battalion | pearl harbor , hawaii midway island guadalcanal tulagi bougainville                                    | robert h. pepper harry k. pickett harold c. roberts kenneth w. benner edward h. forney |
*/

## Question

What is the battalion name for the battalion located at Guantanamo Bay and commanded by the author of the book Rifleman 's Creed ?

## BlendSQL:

```sql
SELECT "battalion name" FROM w 
WHERE "location ( s )" LIKE '%guantanamo bay%'
/* Below, we use double quotes '' to escape */
AND {{LLMSearchMap('Does this include the author of the book Rifleman''s Creed?', "notable commanding officers")}} = TRUE
```

---

 
## Context

-- `w` is sourced from the `2010_FIBA_Under-17_World_Championship_squads` Wikipedia table
CREATE TABLE w (
  "#" INTEGER, 
  pos TEXT, 
  name TEXT, 
  "dob/age" TEXT, 
  height TEXT, 
  club TEXT
)
/*
3 example rows:
SELECT * FROM "w" LIMIT 3
|   # | pos   | name           | dob/age                             | height                 | club                         |
|----:|:------|:---------------|:------------------------------------|:-----------------------|:-----------------------------|
|   4 | guard | quinn cook     | ( 1993-3-23 ) 1993-3-23 ( aged 17 ) | 1.86 metres ( 6.1 ft ) | dematha catholic high school |
|   5 | guard | anthony wroten | ( 1993-4-13 ) 1993-4-13 ( aged 17 ) | 1.96 metres ( 6.4 ft ) | garfield high school         |
|   6 | guard | marquis teague | ( 1993-2-28 ) 1993-2-28 ( aged 17 ) | 1.89 metres ( 6.2 ft ) | pike high school             |
*/

## Question

How many NBA teams did the shortest player play for ?

## BlendSQL:

```sql
SELECT {{
    LLMQA(
        'How many NBA teams has {} played for?', (
            SELECT name FROM w 
            ORDER BY {{LLMMap('Height in feet?', w.height)}}
            LIMIT 1
        )
    )
}}
```

---

## Context 

-- `w` is sourced from the `Venues_of_the_1984_Winter_Olympics` Wikipedia table
CREATE TABLE w (
  venue TEXT, 
  sports TEXT, 
  capacity TEXT
)
/*
3 example rows:
SELECT * FROM "w" LIMIT 3
| venue                | sports                                                                     | capacity   |
|:---------------------|:---------------------------------------------------------------------------|:-----------|
| bjelašnica           | alpine skiing ( men )                                                      | not listed |
| igman , malo polje   | nordic combined ( ski jumping ) , ski jumping                              | not listed |
| igman , veliko polje | biathlon , cross-country skiing , nordic combined ( cross-country skiing ) | not listed |
*/

## Question

What is the capacity of the venue that was named in honor of Juan Antonio Samaranch in 2010 after his death ?

```sql
SELECT capacity FROM w WHERE venue = {{
    LLMQA(
        'Which venue was named in 2010 in honor of Juan Antonio Samaranch after his death?'                
    )
}}
```

---

## Context 

-- `w` is sourced from the `United_States_at_the_2011_World_Aquatics_Championships` Wikipedia table.
CREATE TABLE w (
	medal TEXT, 
	name TEXT, 
	sport TEXT, 
	event TEXT, 
	"time/score" TEXT, 
	date TEXT
)
/*
3 example rows:
SELECT * FROM "w" LIMIT 3
| medal   | name                                     | sport               | event                    | time/score   | date    |
|:--------|:-----------------------------------------|:--------------------|:-------------------------|:-------------|:--------|
| gold    | andrew gemmell sean ryan ashley twichell | open water swimming | 5 km team event          | 57:0.6       | july 21 |
| gold    | dana vollmer                             | swimming            | women 's 100 m butterfly | 56.87        | july 25 |
| gold    | ryan lochte                              | swimming            | men 's 200 m freestyle   | 1:44.44      | july 26 |
*/

## Question

What is the name of the oldest person whose result , not including team race , was above 2 minutes ?

## BlendSQL:

```sql
WITH t AS (
    SELECT name FROM w 
    WHERE CAST(SUBSTR("time/score", 1, INSTR("time/score", ':') -1) AS INT) >= 2
    /* We can infer the below question just given the database values - no need for LLMSearchMap */
    AND {{LLMMap('Is {} a team event?', w.event)}} = FALSE
) SELECT Name FROM t 
/* Use the `LLMSearchMap` function to fetch relevant context */
ORDER BY {{LLMSearchMap('What year was {} born?', t.name)}} ASC LIMIT 1
```

---