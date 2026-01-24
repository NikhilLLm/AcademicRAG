import os
import json
import uuid
from langchain_qdrant import SparseVector
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance, HnswConfigDiff,models,SparseVectorParams
from qdrant_client.http.exceptions import UnexpectedResponse
from dotenv import load_dotenv

# ================= CONFIG =================
INPUT_DIR = "C:/Users/nshej/aisearch/embeddings/chunks"
OUTPUT_DIR = "C:/Users/nshej/aisearch/embeddings/vector_db"

VECTOR_SIZE = 768
BATCH_SIZE = 100


UNIFIED_COLLECTION_NAME = "papers_semantic_v1"

load_dotenv("C:/Users/nshej/aisearch/.env")
QDRANT_URL = "https://72bcce7c-0237-4ae3-a1ec-12a43a79396e.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = os.getenv("qdrant_key")
#==============collection check============


# ================= CONNECT =================
try:
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
   )
except Exception as e:
    print("Error:",e)

collections = client.get_collections()
print("🗑️ Deleting collection (one-time reset)...")
client.delete_collection("papers_semantic")
print("✅ Deleted")
print("✅ Connected")
print("📋 Existing collections:", [c.name for c in collections.collections])

# ================= ENSURE COLLECTION =================
collection_exists = False
existing_points = 0

if collection_exists==True:
    print("Choose option to decide what to do with collection:1/2/3")
    user_input=input("Enter the choice: ")
    if user_input==1:
        print("Deleting the collection")
        client.delete_collection(UNIFIED_COLLECTION_NAME)
        print("Deleted SuccessFully!")
    elif user_input==2:
        print("Skipping deletion according input 2")
        
    
try:
    col = client.get_collection(UNIFIED_COLLECTION_NAME)
    collection_exists = True
    existing_points = col.points_count
    print(f"ℹ️ Collection '{UNIFIED_COLLECTION_NAME}' exists with {existing_points} points")
except UnexpectedResponse:
    print(f"🆕 Creating collection '{UNIFIED_COLLECTION_NAME}'")
    client.create_collection(
    collection_name=UNIFIED_COLLECTION_NAME,
    vectors_config={
        "dense": models.VectorParams(
            size=768,
            distance=models.Distance.COSINE,
            hnsw_config=models.HnswConfigDiff(
                m=32,
                ef_construct=200, #m=this is number of bidirectional graph for each node ef_construct=search depth
            ),
        )
    },
    sparse_vectors_config={
        "bm25": models.SparseVectorParams()
    }
)

    print("✅ Collection created")

# ================= INGEST =================
for field in os.listdir(INPUT_DIR):
    field_path = os.path.join(INPUT_DIR, field)
    if not os.path.isdir(field_path):
        continue

    embedding_file = os.path.join(field_path, "embeddings.jsonl")
    if not os.path.exists(embedding_file):
        print(f"⚠️ Missing embeddings for {field}")
        continue

    print(f"\n🚀 Processing field: {field}")

    seen_ids = set()
    valid_points = []
    skipped = {"missing_id": 0, "invalid_embedding": 0, "duplicate_id": 0}

    with open(embedding_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            raw_id = record.get("id") or record.get("arxiv_id") or record.get("title")
            if not raw_id:
                skipped["missing_id"] += 1
                continue

            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id).strip()))
            dense_vector = record.get("dense_embedding")
            bm25=record.get("sparse_embedding")

            if not isinstance(dense_vector, list) or len(dense_vector) != VECTOR_SIZE:
                skipped["invalid_embedding"] += 1
                continue

            if point_id in seen_ids:
                skipped["duplicate_id"] += 1
                continue

            seen_ids.add(point_id)

            payload = {
                "title": record.get("title"),
                "abstract": record.get("abstract"),
                "text": record.get("text"),
                "authors": record.get("authors"),
                "publication_date": record.get("publication_date"),
                "download_url": record.get("download_url"),
                "field_of_study": record.get("field_of_study") or field,
                "source_repository": record.get("source_repository"),
                "document_type": record.get("document_type"),
                "citation_count": record.get("citation_count"),
            }

            valid_points.append(
                 PointStruct(
                     id=point_id,
                     vector={
                         "dense": dense_vector,           # dense embedding (list[float])
                         "bm25": {
                              "indices": bm25["indices"],
                              "values": bm25["values"],
                            }
                        },
                     payload=payload
                 )

            )

    print(f"📊 Valid points: {len(valid_points)} | Skipped: {skipped}")

    # ================= UPSERT =================
    for i in range(0, len(valid_points), BATCH_SIZE):
        batch = valid_points[i : i + BATCH_SIZE]
        client.upsert(
            collection_name=UNIFIED_COLLECTION_NAME,
            points=batch,
        )
        progress = (i + len(batch)) / len(valid_points) * 100
        print(f"⬆️ Upload progress: {progress:.1f}%")

# ================= SUMMARY =================
info = client.get_collection(UNIFIED_COLLECTION_NAME)
print("\n🎉 DONE")
print(f"📦 Collection: {UNIFIED_COLLECTION_NAME}")
print(f"🔢 Total vectors: {info.points_count}")
print("💡 All fields stored in ONE collection via payload")
