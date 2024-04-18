import pandas as pd
import re
from html import unescape
from google.cloud import storage

def clean_text(text):
    # Decode HTML entities
    text = unescape(text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Replace multiple spaces and newline characters
    text = re.sub(r'\s+', ' ', text)
    # Strip leading and trailing whitespace
    text = text.strip()
    return text


storage_client = storage.Client()
bucket_name = 'my-bucket-int-infra-training-gcp'
file_name = 'combined_devops_data.csv'
local_file_name = 'combined_devops_data.csv'

# Reference the specified bucket and file (blob)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download the file locally
blob.download_to_filename(local_file_name)


# Load the dataset
df = pd.read_csv(local_file_name)

# Check for missing values and print the sum of missing values for each column
print("Missing values before cleanup:")
print(df.isnull().sum())

# Optional: Fill missing values or drop rows with missing values
df.dropna(subset=['input', 'output'], inplace=True)  # Dropping rows where 'input' or 'output' is missing

# Clean the text data in 'input' and 'output' columns
df['input'] = df['input'].apply(clean_text)
df['output'] = df['output'].apply(clean_text)

# Normalize text to lowercase to reduce vocabulary complexity (optional)
df['input'] = df['input'].apply(lambda x: x.lower())
df['output'] = df['output'].apply(lambda x: x.lower())

# Save the cleaned data to a new CSV file
df.to_csv('cleaned_devops_data.csv', index=False)

print("Data cleaning complete. Cleaned data saved to 'cleaned_devops_data.csv'.")

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

# Usage example:
bucket_name = 'my-bucket-int-infra-training-gcp'
source_file_name = 'cleaned_devops_data.csv'
destination_blob_name = 'cleaned_devops_data.csv'

upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
print("Combined data uploaded to csv")