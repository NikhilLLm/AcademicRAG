
import math
import logging
import hashlib
from langchain_core.documents import Document
from Backend.models.groq import groq_llm
from Backend.models.prompts import NOTES_PROMPT

from Backend.notes.text.chunks_embeddings import TextPreprocessor, CustomEmbedder, generate_pdf_id
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import (
    QueryRequest, VectorInput, SparseVector, 
    Prefetch, Filter, FieldCondition, MatchValue,  PayloadSchemaType,FusionQuery,
    Fusion,
)
from Backend.notes.text.model import batch_chain, final_chain
from Backend.embedding.embedd import embed_string
import os
from dotenv import load_dotenv

load_dotenv("C:/Users/nshej/aisearch/.env")

# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

URL = "https://72bcce7c-0237-4ae3-a1ec-12a43a79396e.europe-west3-0.gcp.cloud.qdrant.io"
api_key = os.getenv("qdrant_key")

# ----------------------------
# Qdrant Client
# ----------------------------
try:
    client = QdrantClient(
        url=URL,
        api_key=api_key,
        prefer_grpc=False
    )
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


# ----------------------------
# Hybrid Search with PDF ID Filtering
# ----------------------------
def hybrid_search_for_pdf(query: str, pdf_id: str, collection_name: str, k: int = 30):
    """
    Perform hybrid search filtered by PDF ID.
    This ensures you only search within ONE specific PDF.
    """
    try:
        logger.info(f"Hybrid search for PDF ID: {pdf_id}")
        
        # Get hybrid embeddings for query
        query_embedding = embed_string(query)
        
        # Create filter for this PDF only
        pdf_filter = Filter(
            must=[
                FieldCondition(
                    key="pdf_id",
                    match=MatchValue(value=pdf_id)
                )
            ]
        )
        
        # Perform hybrid search with filter
        search_results = client.query_points(
            collection_name=collection_name,
            prefetch=[
                Prefetch(
                    query=query_embedding["dense_embedding"],
                    using="dense",
                    limit=k,
                    filter=pdf_filter  # ← Only this PDF
                ),
                Prefetch(
                    query=SparseVector(
                        indices=query_embedding["sparse_embedding"]["indices"],
                        values=query_embedding["sparse_embedding"]["values"]
                    ),
                    using="sparse",
                    limit=k,
                    filter=pdf_filter  # ← Only this PDF
                )
            ],
            query=FusionQuery(fusion=Fusion.RRF), #This query takes object not dict 
            limit=k
        )
        
        # Convert to LangChain Document format
        documents = []
        for point in search_results.points:
            doc = Document(
                page_content=point.payload.get("page_content", ""),
                metadata={
                    "pdf_id": point.payload.get("pdf_id"),
                    "pdf_url": point.payload.get("pdf_url"),
                    "chunk_id": point.payload.get("chunk_id"),
                    "section": point.payload.get("section"),
                    "source": point.payload.get("source"),
                    "type": point.payload.get("type")
                }
            )
            documents.append(doc)
        
        logger.info(f"✅ Found {len(documents)} chunks for PDF ID: {pdf_id}")
        return documents
        
    except Exception as e:
        logger.exception(f"Hybrid search failed for PDF ID: {pdf_id}")
        return []


# ----------------------------
# Helper: Batch Extraction (Stage 1)
# ----------------------------
def batch_extract_chunks(chunks, batch_size=15):
    """
    Stage 1: Extract key information from chunks without structure.
    """
    extractions = []
    total_batches = math.ceil(len(chunks) / batch_size)

    logger.info(f"Stage 1: Extracting information | Total batches: {total_batches}")

    for i in range(total_batches):
        try:
            batch = chunks[i * batch_size:(i + 1) * batch_size]
            batch_text = "\n\n---\n\n".join([c.page_content for c in batch])

            extraction = batch_chain.invoke(batch_text)
            extractions.append(extraction)

            logger.info(f"✅ Extracted batch {i + 1}/{total_batches}")

        except Exception as e:
            logger.exception(f"❌ Failed to extract batch {i + 1}")
            continue

    return extractions


# ----------------------------
# Main Pipeline with PDF ID
# ----------------------------
def generate_notes_from_pdf(pdf_url: str):
    """
    Two-stage summarization with hybrid search and PDF isolation:
    1. Extract key info from chunks (batch_chain)
    2. Synthesize into structured notes (final_chain)
    
    This function works on ONE specific PDF only.
    """
    # Generate PDF ID
    pdf_id = generate_pdf_id(pdf_url)
    logger.info(f"Processing PDF ID: {pdf_id}")
    logger.info(f"PDF URL: {pdf_url}")
    
    # ----------------------------
    # Ensure embeddings exist
    # ----------------------------
    batch_size=15
    try:
        ensure_collection_exists(
            pdf_url=pdf_url,
            collection_name="pdf_vectors"
        )
    except Exception as e:
        logger.exception("Failed during embedding preparation stage")
        raise e

    # ----------------------------
    # Retrieval Queries (Filtered by PDF ID)
    # ----------------------------
    RETRIEVAL_QUERIES = [
        "Problem definition and motivation",
        "Algorithm description and methodology",
        "Mathematical formulation and equations",
        "Experimental setup datasets and baselines",
        "Results metrics accuracy F1 runtime",
        "Limitations and future work",
        "Related work and referenced methods"
    ]

    all_chunks = []

    for query in RETRIEVAL_QUERIES:
        try:
            logger.info(f"Performing hybrid search for query: '{query}'")
            retrieved = hybrid_search_for_pdf(
                query=query,
                pdf_id=pdf_id,  # ← Filter by this PDF only
                collection_name="pdf_vectors",
                k=75
            )
            all_chunks.extend(retrieved)
            logger.info(f"✅ Retrieved {len(retrieved)} chunks")

        except Exception as e:
            logger.exception(f"Failed retrieval for query: {query}")
            continue

    # ----------------------------
    # Deduplication
    # ----------------------------
    seen = set()
    unique_chunks = []

    for c in all_chunks:
        try:
            key = c.metadata.get("chunk_id") or c.page_content
            if key not in seen:
                seen.add(key)
                unique_chunks.append(c)
        except Exception as e:
            logger.warning("Skipping malformed chunk during deduplication")
            continue

    logger.info(f"Total unique chunks retrieved for PDF ID '{pdf_id}': {len(unique_chunks)}")

    if len(unique_chunks) == 0:
        logger.error(f"No chunks retrieved for PDF ID '{pdf_id}'! Check if PDF is embedded.")
        raise ValueError(f"No chunks found for PDF ID '{pdf_id}' in collection 'pdf_vectors'")

    # ----------------------------
    # STAGE 1: Batch Extraction
    # ----------------------------
    try:
        logger.info("=" * 50)
        logger.info("STAGE 1: Extracting key information from chunks")
        logger.info("=" * 50)

        batch_extractions = batch_extract_chunks(
            unique_chunks,
            batch_size=batch_size
        )

        logger.info(f"✅ Stage 1 Complete: {len(batch_extractions)} extractions")

    except Exception as e:
        logger.exception("Stage 1 extraction failed")
        raise e

    # ----------------------------
    # STAGE 2: Final Synthesis
    # ----------------------------
    try:
        logger.info("=" * 50)
        logger.info("STAGE 2: Synthesizing structured notes")
        logger.info("=" * 50)

        # Merge all extractions
        merged_extractions = "\n\n=== CHUNK ===\n\n".join(batch_extractions)

        # Use final_chain for structured synthesis
        final_notes = groq_llm(text=merged_extractions,MODEL_NAME="llama-3.3-70b-versatile",max_token=1000,temperature=0.1,prompt_template=NOTES_PROMPT.template)

        logger.info(f"✅ Stage 2 Complete: Final notes generated for PDF ID: {pdf_id}")
        return final_notes

    except Exception as e:
        logger.exception("Stage 2 synthesis failed")
        raise e

# ----------------------------
# Example usage
# ----------------------------
# if __name__ == "__main__":
#     try:
#         pdf_url = "http://arxiv.org/abs/1507.02188v1"
        
#         logger.info("\n" + "=" * 60)
#         logger.info("STARTING TWO-STAGE NOTE GENERATION PIPELINE")
#         logger.info("=" * 60 + "\n")
        
#         notes = generate_notes_from_pdf(pdf_url, batch_size=15)

#         print("\n" + "=" * 60)
#         print("FINAL STRUCTURED NOTES")
#         print("=" * 60 + "\n")
#         print(notes)

#         # ----------------------------
#         # Save notes to file
#         # ----------------------------
#         output_path = r"C:\Users\nshej\aisearch\text_notes.txt"
#         try:
#             with open(output_path, "w", encoding="utf-8") as f:
#                 f.write(notes)
#             logger.info(f"\n✅ Notes successfully saved to: {output_path}")
#         except Exception as e:
#             logger.exception("Failed to save notes to file")

#     except Exception as e:
#         logger.exception("\n❌ Pipeline execution failed")