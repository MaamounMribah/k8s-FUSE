import pandas as pd
from transformers import BartTokenizer
from google.cloud import storage

# Load the tokenizer
tokenizer = BartTokenizer.from_pretrained('facebook/bart-base')

storage_client = storage.Client()
bucket_name = 'my-bucket-int-infra-training-gcp'
file_name = 'cleaned_devops_data.csv'
local_file_name = 'cleaned_devops_data.csv'

# Reference the specified bucket and file (blob)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download the file locally
blob.download_to_filename(local_file_name)

# Load your cleaned dataset
df = pd.read_csv(local_file_name)

# Define a function to tokenize text
def tokenize_data(row):
    inputs = tokenizer.encode_plus(
        row['input'], 
        add_special_tokens=True,    # Add '[CLS]' and '[SEP]'
        max_length=512,             # Max length to truncate/pad
        padding='max_length',       # Pad to max_length
        truncation=True,            # Truncate to max_length
        return_attention_mask=True, # Return attention mask
        return_tensors='pt'         # Return PyTorch tensors
    )
    outputs = tokenizer.encode_plus(
        row['output'],
        add_special_tokens=True,
        max_length=512,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )
    return {'input_ids': inputs['input_ids'].flatten(), 
            'attention_mask': inputs['attention_mask'].flatten(),
            'labels': outputs['input_ids'].flatten()}

# Apply tokenization to each row
tokenized_data = df.apply(tokenize_data, axis=1)
tokenized_df = pd.DataFrame(list(tokenized_data))

# Optional: Save the tokenized data to a file (if needed)
tokenized_df.to_pickle('tokenized_devops_data.pkl')

print("Tokenization complete. Data saved to 'tokenized_devops_data.pkl'.")

def upload_to_gcs(storage_client,bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

# Usage example:
bucket_name = 'my-bucket-int-infra-training-gcp'
source_file_name = 'tokenized_devops_data.pkl'
destination_blob_name = 'tokenized_devops_data.pkl'

upload_to_gcs(storage_client,bucket_name, source_file_name, destination_blob_name)