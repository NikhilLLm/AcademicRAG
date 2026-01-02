import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding

# ================= CONFIG =================
DENSE_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
BM25_MODEL_NAME = "Qdrant/bm25"

BATCH_SIZE = 32

INPUT_ROOT = "C:/Users/nshej/aisearch/data/metadata"
OUTPUT_ROOT = "C:/Users/nshej/aisearch/embeddings/chunks"

# ================= LOAD MODELS =================
dense_embedding_model = SentenceTransformer(DENSE_MODEL_NAME)
bm25_embedding_model = SparseTextEmbedding(BM25_MODEL_NAME)

# ================= HELPERS =================
def load_metadata(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_doc_text(record):
    title = (record.get("title") or "").strip()
    abstract = (record.get("abstract") or "").strip()
    authors = ", ".join(record.get("authors") or [])
    return f"{title}. {abstract}. {authors}".strip()

def get_unique_id(record):
    return record.get("arxiv_id") or record.get("title")

def save_embeddings(vectors, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for item in vectors:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")

# ================= MAIN LOOP =================
for field in os.listdir(INPUT_ROOT):
    field_path = os.path.join(INPUT_ROOT, field)
    if not os.path.isdir(field_path):
        continue

    output_dir = os.path.join(OUTPUT_ROOT, field)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "embeddings.jsonl")

    if os.path.exists(output_path):
        print(f"✅ Skipping {field} (already embedded)")
        continue

    print(f"\n🔍 Embedding field: {field}")

    all_docs, all_ids, all_records = [], [], []
    seen_ids = set()

    for file in sorted(os.listdir(field_path)):
        if not file.endswith(".json"):
            continue

        batch_path = os.path.join(field_path, file)
        records = load_metadata(batch_path)

        for record in records:
            doc_text = build_doc_text(record)
            if not doc_text:
                continue

            eid = get_unique_id(record)
            if not eid or eid in seen_ids:
                continue

            seen_ids.add(eid)
            all_docs.append(doc_text)
            all_ids.append(eid)
            all_records.append(record)

    print(f"📦 Total unique records to embed: {len(all_docs)}")

    vectors = []

    for i in tqdm(range(0, len(all_docs), BATCH_SIZE)):
        batch_docs = all_docs[i:i + BATCH_SIZE]
        batch_ids = all_ids[i:i + BATCH_SIZE]
        batch_records = all_records[i:i + BATCH_SIZE]

        # Dense embeddings
        dense_embeddings = dense_embedding_model.encode(
            batch_docs,
            show_progress_bar=False
        )

        # Sparse (BM25)
        bm25_embeddings = list(bm25_embedding_model.embed(doc for doc in batch_docs))

        for eid, dense, bm25, record in zip(
            batch_ids,
            dense_embeddings,
            bm25_embeddings,
            batch_records,
        ):
            vectors.append({
                "id": eid,

                # Dense vector
                "dense_embedding": dense.tolist(),

                # Sparse vector (JSON-safe)
                "sparse_embedding": {
                    "indices": bm25.indices.tolist(),
                    "values": bm25.values.tolist(),
                },

                # Payload
                "text": build_doc_text(record),
                "title": record.get("title"),
                "abstract": record.get("abstract"),
                "authors": record.get("authors"),
                "publication_date": record.get("publication_date"),
                "download_url": record.get("download_url"),
                "field_of_study": record.get("field_of_study"),
                "arxiv_id": record.get("arxiv_id"),
                "citation": record.get("citation_count"),
            })

    save_embeddings(vectors, output_path)
    print(f"💾 Saved {len(vectors)} vectors to {output_path}")
