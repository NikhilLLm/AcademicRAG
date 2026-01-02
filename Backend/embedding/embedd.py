from Backend.models.hugging_face import hugging_face_embed
from fastembed import SparseTextEmbedding
def embed_string(text:str):

    """
    Takes a string input and returns its embedding.
    """
    BM25_MODEL_NAME = "Qdrant/bm25"
    bm25_embedding_model = SparseTextEmbedding(BM25_MODEL_NAME)
    
    dense_embedding = hugging_face_embed(text)
    bm25_embeddings = next(bm25_embedding_model.query_embed(text))
    enhanced={
        "dense_embedding":dense_embedding,
         "sparse_embedding": {
                    "indices": bm25_embeddings.indices.tolist(),
                    "values": bm25_embeddings.values.tolist(),
           },
    }
    return enhanced
