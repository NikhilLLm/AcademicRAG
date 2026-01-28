"""
Response schemas for API endpoints.
These models ensure consistent response formats.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union


class PaperResult(BaseModel):
    """
    Single paper result from search.
    
    What this does:
    - Defines exact structure of paper data
    - Makes responses predictable for frontend
    - Uses your existing field names from service.py format_result()
    """
    id: str
    title: Optional[str] = None
    authors: Optional[Union[List[str], str]] = None
    abstract: Optional[str] = None
    download_url: Optional[str] = None
    num_pages: Optional[int] = None
    publication_date: Optional[str] = None
    citation_count: Optional[int] = None
    source_repository: Optional[str] = None
    document_type: Optional[str] = None
    field_of_study: Optional[str] = None
    arxiv_id: Optional[str] = None
    score:  Optional[float] = None


class SearchResponse(BaseModel):
    """
    Response for search endpoints.
    
    What this does:
    - Wraps list of papers in consistent format
    - Matches your current {"results": [...]} structure
    """
    results: List[PaperResult]


class JobStatusResponse(BaseModel):
    """
    Response for job status endpoints.
    
    What this does:
    - Standardizes job status responses
    - Matches your current JOBS dict structure
    """
    status: Literal["running", "done", "error", "not_found"]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobInitResponse(BaseModel):
    """
    Response when starting a new job.
    
    What this does:
    - Returns job_id for polling
    - Matches your current {"job_id": "..."} structure
    """
    job_id: str


class ChatSessionResponse(BaseModel):
    """
    Response when initializing chat.
    
    What this does:
    - Returns chat_session_id for subsequent messages
    - Matches your current {"chat_session_id": "..."} structure
    """
    chat_session_id: str


class ErrorResponse(BaseModel):
    """
    Standardized error response.
    
    What this does:
    - Provides consistent error format
    - Shows clear error details to frontend
    """
    detail: str
    status_code: int = Field(default=500)
