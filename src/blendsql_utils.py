import typing as t
import pandas as pd
import json
from transformers import (
    PreTrainedModel,
    PreTrainedTokenizerBase,
)
import traceback
import guidance
from blendsql.models import TransformersLLM, ConstrainedModel

from .args import BlendSQLArguments


def get_full_traceback(e: Exception) -> str:
    """Formats an exception and its traceback as a string."""
    return "".join(traceback.format_exception(type(e), e, e.__traceback__))


def get_blendsql_model(
    model: PreTrainedModel, tokenizer: PreTrainedTokenizerBase
) -> ConstrainedModel:
    import os
    from guidance.models._transformers import TransformersTokenizer
    from transformers import AutoTokenizer
    from guidance.chat import Llama3ChatTemplate

    def new_fallback_byte_decoder():
        byte_decoder = AutoTokenizer.from_pretrained(
            os.getenv("GPT2_TOKENIZER_PATH"), use_fast=False
        ).byte_decoder  # fall back to gpt2 mapping

        # some special tokens may not have their whitespace encoded...
        byte_decoder[" "] = 32
        byte_decoder["\n"] = 10
        byte_decoder["\r"] = 13
        byte_decoder["\t"] = 9
        byte_decoder["▁"] = 32

        return byte_decoder

    # Monkeypatch the method
    TransformersTokenizer._fallback_byte_decoder = new_fallback_byte_decoder

    lm = guidance.models.Transformers(
        model=model,
        tokenizer=tokenizer,
        chat_template=Llama3ChatTemplate,
        compute_log_probs=False,
        echo=False,
    )

    # TODO: should probably add this to blendsql
    class LocalBlendSQLModel(TransformersLLM):

        def __init__(
            self,
            tokenizer: PreTrainedTokenizerBase,
            caching: bool = True,
            **kwargs,
        ):
            ConstrainedModel.__init__(
                self,
                model_name_or_path="",
                requires_config=False,
                tokenizer=tokenizer,
                config={},
                caching=caching,
                **kwargs,
            )

        def _load_model(self):
            return lm

    return LocalBlendSQLModel(tokenizer, caching=False)


def load_blendsql_connection(db, blendsql_model, args):
    from blendsql import BlendSQL
    from blendsql.ingredients import LLMQA, LLMMap
    from blendsql.search import HybridSearch

    if not args.infer_gen_constraints:
        print("LOADING BLENDSQL WITH `infer_gen_constraints=False`")

    bsql = BlendSQL(
        db,
        model=blendsql_model,
        verbose=True,
        infer_gen_constraints=args.infer_gen_constraints,
    )

    LLMSearchMap = LLMMap.from_args(
        searcher=HybridSearch(
            model_name_or_path=args.llmsearchmap_args["searcher_model_name_or_path"],
            documents=bsql.db.execute_to_list(  # type: ignore
                "SELECT DISTINCT CONCAT(title, ' | ', content) FROM documents"
            ),
            k=args.llmsearchmap_args["searcher_k"],
            bm25_weight=args.llmsearchmap_args["searcher_bm25_weight"],
        ),
        num_few_shot_examples=args.llmsearchmap_args["num_few_shot_examples"],
        batch_size=args.llmsearchmap_args["batch_size"],
        enable_constrained_decoding=args.enable_constrained_decoding,
    )

    bsql.ingredients = {
        LLMMap.from_args(
            num_few_shot_examples=args.llmmap_args["num_few_shot_examples"],
            batch_size=args.llmmap_args["batch_size"],
            enable_constrained_decoding=args.enable_constrained_decoding,
        ),
        LLMQA.from_args(
            searcher=HybridSearch(
                model_name_or_path=args.llmqa_args["searcher_model_name_or_path"],
                documents=bsql.db.execute_to_list(  # type: ignore
                    "SELECT DISTINCT CONCAT(title, ' | ', content) FROM documents"
                ),
                k=args.llmqa_args["searcher_k"],
                bm25_weight=args.llmqa_args["searcher_bm25_weight"],
            ),
            num_few_shot_examples=args.llmqa_args["num_few_shot_examples"],
            context_formatter=lambda df: json.dumps(
                df.to_dict(orient="records"),
                ensure_ascii=False,
                indent=4,
            ),
            enable_constrained_decoding=args.enable_constrained_decoding,
        ),
        LLMSearchMap,
    }
    return bsql


def format_blendsql_output(df: t.Union[pd.DataFrame, None]) -> t.Union[str, list]:
    if df is None:
        return []
    if df.empty:
        return []
    flattened_preds = [str(i) for i in df.values.flat]
    return flattened_preds


def do_blendsql_step(
    program: str,
    db_path: str,
    question: str,
    answer: str,
    blendsql_model: ConstrainedModel,
    args: BlendSQLArguments,
):
    print(f"Question: {question}")
    try:
        bsql = load_blendsql_connection(
            db=db_path, blendsql_model=blendsql_model, args=args
        )
        print(program)
        res = bsql.execute(program)
        print(f"Answer: {answer}")
        print(f"Prediction:\n{res.df}")
        return {
            "completion_tokens": res.meta.completion_tokens,
            "prompt_tokens": res.meta.prompt_tokens,
            "process_time_seconds": res.meta.process_time_seconds,
            "prediction": format_blendsql_output(res.df),
            "error": None,
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "completion_tokens": None,
            "prompt_tokens": None,
            "process_time_seconds": None,
            "prediction": None,
            "error": get_full_traceback(e),
        }
