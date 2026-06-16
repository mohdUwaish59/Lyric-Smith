# Database Setup Guide

## Quick Start (SQLite - Development)

The API uses SQLite by default, no setup required:

```bash
# Install dependencies
pip install -r requirements-api.txt

# Initialize database
python init_db.py

# Run the new API
uvicorn api_v2:app --reload
```

The database file `lyricsmith.db` will be created automatically.

## PostgreSQL Setup (Production)

### 1. Install PostgreSQL
- **Windows**: Download from https://www.postgresql.org/download/windows/
- **Mac**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql`

### 2. Create Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE lyricsmith;

# Create user (optional)
CREATE USER lyricsmith_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE lyricsmith TO lyricsmith_user;

# Exit
\q
```

### 3. Configure Environment

Create `.env` file:
```
DATABASE_URL=postgresql://lyricsmith_user:your_password@localhost:5432/lyricsmith
```

Or set environment variable:
```bash
export DATABASE_URL=postgresql://lyricsmith_user:your_password@localhost:5432/lyricsmith
```

### 4. Initialize Database

```bash
python init_db.py
```

### 5. Run API

```bash
uvicorn api_v2:app --reload
```

## Database Schema

### Sessions Table
- `id`: UUID primary key
- `name`: Random generated name ("Melodic Verse", etc.)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `llm_backend`: "ollama" or "huggingface"
- `llm_model`: Model name
- `current_song_id`: Foreign key to current song

### Messages Table
- `id`: UUID primary key
- `session_id`: Foreign key to session
- `role`: "user", "assistant", or "system"
- `content`: Message text
- `created_at`: Timestamp
- `lyrics`: JSON array of generated lines
- `results`: JSON array of generation results
- `generation_request`: JSON of input parameters
- `image_data`: Base64 encoded image (optional)

### Songs Table
- `id`: UUID primary key
- `session_id`: Foreign key to session
- `title`: Song title
- `created_at`: Timestamp
- `sections`: JSON object with song sections

## API Changes (v1 → v2)

### New Endpoints
- `POST /sessions` - Create new session
- `GET /sessions` - List all sessions
- `GET /sessions/{id}` - Get session with messages
- `DELETE /sessions/{id}` - Delete session
- `POST /messages` - Add message to session

### Updated Endpoints
All existing endpoints now require `session_id` in request body:
- `POST /config` - Add `session_id`
- `POST /songs` - Add `session_id`
- `POST /generate` - Add `session_id`

### Migration Path
1. Keep `api.py` for backward compatibility
2. Update frontend to use `api_v2.py`
3. Run both APIs on different ports during transition
4. Deprecate `api.py` after migration

## Testing

```bash
# Test database connection
python -c "from database import engine; print('✅ Database connected:', engine.url)"

# Test session creation
curl -X POST http://localhost:8000/sessions

# List sessions
curl http://localhost:8000/sessions
```

## Troubleshooting

### "no such table" error
Run: `python init_db.py`

### PostgreSQL connection refused
- Check if PostgreSQL is running: `pg_ctl status`
- Start PostgreSQL: `pg_ctl start`

### Permission denied
Check DATABASE_URL username/password and database permissions.

## Backup & Restore

### SQLite
```bash
# Backup
cp lyricsmith.db lyricsmith.db.backup

# Restore
cp lyricsmith.db.backup lyricsmith.db
```

### PostgreSQL
```bash
# Backup
pg_dump lyricsmith > backup.sql

# Restore
psql lyricsmith < backup.sql
```
