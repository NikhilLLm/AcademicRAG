"""Route handlers for search endpoints."""
import asyncio
from fastapi import APIRouter, UploadFile, File, Form,HTTPException,BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional,AsyncGenerator
from Backend.ingestion.extraction import extract_text_for_search, enhance_text_query
from Backend.embedding.embedd import embed_string
from Backend.search.service import SearchService
from Backend.notes.text.chunks_embeddings import TextPreprocessor
from Backend.notes.Visual.image_table_extractor import ImageTableExtractor
from Backend.notes.text.summarizer import generate_notes_from_pdf
from Backend.chat.start_chat_pipeline import prepare_chat
from Backend.chat.schema import ChatMessageRequest
from Backend.chat.chat import hybrid_search_for_pdf,qa_chain

import uuid
from pydantic import BaseModel
router = APIRouter()
search_service = SearchService()

#-------------------------------#
#Schema
#-------------------------------

@router.post("/search_text")
async def search_text(query: str = Form(...)):
    """Search similar papers by text query."""
    # Enhance query and extract author if present
    enhanced = enhance_text_query(query)
    author = enhanced.get("author")
    embeddings = embed_string(enhanced["enhanced_text"])

    dense_embedding = embeddings["dense_embedding"]
    sparse_embedding = embeddings["sparse_embedding"]
    
    # Search with optional author filter
    results = search_service.search(dense_embedding=dense_embedding,sparse_embedding=sparse_embedding, limit=20, author_filter=author)
    
    return {"results": results}

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
        result=generate_notes_from_pdf(pdf_url=pdf_url)
        JOBS[job_id] = {
            "status": "done",
            "result": {"extracted_text": result, "papermetadata": metadata}
        }
    except Exception as e:
        JOBS[job_id] = {"status": "error", "error": str(e)}
    finally:
        ACTIVE_JOBS.pop(vector_index, None)  # ✅ important



JOBS={}
#tasks creation 
ACTIVE_JOBS={}
@router.get("/job-status/{job_id}")
def job_status(job_id: str):
    return JOBS.get(job_id, {"status": "not_found"})
@router.post("/start_short_notes")

async def start_notes(
    vector_index: str = Form(...),
    bg: BackgroundTasks = BackgroundTasks(),
):
    # ✅ If job already exists, reuse it
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



@router.post("/init_chat")
async def init_chat(vector_index: str = Form(...), bg: BackgroundTasks = BackgroundTasks()):
    if vector_index in ACTIVE_CHAT_JOBS:
        return {"chat_session_id": ACTIVE_CHAT_JOBS[vector_index]}

    chat_session_id = str(uuid.uuid4())
    ACTIVE_CHAT_JOBS[vector_index] = chat_session_id
    CHAT_JOBS[chat_session_id] = {"status": "processing"}

    bg.add_task(prepare_chat_pipeline, chat_session_id, vector_index)
    return {"chat_session_id": chat_session_id}

@router.post("/chat/{chat_id}/stream")
async def chat_message(chat_id: str, payload: ChatMessageRequest):

    async def wait_for_chat_done():
        """Wait until the chat job status becomes 'done'."""
        while True:
            chat_state = CHAT_JOBS.get(chat_id)
            if not chat_state:
                raise HTTPException(status_code=404, detail="Chat session not found")
            if chat_state.get("status") == "done":
                return chat_state  # return the chat_state once done
            await asyncio.sleep(0.5)  # check every 0.5s, adjust if needed

    async def stream_answer() -> AsyncGenerator[str, None]:
        
      chat_state = await wait_for_chat_done()
  
      pdf_id = chat_state["pdf_id"]  # ✅ authoritative source
  
      docs = hybrid_search_for_pdf(
          query=payload.message,
          pdf_id=pdf_id,
          collection_name="pdf_vectors",
          k=10
      )
      
      print("Retrieved Chunks for query:", payload.message)
      for i, doc in enumerate(docs):
          print(f"Chunk {i}:{doc.page_content[:200]}...")

      async for chunk in qa_chain(
          user_query=payload.message,
          retrieved_docs=docs,
      ):
       yield chunk
    

    

    return StreamingResponse(
        stream_answer(),
        media_type="text/stream"
    )


