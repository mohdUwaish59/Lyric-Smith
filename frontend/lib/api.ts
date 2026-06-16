// API client for LyricSmith backend

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================================
// Types
// ============================================================================

export interface Session {
  id: string
  name: string
  created_at: string
  updated_at: string
  llm_backend?: string
  llm_model?: string
  current_song_id?: string
  message_count: number
  messages?: Message[]
}

export interface Message {
  id: string
  role: string
  content: string
  created_at: string
  lyrics?: (string | null)[]
  results?: LineResult[]
  generation_request?: GenerateRequest
  image_data?: string
}

export interface LineRequest {
  meaning: string
  syllables: number
  stress?: string
  rhyme_label: string
}

export interface GenerateRequest {
  session_id: string
  song_id: string
  section_name: string
  lines: LineRequest[]
  rhyme_scheme: string
  strictness: 'strict' | 'sung' | 'loose'
}

export interface LineResult {
  line: string | null
  status: string
  attempts: number
  problems?: string[]
}

export interface GenerateResponse {
  job_id: string
  status: string
  lines?: string[]
  results?: LineResult[]
  error?: string
}

export interface Song {
  song_id: string
  title: string
  created: string
  sections: Record<string, any>
}

// Configure LLM
export async function configureLLM(backend: 'ollama' | 'huggingface', model: string, apiToken?: string) {
  try {
    const response = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backend, model, api_token: apiToken })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      const errorMessage = errorData?.detail || `Failed to configure LLM (${response.status})`
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server. Is it running at ' + API_BASE + '?')
    }
    throw error
  }
}

// Create song
export async function createSong(title: string): Promise<Song> {
  try {
    const response = await fetch(`${API_BASE}/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      const errorMessage = errorData?.detail || `Failed to create song (${response.status})`
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server. Is it running?')
    }
    throw error
  }
}

// Get song
export async function getSong(songId: string): Promise<Song> {
  try {
    const response = await fetch(`${API_BASE}/songs/${songId}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      const errorMessage = errorData?.detail || `Failed to get song (${response.status})`
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// List songs
export async function listSongs() {
  const response = await fetch(`${API_BASE}/songs`)
  if (!response.ok) throw new Error('Failed to list songs')
  return response.json()
}

// Generate lyrics
export async function generateLyrics(request: GenerateRequest): Promise<GenerateResponse> {
  try {
    const response = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      let errorMessage = errorData?.detail || `Failed to start generation (${response.status})`
      
      // Handle common errors with helpful messages
      if (typeof errorData?.detail === 'string') {
        if (errorData.detail.includes('LLM not configured')) {
          errorMessage = 'Please configure LLM first (click Settings icon)'
        } else if (errorData.detail.includes('Song not found')) {
          errorMessage = 'Song not found. Please create a song first.'
        } else if (errorData.detail.includes('Ollama')) {
          errorMessage = errorData.detail + ' Make sure Ollama is running: ollama serve'
        }
      }
      
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server. Start it with: uvicorn api:app --reload')
    }
    throw error
  }
}

// Check job status
export async function getJobStatus(jobId: string): Promise<GenerateResponse> {
  try {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      const errorMessage = errorData?.detail || `Failed to get job status (${response.status})`
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Lost connection to API server')
    }
    throw error
  }
}

// Poll for job completion
export async function pollJobUntilComplete(jobId: string, onProgress?: (status: string) => void): Promise<GenerateResponse> {
  let retries = 0
  const maxRetries = 3
  
  while (true) {
    try {
      const job = await getJobStatus(jobId)
      onProgress?.(job.status)
      
      if (job.status === 'completed') {
        return job
      }
      
      if (job.status === 'failed') {
        const errorMsg = job.error || 'Generation failed with unknown error'
        // Parse common Ollama errors
        if (errorMsg.includes('10061') || errorMsg.includes('refused')) {
          throw new Error('Ollama server not running. Start it with: ollama serve')
        } else if (errorMsg.includes('model') && errorMsg.includes('not')) {
          throw new Error('Model not found. Pull it with: ollama pull qwen2.5:7b')
        }
        throw new Error(errorMsg)
      }
      
      retries = 0 // Reset retry counter on successful poll
      await new Promise(resolve => setTimeout(resolve, 5000)) // Poll every 5 seconds
      
    } catch (error) {
      retries++
      if (retries >= maxRetries) {
        throw new Error('Failed to check generation status after multiple attempts. ' + (error instanceof Error ? error.message : ''))
      }
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, 3000))
    }
  }
}


// ============================================================================
// Session Management (API v2)
// ============================================================================

// Create new session
export async function createSession(): Promise<Session> {
  try {
    const response = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new Error(errorData?.detail || `Failed to create session (${response.status})`)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// List all sessions
export async function listSessions(): Promise<{ sessions: Session[] }> {
  try {
    const response = await fetch(`${API_BASE}/sessions`)
    
    if (!response.ok) {
      throw new Error(`Failed to list sessions (${response.status})`)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// Get session with messages
export async function getSession(sessionId: string): Promise<Session> {
  try {
    const response = await fetch(`${API_BASE}/sessions/${sessionId}`)
    
    if (!response.ok) {
      throw new Error(`Failed to get session (${response.status})`)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// Delete session
export async function deleteSession(sessionId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`Failed to delete session (${response.status})`)
    }
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// Add message to session
export async function addMessage(
  sessionId: string,
  role: string,
  content: string,
  extras?: {
    lyrics?: (string | null)[]
    results?: LineResult[]
    generation_request?: GenerateRequest
  }
): Promise<Message> {
  try {
    const response = await fetch(`${API_BASE}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        role,
        content,
        ...extras
      })
    })
    
    if (!response.ok) {
      throw new Error(`Failed to add message (${response.status})`)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// Configure LLM for session
export async function configureLLMForSession(
  sessionId: string,
  backend: 'ollama' | 'huggingface',
  model: string,
  apiToken?: string
) {
  try {
    const response = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        backend,
        model,
        api_token: apiToken
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      const errorMessage = errorData?.detail || `Failed to configure LLM (${response.status})`
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}

// Create song in session
export async function createSongInSession(sessionId: string, title: string): Promise<Song> {
  try {
    const response = await fetch(`${API_BASE}/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, title })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new Error(errorData?.detail || `Failed to create song (${response.status})`)
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server')
    }
    throw error
  }
}
