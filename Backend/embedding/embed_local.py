from fastembed import SparseTextEmbedding, TextEmbedding
from functools import lru_cache

# Initialize local SMALL embedding models lazily for Notes/Chat pipeline
BM25_MODEL_NAME = "Qdrant/bm25"
DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384 dimensions, very fast


@lru_cache(maxsize=1)
def _get_bm25_model() -> SparseTextEmbedding:
    print("🔌 Loading BM25 sparse embedding model for notes/chat...")
    return SparseTextEmbedding(BM25_MODEL_NAME)


@lru_cache(maxsize=1)
def _get_dense_model() -> TextEmbedding:
    print("🔌 Loading BGE-small dense model for notes/chat...")
    return TextEmbedding(DENSE_MODEL_NAME)


def embed_string_small(text: str):
    """
    Takes a string input and returns its embedding using Bge-small (384 dims).
    Used for local PDF notes and chat to ensure speed and consistency.
    """
    dense_model = _get_dense_model()
    sparse_model = _get_bm25_model()

    # FastEmbed returns a generator, so we take the first item
    dense_embedding = list(dense_model.embed([text]))[0]
    bm25_embeddings = next(iter(sparse_model.query_embed(text)))
    
    enhanced = {
        "dense_embedding": dense_embedding.tolist(),
        "sparse_embedding": {
            "indices": bm25_embeddings.indices.tolist(),
            "values": bm25_embeddings.values.tolist(),
        },
    }
    return enhanced
