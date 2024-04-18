import kfp
from kfp import dsl
from kfp import Client

import os
import random
import subprocess
import string

def random_suffix() -> string:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))



def collect_data_op() :
    return dsl.ContainerOp(
        name="Data Collection",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest', 
        command=['python3', '/app/data/collect.py'],
        #command=['echo','ok']
    )

def combine_data_op() :
    return dsl.ContainerOp(
        name="Combine_data",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest', 
        command=['python3', '/app/data/combine.py'],
    )

def cleanning_data_op() :
    return dsl.ContainerOp(
        name="Data cleanning",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest', 
        command=['python3', '/app/data/cleanning.py'],
    )

def preprocessing_data_op() :
    return dsl.ContainerOp(
        name="Data preprocessing",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest', 
        command=['python3', '/app/data/preprocessing.py'],
    )

def fine_tune_model_op():
    return dsl.ContainerOp(
        name="fine-tuning-model",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest',
        command=['python3','/app/Fine-tune-model/fine-tune-model.py'],
        #command=['echo', 'OK'],
        #arguments=[model_path,test_data],
    )

def bert_output_before_fine_tuning_op():
    return dsl.ContainerOp(
        name="output before fine tuning",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest',
        command=['python3','/app/Model_output/model_output.py'],
        #arguments=[model_path,test_data],
    )

def bert_fine_tuned_model_output_op():
    
    return dsl.ContainerOp(
        name="output after fine tuning",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest',
        command=['python3','/app/Fine_tuned_model_output/fine_tuned_model_output.py'],
        #arguments=[model_path,test_data],
        #resource_requests={"cpu": "4", "memory": "4Gi"},
        #resource_limits={"cpu": "8", "memory": "8Gi"},
    )

def evaluate_fine_tuned_model_op():
    #test_data='preprocessed_data.pkl'
    #model_path='model'
    return dsl.ContainerOp(
        name="fine tuned model evaluation",
        image='europe-west3-docker.pkg.dev/int-infra-training-gcp/maamoun/llm_pipeline:latest',
        command=['python3','/app/evaluate_fine_tuned_model/evaluate_fine_tuned_model.py'],
        #arguments=[model_path,test_data],
    )

@dsl.pipeline(
    name='bert Fine-Tuning Pipeline',
    description='A pipeline that fine-tunes bert model with sprecific data.'
)

def llm_pipeline():
    dataset='ag_news'
    split='train[:1%]'
    """
    preprocess_task = preprocess_data_op().set_cpu_request('512Mi').set_cpu_limit('1').set_memory_request('512Mi').set_memory_limit('1Gi')
    fine_tune_model=fine_tune_model_op().after(preprocess_task).set_cpu_request('512Mi').set_cpu_limit('1').set_memory_request('512Mi').set_memory_limit('1Gi')
    
    generate_output_task = bert_output_before_fine_tuning_op().after(fine_tune_model).set_cpu_request('512Mi').set_cpu_limit('1').set_memory_request('512Mi').set_memory_limit('1Gi')
    generate_output_after_fine_tuning_task=bert_fine_tuned_model_output_op()after(generate_output_task).set_cpu_request('512Mi').set_cpu_limit('1').set_memory_request('512Mi').set_memory_limit('1Gi')
    evaluate_fine_tuned_model_task=evaluate_fine_tuned_model_op().after(generate_output_after_fine_tuning_task).set_cpu_request('512Mi').set_cpu_limit('1').set_memory_request('512Mi').set_memory_limit('1Gi')
    """
    combine_data_task=combine_data_op().after(collect_data_task)
    combine_data_task.execution_options.caching_strategy.max_cache_staleness = "P0D"
    
    """
    collect_data_task=collect_data_op()
    collect_data_task.execution_options.caching_strategy.max_cache_staleness = "P0D"
    combine_data_task=combine_data_op().after(collect_data_task)
    combine_data_task.execution_options.caching_strategy.max_cache_staleness = "P0D"
    cleanning_data_task=cleanning_data_op().after(combine_data_task)
    preprocessing_data_task=preprocessing_data_op().after(cleanning_data_task)
    fine_tune_model_task=fine_tune_model_op().after(preprocessing_data_task).set_cpu_request('1').set_cpu_limit('2').set_memory_request('1Gi').set_memory_limit('2Gi')
    fine_tune_model_task.execution_options.caching_strategy.max_cache_staleness = "P0D"
    generate_output_after_fine_tuning_task=bert_fine_tuned_model_output_op().after(fine_tune_model_task)
    generate_output_task = bert_output_before_fine_tuning_op().after(generate_output_after_fine_tuning_task)
    #generate_output_after_fine_tuning_task=bert_fine_tuned_model_output_op().after(generate_output_task)
    evaluate_fine_tuned_model_task=evaluate_fine_tuned_model_op().after(generate_output_task )
    """

endpoint="http://34.49.17.116/"  
kfp_client=Client(host=endpoint)

pipeline_package_path='LLM_pipeline.yaml'
pipeline_name = "BERT Fine-Tuning Pipeline 2"+random_suffix()
pipeline_description = "A pipeline that fine-tunes BERT model with specific data."

experiment_name = "BERT Fine-Tuning Experiments"
experiment_description = "Experiments for fine-tuning BERT models"

if __name__ == "__main__":
    
    #build_push_image()

    # Compile the pipeline to YAML
    kfp.compiler.Compiler().compile(pipeline_func=llm_pipeline, package_path=pipeline_package_path)

    # Define and create an experiment
    experiment_response = kfp_client.create_experiment(name=experiment_name, description=experiment_description)

    # Upload the pipeline
    pipeline_response = kfp_client.upload_pipeline('LLM_pipeline.yaml', pipeline_name=pipeline_name, description=pipeline_description)

    # Extract the experiment ID
    experiment_id = experiment_response.id


    # Extract the pipeline ID
    pipeline_id = pipeline_response.id

    # List versions for the uploaded pipeline and select the most recent version ID
    #version_id=kfp_client.list_pipeline_versions(pipeline_id=pipeline_id)

    
    # Create a run within the defined experiment using the uploaded pipeline and its version
    run_name = f"{pipeline_name} Run "
    #run = kfp_client.create_run_from_pipeline_func(llm_pipeline,arguments={})
    run_response = kfp_client.run_pipeline(experiment_id=experiment_id, job_name=run_name, pipeline_id=pipeline_id, params={})