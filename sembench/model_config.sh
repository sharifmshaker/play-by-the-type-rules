#!/bin/bash
declare -A MODEL_NAME_OR_PATH
declare -A BASE_URL
declare -A EXTRA_BODY
declare -A EXTRA_SERVE_ARGS

MODEL_NAME_OR_PATH["gemma_4b"]="RedHatAI/gemma-3-4b-it-quantized.w4a16"
BASE_URL["gemma_4b"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["gemma_4b"]=""
EXTRA_SERVE_ARGS["gemma_4b"]=''

MODEL_NAME_OR_PATH["gemma_12b"]="RedHatAI/gemma-3-12b-it-quantized.w4a16"
BASE_URL["gemma_12b"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["gemma_12b"]=""
EXTRA_SERVE_ARGS["gemma_12b"]=''

MODEL_NAME_OR_PATH["gemma_e4b"]="prithivMLmods/gemma-4-E4B-it-FP8"
BASE_URL["gemma_e4b"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["gemma_e4b"]=""
EXTRA_SERVE_ARGS["gemma_e4b"]=''

MODEL_NAME_OR_PATH["gemma_e2b"]="prithivMLmods/gemma-4-E2B-it-FP8"
BASE_URL["gemma_e2b"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["gemma_e2b"]=""
EXTRA_SERVE_ARGS["gemma_e2b"]=''

MODEL_NAME_OR_PATH["qwen3_4b_thinking"]="Qwen/Qwen3-4B-Thinking-2507-FP8"
BASE_URL["qwen3_4b_thinking"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["qwen3_4b_thinking"]='{
  "temperature": 0.6,
  "top_p": 0.95,
  "top_k": 20,
  "min_p": 0.0,
  "presence_penalty": 1.0,
  "repetition_penalty": 1.0
}'
EXTRA_SERVE_ARGS["qwen3_4b_thinking"]='--reasoning-parser qwen3'

MODEL_NAME_OR_PATH["qwen3_4b_nothinking"]="Qwen/Qwen3-4B-Instruct-2507-FP8"
BASE_URL["qwen3_4b_nothinking"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["qwen3_4b_nothinking"]='{
  "temperature": 0.6,
  "top_p": 0.95,
  "top_k": 20,
  "min_p": 0.0,
  "presence_penalty": 1.0,
  "repetition_penalty": 1.0
}'
EXTRA_SERVE_ARGS["qwen3_4b_thinking"]='--reasoning-parser qwen3'

MODEL_NAME_OR_PATH["qwen35_4b_nothinking"]="cyankiwi/Qwen3.5-4B-AWQ-4bit"
BASE_URL["qwen35_4b_nothinking"]="http://127.0.0.1:8000/v1/"
EXTRA_BODY["qwen35_4b_nothinking"]='{
  "temperature": 1.0,
  "top_p": 0.95,
  "top_k": 20,
  "min_p": 0.0,
  "presence_penalty": 1.5,
  "repetition_penalty": 1.0,
  "chat_template_kwargs": {"enable_thinking": false}
}'
EXTRA_SERVE_ARGS["qwen35_4b_nothinking"]='--reasoning-parser qwen3'

set_model_config() {
    local key=$1
    model_path="${MODEL_NAME_OR_PATH[$key]}"
    base_url="${BASE_URL[$key]}"
    extra_body="${EXTRA_BODY[$key]}"
    extra_serve_args="${EXTRA_SERVE_ARGS[$key]}"
}