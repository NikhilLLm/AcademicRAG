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
import os
import time
from huggingface_hub import InferenceClient

HF_TOKEN = os.environ.get("HF_TOKEN")

# Initialize client globally
_hf_client = None

def _get_hf_client():
    global _hf_client
    if _hf_client is None:
        print("🔌 Loading Hugging Face Inference Client...")
        _hf_client = InferenceClient(
            provider="hf-inference",
            api_key=HF_TOKEN,
        )
    return _hf_client

def _get_hf_embedding(text: str):
    """
    Get embedding from Hugging Face Inference API using InferenceClient.
    Uses 'feature_extraction' for embeddings.
    """
    client = _get_hf_client()
    
    for attempt in range(5):
        try:
            # Using feature_extraction for embeddings
            embedding = client.feature_extraction(
                text,
                model="sentence-transformers/all-mpnet-base-v2"
            )
            
            # The result is usually a numpy array or list. We need to ensure it's a list.
            # If input is a single string, output is a single vector (list of floats).
            if hasattr(embedding, "tolist"):
                return embedding.tolist()
            return embedding
                
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ HF API Exception: {error_msg}")
            
            # 503 means model is loading, handled by the client usually but good to be safe
            if "503" in error_msg or "loading" in error_msg.lower():
                 print(f"⏳ Model loading, retrying... (Attempt {attempt+1})")
                 time.sleep(5)
                 continue

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
    dense_embedding = _get_hf_embedding(text)
    
    # FastEmbed returns a generator for sparse embeddings
    bm25_model = _get_bm25_model()
    # Handle both single string and list inputs safely
    bm25_generator = bm25_model.query_embed(text)
    bm25_embeddings = next(iter(bm25_generator)) 
    
    enhanced={
        "dense_embedding": dense_embedding, 
         "sparse_embedding": {
                    "indices": bm25_embeddings.indices.tolist(),
                    "values": bm25_embeddings.values.tolist(),
           },
    }
    return enhanced
