"use client"

import { cn } from "@/lib/utils"
import type { Message } from "./lyricsmith-shell"
import { User, Download } from "lucide-react"
import { MarkdownRenderer } from "./markdown-renderer"
import Image from "next/image"
import { AnimatedOrb } from "./animated-orb"
import { Button } from "@/components/ui/button"

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

// Format time for display
function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

// Export generation data as JSON
function exportGenerationData(message: Message) {
  if (!message.lyrics || !message.results || !message.generationRequest) {
    return
  }

  const exportData = {
    metadata: {
      exportedAt: new Date().toISOString(),
      generatedAt: message.createdAt.toISOString(),
      messageId: message.id,
    },
    input: {
      sectionName: message.generationRequest.section_name,
      rhymeScheme: message.generationRequest.rhyme_scheme,
      strictness: message.generationRequest.strictness,
      lines: message.generationRequest.lines.map((line, index) => ({
        lineNumber: index + 1,
        meaning: line.meaning,
        syllables: line.syllables,
        stress: line.stress,
        rhymeLabel: line.rhyme_label,
      })),
    },
    output: {
      successCount: message.lyrics.filter(l => l !== null).length,
      totalLines: message.lyrics.length,
      lines: message.lyrics.map((line, index) => {
        const result = message.results?.[index]
        return {
          lineNumber: index + 1,
          generated: line,
          status: result?.status || 'UNKNOWN',
          attempts: result?.attempts || 0,
          problems: result?.problems || [],
        }
      }),
    },
  }

  // Create blob and download
  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `lyricsmith-generation-${message.id}-${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex max-w-[90%] md:max-w-[80%] gap-2",
        isUser
          ? "ml-auto flex-row-reverse user-message-enter"
          : "mr-auto animate-in fade-in slide-in-from-bottom-2 duration-300 items-end",
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
          isUser ? "bg-white" : "bg-emerald-600",
          !isUser && isStreaming && "sticky bottom-4 self-end transition-all duration-300",
        )}
        style={{
          boxShadow:
            "rgba(14, 63, 126, 0.04) 0px 0px 0px 1px, rgba(42, 51, 69, 0.04) 0px 1px 1px -0.5px, rgba(42, 51, 70, 0.04) 0px 3px 3px -1.5px, rgba(42, 51, 70, 0.04) 0px 6px 6px -3px, rgba(14, 63, 126, 0.04) 0px 12px 12px -6px, rgba(14, 63, 126, 0.04) 0px 24px 24px -12px",
        }}
        aria-hidden="true"
      >
        {isUser ? <User className="w-4 h-4 text-stone-800" /> : <AnimatedOrb className="w-8 h-8 shrink-0" />}
      </div>

      {/* Message content */}
      <div className={cn("flex flex-col", isUser ? "items-end" : "items-start")}>
        {/* Role label (optional, shown on larger screens) */}
        <span className="text-xs text-stone-400 mb-1 hidden sm:block mt-2">{isUser ? "You" : "Assistant"}</span>

        {/* Bubble */}
        <div
          className={cn(
            "rounded-2xl border-none overflow-hidden",
            isUser
              ? "bg-white text-stone-800 border border-stone-200 rounded-br-md"
              : "bg-transparent text-stone-800 rounded-bl-md",
          )}
          style={{
            boxShadow: isUser
              ? "rgba(14, 63, 126, 0.04) 0px 0px 0px 1px, rgba(42, 51, 69, 0.04) 0px 1px 1px -0.5px, rgba(42, 51, 70, 0.04) 0px 3px 3px -1.5px, rgba(42, 51, 70, 0.04) 0px 6px 6px -3px, rgba(14, 63, 126, 0.04) 0px 12px 12px -6px, rgba(14, 63, 126, 0.04) 0px 24px 24px -12px"
              : "none",
            willChange: isStreaming ? "height" : "auto",
            transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          <div
            className={cn(isUser ? "px-4 py-3" : "py-1")}
            style={{
              transition: "max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease",
            }}
          >
            {isUser ? (
              <div className="flex flex-col gap-2">
                {message.imageData && (
                  <div className="w-20 h-20 rounded-lg overflow-hidden border border-stone-200">
                    <Image
                      src={message.imageData || "/placeholder.svg"}
                      alt="Uploaded image"
                      width={80}
                      height={80}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
              </div>
            ) : (
              <>
                <MarkdownRenderer content={message.content || " "} isStreaming={isStreaming} />
                
                {/* Display generated lyrics */}
                {message.lyrics && message.results && (
                  <div className="mt-4 space-y-3 bg-purple-50 rounded-lg p-4 border border-purple-100">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-purple-900">Generated Lyrics:</h3>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-purple-700 bg-purple-100 px-2 py-1 rounded-full">
                          {message.lyrics.filter(l => l !== null).length}/{message.lyrics.length} lines
                        </span>
                        {message.generationRequest && (
                          <Button
                            onClick={() => exportGenerationData(message)}
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-purple-700 hover:text-purple-900 hover:bg-purple-100"
                            title="Export as JSON"
                          >
                            <Download className="w-4 h-4 mr-1" />
                            <span className="text-xs">Export</span>
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    {message.lyrics.map((line, index) => {
                      const result = message.results?.[index]
                      const isSuccess = result?.status === "PASS"
                      const isFailed = !line || line === null
                      
                      return (
                        <div 
                          key={index} 
                          className={cn(
                            "flex items-start gap-2 p-3 rounded-lg transition-all",
                            isFailed ? "bg-red-50 border border-red-100" : "bg-white border border-gray-100 shadow-sm"
                          )}
                        >
                          <span className="text-lg mt-0.5">
                            {isFailed ? "❌" : "✅"}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-baseline gap-2">
                              <span className="text-xs font-medium text-gray-500">Line {index + 1}</span>
                              {result && (
                                <span className="text-xs text-gray-400">
                                  ({result.attempts} {result.attempts === 1 ? "try" : "tries"})
                                </span>
                              )}
                            </div>
                            <p className={cn(
                              "text-sm font-medium mt-1",
                              isFailed ? "text-red-700 italic" : "text-gray-900"
                            )}>
                              {isFailed ? "Failed to generate" : `"${line}"`}
                            </p>
                            {result?.problems && result.problems.length > 0 && (
                              <p className="text-xs text-red-600 mt-1">
                                Issues: {result.problems.join(", ")}
                              </p>
                            )}
                          </div>
                        </div>
                      )
                    })}
                    
                    {/* Summary */}
                    {message.lyrics.filter(l => l === null).length > 0 && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-xs text-amber-800">
                          💡 <strong>Tip:</strong> Failed lines may need simpler meanings or different syllable counts. 
                          Try regenerating with adjusted parameters.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Timestamp */}
        <span className="text-xs text-stone-400 mt-1">{formatTime(message.createdAt)}</span>
      </div>
    </div>
  )
}
