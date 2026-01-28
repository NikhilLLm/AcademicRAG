"""Route handlers for search endpoints."""
import asyncio
import logging
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator

from Backend.ingestion.extraction import extract_text_for_search, enhance_text_query
from Backend.embedding.embedd import embed_string
from Backend.search.service import SearchService
from Backend.notes.text.chunks_embeddings import TextPreprocessor
from Backend.notes.Visual.image_table_extractor import ImageTableExtractor
from Backend.notes.text.summarizer import generate_notes_from_pdf
from Backend.chat.start_chat_pipeline import prepare_chat
from Backend.chat.chat import hybrid_search_for_pdf, qa_chain
from Backend.database.qdrant_client import get_collection_name
# Pydantic schemas
from Backend.schemas.requests import (
    SearchTextRequest,
    StartNotesRequest,
    InitChatRequest,
    ChatMessageRequest
)
from Backend.schemas.responses import (
    SearchResponse,
    JobStatusResponse,
    JobInitResponse,
    ChatSessionResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()
search_service = SearchService()

#-------------------------------#
#Schema
#-------------------------------

@router.post("/search_text", response_model=SearchResponse)
async def search_text(request: SearchTextRequest):
    """
    Search similar papers by text query.
    
    What changed:
    - Now uses SearchTextRequest (validates query length)
    - Added response_model for consistent output
    - All logic stays the same!
    """
    try:
        # Enhance query and extract author if present (same as before)
        enhanced = enhance_text_query(request.query)
        author = enhanced.get("author")
        embeddings = embed_string(enhanced["enhanced_text"])

        dense_embedding = embeddings["dense_embedding"]
        sparse_embedding = embeddings["sparse_embedding"]
        
        # Search with optional author filter (same as before)
        results = search_service.search(
            dense_embedding=dense_embedding,
            sparse_embedding=sparse_embedding,
            limit=20,
            author_filter=author
        )
        
        return {"results": results}
    
    except ValueError as e:
        # Handle validation or processing errors
        logger.error(f"Search validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload")
async def upload(file: UploadFile = File(...)): 
    """Search similar papers by uploading either an image or a PDF.""" 
    contents = await file.read()

    try:
        # Step 1: Determine file type from content type
        if file.content_type in ["image/png", "image/jpeg", "image/jpg"]:
            file_type = "image"
        elif file.content_type == "application/pdf":
            file_type = "pdf"
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Step 2: Extract text (now with file_type parameter)
        result = extract_text_for_search(
            file_bytes=contents,
            file_type=file_type  # ✅ REQUIRED!
        )
        
        # Step 3: Handle the dict return
        # Option A: If your function returns dict with summary and embedding
        summary_text = result
        embeddings= embed_string(summary_text)
        dense_embedding = embeddings["dense_embedding"]
        sparse_embedding = embeddings["sparse_embedding"]
    
    # Search with optional author filter
        results = search_service.search(dense_embedding=dense_embedding,sparse_embedding=sparse_embedding, limit=5)
      # Fixed: serarch -> search
        
        return {"results":results}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



def run_notes_job(job_id,vector_index):
    try:
        """Generate short notes for a selected paper by its vector index."""
        #getting metadata and full text pdf from vector index
        metadata=search_service.get_metadata_by_id(vector_index)
        if not metadata:
            return {"error": "Paper not found"}
        
        # Get PDF URL
        pdf_url = metadata.get('download_url', '')
        if not pdf_url:
            return {"error": "No PDF URL available"}
            
        # result is now { "notes": ..., "visuals": ... }
        output = generate_notes_from_pdf(pdf_url=pdf_url)
        
        JOBS[job_id] = {
            "status": "done",
            "result": {
                "extracted_text": output["notes"],
                "visuals": output["visuals"],
                "papermetadata": metadata
            }
        }
    except Exception as e:
        JOBS[job_id] = {"status": "error", "error": str(e)}
    finally:
        ACTIVE_JOBS.pop(vector_index, None)  # ✅ important

#--------------------------------
# NOTES GENERATION ENDPOINTS
#--------------------------------

JOBS = {}
ACTIVE_JOBS = {}


@router.get("/job-status/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str):
    """
    Check status of a notes generation job.
    
    What this does:
    - Returns job status from JOBS dict (same as before)
    - Now uses JobStatusResponse for consistent format
    """
    return JOBS.get(job_id, {"status": "not_found"})


@router.post("/start_short_notes", response_model=JobInitResponse)
async def start_notes(
    request: StartNotesRequest,
    bg: BackgroundTasks = BackgroundTasks(),
):
    """
    Start generating notes for a paper.
    
    What changed:
    - Now uses StartNotesRequest (validates vector_index)
    - Added response_model
    - Logic stays exactly the same!
    """
    vector_index = request.vector_index
    
    # ✅ If job already exists, reuse it (same as before)
    if vector_index in ACTIVE_JOBS:
        job_id = ACTIVE_JOBS[vector_index]
        return {"job_id": job_id}

    job_id = str(uuid.uuid4())
    ACTIVE_JOBS[vector_index] = job_id
    JOBS[job_id] = {"status": "running"}

    bg.add_task(run_notes_job, job_id, vector_index)

    return {"job_id": job_id}


#################################
#-------------- CHAT ENDPOINT ---------
##################################
CHAT_JOBS = {}
ACTIVE_CHAT_JOBS = {}

def prepare_chat_pipeline(chat_session_id: str, vector_index: str):
    try:
        metadata = search_service.get_metadata_by_id(vector_index)
        if not metadata:
            CHAT_JOBS[chat_session_id] = {
                "status": "error",
                "error": "Paper not found"
            }
            return

        pdf_url = metadata.get("download_url")
        if not pdf_url:
            CHAT_JOBS[chat_session_id] = {
                "status": "error",
                "error": "No PDF URL available"
            }
            return

        result = prepare_chat(pdf_url=pdf_url)

        CHAT_JOBS[chat_session_id] = {
            "status": "done",
            "pdf_id": result["pdf_id"],   # ✅ store here
        }

    except Exception as e:
        CHAT_JOBS[chat_session_id] = {
            "status": "error",
            "error": str(e)
        }

    finally:
        ACTIVE_CHAT_JOBS.pop(vector_index, None)

@router.get("/chat-job-status/{chat_session_id}")
def chat_job_status(chat_session_id: str):
    return CHAT_JOBS.get(chat_session_id, {"status": "not_found"})



@router.post("/init_chat", response_model=ChatSessionResponse)
async def init_chat(
    request: InitChatRequest,
    bg: BackgroundTasks = BackgroundTasks()
):
    """
    Initialize chat session for a paper.
    
    What changed:
    - Now uses InitChatRequest (validates vector_index)
    - Added response_model
    - Logic stays the same!
    """
    vector_index = request.vector_index
    
    if vector_index in ACTIVE_CHAT_JOBS:
        return {"chat_session_id": ACTIVE_CHAT_JOBS[vector_index]}

    chat_session_id = str(uuid.uuid4())
    ACTIVE_CHAT_JOBS[vector_index] = chat_session_id
    CHAT_JOBS[chat_session_id] = {"status": "processing"}

    bg.add_task(prepare_chat_pipeline, chat_session_id, vector_index)
    return {"chat_session_id": chat_session_id}


@router.post("/chat/{chat_id}/stream")
async def chat_message(chat_id: str, request: ChatMessageRequest):
    """
    Send a message in an active chat session.
    
    What changed:
    - Now uses ChatMessageRequest (validates message)
    - Replaced print() with logger.info()
    - Logic stays exactly the same!
    """

    async def wait_for_chat_done():
        """Wait until the chat job status becomes 'done'."""
        while True:
            chat_state = CHAT_JOBS.get(chat_id)
            if not chat_state:
                raise HTTPException(status_code=404, detail="Chat session not found")
            if chat_state.get("status") == "done":
                return chat_state
            await asyncio.sleep(0.5)

    async def stream_answer() -> AsyncGenerator[str, None]:
        chat_state = await wait_for_chat_done()
        pdf_id = chat_state["pdf_id"]
        
        docs = hybrid_search_for_pdf(
            query=request.message,
            pdf_id=pdf_id,
            collection_name=get_collection_name("pdf_vectors_v2"),
            k=100
        )
        
        # Changed: print() -> logger.info()
        logger.info(f"Retrieved {len(docs)} chunks for query: {request.message}")
        for i, doc in enumerate(docs):
            logger.debug(f"Chunk {i}: {doc.page_content[:200]}...")

        async for chunk in qa_chain(
            user_query=request.message,
            retrieved_docs=docs,
        ):
            yield chunk

    return StreamingResponse(
        stream_answer(),
        media_type="text/stream"
    )


