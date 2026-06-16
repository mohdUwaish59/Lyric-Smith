"use client"

import { useState, useEffect } from "react"
import { Plus, MessageSquare, Trash2, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface Session {
  id: string
  name: string
  created_at: string
  updated_at: string
  message_count: number
}

interface SessionSidebarProps {
  currentSessionId: string | null
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
  onDeleteSession: (sessionId: string) => void
}

export function SessionSidebar({
  currentSessionId,
  onSessionSelect,
  onNewSession,
  onDeleteSession,
}: SessionSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const response = await fetch("http://localhost:8000/sessions")
      const data = await response.json()
      setSessions(data.sessions)
    } catch (error) {
      console.error("Failed to load sessions:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    if (confirm("Delete this chat session? This cannot be undone.")) {
      try {
        await fetch(`http://localhost:8000/sessions/${sessionId}`, {
          method: "DELETE",
        })
        setSessions(prev => prev.filter(s => s.id !== sessionId))
        onDeleteSession(sessionId)
      } catch (error) {
        console.error("Failed to delete session:", error)
      }
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="w-64 h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <Button
          onClick={onNewSession}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white"
          size="sm"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
            Loading...
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-400 text-sm text-center p-4">
            <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
            No chats yet
            <span className="text-xs mt-1">Click "New Chat" to start</span>
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => onSessionSelect(session.id)}
                onMouseEnter={() => setHoveredId(session.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={cn(
                  "group relative p-3 rounded-lg cursor-pointer transition-all",
                  currentSessionId === session.id
                    ? "bg-purple-50 border border-purple-200"
                    : "hover:bg-gray-50 border border-transparent"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3
                      className={cn(
                        "text-sm font-medium truncate",
                        currentSessionId === session.id
                          ? "text-purple-900"
                          : "text-gray-900"
                      )}
                    >
                      {session.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {formatDate(session.updated_at)}
                      </span>
                      {session.message_count > 0 && (
                        <span className="text-xs text-gray-400">
                          • {session.message_count} messages
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Delete button */}
                  {hoveredId === session.id && (
                    <Button
                      onClick={(e) => handleDelete(e, session.id)}
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <Calendar className="w-3.5 h-3.5" />
          <span>{sessions.length} session{sessions.length !== 1 ? 's' : ''}</span>
        </div>
      </div>
    </div>
  )
}
