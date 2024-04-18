import pandas as pd
from google.cloud import storage

    


storage_client = storage.Client()
bucket_name = 'my-bucket-int-infra-training-gcp'
file_name = 'old_devops_data.csv'
local_file_name = 'old_devops_data.csv'

# Reference the specified bucket and file (blob)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download the file locally
blob.download_to_filename(local_file_name)

# Load the CSV file into a pandas DataFrame
old_data = pd.read_csv(local_file_name)

# Assuming the old dataset does not have 'link' and 'snippet' columns
# Add empty 'link' and 'snippet' columns to the old dataset to match the new one
old_data['link'] = ''
old_data['snippet'] = ''


file_name = 'new_devops_data.csv'
local_file_name = 'new_devops_data.csv'

# Reference the specified bucket and file (blob)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download the file locally
blob.download_to_filename(local_file_name)

# Load the new dataset
new_data = pd.read_csv(local_file_name)


# If the 'content' column contains 'Article content not found.', replace it with empty strings
new_data['content'].replace('Article content not found.', '', inplace=True)

# Rename the columns of the new dataset to match the old dataset
new_data_aligned = new_data.rename(columns={'title': 'input', 'content': 'output'})

# Combine the datasets
combined_data = pd.concat([old_data, new_data_aligned[['input', 'output', 'link', 'snippet']]], ignore_index=True)

# Save the combined dataset
combined_data.to_csv('combined_devops_data.csv', index=False)

print("Combined data saved to combined_devops_data.csv")

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

# Usage example:
bucket_name = 'my-bucket-int-infra-training-gcp'
source_file_name = 'combined_devops_data.csv'
destination_blob_name = 'combined_devops_data.csv'

upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
print("Combined data uploaded to csv")