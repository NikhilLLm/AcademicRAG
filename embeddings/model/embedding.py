import os
import json
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# === CONFIG ===
# Use the model name (string) here. Creating a SentenceTransformer
# instance is done below when we actually load the model.
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

BATCH_SIZE = 32

# === PATHS ===
INPUT_ROOT = "C:/Users/nshej/aisearch/data/metadata"
OUTPUT_ROOT = "C:/Users/nshej/aisearch/embeddings/chunks"

# === LOAD MODEL ===
# Instantiate the SentenceTransformer using the model name string.
model = SentenceTransformer(MODEL_NAME)

# === HELPERS ===
def load_metadata(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_text(record):
    title = (record.get("title") or "").strip()
    abstract = record.get("abstract")
    abstract = abstract.strip() if isinstance(abstract, str) else ""

    if abstract and "no abstract" not in abstract.lower():
        return f"{title}. {abstract}"
    return title

def get_unique_id(record):
    return record.get("arxiv_id") or record.get("title")

def save_embeddings(vectors, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in vectors:
            json.dump(item, f)
            f.write('\n')

# === MAIN LOOP ===
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
    all_texts, all_ids, all_records = [], [], []
    seen_ids = set()

    # Load and combine all batches
    for file in sorted(os.listdir(field_path)):
        if not file.endswith(".json"):
            continue
        batch_path = os.path.join(field_path, file)
        records = load_metadata(batch_path)

        for record in records:
            text = build_text(record)
            if not text:
                continue
            eid = get_unique_id(record)
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)
            all_texts.append(text)
            all_ids.append(eid)
            all_records.append(record)

    print(f"📦 Total unique records to embed: {len(all_texts)}")
    vectors = []

    for i in tqdm(range(0, len(all_texts), BATCH_SIZE)):
        batch_texts = all_texts[i:i+BATCH_SIZE]
        batch_ids = all_ids[i:i+BATCH_SIZE]
        batch_records = all_records[i:i+BATCH_SIZE]
        embeddings = model.encode(batch_texts, show_progress_bar=False)

        for eid, emb, raw_text, record in zip(batch_ids, embeddings, batch_texts, batch_records):
            vectors.append({
                "id": eid, #
                "embedding": emb.tolist(),
                "text": raw_text,
                "title": record.get("title"),
                "abstract": record.get("abstract"),
                "authors": record.get("authors"),
                "publication_date": record.get("publication_date"),
                "download_url": record.get("download_url"),
                "field_of_study": record.get("field_of_study"),
                "arxiv_id": record.get("arxiv_id"),
            })

    save_embeddings(vectors, output_path)
    print(f"💾 Saved {len(vectors)} vectors to {output_path}")
