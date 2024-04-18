
import pandas as pd
import datasets
from datasets import Dataset
from transformers import BartForConditionalGeneration, BartTokenizer, TrainingArguments, Trainer
import numpy as np
import os
from google.cloud import storage


# Assuming you have set up the GCP authentication
credentials_file='int-infra-training-gcp-b4ede48008c9.json'
storage_client = storage.Client.from_service_account_json(credentials_file)

bucket_name = 'my-bucket-int-infra-training-gcp'
file_name = 'tokenized_devops_data.pkl'
local_file_name = 'tokenized_devops_data.pkl'

bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download the file locally
blob.download_to_filename(local_file_name)


tokenized_data = pd.read_pickle(local_file_name)


# If tensors are present, convert them to lists
for column in tokenized_data.columns:
    if pd.api.types.is_object_dtype(tokenized_data[column]):
        try:
            # Attempt to convert any tensors or other complex types to lists
            tokenized_data[column] = tokenized_data[column].apply(lambda x: x.tolist() if hasattr(x, 'tolist') else x)
        except Exception as e:
            print(f"Failed to convert {column}: {e}")

# Re-check to print specific types of each column
for column in tokenized_data.columns:
    unique_type = {type(x).__name__ for x in tokenized_data[column]}
    print(f"Column {column} contains types: {unique_type}")

# Convert DataFrame to Dataset
dataset = Dataset.from_pandas(tokenized_data)

# Setup the model, tokenizer, and training arguments as before
model = BartForConditionalGeneration.from_pretrained('facebook/bart-base')
tokenizer = BartTokenizer.from_pretrained('facebook/bart-base')

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    evaluation_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    eval_dataset=dataset
)

# Train the model
trainer.train()
print("model trained successfully")
# Save the model and tokenizer
model.save_pretrained('saved_model')
tokenizer.save_pretrained('saved_model')

print("Model and tokenizer have been saved.")


def upload_directory_to_gcs(storage_client, bucket_name, source_folder, destination_blob_prefix):
    # Uploads a directory to the GCS bucket.
    bucket = storage_client.bucket(bucket_name)

    for root, dirs, files in os.walk(source_folder):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, source_folder)
            blob_path = os.path.join(destination_blob_prefix, relative_path)
            
            blob = bucket.blob(blob_path)
            try:
                blob.upload_from_filename(local_path)
                print(f"Uploaded {local_path} to {blob_path}.")
            except Exception as e:
                print(f"Failed to upload {local_path} to {blob_path}. Exception: {e}")




# Save the fine-tuned model and tokenizer for later use
local_model_folder = 'saved_model'

# Save the fine-tuned model and tokenizer for later use
model.save_pretrained(local_model_folder)
tokenizer.save_pretrained(local_model_folder)
print("model saved in bart-finetuned locally")
# Define your GCS bucket name and the GCS folder where you want to save your model
bucket_name = 'my-bucket-int-infra-training-gcp'
destination_blob_prefix = 'saved_model'


# Upload the model and tokenizer to GCS
upload_directory_to_gcs(storage_client,bucket_name, local_model_folder, destination_blob_prefix)
print("model saved in bart-finetuned in GCS bucket")

os.remove(local_file_name)

