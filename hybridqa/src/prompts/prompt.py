from pathlib import Path
import typing as t 

CURR_DIR = Path(__file__).parent


BLENDSQL_PROMPT = """Generate BlendSQL given the question to answer the question correctly. BlendSQL is a superset of SQL, which adds external function calls for information not found within native SQL. These function calls are always wrapped in double-curly brackets ("{{", "}}").

{documentation}

# Parsing Examples

Note that ALL content in the database is LOWERCASED.

"""

BASELINE_PROMPT = """Answer the question using the table and text context provided.
Keep the answers as short as possible, without leading context. For example, do not say 'The answer is 2', simply say '2'.

## Table Context

{serialized_db}

## Text Context

{text_context}

## Question

{question}

## Answer:

"""

BASELINE_NO_CONTEXT_PROMPT = """Answer the question.
Keep the answers as short as possible, without leading context. For example, do not say 'The answer is 2', simply say '2'.
You MUST provide an answer.

## Question

{question}

## Answer:

"""

def get_blendsql_prompt(documentation_filename: t.Optional[str] = None, fewshot_filename: t.Optional[str] = None) -> str:
    if all(x is None for x in [documentation_filename, fewshot_filename]):
        print("WARNING\nBoth `documentation_filename` and `fewshot_filename` are None. Is this on purpose?")
    
    return BLENDSQL_PROMPT.format(documentation=open(CURR_DIR / documentation_filename).read() if documentation_filename is not None else '') + (open(CURR_DIR / fewshot_filename).read() if fewshot_filename is not None else '')

