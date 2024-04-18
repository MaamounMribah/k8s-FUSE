from transformers import BartForConditionalGeneration, BartTokenizer
from datasets import load_dataset, load_metric
import torch
import os
from google.cloud import storage

# Function to download model from GCS
def download_model(storage_client,bucket_name, source_blob_prefix, destination_dir):
    #Downloads a model from GCS to a local directory.
    bucket = storage_client.bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=source_blob_prefix)
    for blob in blobs:
        destination_file_name = os.path.join(destination_dir, blob.name[len(source_blob_prefix):])
        # Ensure the directory exists
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        # Download the blob to the destination file
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded {blob.name} to {destination_file_name}.")



# initialize the GCP client
storage_client = storage.Client()

# GCS bucket name and model prefix
bucket_name = 'my-bucket-int-infra-training-gcp'
source_blob_prefix = 'saved_model/'

# Local directory to store the downloaded model files
destination_dir = 'saved_model'

# Download the model from GCS
download_model(storage_client,bucket_name, source_blob_prefix, destination_dir)

#destination_dir='bart-finetuned'
# After downloading, load the model and tokenizer from the local directory
fine_tuned_tokenizer = BartTokenizer.from_pretrained(destination_dir)
fine_tuned_model = BartForConditionalGeneration.from_pretrained(destination_dir)


# Step 1: Load Models and Tokenizers
original_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")
original_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large")


# Ensure both models are in evaluation mode
original_model.eval()
fine_tuned_model.eval()

# Move models to GPU if available
if torch.cuda.is_available():
    original_model.to('cuda')
    fine_tuned_model.to('cuda')

bucket_name = 'my-bucket-int-infra-training-gcp'
file_name = 'devops_qa_dataset.csv'
local_file_name = 'local_devops_qa_dataset.csv'

bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download the file locally
blob.download_to_filename(local_file_name)

# Now, load the dataset from the local file
evaluation_dataset = load_dataset('csv', data_files=local_file_name)['train']

# Adjusting the dataset mapping to your dataset structure
evaluation_data = evaluation_dataset.map(lambda examples: {'inputs': examples['input'], 'targets': examples['output']}, batched=True)

# Step 3: Define the Evaluation Function
def evaluate_model(model, tokenizer, dataset, device='cuda' if torch.cuda.is_available() else 'cpu'):
    rouge = load_metric("rouge")
    predictions = []
    references = []

    for example in dataset:
        inputs = tokenizer(example['inputs'], return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
        outputs = model.generate(inputs['input_ids'], max_length=150, early_stopping=True)
        
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        predictions.append(prediction)
        references.append(example['targets'])
    
    results = rouge.compute(predictions=predictions, references=references)
    return results

# Step 4: Run the Evaluation
original_eval_results = evaluate_model(original_model, original_tokenizer, evaluation_data)
fine_tuned_eval_results = evaluate_model(fine_tuned_model, fine_tuned_tokenizer, evaluation_data)


# Extracting the f1 scores from the results
original_f1_scores = {key: value.mid.fmeasure for key, value in original_eval_results.items()}
fine_tuned_f1_scores = {key: value.mid.fmeasure for key, value in fine_tuned_eval_results.items()}

print("Original Model Evaluation F1 Scores:\n", original_f1_scores)
print("\nFine-tuned Model Evaluation F1 Scores:\n", fine_tuned_f1_scores)