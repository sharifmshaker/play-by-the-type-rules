#! /bin/bash

task="hybridqa"
split="validation"
num_examples=1000
searcher_k=30

base_model_dir="/home/jovyan/model-registry"
searcher_model_name_or_path="/home/jovyan/model-registry/sentence-transformers_all-mpnet-base-v2"
base_output_dir="results/blendsql/hybridqa/${split}/baselines"

# Spawn local jobs 
for model in "meta-llama_meta-llama-3.1-8b-instruct" "meta-llama_llama-3.2-3b-instruct" "meta-llama_llama-3.2-1b-instruct"; do
    for mode in "baseline" "baseline-no-context"; do
        outdir=${base_output_dir}/${model}/${mode}
        mkdir -p ${outdir}
        job="python runner.py --mode ${mode}"
        job+=" --output_dir ${outdir}"
        job+=" --task ${task} --split ${split} --num_examples ${num_examples}"
        job+=" --model_name_or_path ${base_model_dir}/${model}"
        job+=" --searcher_k ${searcher_k}"
        job+=" --searcher_model_name_or_path ${searcher_model_name_or_path}"
        job+=" --bm25_weight 0.5"
        echo ${job}
        export JOB=${job}; bash SUBMIT.sh
    done
done

# Spawn remote vLLM jobs 
for i in "meta-llama_llama-3.3-70b-instruct","..."; do
    for mode in "baseline" "baseline-no-context"; do
        IFS=',' read model service <<< "${i}"
        mkdir -p ${outdir}
        outdir=${base_output_dir}/${model}/${mode}
        job="python runner.py --mode ${mode}"
        job+=" --output_dir ${outdir}"
        job+=" --task ${task} --split ${split} --num_examples ${num_examples}"
        job+=" --model_name_or_path ${base_model_dir}/${model}"
        job+=" --parsing_service_model_name ${model}"
        job+=" --parsing_service ${service}"
        job+=" --searcher_k ${searcher_k}"
        job+=" --searcher_model_name_or_path ${searcher_model_name_or_path}"
        job+=" --bm25_weight 0.5"
        job+=" &> ${outdir}/out.log; exit"
        echo ${job}
        export JOB=${job}; nohup bash SUBMIT.sh &
    done
done