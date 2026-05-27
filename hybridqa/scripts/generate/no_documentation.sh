#! /bin/bash

task="hybridqa"
split="validation"
num_examples=1000
mode="program-synthesis"

base_model_dir="/home/jovyan/model-registry"
base_output_dir="results/blendsql/hybridqa/${split}/generations"

# Spawn local jobs 
for i in "meta-llama_meta-llama-3.1-8b-instruct",'0,1' "meta-llama_llama-3.2-3b-instruct",'2' "meta-llama_llama-3.2-1b-instruct",'3'; do
    IFS=',' read model cuda_devices <<< "${i}"
    outdir=${base_output_dir}/no_documentation/${model} 
    mkdir -p ${outdir}
    job="CUDA_VISIBLE_DEVICES="${cuda_devices}" python runner.py --mode ${mode} --use_documentation 0"
    job+=" --output_dir ${outdir}"
    job+=" --task ${task} --split ${split} --num_examples ${num_examples}"
    job+=" --model_name_or_path ${base_model_dir}/${model}"
    job+=" &> ${outdir}/out.log; exit"
    echo ${job}
    export JOB=${job}; nohup bash SUBMIT.sh &
done

# Spawn remote vLLM jobs 
for i in "meta-llama_llama-3.3-70b-instruct","..."; do
    IFS=',' read model service <<< "${i}"
    outdir=${base_output_dir}/no_documentation/${model}
    job="python runner.py --mode ${mode} --use_documentation 0"
    mkdir -p ${outdir}
    job+=" --output_dir ${outdir}"
    job+=" --task ${task} --split ${split} --num_examples ${num_examples}"
    job+=" --model_name_or_path ${base_model_dir}/${model}"
    job+=" --parsing_service_model_name ${model}"
    job+=" --parsing_service ${service}"
    job+=" &> ${outdir}/out.log; exit"
    echo ${job}
    export JOB=${job}; nohup bash SUBMIT.sh &
done