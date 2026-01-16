# **General Syntax**

BlendSQL is a superset of SQLite. All traditional SQLite syntax is valid. However, BlendSQL adds one new aggregate function `LLMQA`, and one new scalar function `LLMMap`. The Lark context-free grammar for the two new functions is below.


### [BEGIN blendsql Functions]
BLENDSQL_FUNCTION_BEGIN: "{{"
BLENDSQL_FUNCTION_END: "}}"

// The `LLMQA` is an aggregate function that returns a single scalar value. The `question` argument can contain an f-string formatted variable.
LLMQA: "LLMQA"i
blendsql_aggregate_functions: (LLMQA)

// The `LLMMap` is a unary scalar function, much like `LENGTH` or `ABS` in SQlite. The output of this function is set as a new column in a temporary table, for later use within the wider query.
LLMMAP: "LLMMap"i
// If a given question requires knowledge outside of what is present in the database values, the `LLMSearchMap` function can be utilized. This will fetch relevant context for each mapped value in the database. 
LLMSEARCHMAP: "LLMSearchMap"i
blendsql_scalar_functions: (LLMMAP|LLMSEARCHMAP)

tuple: "(" [literal ","]* literal ")"
value_array: (tuple | "(" subquery ")" | column_ref)
column_ref: [tablename "."] columnname
question: QUOTED_STRING // Use double-quotes (e.g. `''`, `""`) to escape quotes in strings. 

blendsql_aggregate_args: question ["," value_array]
blendsql_aggregate_expr: BLENDSQL_FUNCTION_BEGIN blendsql_aggregate_functions "(" blendsql_aggregate_args ")" BLENDSQL_FUNCTION_END

blendsql_scalar_args: question "," column_ref
blendsql_scalar_expr: BLENDSQL_FUNCTION_BEGIN blendsql_scalar_functions "(" blendsql_scalar_args ")" BLENDSQL_FUNCTION_END
### [END blendsql Functions]