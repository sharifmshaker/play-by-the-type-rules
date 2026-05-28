import typing as t
from functools import cache
import requests
import torch
from transformers import PreTrainedTokenizerBase, AutoModelForCausalLM

PORT = 8000
VLLM_URL = (
    lambda service: f"http://my-vllm-url-{service}:{PORT}/v1/completions"
)
DEFAULT_PARAMETERS = {"temperature": 0.0}


def format_prompt(
    model_name: str,
    prompt: str,
    tokenizer: PreTrainedTokenizerBase,
    completion: t.Optional[str] = None,
    keep_eot_token=False,
) -> str:
    trim_suffix = ""
    # Handle llama model quirks
    if any(tag in model_name for tag in ["3.1"]):
        trim_suffix = (
            """<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"""
        )
    elif any(tag in model_name for tag in ["3.2", "3.3"]):
        trim_suffix = """<|eot_id|>"""
    elif "gemma" in model_name:
        trim_suffix = "<end_of_turn>" 

    messages = [{"role": "user", "content": prompt}]
    if completion is not None:
        messages.append({"role": "assistant", "content": completion})

    add_generation_prompt = bool(completion is None)
    tokenized_message: str = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=add_generation_prompt,
    ) # type: ignore
    if not add_generation_prompt and not keep_eot_token:
        tokenized_message = tokenized_message.removesuffix(trim_suffix)
    return tokenized_message


@cache
def get_lm_pred(
    prompt: str,
    max_tokens: int,
    tokenizer: PreTrainedTokenizerBase,
    model_name: str,
    model: t.Optional[AutoModelForCausalLM] = None,
    service: t.Optional[str] = None,
    completion: t.Optional[str] = None,
    stop: t.Optional[str] = None,
    post_process_f: t.Optional[t.Callable] = None,
    guided_grammar: t.Optional[str] = None,
    num_rollouts: t.Optional[int] = None,
    **kwargs,
) -> t.Tuple[t.Optional[str], t.Optional[str]]:
    """Returns tuple containing (generated_text, error). 
    """
    if post_process_f is None:
        post_process_f = lambda x: x 

    if all(x is None for x in [model, service]):
        raise ValueError("One of `model`, `service` must be passed!")

    tokenized_message = format_prompt(
        model_name=model_name,
        prompt=prompt,
        tokenizer=tokenizer,
        completion=completion
    )

    if service is not None:
        # Generate with vLLM
        payload = {
            "model": f"/model-registry/{model_name}",
            "prompt": tokenized_message,
            "max_tokens": max_tokens,
        } | DEFAULT_PARAMETERS | kwargs
        if stop is not None:
            payload["stop_token_ids"] = tokenizer.encode(stop)
            payload["include_stop_str_in_output"] = False
        if guided_grammar is not None:
            payload["guided_grammar"] = guided_grammar

        resp = requests.post(
            VLLM_URL(service),
            json=payload,
        )
        try:
            resp.raise_for_status()
            response, error = (resp.json()["choices"][0]["text"], None)
        except:
            response, error = (None, resp.text)
    else:
        if guided_grammar is None:
            # Generate with local transformers implementation
            with torch.no_grad():
                prompt_inputs = tokenizer(
                    text=tokenized_message,
                    return_tensors="pt",
                    padding=True,
                    padding_side="left",
                    add_special_tokens=False,
                )
                prompt_inputs = prompt_inputs.to(model.device)
                if num_rollouts is None:
                    outputs = model.generate(
                        **prompt_inputs,
                        do_sample=False,
                        stop_strings=stop,
                        max_new_tokens=2000,
                        tokenizer=tokenizer
                    )
                    outputs = outputs[:, prompt_inputs["input_ids"].shape[1] :]
                    decoded_output = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
                    response, error = (decoded_output, None)
                else:
                    # Generate n and return as list
                    responses = []
                    for _ in range(num_rollouts):
                        outputs = model.generate(
                            **prompt_inputs,
                            do_sample=True,
                            temperature=0.9,
                            top_p=1.0,
                            max_new_tokens=2000,
                            tokenizer=tokenizer
                        )
                        outputs = outputs[:, prompt_inputs["input_ids"].shape[1] :]
                        decoded_output = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
                        responses.append(post_process_f(decoded_output))
                    return (responses, None) 
        else:
            # Use guidance
            import guidance 
            try:
                lm = guidance.models.Transformers(
                    model=model,
                    tokenizer=tokenizer,
                    echo=False,
                    chat_template=guidance.chat.Llama3ChatTemplate
                )
                with guidance.user():
                    lm += prompt
                with guidance.assistant():
                    lm += completion
                    lm += guided_grammar
                response, error = lm['program'], None
            except Exception as e:
                response, error = None, e 
    return (post_process_f(response) if response is not None else response, error)
