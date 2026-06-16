#!/usr/bin/env python3
"""
api.py - FastAPI backend for LyricSmith

REST API that wraps the lyric generation engine.
Frontend can call these endpoints to generate validated lyrics.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
import uuid
from datetime import datetime

from lyricsmith import LineSpec, Strictness, generate_section
from lyricsmith.llm import OllamaClient, HuggingFaceClient

# Initialize FastAPI app
app = FastAPI(
    title="LyricSmith API",
    description="AI-powered songwriting assistant with validated lyrics",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use database)
songs = {}
generation_jobs = {}
llm_client = None


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
    backend: LLMBackend
    model: str
    api_token: Optional[str] = None  # For HuggingFace


class LineRequest(BaseModel):
    meaning: str
    syllables: int
    stress: Optional[str] = None  # Auto-generate if not provided
    rhyme_label: str = "."


class GenerateRequest(BaseModel):
    song_id: str
    section_name: str
    lines: List[LineRequest]
    rhyme_scheme: str
    strictness: StrictnessLevel = StrictnessLevel.sung


class SongCreateRequest(BaseModel):
    title: str


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


class SongResponse(BaseModel):
    song_id: str
    title: str
    created: str
    sections: Dict


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """API health check."""
    return {
        "service": "LyricSmith API",
        "status": "running",
        "version": "1.0.0",
        "llm_configured": llm_client is not None
    }


@app.post("/config")
def configure_llm(config: ConfigRequest):
    """Configure the LLM backend (Ollama or HuggingFace)."""
    global llm_client
    
    try:
        if config.backend == LLMBackend.ollama:
            llm_client = OllamaClient(model=config.model)
            return {
                "status": "success",
                "backend": "ollama",
                "model": config.model
            }
        
        elif config.backend == LLMBackend.huggingface:
            if not config.api_token:
                raise HTTPException(400, "api_token required for HuggingFace")
            
            llm_client = HuggingFaceClient(
                model=config.model,
                api_token=config.api_token
            )
            return {
                "status": "success",
                "backend": "huggingface",
                "model": config.model
            }
    
    except Exception as e:
        raise HTTPException(500, f"LLM configuration failed: {str(e)}")


@app.post("/songs", response_model=SongResponse)
def create_song(request: SongCreateRequest):
    """Create a new song project."""
    song_id = str(uuid.uuid4())
    songs[song_id] = {
        "title": request.title,
        "created": datetime.now().isoformat(),
        "sections": {}
    }
    return SongResponse(
        song_id=song_id,
        title=request.title,
        created=songs[song_id]["created"],
        sections={}
    )


@app.get("/songs/{song_id}", response_model=SongResponse)
def get_song(song_id: str):
    """Get a song project by ID."""
    if song_id not in songs:
        raise HTTPException(404, "Song not found")
    
    song = songs[song_id]
    return SongResponse(
        song_id=song_id,
        title=song["title"],
        created=song["created"],
        sections=song["sections"]
    )


@app.get("/songs")
def list_songs():
    """List all song projects."""
    return {
        "songs": [
            {
                "song_id": sid,
                "title": song["title"],
                "created": song["created"],
                "section_count": len(song["sections"])
            }
            for sid, song in songs.items()
        ]
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_lyrics(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate validated lyrics for a section.
    
    This is async because generation can take 2-4 minutes.
    Returns a job_id immediately, client polls /jobs/{job_id} for status.
    """
    if not llm_client:
        raise HTTPException(400, "LLM not configured. Call /config first")
    
    if request.song_id not in songs:
        raise HTTPException(404, "Song not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    generation_jobs[job_id] = {
        "status": "processing",
        "created": datetime.now().isoformat(),
        "lines": None,
        "results": None,
        "error": None
    }
    
    # Start generation in background
    background_tasks.add_task(
        _generate_lyrics_task,
        job_id,
        request
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

def _generate_lyrics_task(job_id: str, request: GenerateRequest):
    """Background task for lyrics generation."""
    try:
        # Build slots from request
        slots = []
        for i, line_req in enumerate(request.lines):
            # Auto-generate stress pattern if not provided
            stress = line_req.stress
            if not stress:
                # Default: iambic (alternating 01)
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
        
        # Convert results to API format
        api_results = []
        for r in results:
            api_results.append(LineResult(
                line=r.accepted,
                status=r.status,
                attempts=r.attempts,
                problems=r.best_near_miss.problems if r.best_near_miss else None
            ))
        
        # Update job
        generation_jobs[job_id]["status"] = "completed"
        generation_jobs[job_id]["lines"] = lines
        generation_jobs[job_id]["results"] = api_results
        
        # Save to song if all successful
        if request.song_id in songs and all(lines):
            songs[request.song_id]["sections"][request.section_name] = {
                "lines": lines,
                "rhyme_scheme": request.rhyme_scheme,
                "created": datetime.now().isoformat()
            }
    
    except Exception as e:
        generation_jobs[job_id]["status"] = "failed"
        generation_jobs[job_id]["error"] = str(e)


# ============================================================================
# Run with: uvicorn api:app --reload
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
