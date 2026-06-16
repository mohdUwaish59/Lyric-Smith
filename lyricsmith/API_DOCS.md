# LyricSmith API Documentation

FastAPI backend for the LyricSmith lyric generation engine.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements-api.txt
```

### 2. Start Ollama (in separate terminal)
```bash
ollama serve
```

### 3. Start API Server
```bash
uvicorn api:app --reload
```

Server runs at: **http://localhost:8000**

### 4. View Interactive Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## API Endpoints

### Health Check
```http
GET /
```

**Response:**
```json
{
  "service": "LyricSmith API",
  "status": "running",
  "version": "1.0.0",
  "llm_configured": true
}
```

---

### Configure LLM
```http
POST /config
```

**Body (Ollama):**
```json
{
  "backend": "ollama",
  "model": "llama3.1"
}
```

**Body (HuggingFace):**
```json
{
  "backend": "huggingface",
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "api_token": "hf_..."
}
```

**Response:**
```json
{
  "status": "success",
  "backend": "ollama",
  "model": "llama3.1"
}
```

---

### Create Song
```http
POST /songs
```

**Body:**
```json
{
  "title": "My Song"
}
```

**Response:**
```json
{
  "song_id": "uuid-here",
  "title": "My Song",
  "created": "2026-06-13T...",
  "sections": {}
}
```

---

### Generate Lyrics
```http
POST /generate
```

**Body:**
```json
{
  "song_id": "uuid-here",
  "section_name": "verse1",
  "lines": [
    {
      "meaning": "introduce the boy alone",
      "syllables": 8,
      "stress": "01010101",
      "rhyme_label": "A"
    },
    {
      "meaning": "describe the darkness",
      "syllables": 10,
      "rhyme_label": "B"
    }
  ],
  "rhyme_scheme": "ABBA",
  "strictness": "sung"
}
```

**Response (immediate):**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "lines": null,
  "results": null
}
```

---

### Check Job Status
```http
GET /jobs/{job_id}
```

**Response (processing):**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "lines": null,
  "results": null
}
```

**Response (completed):**
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "lines": [
    "The boy alone in his room",
    "The darkness wraps around",
    ...
  ],
  "results": [
    {
      "line": "The boy alone in his room",
      "status": "PASS",
      "attempts": 12,
      "problems": null
    },
    ...
  ]
}
```

---

### Get Song
```http
GET /songs/{song_id}
```

**Response:**
```json
{
  "song_id": "uuid-here",
  "title": "My Song",
  "created": "2026-06-13T...",
  "sections": {
    "verse1": {
      "lines": ["...", "...", "..."],
      "rhyme_scheme": "ABBA",
      "created": "2026-06-13T..."
    }
  }
}
```

---

### List Songs
```http
GET /songs
```

**Response:**
```json
{
  "songs": [
    {
      "song_id": "uuid-1",
      "title": "Song 1",
      "created": "2026-06-13T...",
      "section_count": 2
    },
    ...
  ]
}
```

---

## Frontend Integration

### React Example

```javascript
// 1. Configure LLM
const configLLM = async () => {
  const response = await fetch('http://localhost:8000/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      backend: 'ollama',
      model: 'llama3.1'
    })
  });
  return response.json();
};

// 2. Create song
const createSong = async (title) => {
  const response = await fetch('http://localhost:8000/songs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  return response.json();
};

// 3. Generate lyrics
const generateLyrics = async (songId, section) => {
  const response = await fetch('http://localhost:8000/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      song_id: songId,
      section_name: 'verse1',
      lines: [
        { meaning: 'intro', syllables: 8, rhyme_label: 'A' },
        { meaning: 'develop', syllables: 10, rhyme_label: 'B' },
        { meaning: 'develop', syllables: 10, rhyme_label: 'B' },
        { meaning: 'conclude', syllables: 8, rhyme_label: 'A' }
      ],
      rhyme_scheme: 'ABBA',
      strictness: 'sung'
    })
  });
  return response.json();
};

// 4. Poll for completion
const pollJob = async (jobId) => {
  while (true) {
    const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
    const job = await response.json();
    
    if (job.status === 'completed') {
      return job.lines;
    } else if (job.status === 'failed') {
      throw new Error(job.error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5s
  }
};

// 5. Complete flow
const generateVerse = async () => {
  await configLLM();
  const song = await createSong('My Song');
  const job = await generateLyrics(song.song_id);
  const lines = await pollJob(job.job_id);
  console.log('Generated lines:', lines);
};
```

---

## Testing

```bash
# Make sure API is running
uvicorn api:app --reload

# In another terminal, run test
python test_api.py
```

---

## Production Deployment

### With Gunicorn (production server)
```bash
pip install gunicorn
gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### With Docker
```dockerfile
FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install -r requirements-api.txt
RUN pip install -e .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Notes

- **Generation is async** - Takes 2-4 minutes per section
- **Poll /jobs/{job_id}** - Check every 5 seconds for updates
- **CORS enabled** - Frontend can call from any origin
- **In-memory storage** - For production, add database (PostgreSQL/MongoDB)
- **No auth** - Add authentication for production

---

## Next Steps

1. ✅ API is ready
2. Build frontend (React/Vue/Svelte)
3. Add database (PostgreSQL)
4. Add authentication (JWT)
5. Deploy to cloud (Heroku/AWS/Google Cloud)
