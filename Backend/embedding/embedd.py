from fastembed import SparseTextEmbedding
from functools import lru_cache

# Model names
BM25_MODEL_NAME = "Qdrant/bm25"
DENSE_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"


@lru_cache(maxsize=1)
def _get_bm25_model() -> SparseTextEmbedding:
    """Lazily load and cache the BM25/sparse embedding model.

    Using lru_cache ensures a single instance per process without loading the
    model at import time, which is friendlier for production (e.g. Railway).
    """
    print("🔌 Loading BM25 sparse embedding model...")
    return SparseTextEmbedding(BM25_MODEL_NAME)


# Global variable -> load once
import requests
import os
import time

HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-mpnet-base-v2"
HF_TOKEN = os.environ.get("HF_TOKEN")

def _get_hf_embedding(text: str):
    """
    Get embedding from Hugging Face Inference API.
    Retries up to 3 times for model loading (503 error).
    """
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    
    for attempt in range(5):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload)
            
            # If model is loading, wait and retry
            if response.status_code == 503:
                data = response.json()
                wait_time = data.get("estimated_time", 10.0)
                print(f"⏳ Model loading, waiting {wait_time}s... (Attempt {attempt+1})")
                time.sleep(min(wait_time, 20.0)) # Cap wait at 20s
                continue
                
            if response.status_code != 200:
                print(f"❌ HF API Error: {response.status_code} - {response.text}")
                raise ValueError(f"HF API returned status {response.status_code}")
                
            # Valid response
            embedding = response.json()
            
            # Ensure it's a list (embedding vector)
            if isinstance(embedding, list):
                return embedding
            else:
                raise ValueError(f"Unexpected response format: {embedding}")
                
        except Exception as e:
            print(f"⚠️ HF API Exception: {e}")
            if attempt == 4:
                raise e
            time.sleep(2)
            
    raise TimeoutError("Failed to get embedding from HF API after retries")


def embed_string(text: str):
    """
    Takes a string input and returns its embedding.
    Using Hugging Face API for dense (MPNet 768d) and fastembed for sparse.
    """
    # Use HF API for dense embedding
    # Correct format is a list of floats
    dense_embedding = _get_hf_embedding(text)
    
    # FastEmbed returns a generator for sparse embeddings
    bm25_model = _get_bm25_model()
    bm25_embeddings = next(iter(bm25_model.query_embed(text)))
    
    enhanced={
        "dense_embedding": dense_embedding, # Already a list
         "sparse_embedding": {
                    "indices": bm25_embeddings.indices.tolist(),
                    "values": bm25_embeddings.values.tolist(),
           },
    }
    return enhanced
