"use client"

import { useState, useEffect, useCallback } from "react"
import { Music, Settings, Menu } from "lucide-react"
import { MessageList } from "./message-list"
import { LyricComposer } from "./lyric-composer"
import { Button } from "@/components/ui/button"
import { ConfigDialog } from "./config-dialog"
import { ConnectionStatus } from "./connection-status"
import { SessionSidebar } from "./session-sidebar"
import * as api from "@/lib/api"

export interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  createdAt: Date
  lyrics?: (string | null)[]
  results?: api.LineResult[]
  imageData?: string
  generationRequest?: api.GenerateRequest
}

const SESSION_STORAGE_KEY = "lyricsmith-current-session"

export function LyricSmithShell() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentSong, setCurrentSong] = useState<api.Song | null>(null)
  const [isConfigured, setIsConfigured] = useState(false)
  const [showConfig, setShowConfig] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const [isLoadingSession, setIsLoadingSession] = useState(false)

  // Initialize: Load or create session
  useEffect(() => {
    initializeSession()
  }, [])

  const initializeSession = async () => {
    try {
      // Try to load last session from localStorage
      const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY)
      
      if (storedSessionId) {
        // Load existing session
        await loadSession(storedSessionId)
      } else {
        // Create new session
        await createNewSession()
      }
    } catch (e) {
      console.error("Failed to initialize session:", e)
      // Fallback: create new session
      await createNewSession()
    } finally {
      setIsLoaded(true)
    }
  }

  const createNewSession = async () => {
    try {
      const session = await api.createSession()
      setCurrentSessionId(session.id)
      localStorage.setItem(SESSION_STORAGE_KEY, session.id)
      setMessages([])
      setCurrentSong(null)
      setIsConfigured(false)
      setShowConfig(true) // Show config dialog for new session
    } catch (e) {
      console.error("Failed to create session:", e)
      setError("Failed to create new session")
    }
  }

  const loadSession = async (sessionId: string) => {
    setIsLoadingSession(true)
    try {
      const session = await api.getSession(sessionId)
      setCurrentSessionId(session.id)
      localStorage.setItem(SESSION_STORAGE_KEY, session.id)
      
      // Load messages
      if (session.messages) {
        const messagesWithDates: Message[] = session.messages.map((msg: api.Message) => ({
          id: msg.id,
          role: msg.role as "user" | "assistant" | "system",
          content: msg.content,
          createdAt: new Date(msg.created_at),
          lyrics: msg.lyrics,
          results: msg.results,
          generationRequest: msg.generation_request,
          imageData: msg.image_data
        }))
        setMessages(messagesWithDates)
      } else {
        setMessages([])
      }
      
      // Load current song if exists
      if (session.current_song_id) {
        const song = await api.getSong(session.current_song_id)
        setCurrentSong(song)
      } else {
        setCurrentSong(null)
      }
      
      // Check if configured
      setIsConfigured(!!session.llm_backend && !!session.llm_model)
      
      setError(null)
    } catch (e) {
      console.error("Failed to load session:", e)
      setError("Failed to load session")
    } finally {
      setIsLoadingSession(false)
    }
  }

  const handleSessionSelect = useCallback((sessionId: string) => {
    if (sessionId !== currentSessionId) {
      loadSession(sessionId)
    }
  }, [currentSessionId])

  const handleNewSession = useCallback(() => {
    createNewSession()
  }, [])

  const handleDeleteSession = useCallback((sessionId: string) => {
    if (sessionId === currentSessionId) {
      // If deleting current session, create a new one
      createNewSession()
    }
  }, [currentSessionId])

  const handleConfigure = useCallback(async (backend: 'ollama' | 'huggingface', model: string, apiToken?: string) => {
    if (!currentSessionId) {
      setError("No session active")
      return
    }

    try {
      await api.configureLLMForSession(currentSessionId, backend, model, apiToken)
      setIsConfigured(true)
      setShowConfig(false)
      setError(null)
      
      // Add system message and save to DB
      const systemMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "system",
        content: `✅ LLM configured: ${backend} with model ${model}`,
        createdAt: new Date()
      }
      setMessages(prev => [...prev, systemMessage])
      
      // Save to database
      await api.addMessage(currentSessionId, "system", systemMessage.content)
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Configuration failed'
      setError(errorMessage)
      
      const errorMsg: Message = {
        id: `msg-${Date.now()}`,
        role: "system",
        content: `❌ Configuration failed:\n\n${errorMessage}`,
        createdAt: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
      await api.addMessage(currentSessionId, "system", errorMsg.content).catch(() => {})
    }
  }, [currentSessionId])

  const handleCreateSong = useCallback(async (title: string) => {
    if (!currentSessionId) {
      setError("No session active")
      return
    }

    try {
      setError(null)
      const song = await api.createSongInSession(currentSessionId, title)
      setCurrentSong(song)
      
      const systemMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "system",
        content: `🎵 Created song: "${title}"`,
        createdAt: new Date()
      }
      setMessages(prev => [...prev, systemMessage])
      await api.addMessage(currentSessionId, "system", systemMessage.content)
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create song'
      setError(errorMessage)
      
      const errorMsg: Message = {
        id: `msg-${Date.now()}`,
        role: "system",
        content: `❌ Failed to create song:\n\n${errorMessage}`,
        createdAt: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
      await api.addMessage(currentSessionId, "system", errorMsg.content).catch(() => {})
    }
  }, [currentSessionId])

  const handleGenerateLyrics = useCallback(
    async (request: Omit<api.GenerateRequest, 'session_id'>) => {
      if (!currentSessionId) {
        setError("No session active")
        return
      }

      if (!currentSong) {
        setError('Create a song first')
        return
      }

      setError(null)
      setIsGenerating(true)

      // User message
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "user",
        content: `Generate ${request.section_name} with ${request.lines.length} lines (${request.rhyme_scheme})`,
        createdAt: new Date()
      }

      // Processing message
      const processingMessage: Message = {
        id: `msg-${Date.now()}-processing`,
        role: "assistant",
        content: "Generating lyrics... This may take 2-4 minutes.",
        createdAt: new Date()
      }

      setMessages(prev => [...prev, userMessage, processingMessage])
      await api.addMessage(currentSessionId, "user", userMessage.content)

      try {
        // Add session_id to request
        const fullRequest: api.GenerateRequest = {
          ...request,
          session_id: currentSessionId
        }

        // Start generation
        const job = await api.generateLyrics(fullRequest)
        
        // Poll for completion
        const result = await api.pollJobUntilComplete(job.job_id, (status) => {
          setMessages(prev => 
            prev.map(msg => 
              msg.id === processingMessage.id 
                ? { ...msg, content: `Status: ${status}...` }
                : msg
            )
          )
        })

        // Update with results
        if (result.status === 'completed' && result.lines) {
          const successMessage: Message = {
            id: processingMessage.id,
            role: "assistant",
            content: "✅ Lyrics generated successfully!",
            createdAt: new Date(),
            lyrics: result.lines,
            results: result.results,
            generationRequest: fullRequest
          }
          setMessages(prev => 
            prev.map(msg => msg.id === processingMessage.id ? successMessage : msg)
          )
          
          // Save to database
          await api.addMessage(currentSessionId, "assistant", successMessage.content, {
            lyrics: result.lines,
            results: result.results,
            generation_request: fullRequest
          })
          
          // Refresh song data
          const updatedSong = await api.getSong(currentSong.song_id)
          setCurrentSong(updatedSong)
        } else {
          throw new Error(result.error || 'Generation failed')
        }
      } catch (e) {
        console.error('Generation error:', e)
        const errorMessage = e instanceof Error ? e.message : 'Generation failed'
        setError(errorMessage)
        
        const errorContent = `❌ Generation failed:\n\n${errorMessage}\n\n` +
          (errorMessage.includes('Ollama') 
            ? '💡 Make sure Ollama is running: ollama serve' 
            : errorMessage.includes('model')
            ? '💡 Pull the model: ollama pull qwen2.5:7b'
            : errorMessage.includes('API server')
            ? '💡 Start the API: uvicorn api_v2:app --reload'
            : '')
        
        setMessages(prev => 
          prev.map(msg => 
            msg.id === processingMessage.id 
              ? { ...msg, content: errorContent }
              : msg
          )
        )
        
        await api.addMessage(currentSessionId, "assistant", errorContent).catch(() => {})
      } finally {
        setIsGenerating(false)
      }
    },
    [currentSessionId, currentSong]
  )

  return (
    <div className="relative h-dvh flex bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      {/* Sidebar */}
      {showSidebar && (
        <SessionSidebar
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 relative">
        {/* Header */}
        <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between">
          <Button
            onClick={() => setShowSidebar(!showSidebar)}
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/80 hover:bg-white shadow-sm"
            aria-label="Toggle sidebar"
          >
            <Menu className="w-5 h-5 text-purple-600" />
          </Button>

          <div className="text-center">
            <h1 className="text-lg font-semibold text-gray-800">LyricSmith</h1>
            {currentSong && (
              <p className="text-sm text-gray-600">{currentSong.title}</p>
            )}
          </div>

          <Button
            onClick={() => setShowConfig(true)}
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/80 hover:bg-white shadow-sm"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5 text-purple-600" />
          </Button>
        </div>

        {isLoadingSession ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading session...</p>
            </div>
          </div>
        ) : (
          <>
            <MessageList 
              messages={messages} 
              isStreaming={isGenerating} 
              error={error} 
              onRetry={() => {}} 
              isLoaded={isLoaded} 
            />

            <LyricComposer
              onGenerateLyrics={handleGenerateLyrics as any}
              onCreateSong={handleCreateSong}
              isGenerating={isGenerating}
              disabled={!isConfigured}
              currentSong={currentSong}
            />
          </>
        )}

        <ConfigDialog
          open={showConfig || (!isConfigured && isLoaded)}
          onClose={() => setShowConfig(false)}
          onConfigure={handleConfigure}
        />

        <ConnectionStatus />
      </div>
    </div>
  )
}

