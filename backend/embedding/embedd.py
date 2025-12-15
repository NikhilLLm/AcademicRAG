from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
import uuid

# === CONFIG ===
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
VECTOR_SIZE = 768
COLLECTION_NAME = "user_uploads"

# === Initialize model and Qdrant client ===
model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(host="localhost", port=6333)

# === Ensure collection exists ===
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
)

def embed_and_store_pdf(metadata: dict):
    """
    Takes extracted metadata, embeds title+abstract, and stores in Qdrant.
    """
    text = f"{metadata.get('title', '')}. {metadata.get('abstract', '')}".strip()
    embedding = model.encode(text).tolist()
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, metadata.get("title", "unknown")))

    payload = {
        "title": metadata.get("title"),
        "abstract": metadata.get("abstract"),
        "text": text,
        "authors": metadata.get("authors"),
        "publication_date": metadata.get("publication_date"),
        "field_of_study": metadata.get("field_of_study"),
        "document_type": metadata.get("document_type"),
        "source_repository": metadata.get("source_repository"),
        "citation_count": metadata.get("citation_count"),
        "arxiv_id": metadata.get("arxiv_id"),
        "download_url": metadata.get("download_url")
    }

    point = PointStruct(id=point_id, vector=embedding, payload=payload)
    client.upsert(collection_name=COLLECTION_NAME, points=[point])
    return embedding
def embed_string(text:str):

    """
    Takes a string input and returns its embedding.
    """
    
    embedding = model.encode(text).tolist()
    return embedding

