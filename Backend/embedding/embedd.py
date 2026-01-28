from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer

# Initialize local embedding models ONCE globally
BM25_MODEL_NAME = "Qdrant/bm25"
DENSE_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

print("🔌 Loading Local Embedding Models...")
bm25_embedding_model = SparseTextEmbedding(BM25_MODEL_NAME)
dense_embedding_model = SentenceTransformer(DENSE_MODEL_NAME)
print("✅ Local Embedding Models Loaded")

def embed_string(text:str):
    """
    Takes a string input and returns its embedding.
    Using sentence-transformers for dense (768) and fastembed for sparse.
    """
    # Use sentence-transformers for dense embedding
    dense_embedding = dense_embedding_model.encode(text)
    
    # FastEmbed returns a generator for sparse embeddings
    bm25_embeddings = next(iter(bm25_embedding_model.query_embed(text)))
    
    enhanced={
        "dense_embedding": dense_embedding.tolist(),
         "sparse_embedding": {
                    "indices": bm25_embeddings.indices.tolist(),
                    "values": bm25_embeddings.values.tolist(),
           },
    }
    return enhanced
