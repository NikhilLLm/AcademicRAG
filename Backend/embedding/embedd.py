from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer
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


@lru_cache(maxsize=1)
def _get_dense_model() -> SentenceTransformer:
    """Lazily load and cache the dense embedding model."""
    print("🔌 Loading dense embedding model...")
    return SentenceTransformer(DENSE_MODEL_NAME)


def embed_string(text: str):
    """
    Takes a string input and returns its embedding.
    Using sentence-transformers for dense (768) and fastembed for sparse.
    """
    # Use sentence-transformers for dense embedding
    dense_model = _get_dense_model()
    dense_embedding = dense_model.encode(text)
    
    # FastEmbed returns a generator for sparse embeddings
    bm25_model = _get_bm25_model()
    bm25_embeddings = next(iter(bm25_model.query_embed(text)))
    
    enhanced={
        "dense_embedding": dense_embedding.tolist(),
         "sparse_embedding": {
                    "indices": bm25_embeddings.indices.tolist(),
                    "values": bm25_embeddings.values.tolist(),
           },
    }
    return enhanced
