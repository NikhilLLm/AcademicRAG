"""Route handlers for search endpoints."""
from fastapi import APIRouter, UploadFile, File, Form,HTTPException,BackgroundTasks
from typing import Optional
from Backend.ingestion.extraction import extract_text_for_search, enhance_text_query
from Backend.embedding.embedd import embed_string
from Backend.search.service import SearchService
from Backend.notes.text.chunks_embeddings import TextPreprocessor
from Backend.notes.Visual.image_table_extractor import ImageTableExtractor
from Backend.notes.text.summarizer import generate_notes_from_pdf
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


#so here when user click on the any of the output paper it's vector index is used for creating short notes

# async def get_short_notes(vector_index: str = Form(...)):
#     """Generate short notes for a selected paper by its vector index."""
#     #getting metadata and full text pdf from vector index
#     metadata=search_service.get_metadata_by_id(vector_index)
#     if not metadata:
#         return {"error": "Paper not found"}
    
#     # Get PDF URL
#     pdf_url = metadata.get('download_url', '')
#     if not pdf_url:
#         return {"error": "No PDF URL available"}
    
#     # Generate notes passing pdf_url to raw text
#     # raw_text_processor = TextPreprocessor(pdf_url)#this will call instance of pdfclass not full text
#     # raw_text_processor = raw_text_processor.get_retriever()
#     notes = generate_notes_from_pdf(pdf_url=pdf_url)
    
   
#     # return {"short_notes": notes, "metadata": metadata}
#     return 
#introduce that running process in the backend
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

