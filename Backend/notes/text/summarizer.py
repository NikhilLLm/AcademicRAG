
import math
import logging
import hashlib
from langchain_core.documents import Document
from Backend.models.groq import groq_llm
from Backend.models.prompts import NOTES_PROMPT,VALIDATION_PROMPT,FINAL_NOTES_PROMPT

from Backend.notes.text.chunks_embeddings import TextPreprocessor, CustomEmbedder, generate_pdf_id
from langchain_qdrant import QdrantVectorStore
from Backend.database.qdrant_client import get_qdrant_client, get_collection_name
from qdrant_client.models import (
    QueryRequest, VectorInput, SparseVector, 
    Prefetch, Filter, FieldCondition, MatchValue,  PayloadSchemaType,FusionQuery,
    Fusion,
)
from Backend.notes.text.model import batch_chain
from Backend.embedding.embed_local import embed_string_small

# ----------------------------
# Logging Configuration
# ----------------------------
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
        query_embedding = embed_string_small(query)
        
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
            payload = point.payload or {}
            doc = Document(
                page_content=payload.get("page_content", ""),
                metadata={
                    "pdf_id": payload.get("pdf_id"),
                    "pdf_url": payload.get("pdf_url"),
                    "chunk_id": payload.get("chunk_id"),
                    "section": payload.get("section"),
                    "source": payload.get("source"),
                    "type": payload.get("type"),
                    "image_base64": payload.get("image_base64") # ✅ Retrieve Base64
                }
            )
            documents.append(doc)
        
        logger.info(f"✅ Found {len(documents)} chunks for PDF ID: {pdf_id}")
        # Debug: Check if any chunk has image_base64
        visual_count = sum(1 for d in documents if d.metadata.get("image_base64"))
        logger.info(f"🔍 Chunks with image_base64: {visual_count}")
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

def generate_final_notes_with_validation(
    merged_extractions: str,
    max_iterations: int = 2
) -> str:
    """
    Iterative generate → validate → repair loop
    """

    # -------- Step 1: Draft structured notes --------
    notes = groq_llm(
        text=merged_extractions,
        MODEL_NAME="llama-3.3-70b-versatile",
        max_token=1200,
        temperature=0.1,
        prompt_template=NOTES_PROMPT
    )

    for iteration in range(max_iterations):
        logger.info(f"🔁 Validation loop iteration {iteration + 1}")

        # -------- Step 2: Validate --------
        validation_report = groq_llm(
            text={
                "notes": notes,
                "source": merged_extractions
            },
            MODEL_NAME="openai/gpt-oss-20b",   # or DeepSeek-R1
            max_token=600,
            temperature=0.0,
            prompt_template=VALIDATION_PROMPT
        )

        # Optional: break early if no issues
        if '"incorrect_claims": []' in validation_report and \
           '"unsupported_claims": []' in validation_report and \
           '"speculative_claims": []' in validation_report:
            logger.info("✅ Notes passed validation with no critical issues")
            break

        # -------- Step 3: Repair --------
        notes = groq_llm(
            text={
                "validation": validation_report,
                "notes": notes
            },
            MODEL_NAME="llama-3.1-8b-instant",
            max_token=1200,
            temperature=0.1,
            prompt_template=FINAL_NOTES_PROMPT
        )

    return notes

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
            collection_name=get_collection_name("pdf_vectors_v2")
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
                collection_name=get_collection_name("pdf_vectors_v2"),
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
        raise ValueError(f"No chunks found for PDF ID '{pdf_id}' in collection '{get_collection_name('pdf_vectors_v2')}'")

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
        final_notes = generate_final_notes_with_validation(
            merged_extractions=merged_extractions,
            max_iterations=2
        )


        logger.info(f"✅ Stage 2 Complete: Final notes generated for PDF ID: {pdf_id}")
        # Collect visuals
        visuals = []
        seen_visuals = set()
        for c in unique_chunks:
            b64 = c.metadata.get("image_base64")
            if b64 and b64 not in seen_visuals:
                # Extract description from <figure_description> tags if present
                content = c.page_content
                description = content
                if "<figure_description>" in content:
                    description = content.replace("<figure_description>", "").replace("</figure_description>", "").strip()

                visuals.append({
                    "type": "image",
                    "base64": b64,
                    "caption": description[:100] + "..." if len(description) > 100 else description,
                    "description": description
                })
                seen_visuals.add(b64)

        logger.info(f"✅ Stage 2 Complete: Final notes generated for PDF ID: {pdf_id}")
        
        return {
            "notes": final_notes,
            "visuals": visuals[:5] # Return top 5 visuals
        }

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