
import math
import logging
import hashlib
from langchain_core.documents import Document

from Backend.models.prompts import FACTUAL_QA_PROMPT
from Backend.database.qdrant_client import get_qdrant_client
from qdrant_client.models import (
    QueryRequest, VectorInput, SparseVector, 
    Prefetch, Filter, FieldCondition, MatchValue,  PayloadSchemaType,FusionQuery,
    Fusion,
)
from Backend.notes.text.model import batch_chain
from Backend.embedding.embed_local import embed_string_small
from Backend.ingestion.extraction import enhance_text_query
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import AsyncGenerator

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

def hybrid_search_for_pdf(query: str, pdf_id: str, collection_name: str, k: int = 100):
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
                    "type": payload.get("type")
                }
            )
            documents.append(doc)
        
        logger.info(f"✅ Found {len(documents)} chunks for PDF ID: {pdf_id}")
        return documents
        
    except Exception as e:
        logger.exception(f"Hybrid search failed for PDF ID: {pdf_id}")
        return []
    
#------------------------------------
# CALLING LLM WITH STREAM RESPONSE
#-----------------------------------
async def groq_llm_stream(
    text,
    MODEL_NAME: str,
    max_token: int | None,
    temperature: float,
    prompt_template: PromptTemplate,
) -> AsyncGenerator[str, None]:

    if text is None:
        return  # ✅ just exit, not return ""

    model = ChatGroq(
        temperature=temperature,
        model=MODEL_NAME,
        max_tokens=max_token,
        streaming=True
    )

    chain = prompt_template | model

    expected_vars = prompt_template.input_variables
    missing = set(expected_vars) - set(text.keys())
    if missing:
        raise KeyError(f"Missing prompt variables: {missing}")

    async for chunk in chain.astream(text):
        content = chunk.content

        # ✅ normalize to string
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            # list[str | dict] → string
            yield "".join(
                part if isinstance(part, str) else str(part)
                for part in content
            )
#-----------------------
#  QA_CHAIN
#-----------------------
async def qa_chain(
    user_query: str,
    retrieved_docs: list,
) -> AsyncGenerator[str, None]:

    context = "\n".join(
        f"[Source {i+1}]\n{doc.page_content}"
        for i, doc in enumerate(retrieved_docs)
    )

    query = enhance_text_query(user_input=user_query)

    async for token in groq_llm_stream(
        text={
            "context": context,
            "question": query["enhanced_text"]
        },
        MODEL_NAME="llama-3.3-70b-versatile",
        temperature=0.3,
        max_token=None,
        prompt_template=FACTUAL_QA_PROMPT,
    ):
        yield token
