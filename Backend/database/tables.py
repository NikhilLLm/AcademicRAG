from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

Base = declarative_base()

# User Table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    papers = relationship("Paper", back_populates="user", cascade="all, delete-orphan")

# Paper Table
class Paper(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    pdf_url = Column(String)
    qdrant_id = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="papers")
    notes = relationship("Notes", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="paper", cascade="all, delete-orphan")

# Notes Table
class Notes(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), unique=True)
    content = Column(Text, nullable=False)
    visuals = Column(Text, nullable=False) # JSON stored as Text

    paper = relationship("Paper", back_populates="notes")

# ChatSession Table
class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    paper = relationship("Paper", back_populates="sessions")
    messages = relationship("ChatMessages", back_populates="session", cascade="all, delete-orphan")

# Chat Messages Table
class ChatMessages(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")

