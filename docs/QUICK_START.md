# LyricSmith Quick Start Guide

## 🚀 Getting Started

### Backend Setup

1. **Install Python Dependencies**
   ```bash
   cd lyricsmith
   pip install -r requirements-api.txt
   ```

2. **Initialize Database**
   ```bash
   python init_db.py
   ```
   This creates a SQLite database (`lyricsmith.db`) by default.

3. **Start the API Server**
   ```bash
   uvicorn api_v2:app --reload
   ```
   The API will run at `http://localhost:8000`

4. **Start Ollama** (in separate terminal)
   ```bash
   ollama serve
   ```

5. **Pull the Model** (if not already downloaded)
   ```bash
   ollama pull qwen2.5:7b
   ```

### Frontend Setup

1. **Install Node Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```
   The frontend will run at `http://localhost:3000`

---

## 📱 Using the Application

### First Time Setup

1. **Open the App** - Navigate to `http://localhost:3000`
2. **New Session Created** - A session with random name is automatically created
3. **Configure LLM** - Settings dialog opens automatically
   - Select Backend: Ollama
   - Enter Model: qwen2.5:7b
   - Click Configure

### Creating Lyrics

1. **Create a Song**
   - Enter a song title
   - Click "Create Song"

2. **Generate Lyrics**
   - Fill in the lyric composer form:
     - Section name (e.g., "verse1")
     - Number of lines
     - Rhyme scheme (e.g., "AABB")
     - Meanings for each line
     - Syllable counts
   - Click "Generate"
   - Wait 2-4 minutes for generation

3. **View Results**
   - See generated lines with success/fail status
   - View attempt counts
   - Export as JSON if needed

### Session Management

- **Sidebar** - Click menu icon (☰) to show/hide
- **New Chat** - Start a fresh session
- **Switch Sessions** - Click any session in sidebar
- **Delete Session** - Hover and click trash icon

### Export Feature

- Click **Export** button on any generated lyrics
- Downloads JSON file with:
  - Input parameters (meanings, syllables, etc.)
  - Output results (lines, attempts, status)
  - Metadata (timestamps, IDs)

---

## 🗄️ Database Options

### SQLite (Default - No Setup Required)
- File: `lyricsmith/lyricsmith.db`
- Perfect for development and single-user
- No additional configuration needed

### PostgreSQL (Production)

1. **Install PostgreSQL**
   - Windows: https://www.postgresql.org/download/
   - Mac: `brew install postgresql`
   - Linux: `sudo apt install postgresql`

2. **Create Database**
   ```sql
   CREATE DATABASE lyricsmith;
   ```

3. **Set Environment Variable**
   ```bash
   export DATABASE_URL=postgresql://username:password@localhost:5432/lyricsmith
   ```
   Or create `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/lyricsmith
   ```

4. **Initialize**
   ```bash
   python init_db.py
   ```

---

## 🔧 Troubleshooting

### "API server not connected"
- Check if API is running: `uvicorn api_v2:app --reload`
- Verify port: `http://localhost:8000`

### "Ollama server not running"
- Start Ollama: `ollama serve`
- Check if model is available: `ollama list`

### "Failed to create session"
- Check database initialization: `python init_db.py`
- Verify DATABASE_URL in environment

### Session not loading
- Check browser console for errors
- Clear localStorage: `localStorage.clear()`
- Create new session

### Generation fails immediately
- Verify LLM is configured for the session
- Check that Ollama is running
- Ensure model is pulled

---

## 📊 Features

### ✅ Completed Features
- Session-based chat with persistence
- Random session names ("Melodic Verse", "Cosmic Anthem")
- Sidebar with session list
- Full database persistence (SQLite/PostgreSQL)
- Export generation results as JSON
- Error handling with helpful messages
- Real-time connection status monitoring

### 🎯 Key Features
- **Validated Lyrics Generation** - Syllable count, stress patterns, rhyme matching
- **Multiple Strictness Levels** - strict, sung, loose
- **Session Management** - Create, switch, delete sessions
- **Message History** - All conversations persisted
- **Export to JSON** - Complete input/output data
- **Auto-generated Names** - Random creative session names

---

## 📝 Example Workflow

1. **Start Services**
   ```bash
   # Terminal 1: Backend
   cd lyricsmith
   python init_db.py
   uvicorn api_v2:app --reload

   # Terminal 2: Ollama
   ollama serve

   # Terminal 3: Frontend
   cd frontend
   npm run dev
   ```

2. **Open App** - `http://localhost:3000`

3. **Configure** - Select Ollama + qwen2.5:7b

4. **Create Song** - "My First Song"

5. **Generate** - 4 lines with AABB rhyme scheme

6. **Export** - Download results as JSON

7. **New Session** - Start fresh or switch between sessions

---

## 🆘 Need Help?

- **API Docs**: http://localhost:8000/docs
- **Database Setup**: See `DATABASE_SETUP.md`
- **Export Format**: See `EXPORT_FEATURE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`

---

## 🎉 That's It!

You now have a fully functional AI-powered lyric generation system with:
- ✅ Session management
- ✅ Database persistence  
- ✅ Export functionality
- ✅ Beautiful UI with sidebar
- ✅ Error handling
- ✅ Real-time status monitoring

Happy songwriting! 🎵
