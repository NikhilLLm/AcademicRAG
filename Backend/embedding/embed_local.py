from fastembed import SparseTextEmbedding, TextEmbedding

# Initialize local SMALL embedding models ONCE globally for Notes/Chat pipeline
# This is separate from the main global paper search models
BM25_MODEL_NAME = "Qdrant/bm25"
DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5" # 384 dimensions, very fast

print("🔌 Loading Fast Local Embedding Models for Notes/Chat...")
bm25_embedding_model = SparseTextEmbedding(BM25_MODEL_NAME)
dense_embedding_model = TextEmbedding(DENSE_MODEL_NAME)
print("✅ Local Small Embedding Models Loaded")

def embed_string_small(text: str):
    """
    Takes a string input and returns its embedding using Bge-small (384 dims).
    Used for local PDF notes and chat to ensure speed and consistency.
    """
    # FastEmbed returns a generator, so we take the first item
    dense_embedding = list(dense_embedding_model.embed([text]))[0]
    bm25_embeddings = next(iter(bm25_embedding_model.query_embed(text)))
    
    enhanced = {
        "dense_embedding": dense_embedding.tolist(),
        "sparse_embedding": {
            "indices": bm25_embeddings.indices.tolist(),
            "values": bm25_embeddings.values.tolist(),
        },
    }
    return enhanced
