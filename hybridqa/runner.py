import os
os.environ["DB_DIR"] = "..."
os.environ["GPT2_TOKENIZER_PATH"] = "..."
if "HF_ENDPOINT" in os.environ:
    del os.environ["HF_ENDPOINT"]
if "HF_HUB_OFFLINE" in os.environ:
    del os.environ["HF_HUB_OFFLINE"]
os.environ["BLENDSQL_ALWAYS_LOWERCASE_RESPONSE"] = '1'
import transformers
import datasets
import json 
import time 
import sys
import torch 
import gc
from pathlib import Path
from tqdm.auto import tqdm
from transformers import HfArgumentParser, AutoTokenizer
from blendsql.models import ConstrainedModel
from blendsql.db import SQLite
from blendsql.search import HybridSearch

from src.blendsql_utils import get_blendsql_model, do_blendsql_step
from src.metric_utils import calculate_metrics
from src.tasks.task_utils import load_task, get_serialized_hybridqa_db
from src.model_utils import load_model_and_tokenizer
from src.generate import get_lm_pred
from src.grammar import load_grammar
from src.prompts.prompt import get_blendsql_prompt, BASELINE_PROMPT, BASELINE_NO_CONTEXT_PROMPT
from src.args import ExperimentArgs, BlendSQLArguments, BaselineArgs

transformers.logging.set_verbosity_error()
datasets.logging.set_verbosity_error()


def get_model_tokenizer_from_args(args: ExperimentArgs) -> tuple:
    # Are we using a local model, or a remote vLLM service?
    model = None
    if args.parsing_service is not None:
        print("Using remote vLLM service...")
        tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    else:
        print("Using local model...")
        model, tokenizer = load_model_and_tokenizer(args.model_name_or_path)
    return (model, tokenizer)

def main():
    parser = HfArgumentParser([ExperimentArgs, BlendSQLArguments, BaselineArgs]) # type: ignore
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        (args, blendsql_args, baseline_args) = parser.parse_json_file(json_file=os.path.abspath(sys.argv[1]))
    else:
        (args, blendsql_args, baseline_args) = parser.parse_args_into_dataclasses() # type: ignore
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    with open(output_dir / "config.json", "w") as f:
        json.dump(vars(args) | vars(blendsql_args) | vars(baseline_args), f, indent=4) 

    dataset, metric = load_task(args.task, split=args.split, num_examples=args.num_examples)

    if args.mode.startswith('baseline'):
        # Run baseline generation experiment
        if args.mode == 'baseline':
            with open(output_dir / "prompt.md", "w") as f:
                f.write(BASELINE_PROMPT) 
        elif args.mode == 'baseline-no-context': 
            with open(output_dir / "prompt.md", "w") as f:
                f.write(BASELINE_NO_CONTEXT_PROMPT) 
        predictions = []
        model, tokenizer = get_model_tokenizer_from_args(args)
        for idx, example in enumerate(tqdm(dataset, total=len(dataset))):
            curr_pred = {
                "db_path": example["db_path"],
                "question_id": example["question_id"],
                "question": example["question"],
                "answer_text": example["answer_text"],
                "error": None,
                "prompt": None
            }
            try:
                if args.mode in ['baseline', 'baseline-all-context']:
                    db = SQLite(example["db_path"])
                    if args.mode == 'baseline':
                        searcher = HybridSearch(
                            model_name_or_path=baseline_args.searcher_model_name_or_path,
                            documents=db.execute_to_list(
                                "SELECT DISTINCT CONCAT(title, ' | ', content) FROM documents"
                            ),
                            k=baseline_args.searcher_k,
                            bm25_weight=baseline_args.bm25_weight,
                        )
                        text_context="\n\n".join(searcher(example["question"])[0])
                    elif args.mode == 'baseline-all-context':
                        documents = []
                        for row in example["table"]["rows"]:
                            for url_data in row["urls"]:
                                for url, summary in zip(url_data["url"], url_data["summary"]):
                                    title = url.split("/")[-1].replace("_", " ")
                                    documents.append(f"### {title}\n\n{summary}")
                            text_context="\n\n".join(documents)
                    prompt = BASELINE_PROMPT.format(
                        serialized_db=get_serialized_hybridqa_db(example),
                        text_context=text_context,
                        question=example["question"],
                    )
                    if idx == 0:
                        print(prompt)
                elif args.mode == 'baseline-no-context':
                    prompt = BASELINE_NO_CONTEXT_PROMPT.format(
                        question=example["question"],
                    )
                curr_pred['prompt'] = prompt
            except Exception as error:
                print(f"ERROR: {error}")
                curr_pred['error'] = str(error)
                curr_pred['prediction'] = None 
                predictions.append(curr_pred)
                continue
            response, error = get_lm_pred(
                prompt,
                max_tokens=10000,
                model=model,
                model_name=args.parsing_service_model_name or args.model_name_or_path,
                service=args.parsing_service,
                tokenizer=tokenizer,
            )
            if error is not None:
                print(f"ERROR: {error}")
            print(example['question'])
            print(response)
            curr_pred['prediction'] = response
            curr_pred['completion_tokens'] = len(tokenizer.encode(response))
            curr_pred['prompt_tokens'] = len(tokenizer.encode(prompt))
            predictions.append(curr_pred)
        
        print(f'Saving to {output_dir / "predictions.json"}...')
        with open(output_dir / "predictions.json", "w") as f:
            json.dump(predictions, f, indent=4)
        
        # Calculate metrics on results
        aggregated_metrics, metric_df = calculate_metrics(predictions, metric)
        print(json.dumps(aggregated_metrics, indent=4))
        with open(output_dir / "metrics.json", "w") as f:
            json.dump(aggregated_metrics, f, indent=4)
        with open(output_dir / "metric_df.csv", "wb") as f:
            metric_df.to_csv(f, index=False)
            
    elif args.mode.startswith('program-synthesis'):
        # Run BlendSQL experiment
        if args.generation_path is not None:
            print(f"Loading existing BlendSQL queries at {args.generation_path}...")
            with open(args.generation_path, "r") as f:
                generations = json.load(f)
        else:
            print(f"Generating BlendSQL queries using {args.model_name_or_path}...")
            
            generations = []
            model, tokenizer = get_model_tokenizer_from_args(args)
            
            if args.mode == 'program-synthesis':
                documentation_filename = "blendsql-documentation.md"
                fewshot_filename=f"{args.task}-fewshot.md"
            elif args.mode == 'program-synthesis-grammar-prompting':
                documentation_filename = "grammar-prompting.md"
                fewshot_filename=f"{args.task}-fewshot.md"
            else:
                raise ValueError(f"Unknown mode {args.mode}")

            if not args.use_documentation:
                print("NOT USING DOCUMENTATION, as `use_documentation=False`")
                documentation_filename = None 

            if not args.use_fewshot_examples:
                print("NOT USING FEWSHOT EXAMPLES, as `use_fewshot_examples=False`")
                fewshot_filename = None
                
            base_prompt = get_blendsql_prompt(
                documentation_filename=documentation_filename,
                fewshot_filename=fewshot_filename
            )
            
            with open(output_dir / "prompt.md", "w") as f:
                f.write(base_prompt) 

            guided_grammar = None 
            if args.use_guided_grammar:
                print("Loading guided_grammar...")
                from blendsql.ingredients import LLMQA, LLMMap
                
                LLMSearchMap = LLMMap.from_args()
                # Use guidance 
                from guidance.library import lark 
                guided_grammar = lark(
                    load_grammar(
                        ingredients=[LLMQA, LLMMap, LLMSearchMap]
                    ),
                    name="program",
                    max_tokens=500
                )
 
            for idx, example in enumerate(tqdm(dataset, total=len(dataset))):
                curr_pred = {
                    "db_path": example["db_path"],
                    "question_id": example["question_id"],
                    "question": example["question"],
                    "answer_text": example["answer_text"]
                }
                prompt = (
                    base_prompt
                    + f"\n## Context\n\n{get_serialized_hybridqa_db(example)}\n\n## Question\n\n{example['question']}\n\n## BlendSQL:\n\n"
                )
                
                response, error = get_lm_pred(
                    prompt,
                    completion="```sql\n",
                    max_tokens=10000,
                    stop="```",
                    model=model,
                    model_name=args.parsing_service_model_name or args.model_name_or_path,
                    service=args.parsing_service,
                    tokenizer=tokenizer,
                    post_process_f = lambda x: x.strip().removeprefix("```").removesuffix("```").rstrip('`'),
                    guided_grammar=guided_grammar,
                )
                if error is not None:
                    print(f"ERROR: {error}")
                print(example['question'])
                print(response)
                curr_pred['response'] = response
                curr_pred['completion_tokens'] = len(tokenizer.encode(response)) if response is not None else -1
                curr_pred['prompt_tokens'] = len(tokenizer.encode(prompt))
                generations.append(curr_pred)
                
            print(f'Saving to {output_dir / "generations.json"}...')
            with open(output_dir / "generations.json", "w") as f:
                json.dump(generations, f, indent=4)

        if blendsql_args.blendsql_model_name_or_path is not None:
            blendsql_model: ConstrainedModel = get_blendsql_model(*load_model_and_tokenizer(blendsql_args.blendsql_model_name_or_path))
            print(f"Executing BlendSQL queries at '{args.generation_path}'...")
            predictions = []
            for idx, item in enumerate(tqdm(generations)):
                prediction = do_blendsql_step(
                    program=item['response'],
                    db_path=item['db_path'],
                    question=item['question'],
                    answer=item['answer_text'],
                    blendsql_model=blendsql_model,
                    args=blendsql_args
                )
                predictions.append(item | prediction)
                if idx % 5 == 0:
                    torch.cuda.empty_cache()
                    gc.collect()
                if idx % 1000 == 0:
                    # Save a checkpoint
                    aggregated_metrics, metric_df = calculate_metrics(predictions, metric)
                    with open(output_dir / "metrics.json", "w") as f:
                        json.dump(aggregated_metrics, f, indent=4)
                    with open(output_dir / "metric_df.csv", "wb") as f:
                        metric_df.to_csv(f, index=False) 
            # Calculate metrics on results
            aggregated_metrics, metric_df = calculate_metrics(predictions, metric)
            print(json.dumps(aggregated_metrics, indent=4))
            with open(output_dir / "metrics.json", "w") as f:
                json.dump(aggregated_metrics, f, indent=4)
            with open(output_dir / "metric_df.csv", "wb") as f:
                metric_df.to_csv(f, index=False)

    print(f"Saved files to {output_dir}.")
    torch.cuda.empty_cache()
    gc.collect()
    
if __name__ == "__main__":
    main()
