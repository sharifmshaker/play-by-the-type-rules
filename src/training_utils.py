from .generate import format_prompt
from .prompts.prompt import get_blendsql_prompt, BASELINE_PROMPT


def format_baseline_training_prompt(
    tokenizer, model_name_or_path, example
):
    text_context="\n\n".join(example['documents'])
    prompt = BASELINE_PROMPT.format(
        serialized_db=example['serialized_db'],
        text_context=text_context,
        question=example["question"],
    )
    formatted_text = format_prompt(
        model_name=model_name_or_path,
        prompt=prompt,
        completion=example["answer_text"],
        tokenizer=tokenizer,
        keep_eot_token=True,
    )
    if example['question_id'] == '00013190d4370f73':
        print(formatted_text)
    return formatted_text


def format_program_synthesis_training_prompt(tokenizer, model_name_or_path, example, include_completion: bool = True):
    base_prompt = get_blendsql_prompt(
        documentation_filename="blendsql-documentation.md",
    )

    blendsql_query = None
    if include_completion:
        blendsql_query = example['response'].strip('\n')

    prompt = (
        base_prompt
        + f"\n## Context\n\n{example['serialized_db']}\n\n## Question\n\n{example['question']}\n\n## BlendSQL:\n\n"
    )

    formatted_text = (
        format_prompt(
            model_name=model_name_or_path,
            prompt=prompt,
            completion=(
                f"```sql\n{blendsql_query}```" if include_completion else f"```sql\n"
            ),
            tokenizer=tokenizer,
            keep_eot_token=False,
        )
    )
    if example["question_id"] == "00013190d4370f73":
        print(formatted_text)
    return formatted_text
