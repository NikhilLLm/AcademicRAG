import math
import logging
import hashlib
from langchain_core.documents import Document


from Backend.notes.text.chunks_embeddings import TextPreprocessor, CustomEmbedder, generate_pdf_id
from langchain_qdrant import QdrantVectorStore
from Backend.database.qdrant_client import get_qdrant_client, get_collection_name
from qdrant_client.models import (
    QueryRequest, VectorInput, SparseVector, 
    Prefetch, Filter, FieldCondition, MatchValue,  PayloadSchemaType,FusionQuery,
    Fusion,
)
from Backend.notes.text.model import batch_chain, final_chain
from Backend.embedding.embed_local import embed_string_small

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ----------------------------
# Qdrant Client - Centralized
# ----------------------------
try:
    client = get_qdrant_client()
    logger.info("Connected to Qdrant successfully")
except Exception as e:
    logger.exception("Failed to connect to Qdrant")
    raise e


# ----------------------------
# Collection Check with PDF ID
# ----------------------------
def ensure_collection_exists(pdf_url: str, collection_name: str):
    """
    Ensures collection exists and checks if THIS specific PDF is already embedded.
    """
    try:
        pdf_id = generate_pdf_id(pdf_url)
        
        # Check if collection exists
        collections = client.get_collections().collections
        existing = [c.name for c in collections]

        if collection_name not in existing:
            logger.warning(f"⚠️ Collection '{collection_name}' not found. Creating...")
            processor = TextPreprocessor(pdf_url)
            vector_store = processor.process_pdf()
            
            if vector_store is None:
                raise RuntimeError("Embedding pipeline failed to create vector store")
            
            logger.info(f"✅ Collection '{collection_name}' created with PDF ID: {pdf_id}")
            return

        # Collection exists - check if this PDF is already embedded
        
        client.create_payload_index(
                    collection_name=collection_name,
                    field_name="pdf_id",
                    field_schema=PayloadSchemaType.KEYWORD
        )
        collection_info = client.get_collection(collection_name)
        # Try to find points with this pdf_id
        search_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="pdf_id",
                        match=MatchValue(value=pdf_id)
                    )
                ]
            ),
            limit=1
        )
        points, _ = search_result
        if len(points) > 0:  # Points found for this PDF
            logger.info(f"✅ PDF ID '{pdf_id}' already exists in collection. Skipping embedding.")
            return
        
        # PDF not found - run embedding
        logger.warning(f"⚠️ PDF ID '{pdf_id}' not found in collection. Running embedding pipeline...")
        processor = TextPreprocessor(pdf_url)
        vector_store = processor.process_pdf()
        
        if vector_store is None:
            raise RuntimeError("Embedding pipeline failed")
        logger.info(f"✅ PDF ID '{pdf_id}' embedded successfully")

    except Exception as e:
        logger.exception("❌ Failed while ensuring collection existence")
        raise e
    
def prepare_chat(pdf_url: str) -> dict:
    """
    Prepare PDF for chat usage.
    Returns chat-level readiness info.
    """
    pdf_id = generate_pdf_id(pdf_url)
    logger.info(f"Preparing chat for PDF ID: {pdf_id}")

    ensure_collection_exists(
        pdf_url=pdf_url,
        collection_name=get_collection_name("pdf_vectors_v2")
    )

    return {
        "pdf_id": pdf_id,
        "status": "ready"
    }
    