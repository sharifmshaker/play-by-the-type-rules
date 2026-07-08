"""
model_factory.py — let SemBench's eval_blendsql.py drive Gemini as well as vLLM.

SemBench's src/eval_scripts/eval_blendsql.py hard-codes the vLLM backend:

    bsql = BlendSQL(
        DuckDB(con),
        model=VLLM(model_name_or_path=model_name_or_path,
                   base_url=base_url, extra_body=extra_body),
        ...
    )

To reuse ALL of SemBench's machinery (query iteration, ground truth, metrics,
CSV logging) while swapping the model, make two edits to eval_blendsql.py:

  1) at the top:      from model_factory import make_model
  2) replace the      model=VLLM(...)      argument with     model=make_model()

Then select the backend per run via env vars (see run_gemini.sh):
    BACKEND=gemini  MODEL_NAME_OR_PATH=gemini-3.1-flash-lite  GEMINI_API_KEY=...

Backend defaults to "vllm", so the stock Gemma runs via run.sh are unaffected.
"""
import os


def make_model():
    backend = os.getenv("BACKEND", "vllm").lower()
    name = os.environ["MODEL_NAME_OR_PATH"]

    # extra_body carries vLLM sampling params / chat_template_kwargs (from
    # model_config.sh EXTRA_BODY). Harmless-but-unused for API backends.
    extra_body = None
    if os.getenv("EXTRA_BODY"):
        import json
        extra_body = json.loads(os.environ["EXTRA_BODY"])

    if backend == "vllm":
        from blendsql.models import VLLM
        return VLLM(model_name_or_path=name,
                    base_url=os.environ["BASE_URL"],
                    extra_body=extra_body)

    if backend == "gemini":
        from blendsql.models import Gemini
        # NOTE: the stock Gemini class does NOT enforce BlendSQL's grammar
        # (constrained decoding is vLLM-only). Run these with
        # ENABLE_CONSTRAINED_DECODING=false so the Gemma side can be compared
        # like-for-like (also set to false). To give Gemini its own structured
        # output instead, subclass Gemini and override _format_inputs to map
        # item.grammar -> extra_body["response_format"]
        # (see FINDINGS.md -> "Limitations & further study": model-fair CD test).
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return Gemini(name, api_key=api_key)

    raise ValueError(f"Unknown BACKEND={backend!r} (expected 'vllm' or 'gemini')")
