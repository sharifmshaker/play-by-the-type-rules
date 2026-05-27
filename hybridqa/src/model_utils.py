from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)

def load_model_and_tokenizer(model_path):
    import torch

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        # attn_implementation="flash_attention_2",
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left")
    tokenizer.pad_token = tokenizer.eos_token
    return (model, tokenizer)

