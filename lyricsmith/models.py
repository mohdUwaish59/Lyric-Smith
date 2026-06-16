#!/usr/bin/env python3
"""
models.py - SQLAlchemy database models
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import random


# Random session name generator
ADJECTIVES = ["Melodic", "Harmonic", "Rhythmic", "Lyrical", "Sonic", "Acoustic", "Dynamic", "Vibrant", "Ethereal", "Cosmic"]
NOUNS = ["Verse", "Chorus", "Ballad", "Symphony", "Melody", "Anthem", "Rhapsody", "Sonnet", "Harmony", "Tune"]

def generate_session_name():
    """Generate a random session name like 'Melodic Verse' or 'Cosmic Anthem'"""
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"


class Session(Base):
    """Chat session model"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # LLM configuration for this session
    llm_backend = Column(String)  # "ollama" or "huggingface"
    llm_model = Column(String)
    
    # Current song ID (if any)
    current_song_id = Column(String, ForeignKey("songs.id"))
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")
    songs = relationship("Song", back_populates="session", cascade="all, delete-orphan", foreign_keys="[Song.session_id]")
    current_song = relationship("Song", foreign_keys=[current_song_id], post_update=True, uselist=False)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "llm_backend": self.llm_backend,
            "llm_model": self.llm_model,
            "current_song_id": self.current_song_id,
            "message_count": len(self.messages)
        }


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional fields for lyric generation
    lyrics = Column(JSON)  # Array of generated lines
    results = Column(JSON)  # Array of generation results
    generation_request = Column(JSON)  # Original generation request
    image_data = Column(Text)  # Base64 image data
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "lyrics": self.lyrics,
            "results": self.results,
            "generation_request": self.generation_request,
            "image_data": self.image_data
        }


class Song(Base):
    """Song model"""
    __tablename__ = "songs"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sections = Column(JSON, default=dict)  # Song sections with lyrics
    
    # Relationships
    session = relationship("Session", back_populates="songs", foreign_keys=[session_id])
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "song_id": self.id,
            "title": self.title,
            "created": self.created_at.isoformat(),
            "sections": self.sections or {}
        }
