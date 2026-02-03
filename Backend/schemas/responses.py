"""
Response schemas for API endpoints.
These models ensure consistent response formats.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime



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
    results: List[dict]


class JobStatusResponse(BaseModel):
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


class JobInitResponse(BaseModel):
    job_id: str



class ErrorResponse(BaseModel):
    """
    Standardized error response.
    
    What this does:
    - Provides consistent error format
    - Shows clear error details to frontend
    """
    detail: str
    status_code: int = Field(default=500)

class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: Literal["bearer"]

class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: Literal["bearer"]


class NotesListItem(BaseModel):
    """Response for listing user's notes (without full content)"""
    id: int
    pdf_id: str
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    has_content: bool  # Whether notes have been generated

    class Config:
        from_attributes = True


class NotesDetailResponse(BaseModel):
    """Response for full notes detail"""
    id: int
    pdf_id: str
    title: str
    content: Optional[str]
    visuals: Optional[str]  # JSON string   
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== CHAT RESPONSES ====================
class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchHistoryItem(BaseModel):
    id: int
    query: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    pdf_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ChatSessionDetailResponse(BaseModel):
    id: int
    pdf_id:str
    title: str
    created_at: datetime
    updated_at: datetime