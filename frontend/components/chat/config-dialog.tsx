"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface ConfigDialogProps {
  open: boolean
  onClose: () => void
  onConfigure: (backend: 'ollama' | 'huggingface', model: string, apiToken?: string) => Promise<void>
}

export function ConfigDialog({ open, onClose, onConfigure }: ConfigDialogProps) {
  const [backend, setBackend] = useState<'ollama' | 'huggingface'>('ollama')
  const [model, setModel] = useState('qwen2.5:7b')
  const [apiToken, setApiToken] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    setError('')
    setIsLoading(true)
    
    try {
      await onConfigure(backend, model, apiToken || undefined)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Configuration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Configure LLM</DialogTitle>
          <DialogDescription>
            Connect to your LLM backend to start generating lyrics
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Backend Selection */}
          <div className="space-y-2">
            <Label>Backend</Label>
            <Select value={backend} onValueChange={(v) => setBackend(v as any)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ollama">Ollama (Local)</SelectItem>
                <SelectItem value="huggingface">HuggingFace API</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <Label>Model</Label>
            {backend === 'ollama' ? (
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="qwen2.5:7b">Qwen 2.5 7B</SelectItem>
                  <SelectItem value="qwen2.5:14b">Qwen 2.5 14B</SelectItem>
                  <SelectItem value="llama3.1">Llama 3.1 8B</SelectItem>
                  <SelectItem value="mistral">Mistral 7B</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <Input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="Qwen/Qwen2.5-7B-Instruct"
              />
            )}
          </div>

          {/* API Token for HuggingFace */}
          {backend === 'huggingface' && (
            <div className="space-y-2">
              <Label>API Token</Label>
              <Input
                type="password"
                value={apiToken}
                onChange={(e) => setApiToken(e.target.value)}
                placeholder="hf_..."
              />
              <p className="text-xs text-gray-500">
                Get your token from{" "}
                <a 
                  href="https://huggingface.co/settings/tokens" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  huggingface.co/settings/tokens
                </a>
              </p>
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <Button 
            onClick={handleSubmit} 
            disabled={isLoading}
            className="w-full"
          >
            {isLoading ? 'Configuring...' : 'Configure'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
