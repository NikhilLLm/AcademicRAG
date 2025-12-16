"""Route handlers for search endpoints."""
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from backend.ingestion.extraction import extract_metadata, extract_text_from_image, enhance_text_query
from backend.embedding.embedd import embed_string
from backend.search.service import SearchService
from backend.notes.text.chunks_embeddings import TextPreprocessor
from backend.notes.text.extractor import PDFTextExtractor
from backend.notes.Visual.image_table_extractor import ImageTableExtractor
from backend.notes.Visual.visual_summary import save_notes
from backend.notes.text.summarizer import summarize
router = APIRouter()
search_service = SearchService()


@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """Search similar papers by uploading an image."""
    # Extract text from image
    contents = await file.read()
    text = extract_text_from_image(contents)
    
    # Embed and search
    query_vector = embed_string(text)
    results = search_service.search(query_vector, limit=5)
    
    # return {"similar_pdfs": results[:5]}
    return len(results)


@router.post("/search_text")
async def search_text(query: str = Form(...)):
    """Search similar papers by text query."""
    # Enhance query and extract author if present
    enhanced = enhance_text_query(query)
    query_vector = embed_string(enhanced["enhanced_text"])
    author = enhanced.get("author")
    
    # Search with optional author filter
    results = search_service.search(query_vector, limit=3, author_filter=author)
    
    # return {"similar_pdfs": results[:20]}
    return len(results)


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Search similar papers by uploading a PDF."""
    # Extract metadata from PDF
    contents = await file.read()
    metadata = extract_metadata(contents)
    
    # Build text from title + abstract and search
    text = f"{metadata.get('title', '')}. {metadata.get('abstract', '')}".strip()
    query_vector = embed_string(text)
    results = search_service.search(query_vector, limit=5)
    
    # return {"similar_pdfs": results[:5]}
    return len(results)


@router.post("/get_short_notes")
#so here when user click on the any of the output paper it's vector index is used for creating short notes

async def get_short_notes(vector_index: str = Form(...),collection_name: str = Form(...)):
    """Generate short notes for a selected paper by its vector index."""
    #getting metadata and full text pdf from vector index
    metadata=search_service.get_metadata_by_id(vector_index,collection_name)
    if not metadata:
        return {"error": "Paper not found"}
    
    # Get PDF URL
    pdf_url = metadata.get('download_url', '')
    if not pdf_url:
        return {"error": "No PDF URL available"}
    
    # Generate notes passing pdf_url to raw text
    raw_text_processor = TextPreprocessor(pdf_url)#this will call instance of pdfclass not full text
    raw_text_processor = raw_text_processor.get_retriever()
    notes = summarize(pdf_url=pdf_url)
    
   
    # return {"short_notes": notes, "metadata": metadata}
    return {"extracted_text": notes, "metadata": metadata}
    