from Backend.database.db_session import get_session
from Backend.database.tables import User, Notes, SearchHistory, ChatSession, ChatMessages
from Backend.schemas.responses import UserResponse, NotesListItem, NotesDetailResponse, SearchHistoryItem,ChatSessionDetailResponse
from Backend.schemas.requests import InitChatRequest
from sqlalchemy.orm import Session
from Backend.utils.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import json

from Backend.search.service import SearchService

router = APIRouter()

# Shared search service instance to resolve titles from Qdrant when notes are missing
_search_service = SearchService()


@router.get("/user", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info"""
    return UserResponse(id=current_user.id, email=current_user.email)


@router.get("/notes", response_model=List[NotesListItem])
def get_user_notes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all saved papers for the current user"""
    notes = session.query(Notes).filter(
        Notes.user_id == current_user.id
    ).order_by(Notes.created_at.desc()).all()
    
    return [
        NotesListItem(
            id=note.id,
            pdf_id=note.pdf_id,
            title=note.title,
            created_at=note.created_at,
            updated_at=note.updated_at,
            has_content=bool(note.content)
        )
        for note in notes
    ]


@router.get("/search_history", response_model=List[SearchHistoryItem])
def get_search_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get recent search history for the current user"""
    history = session.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.created_at.desc()).limit(20).all()
    
    return history
async def get_recent_messages(session: Session, chat_id: int, limit: int = 8):
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id")
    return (
        session.query(ChatMessages)
        .filter(ChatMessages.chat_session_id == chat_id_int)
        .order_by(ChatMessages.created_at.desc())
        .limit(limit)
        .all()[::-1]
    )


@router.get("/recent_messages", response_model=List[ChatSessionDetailResponse])
def get_chat_session(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get the recent Messages"""
    chat_info = session.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    #checking why notes_info is empty array 
    notes_info = session.query(Notes).filter(
        Notes.user_id == current_user.id    
    ).order_by(Notes.created_at.desc()).all()
    print(current_user.id)
    print(notes_info)
    # Map pdf_id -> title from existing notes (preferred)
    pdf_title_map = {note.pdf_id: note.title for note in notes_info}

    # Fallback: resolve missing titles from Qdrant metadata so chats have
    # meaningful titles even if the user never generated notes.
    for chat in chat_info:
        if chat.pdf_id not in pdf_title_map:
            try:
                meta = _search_service.get_metadata_by_id(chat.pdf_id)
                if meta and meta.get("title"):
                    pdf_title_map[chat.pdf_id] = meta["title"]
            except Exception:
                # If Qdrant/metadata lookup fails, we silently keep "Untitled"
                continue

    # Build chat response
    chats = [
        ChatSessionDetailResponse(
            id=chat.id,
            pdf_id=chat.pdf_id,
            title=pdf_title_map.get(chat.pdf_id, "Untitled"),
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        for chat in chat_info
    ]

    return chats


   
