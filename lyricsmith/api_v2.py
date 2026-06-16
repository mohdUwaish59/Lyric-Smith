#!/usr/bin/env python3
"""
api_v2.py - FastAPI backend for LyricSmith with Database Support

REST API with PostgreSQL persistence for sessions, messages, and songs.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from lyricsmith import LineSpec, Strictness, generate_section
from lyricsmith.llm import OllamaClient, HuggingFaceClient
from database import get_db, engine
from models import Session as DBSession, Message as DBMessage, Song as DBSong, generate_session_name, Base

# Initialize database
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="LyricSmith API v2",
    description="AI-powered songwriting assistant with database persistence",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state (LLM clients per session)
llm_clients = {}  # session_id -> LLMClient
generation_jobs = {}  # job_id -> job_data


# ============================================================================
# Request/Response Models
# ============================================================================

class StrictnessLevel(str, Enum):
    strict = "strict"
    sung = "sung"
    loose = "loose"

class LLMBackend(str, Enum):
    ollama = "ollama"
    huggingface = "huggingface"

class ConfigRequest(BaseModel):
    session_id: str
    backend: LLMBackend
    model: str
    api_token: Optional[str] = None

class LineRequest(BaseModel):
    meaning: str
    syllables: int
    stress: Optional[str] = None
    rhyme_label: str = "."

class GenerateRequest(BaseModel):
    session_id: str
    song_id: str
    section_name: str
    lines: List[LineRequest]
    rhyme_scheme: str
    strictness: StrictnessLevel = StrictnessLevel.sung

class SongCreateRequest(BaseModel):
    session_id: str
    title: str

class MessageCreateRequest(BaseModel):
    session_id: str
    role: str
    content: str
    lyrics: Optional[List[Optional[str]]] = None
    results: Optional[List[Dict]] = None
    generation_request: Optional[Dict] = None

class LineResult(BaseModel):
    line: Optional[str]
    status: str
    attempts: int
    problems: Optional[List[str]] = None

class GenerateResponse(BaseModel):
    job_id: str
    status: str
    lines: Optional[List[Optional[str]]] = None
    results: Optional[List[LineResult]] = None
    error: Optional[str] = None


# ============================================================================
# Session Endpoints
# ============================================================================

@app.get("/")
def root():
    """API health check."""
    return {
        "service": "LyricSmith API v2",
        "status": "running",
        "version": "2.0.0",
        "database": "connected"
    }

@app.post("/sessions")
def create_session(db: Session = Depends(get_db)):
    """Create a new chat session with random name."""
    session_id = str(uuid.uuid4())
    session = DBSession(
        id=session_id,
        name=generate_session_name(),
        created_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session.to_dict()

@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    """List all chat sessions."""
    sessions = db.query(DBSession).order_by(DBSession.updated_at.desc()).all()
    return {
        "sessions": [s.to_dict() for s in sessions]
    }

@app.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get a session with all its messages."""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    result = session.to_dict()
    result["messages"] = [m.to_dict() for m in session.messages]
    return result

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session and all its data."""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Clean up in-memory data
    llm_clients.pop(session_id, None)
    
    db.delete(session)
    db.commit()
    
    return {"status": "deleted"}


# ============================================================================
# Message Endpoints
# ============================================================================

@app.post("/messages")
def create_message(request: MessageCreateRequest, db: Session = Depends(get_db)):
    """Add a message to a session."""
    session = db.query(DBSession).filter(DBSession.id == request.session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    message = DBMessage(
        id=str(uuid.uuid4()),
        session_id=request.session_id,
        role=request.role,
        content=request.content,
        lyrics=request.lyrics,
        results=request.results,
        generation_request=request.generation_request,
        created_at=datetime.utcnow()
    )
    
    db.add(message)
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    
    return message.to_dict()


# ============================================================================
# LLM Configuration
# ============================================================================

@app.post("/config")
def configure_llm(config: ConfigRequest, db: Session = Depends(get_db)):
    """Configure LLM for a session."""
    session = db.query(DBSession).filter(DBSession.id == config.session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    try:
        if config.backend == LLMBackend.ollama:
            llm_clients[config.session_id] = OllamaClient(model=config.model)
        elif config.backend == LLMBackend.huggingface:
            if not config.api_token:
                raise HTTPException(400, "api_token required for HuggingFace")
            llm_clients[config.session_id] = HuggingFaceClient(
                model=config.model,
                api_token=config.api_token
            )
        
        # Update session
        session.llm_backend = config.backend.value
        session.llm_model = config.model
        session.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "backend": config.backend.value,
            "model": config.model
        }
    
    except Exception as e:
        raise HTTPException(500, f"LLM configuration failed: {str(e)}")


# ============================================================================
# Song Endpoints
# ============================================================================

@app.post("/songs")
def create_song(request: SongCreateRequest, db: Session = Depends(get_db)):
    """Create a new song."""
    session = db.query(DBSession).filter(DBSession.id == request.session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    song_id = str(uuid.uuid4())
    song = DBSong(
        id=song_id,
        session_id=request.session_id,
        title=request.title,
        created_at=datetime.utcnow(),
        sections={}
    )
    
    db.add(song)
    session.current_song_id = song_id
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(song)
    
    return song.to_dict()

@app.get("/songs/{song_id}")
def get_song(song_id: str, db: Session = Depends(get_db)):
    """Get a song by ID."""
    song = db.query(DBSong).filter(DBSong.id == song_id).first()
    if not song:
        raise HTTPException(404, "Song not found")
    
    return song.to_dict()


# ============================================================================
# Generation Endpoints
# ============================================================================

@app.post("/generate", response_model=GenerateResponse)
async def generate_lyrics(request: GenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Generate validated lyrics (async background task)."""
    
    # Check session
    session = db.query(DBSession).filter(DBSession.id == request.session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Check LLM
    if request.session_id not in llm_clients:
        raise HTTPException(400, "LLM not configured. Call /config first")
    
    # Check song
    song = db.query(DBSong).filter(DBSong.id == request.song_id).first()
    if not song:
        raise HTTPException(404, "Song not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    generation_jobs[job_id] = {
        "status": "processing",
        "created": datetime.utcnow().isoformat(),
        "lines": None,
        "results": None,
        "error": None,
        "session_id": request.session_id,
        "song_id": request.song_id,
        "section_name": request.section_name
    }
    
    # Start generation in background
    background_tasks.add_task(
        _generate_lyrics_task,
        job_id,
        request,
        request.session_id
    )
    
    return GenerateResponse(
        job_id=job_id,
        status="processing",
        lines=None,
        results=None
    )

@app.get("/jobs/{job_id}", response_model=GenerateResponse)
def get_job_status(job_id: str):
    """Check status of a generation job."""
    if job_id not in generation_jobs:
        raise HTTPException(404, "Job not found")
    
    job = generation_jobs[job_id]
    return GenerateResponse(
        job_id=job_id,
        status=job["status"],
        lines=job.get("lines"),
        results=job.get("results"),
        error=job.get("error")
    )


# ============================================================================
# Background Tasks
# ============================================================================

def _generate_lyrics_task(job_id: str, request: GenerateRequest, session_id: str):
    """Background task for lyrics generation."""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        llm_client = llm_clients.get(session_id)
        if not llm_client:
            raise Exception("LLM client not found")
        
        # Build slots
        slots = []
        for i, line_req in enumerate(request.lines):
            stress = line_req.stress
            if not stress:
                stress = "01" * (line_req.syllables // 2)
                if line_req.syllables % 2:
                    stress += "0"
            
            slots.append({
                "meaning": line_req.meaning,
                "spec": LineSpec(line_req.syllables, stress),
                "rhyme_label": request.rhyme_scheme[i] if i < len(request.rhyme_scheme) else "."
            })
        
        # Generate
        lines, results = generate_section(
            llm_client,
            slots,
            strictness=Strictness(request.strictness.value),
            candidates_per_round=8,
            max_rounds=6
        )
        
        # Convert results
        api_results = []
        for r in results:
            api_results.append({
                "line": r.accepted,
                "status": r.status,
                "attempts": r.attempts,
                "problems": r.best_near_miss.problems if r.best_near_miss else None
            })
        
        # Update job
        generation_jobs[job_id]["status"] = "completed"
        generation_jobs[job_id]["lines"] = lines
        generation_jobs[job_id]["results"] = api_results
        
        # Update song in database
        song = db.query(DBSong).filter(DBSong.id == request.song_id).first()
        if song and all(lines):
            if not song.sections:
                song.sections = {}
            song.sections[request.section_name] = {
                "lines": lines,
                "rhyme_scheme": request.rhyme_scheme,
                "created": datetime.utcnow().isoformat()
            }
            db.commit()
    
    except Exception as e:
        generation_jobs[job_id]["status"] = "failed"
        generation_jobs[job_id]["error"] = str(e)
    
    finally:
        db.close()


# ============================================================================
# Run with: uvicorn api_v2:app --reload
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
