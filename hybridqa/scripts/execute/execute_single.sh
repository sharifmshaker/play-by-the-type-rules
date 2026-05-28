#! /bin/bash

# Saves results in `{parsing_model}/{execution_model}/{constrained|unconstrained}` directories
task="hybridqa"
split="validation"
num_examples=1000
mode="program-synthesis"

base_model_dir="/home/jovyan/model-registry"
searcher_model_name_or_path="/home/jovyan/model-registry/sentence-transformers_all-mpnet-base-v2"
base_output_dir="results/blendsql/hybridqa/${split}/executions"

base_generation_path="results/blendsql/hybridqa/${split}/generations"
execution_model="meta-llama_llama-3.2-1b-instruct"
parsing_model="meta-llama_meta-llama-3.1-8b-instruct"
subdir="constrained"
enable_constrained_decoding=0
infer_gen_constraints=0

outdir=${base_output_dir}/${parsing_model}/${execution_model}/${subdir}
mkdir -p ${outdir}
job="python runner.py --mode program-synthesis"
job+=" --output_dir ${outdir}"
job+=" --task ${task} --split ${split} --num_examples ${num_examples}"
job+=" --enable_constrained_decoding ${enable_constrained_decoding} --infer_gen_constraints ${infer_gen_constraints}"
job+=" --generation_path ${base_generation_path}/${parsing_model}/generations.json"
job+=" --blendsql_model_name_or_path ${base_model_dir}/${execution_model}"
job+=" --llmmap_args '{\"num_few_shot_examples\": 3, \"batch_size\": 100}'"
job+=" --llmsearchmap_args '{\"num_few_shot_examples\": 3, \"batch_size\": 1, \"searcher_model_name_or_path\": \"${searcher_model_name_or_path}\", \"searcher_bm25_weight\": 0.5, \"searcher_k\": 1}'"
job+=" --llmqa_args '{\"num_few_shot_examples\": 0, \"searcher_model_name_or_path\": \"${searcher_model_name_or_path}\", \"searcher_bm25_weight\": 0.5, \"searcher_k\": 10}'"
export JOB=${job}; bash SUBMIT.sh | tee ${outdir}/out.log
