FROM python:3.10    

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY Maamoun/LLM-Pipeline-GCP .


RUN pip install beautifulsoup4 requests-html requests lxml[html_clean] pandas webdriver-manager torch transformers  datasets numpy scipy nltk rouge_score sacrebleu google-cloud-storage transformers[torch]  --progress-bar off
#pandas  scikit-learn tensorflow transformers[torch] sentencepiece pynput 


# Define environment variable for better memory management in PyTorch
ENV PYTORCH_CUDA_ALLOC_CONF 'expandable_segments:True'

ENTRYPOINT []

