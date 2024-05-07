from llama_index.core import VectorStoreIndex, QueryBundle, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from index import get_es_vector_store  

def run_query():
    query = input("Please enter your query: ")

    local_llm = Ollama(model="mistral")
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-distilroberta-v1")

    index = VectorStoreIndex.from_vector_store(get_es_vector_store())
    query_engine = index.as_query_engine(local_llm, similarity_top_k=3, streaming=True, response_mode="tree_summarize")

    bundle = QueryBundle(query, embedding=Settings.embed_model.get_query_embedding(query))
    result = query_engine.query(bundle)
    return result.print_response_stream()

result = run_query()
print(result)
