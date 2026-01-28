"""
Request schemas for API endpoints.
These models validate incoming data from the frontend.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class SearchTextRequest(BaseModel):
    """
    Request model for text-based paper search.
    
    What this does:
    - Validates that query is a string
    - Ensures query is between 3-500 characters
    - Prevents empty/too-short searches
    """
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        description="Search query for finding papers"
    )
    
    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Remove extra whitespace and validate not blank."""
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be blank')
        return v


class StartNotesRequest(BaseModel):
    """
    Request model for starting notes generation.
    
    What this does:
    - Validates vector_index is provided
    - Ensures it's a valid non-empty string (your paper ID from Qdrant)
    """
    vector_index: str = Field(
        ...,
        min_length=1,
        description="Vector index (paper ID) to generate notes for"
    )


class InitChatRequest(BaseModel):
    """
    Request model for initializing chat session.
    
    What this does:
    - Validates vector_index for chat initialization
    - Same as notes request, ensures valid paper ID
    """
    vector_index: str = Field(
        ...,
        min_length=1,
        description="Vector index (paper ID) to chat with"
    )


class ChatMessageRequest(BaseModel):
    """
    Request model for sending chat messages.
    
    What this does:
    - Validates chat message is not empty
    - Limits message length to prevent abuse
    
    Note: This already exists in Backend/chat/schema.py
    We'll consolidate it here for consistency
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question about the paper"
    )
    
    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        """Ensure message is not just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError('Message cannot be blank')
        return v
