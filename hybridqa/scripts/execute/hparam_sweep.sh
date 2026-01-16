#! /bin/bash

# Saves results in `{parsing_model}/{execution_model}/{constrained|unconstrained}` directories
task="hybridqa"
split="validation"
num_examples=1000
mode="program-synthesis"

base_model_dir="/home/jovyan/model-registry"
searcher_model_name_or_path="/home/jovyan/model-registry/sentence-transformers_all-mpnet-base-v2"
base_generation_path="results/blendsql/hybridqa/${split}/generations"
base_output_dir="results/blendsql/hybridqa/${split}/executions/"
execution_model="meta-llama_meta-llama-3.1-8b-instruct"
parsing_model="meta-llama_llama-3.3-70b-instruct"

for llmqa_k in 10 15 20; do
    for llmsearchmap_k in 1 3 5; do
        outdir=${base_output_dir}/hparam_sweep/${parsing_model}/${execution_model}/llmqa_k_${llmqa_k}/llmsearchmap_k_${llmsearchmap_k}
        mkdir -p ${outdir}
        job="python runner.py --mode ${mode}"
        job+=" --output_dir ${outdir}"
        job+=" --task ${task} --split ${split} --num_examples ${num_examples}"
        job+=" --generation_path ${base_generation_path}/${parsing_model}/generations.json"
        job+=" --blendsql_model_name_or_path ${base_model_dir}/${execution_model}"
        job+=" --llmmap_args '{\"num_few_shot_examples\": 3, \"batch_size\": 100'}"
        job+=" --llmsearchmap_args '{\"num_few_shot_examples\": 3, \"batch_size\": 1, \"searcher_model_name_or_path\": \"${searcher_model_name_or_path}\", \"searcher_bm25_weight\": 0.5, \"searcher_k\": ${llmsearchmap_k}'}"
        job+=" --llmqa_args '{\"num_few_shot_examples\": 0, \"searcher_model_name_or_path\": \"${searcher_model_name_or_path}\", \"searcher_bm25_weight\": 0.5, \"searcher_k\": ${llmqa_k}}'"
        export JOB=${job}; bash SUBMIT.sh | tee ${outdir}/out.log
    done
done