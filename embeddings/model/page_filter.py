import fitz
import requests
from io import BytesIO
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import os
import time

load_dotenv("C:/Users/nshej/aisearch/.env")

client = QdrantClient(
    url="https://72bcce7c-0237-4ae3-a1ec-12a43a79396e.europe-west3-0.gcp.cloud.qdrant.io",
    api_key=os.getenv("qdrant_key"),
)

COLLECTION = "papers_semantic_v1"
PAGE_CACHE = {}

def get_num_pages(abs_url):
    """Download PDF and get page count, with caching."""
    if abs_url in PAGE_CACHE:
        return PAGE_CACHE[abs_url]

    pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"
    r = requests.get(pdf_url, timeout=15)
    r.raise_for_status()

    with fitz.open(stream=BytesIO(r.content), filetype="pdf") as doc:
        PAGE_CACHE[abs_url] = doc.page_count
        return doc.page_count

def enrich_num_pages():
    print("Starting full enrichment of num_pages for all points...")

    offset = None
    processed = 0
    MAX_PER_RUN = 200

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            with_payload=True,
            limit=100,
            offset=offset,
        )

        for p in points:
            # Skip already processed
            if p.payload.get("num_pages") is not None:
                continue

            abs_url = p.payload.get("download_url")
            if not abs_url:
                continue

            try:
                num_pages = get_num_pages(abs_url)
            except Exception as e:
                print(f"❌ Failed {abs_url}: {e}")
                continue

            client.set_payload(
                collection_name=COLLECTION,
                payload={"num_pages": num_pages},
                points=[p.id],   # ✅ FAST & CORRECT
            )

            processed += 1
            print(f"✅ {p.id} → {num_pages} pages")

            if processed >= MAX_PER_RUN:
                print("🛑 Batch limit reached, stopping")
                return

        if offset is None:
            break


if __name__ == "__main__":
    print("Starting full enrichment of num_pages for all points...")
    enrich_num_pages()

    print("\nCreating payload index for num_pages...")
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="num_pages",
        field_schema=models.PayloadSchemaType.INTEGER
    )
    print("✅ Payload index ready")
