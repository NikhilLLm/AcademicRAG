"""Route handlers for search endpoints."""
import asyncio
import logging
import uuid
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime
from Backend.ingestion.extraction import extract_text_for_search, enhance_text_query
from Backend.embedding.embedd import embed_string
from Backend.search.service import SearchService
from Backend.notes.text.chunks_embeddings import TextPreprocessor
from Backend.notes.Visual.image_table_extractor import ImageTableExtractor
from Backend.notes.text.summarizer import generate_notes_from_pdf
from Backend.chat.start_chat_pipeline import prepare_chat
from Backend.chat.chat import hybrid_search_for_pdf, qa_chain
from Backend.database.qdrant_client import get_collection_name
from Backend.database.db_session import get_session
from Backend.database.tables import User, Notes,SearchHistory,ChatSession,ChatMessages, NotesJob, ChatPrepJob
from Backend.utils.dependencies import get_current_user,get_optional_user
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
    ChatSessionResponse,ChatMessageResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()
search_service = SearchService()

#-------------------------------#
#Schema
#-------------------------------

@router.post("/search_text", response_model=SearchResponse)
def search_text(
    request: SearchTextRequest, 
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user) # Now optional!
):
    """
    Search similar papers by text query.
    Saves history if user is logged in.
    """
    try:
        # Save Search History if user exists
        if current_user:
            try:
                new_history = SearchHistory(user_id=current_user.id, query=request.query)
                session.add(new_history)
                session.commit()
            except Exception as e:
                logger.error(f"Failed to save search history: {e}")
                
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
def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
): 
    """Search similar papers by uploading either an image or a PDF.""" 
    contents = file.read()

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



def run_notes_job(job_id, vector_index, user_id):
    """Generate notes for a paper and store both DB record and job status."""
    logger.info(f"Starting notes job {job_id} for vector {vector_index}")
    session = next(get_session())
    try:
        job = session.query(NotesJob).filter(NotesJob.id == job_id).first()
        if not job:
            logger.error(f"NotesJob {job_id} not found in DB")
            return

        # Get metadata from Qdrant
        metadata = search_service.get_metadata_by_id(vector_index)
        if not metadata:
            logger.error(f"Metadata not found for vector {vector_index}")
            job.status = "error"
            job.error = "Paper not found"
            session.commit()
            return
        
        logger.info(f"Found metadata: {metadata.get('title')}")
        
        # Get PDF URL and title
        pdf_url = metadata.get('download_url', '')
        title = metadata.get('title', 'Untitled Paper')
        
        logger.info(f"Generating notes content for PDF: {pdf_url}")
        
        # ---------------------------------------------------------
        # GENERATE CONTENT (LLM + Visuals)
        # ---------------------------------------------------------
        generated_data = generate_notes_from_pdf(pdf_url)
        content_text = generated_data.get("notes", "")
        visuals_list = generated_data.get("visuals", [])
        
        # ---------------------------------------------------------
        # SAVE TO DB
        # ---------------------------------------------------------
        session = next(get_session())
        try:
            # Check if already exists
            existing_note = session.query(Notes).filter(
                Notes.user_id == user_id,
                Notes.pdf_id == vector_index
            ).first()
            
            if not existing_note:
                logger.info(f"Saving new note to DB for user {user_id}")
                new_note = Notes(
                    user_id=user_id,
                    pdf_id=vector_index,
                    title=title,
                    pdf_url=pdf_url,
                    content=content_text,                # ✅ Saved
                    visuals=json.dumps(visuals_list)     # ✅ Saved as JSON string
                )
                session.add(new_note)
                session.commit()
            else:
                logger.info(f"Note already exists for user {user_id}. Updating content.")
                # Update existing note if it was empty
                existing_note.content = content_text
                existing_note.visuals = json.dumps(visuals_list)
                session.commit()
                
        except Exception as e:
            logger.error(f"DB Error saving note: {e}")
            raise e
        finally:
            session.close()
        
        # Mark job as done and RETURN FULL DATA (stored as JSON in NotesJob)
        logger.info(f"Job {job_id} marked as done")
        job.status = "done"
        job_result = {
            "message": "Notes generated successfully",
            "extracted_text": content_text,          # For Frontend
            "visuals": visuals_list,                 # For Frontend
            "papermetadata": {                       # For Frontend
                "title": title,
                "download_url": pdf_url, 
                "authors": metadata.get("authors", []),
            },
        }
        # Persist in DB
        job.result = json.dumps(job_result)
        job.error = None
        session.commit()

        # Also update legacy in-memory dict to preserve old behaviour
        JOBS[job_id] = {
            "status": "done",
            "result": job_result,
        }
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job = session.query(NotesJob).filter(NotesJob.id == job_id).first()
        if job:
            job.status = "error"
            job.error = str(e)
            session.commit()
        # Reflect error in legacy dict too
        JOBS[job_id] = {"status": "error", "error": str(e)}
    finally:
        session.close()

#--------------------------------
# NOTES GENERATION ENDPOINTS
#--------------------------------

# Legacy in-memory structures are no longer the source of truth for jobs.
# They are kept here only to avoid breaking imports, but all status is stored
# in the database tables NotesJob and ChatPrepJob.
JOBS = {}
ACTIVE_JOBS = {}


@router.get("/job-status/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, session: Session = Depends(get_session)):
    """Check status of a notes generation job.

    For compatibility with the existing frontend, we first look at the legacy
    in-memory JOBS dict (same shape as before). If nothing is found there,
    we fall back to the DB-backed NotesJob table.
    """
    # 1) Legacy in-memory behaviour (preserves existing frontend expectations)
    if job_id in JOBS:
        return JOBS[job_id]

    # 2) DB-backed fallback (in case process restarted or JOBS was cleared)
    job = session.query(NotesJob).filter(NotesJob.id == job_id).first()
    if not job:
        return {"status": "not_found"}

    result_dict = None
    if job.result:
        try:
            result_dict = json.loads(job.result)
        except Exception:
            result_dict = None

    return {
        "status": job.status,
        "result": result_dict,
        "error": job.error,
    }


@router.post("/start_short_notes", response_model=JobInitResponse)
async def start_notes(
    request: StartNotesRequest,
    bg: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Start generating notes for a paper.
    
    What changed:
    - Now uses StartNotesRequest (validates vector_index)
    - Added response_model
    - Logic stays exactly the same!
    """
    vector_index = request.vector_index

    # If a job for this user and vector_index already exists, reuse its ID.
    existing_job = (
        session.query(NotesJob)
        .filter(
            NotesJob.user_id == current_user.id,
            NotesJob.vector_index == vector_index,
        )
        .order_by(NotesJob.created_at.desc())
        .first()
    )
    if existing_job:
        return {"job_id": existing_job.id}

    job_id = str(uuid.uuid4())
    new_job = NotesJob(
        id=job_id,
        user_id=current_user.id,
        vector_index=vector_index,
        status="running",
    )
    session.add(new_job)
    session.commit()

    bg.add_task(run_notes_job, job_id, vector_index, current_user.id)

    return {"job_id": job_id}


#################################
#-------------- CHAT ENDPOINT ---------
##################################
# Same for chat preparation jobs – DB-backed via ChatPrepJob.
CHAT_JOBS = {}
ACTIVE_CHAT_JOBS = {}

def prepare_chat_pipeline(chat_session_id: str, vector_index: str):
    session = next(get_session())
    try:
        job = session.query(ChatPrepJob).filter(ChatPrepJob.id == chat_session_id).first()
        if not job:
            logger.error(f"ChatPrepJob {chat_session_id} not found in DB")
            return

        metadata = search_service.get_metadata_by_id(vector_index)
        if not metadata:
            job.status = "error"
            job.error = "Paper not found"
            session.commit()
            return

        pdf_url = metadata.get("download_url")
        if not pdf_url:
            job.status = "error"
            job.error = "No PDF URL available"
            session.commit()
            return

        result = prepare_chat(pdf_url=pdf_url)

        job.status = "done"
        job.pdf_id = result["pdf_id"]  # store here
        job.error = None
        session.commit()

    except Exception as e:
        logger.error(f"Chat preparation failed for {chat_session_id}: {e}")
        job = session.query(ChatPrepJob).filter(ChatPrepJob.id == chat_session_id).first()
        if job:
            job.status = "error"
            job.error = str(e)
            session.commit()
    finally:
        session.close()

@router.get("/chat-job-status/{chat_session_id}")
def chat_job_status(chat_session_id: str, session: Session = Depends(get_session)):
    job = session.query(ChatPrepJob).filter(ChatPrepJob.id == chat_session_id).first()
    if not job:
        return {"status": "not_found"}

    return {
        "status": job.status,
        "pdf_id": job.pdf_id,
        "error": job.error,
    }


#May error come here so check the Valid Response is coming or not from frontend
@router.post("/init_chat")
async def init_chat(
    request: InitChatRequest,
    bg: BackgroundTasks = BackgroundTasks(),
    session:Session=Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize chat session for a paper.
    
    What changed:
    - Now uses InitChatRequest (validates vector_index)
    - Added response_model
    - Logic stays the same!
    """
    vector_index = request.vector_index

    # If a prep job already exists for this user/vector_index, reuse it.
    existing_prep = (
        session.query(ChatPrepJob)
        .filter(
            ChatPrepJob.user_id == current_user.id,
            ChatPrepJob.vector_index == vector_index,
        )
        .order_by(ChatPrepJob.created_at.desc())
        .first()
    )
    if existing_prep:
        return {"chat_session_id": existing_prep.id}
    #Saving the chatSession in ChatSession table with attirbutes id,user_id,pdf_id,created_at,upadated_at
    try:
        chat_session = ChatSession(
            user_id=current_user.id,
            pdf_id=vector_index,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(chat_session)
        session.commit()
    except Exception as e:
        logger.error(f"DB Error saving chat session: {e}")
        raise e

    chat_session_id = str(uuid.uuid4())

    prep_job = ChatPrepJob(
        id=chat_session_id,
        user_id=current_user.id,
        vector_index=vector_index,
        status="processing",
    )
    session.add(prep_job)
    session.commit()

    bg.add_task(prepare_chat_pipeline, chat_session_id, vector_index)
    return {"chat_session_id": chat_session_id}


def get_recent_messages(session: Session, chat_id: str, limit: int = 8):
    """Return the most recent chat messages as simple dicts for LLM context.

    We avoid casting chat_id to int here to stay compatible with the existing
    stored values, and we sort newest->oldest then reverse to keep chronological
    order for the LLM.
    """
    messages = (
        session.query(ChatMessages)
        .filter(ChatMessages.chat_session_id == chat_id)
        .order_by(ChatMessages.created_at.desc())
        .limit(limit)
        .all()[::-1]
    )

    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.post("/chat/{chat_id}/stream")
async def chat_message(chat_id: str, request: ChatMessageRequest,session:Session=Depends(get_session),current_user: User = Depends(get_current_user)):
    """
    Send a message in an active chat session.
    
    What changed:
    - Now uses ChatMessageRequest (validates message)
    - Replaced print() with logger.info()
    - Logic stays exactly the same!
    """
    #User Message
    
    user_message = ChatMessages(
        chat_session_id=chat_id,
        role="user",
        content=request.message,
        created_at=datetime.now()
    )
    session.add(user_message)
    session.commit()

    async def wait_for_chat_done():
        """Wait until the chat prep job status becomes 'done' using DB-backed state.

        This replaces the old in-memory CHAT_JOBS polling so that new chat
        sessions created via ChatPrepJob work correctly.
        """
        while True:
            job = (
                session.query(ChatPrepJob)
                .filter(ChatPrepJob.id == chat_id)
                .first()
            )
            if not job:
                raise HTTPException(status_code=404, detail="Chat session not found")
            if job.status == "done":
                return job
            if job.status == "error":
                raise HTTPException(status_code=500, detail=job.error or "Chat preparation failed")
            await asyncio.sleep(0.5)
 
    async def stream_answer() -> AsyncGenerator[str, None]:
        job = await wait_for_chat_done()
        pdf_id = job.pdf_id
        
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
        #making response in one string
        response_text = ""
        async for chunk in qa_chain(
            user_query=request.message,
            retrieved_docs=docs,
            chat_history=get_recent_messages(session, chat_id, limit=4)
        ):
            response_text += chunk
            yield chunk
        #Assistant Message
        assistant_message = ChatMessages(
            chat_session_id=chat_id,
            role="assistant",
            content=response_text,
            created_at=datetime.now(),
            
        )
        session.add(assistant_message)
        session.commit()
    return StreamingResponse(
        stream_answer(),
        media_type="text/stream"
    )


