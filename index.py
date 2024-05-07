from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv
import elastic_transport
from tqdm import tqdm
import logging, sys
import subprocess
import shutil
import time
import re
import os

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

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
    branch = os.getenv("GITHUB_BRANCH")
    
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
    reader = SimpleDirectoryReader(local_repo_path, recursive=True, filename_as_id=True)
    documents = []
    for docs in tqdm(reader.iter_data(), desc="Loading data"):
        for doc in docs:
            documents.append(doc)
    print(f"Loaded {len(documents)} documents.")
    print("Data loaded from local directory.")
    return documents

def get_es_vector_store():
    print("Initializing Elasticsearch store...")
    es_cloud_id = os.getenv("ELASTIC_CLOUD_ID")
    es_user = os.getenv("ELASTIC_USER")
    es_password = os.getenv("ELASTIC_PASSWORD")
    index_name = os.getenv("ELASTIC_INDEX")
    retries = 3
    for attempt in range(retries):
        try:
            es_vector_store = ElasticsearchStore(
                index_name=index_name,
                es_cloud_id=es_cloud_id,
                es_user=es_user,
                es_password=es_password
            )
            print("Elasticsearch store initialized.")
            return es_vector_store
        except elastic_transport.ConnectionTimeout:
            print(f"Connection attempt {attempt + 1}/{retries} timed out. Retrying...")
            time.sleep(5)  
    raise Exception("Failed to initialize Elasticsearch store after multiple attempts")

def add_extra_metadata(documents):
    for doc in documents:
        file_name = doc.metadata.get("file_name", "")
        file_extension = file_name.split(".")[-1].lower()

        extra_metadata = {}
        if file_extension in ["md", "asciidoc", "txt"]:
            extra_metadata["type"] = "readme"
        elif file_extension in ["yaml", "yml"]:
            extra_metadata["type"] = "yaml"
        elif file_extension == "go":
            extra_metadata["type"] = "go"
        elif file_extension == "json":
            extra_metadata["type"] = "json"
        elif file_extension == "png":
            extra_metadata["type"] = "image"
        elif file_extension == "sh":
            extra_metadata["type"] = "shell"
        elif file_extension == "tpl":
            extra_metadata["type"] = "template"
        elif file_extension == "mod":
            extra_metadata["type"] = "module"
        else:
            extra_metadata["type"] = "others"

        if "test" in file_name.lower():
            extra_metadata["type"] = "test"

        stripped_metadata =  doc.metadata.copy()
        for key in doc.metadata:
            if key not in ["file_name", "file_path", "type"]:
                del stripped_metadata[key]
        doc.metadata = stripped_metadata
        doc.metadata.update(extra_metadata)

def main():
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")    
    branch = os.getenv("GITHUB_BRANCH")
    github_url = f"https://github.com/{owner}/{repo}"
    owner, repo = parse_github_url(github_url)
    if not validate_owner_repo(owner, repo):
        raise ValueError("Invalid GitHub URL")

    base_path = "/tmp"
    local_repo_path = clone_repository(owner, repo, {branch}, base_path)

    branch = "main"
    if not os.path.exists(local_repo_path):
        clone_repository(owner, repo, branch, local_repo_path)

    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-distilroberta-v1")
    
    Settings.embed_model = embed_model

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=1000, chunk_overlap=50),
            Settings.embed_model
        ],
        vector_store=get_es_vector_store()
    )

    documents = get_documents(local_repo_path)
    print("Starting the pipeline...")

    add_extra_metadata(documents)

    pipeline.run(show_progress=True, documents=documents)
    print(".....Done running pipeline.....\n")   

    shutil.rmtree(local_repo_path)
    print("Repository removed from local storage.")    

if __name__ == "__main__":
    main()
