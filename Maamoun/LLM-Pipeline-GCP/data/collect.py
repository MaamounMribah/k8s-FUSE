import json
import requests
from requests_html import HTMLSession
from google.cloud import storage
import pandas as pd

#credentials_file='int-infra-training-gcp-b4ede48008c9.json'
#storage_client = storage.Client.from_service_account_json(credentials_file)
storage_client = storage.Client()

def fetch_article_content(url):
    """Fetches article content from a URL using requests-html to render JavaScript."""
    session = HTMLSession()
    try:
        response = session.get(url)
        # Render JavaScript if necessary
        response.html.render(timeout=20)
        content = response.html.find('article', first=True) \
                 or response.html.find('.post-content', first=True) \
                 or response.html.find('[role="main"]', first=True)
        return content.text if content else "Article content not found."
    except Exception as e:
        print(f"Failed to fetch content from {url}: {str(e)}")
        return "Failed to fetch content."
    finally:
        session.close()

def fetch_devops_search_results(api_key, search_engine_id, queries):
    """Fetches search results and extracts content for each link found."""
    devops_data = []
    for query in queries:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={search_engine_id}&num=10"
        response = requests.get(url)
        results = response.json()

        for item in results.get('items', []):
            article_url = item['link']
            article_content = fetch_article_content(article_url)  # Fetch the full content using requests-html

            data = {
                'title': item.get('title'),
                'link': article_url,
                'snippet': item.get('snippet'),
                'content': article_content
            }
            devops_data.append(data)

    return devops_data

def save_to_csv(data, filename='new_devops_data.csv'):
    """Saves the extracted data to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data successfully saved to {filename}")

def fetch_keywords_from_gcs(storage_client,bucket_name, blob_name):
    """Fetches keywords from a JSON file stored in Google Cloud Storage."""
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Download the contents of the blob into a string
    keywords_json = blob.download_as_text()

    # Convert the JSON string into a Python list
    keywords = json.loads(keywords_json)

    return keywords

def upload_to_gcs(storage_client,bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


# Main logic for fetching and processing data
if __name__ == "__main__":
    # Configuration
    api_key = 'AIzaSyDsmk_AflKCr0UF-GnHrNUxCOODCivVM0I'
    search_engine_id = 'f1d3b20a4954b4efe'
    bucket_name = 'my-bucket-int-infra-training-gcp'
    blob_name = 'keywords.json'
    output_csv = 'new_devops_data.csv'
    destination_blob_name = output_csv

    # Fetch keywords and process search results
    queries = fetch_keywords_from_gcs(storage_client,bucket_name, blob_name)
    """
    queries = [
        "ci/cd", "devops", "automation", "docker", "container",
        "gitlab", "github", "jenkins", "kubernetes", "ansible",
        "terraform", "cloud computing", "aws", "azure", "gcp",
        "infrastructure as code", "continuous integration", "continuous deployment",
        "microservices", "serverless", "monitoring", "logging",
        "agile development", "scrum", "virtualization", "linux containers",
        "orchestration", "configuration management", "build pipelines",
        "deployment strategies", "system administration", "networking",
        "security", "compliance as code", "site reliability engineering",
        "performance tuning", "load balancing", "scalability", "cloud architecture",
        "service mesh", "observability", "cloud security", "cloud services",
        "cloud storage", "data management", "scripting", "programming",
        "software development lifecycle", "SDLC", "IT operations", "sysops",
        "data center automation", "API development", "testing automation"
    ]
    """
    devops_articles = fetch_devops_search_results(api_key, search_engine_id, queries)
    save_to_csv(devops_articles, output_csv)

    # Optionally upload results back to GCS
    upload_to_gcs(storage_client,bucket_name, output_csv, destination_blob_name)
