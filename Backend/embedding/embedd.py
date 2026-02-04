from fastembed import SparseTextEmbedding
from functools import lru_cache
from models.hugging_face import hugging_face_embed
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





def embed_string(text: str):
    """
    Takes a string input and returns its embedding.
    Using Hugging Face API for dense (MPNet 768d) and fastembed for sparse.
    """
    # Use HF API for dense embedding
    dense_embedding = hugging_face_embed(text)
    
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
