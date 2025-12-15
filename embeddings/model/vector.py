import os
import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance,HnswConfigDiff

# === Configuration ===
INPUT_DIR = "C:/Users/nshej/aisearch/embeddings/chunks"
OUTPUT_DIR = "C:/Users/nshej/aisearch/embeddings/vector_db"
VECTOR_SIZE = 768
BATCH_SIZE = 100

# === Initialize Qdrant client ===
client = QdrantClient(host="localhost", port=6333)

# === Ingest vectors per field ===
for field in os.listdir(INPUT_DIR):
    field_path = os.path.join(INPUT_DIR, field)
    if not os.path.isdir(field_path):
        continue

    embedding_file = os.path.join(field_path, "embeddings.jsonl")
    if not os.path.exists(embedding_file):
        print(f"⚠️ No embedding file found for field '{field}' — skipping.")
        continue

    collection_name = field.replace(" ", "_").lower()
    print(f"\n🚀 Ingesting vectors into collection: {collection_name}")

    # === Create or reset collection ===
    #using HNSW index for faster search
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        hnsw_config=HnswConfigDiff(
        m=32,                 # Higher = better recall (default 16)
        ef_construct=200,     # Higher = better accuracy while indexing
               
        )
    )

    seen_ids = set()
    valid_points = []
    skipped = {
        "missing_id": 0,
        "invalid_embedding": 0,
        "duplicate_id": 0
    }

    with open(embedding_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"❌ Line {line_num}: Invalid JSON — skipping.")
                continue

            raw_id = record.get("id") or record.get("arxiv_id") or record.get("title")
            if raw_id is None or str(raw_id).strip() == "":
                skipped["missing_id"] += 1
                continue

            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id).strip()))
            vector = record.get("embedding")

            if not isinstance(vector, list) or len(vector) != VECTOR_SIZE:
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
                "field_of_study": record.get("field_of_study"),
                "source_repository": record.get("source_repository"),
                "document_type": record.get("document_type"),
                "citation_count": record.get("citation_count")
            }

            valid_points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    # === Upload in batches ===
    total_uploaded = 0
    for i in range(0, len(valid_points), BATCH_SIZE):
        batch = valid_points[i:i + BATCH_SIZE]
        client.upsert(collection_name=collection_name, points=batch)
        total_uploaded += len(batch)

    # === Log summary ===
    print(f"✅ Uploaded {total_uploaded} vectors to '{collection_name}'")
    print(f"⚠️ Skipped: {skipped['missing_id']} missing ID, {skipped['invalid_embedding']} invalid embedding, {skipped['duplicate_id']} duplicates")

    # === Write info.txt ===
    output_path = os.path.join(OUTPUT_DIR, collection_name)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, "info.txt"), "w", encoding="utf-8") as f:
        f.write(f"Collection: {collection_name}\n")
        f.write(f"Total uploaded: {total_uploaded}\n")
        f.write(f"Skipped due to missing ID: {skipped['missing_id']}\n")
        f.write(f"Skipped due to invalid embedding: {skipped['invalid_embedding']}\n")
        f.write(f"Skipped due to duplicate ID: {skipped['duplicate_id']}\n")
