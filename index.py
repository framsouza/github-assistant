from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv
from tqdm import tqdm
import subprocess
import shutil
import time
import re
import os

load_dotenv('.env')

def parse_github_url(url):
    pattern = r"https://github\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, url)
    return match.groups() if match else (None, None)

def validate_owner_repo(owner, repo):
    return bool(owner) and bool(repo)

def clone_repository(owner, repo, branch, base_path):
    local_repo_path = os.path.join(base_path, owner, repo)
    clone_url = f"https://github.com/{owner}/{repo}.git"
    attempts = 3 
    
    for attempt in range(attempts):
        try:
            if not os.path.exists(local_repo_path):
                os.makedirs(local_repo_path, exist_ok=True)
            print(f"Attempting to clone repository... Attempt {attempt + 1}")
            subprocess.run(["git", "clone", "-b", branch, clone_url, local_repo_path], check=True)
            print(f"Repository cloned into {local_repo_path}.")
            return local_repo_path
        except subprocess.CalledProcessError:
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(10)  
            if attempt < attempts - 1:
                continue
            else:
                raise Exception("Failed to clone repository after multiple attempts")

def get_documents(local_repo_path):
    print("Reading data from local directory...")
    reader = SimpleDirectoryReader(local_repo_path, recursive=True)
    documents = []
    for docs in tqdm(reader.iter_data(), desc="Loading data"):
        for doc in docs:
            documents.append(doc)
    print(f"Loaded {len(documents)} documents.")
    print("Data loaded from local directory.")
    return documents

def get_es_vector_store():
    print("Initializing Elasticsearch store...")
    es_vector_store = ElasticsearchStore(
        index_name=os.getenv("ELASTIC_INDEX"),
        es_cloud_id=os.getenv("ELASTIC_CLOUD_ID"),
        es_user=os.getenv("ELASTIC_USER"),
        es_password=os.getenv("ELASTIC_PASSWORD"),
        batch_size=100
    )
    print("Elasticsearch store initialized.")
    return es_vector_store

def main():
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")    
    github_url = f"https://github.com/{owner}/{repo}"
    owner, repo = parse_github_url(github_url)
    if not validate_owner_repo(owner, repo):
        raise ValueError("Invalid GitHub URL")

    base_path = "/tmp"
    local_repo_path = clone_repository(owner, repo, "main", base_path)

    branch = "main"
    if not os.path.exists(local_repo_path):
        clone_repository(owner, repo, branch, local_repo_path)

    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-distilroberta-v1"
    )

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=350, chunk_overlap=50),
            Settings.embed_model
        ],
        vector_store=get_es_vector_store()
    )

    documents = get_documents(local_repo_path)
    print("Starting the pipeline...")

    pipeline.run(show_progress=True, documents=documents)
    print(".....Done running pipeline.....\n")   

    shutil.rmtree(local_repo_path)
    print("Repository removed from local storage.")    

if __name__ == "__main__":
    main()
