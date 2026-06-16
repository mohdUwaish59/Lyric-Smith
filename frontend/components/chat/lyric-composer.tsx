"use client"

import { useState } from "react"
import { Send, Plus, Music } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type * as api from "@/lib/api"

interface LyricComposerProps {
  onGenerateLyrics: (request: api.GenerateRequest) => void
  onCreateSong: (title: string) => void
  isGenerating: boolean
  disabled: boolean
  currentSong: api.Song | null
}

export function LyricComposer({
  onGenerateLyrics,
  onCreateSong,
  isGenerating,
  disabled,
  currentSong
}: LyricComposerProps) {
  const [showSongForm, setShowSongForm] = useState(!currentSong)
  const [songTitle, setSongTitle] = useState('')
  
  // Lyrics form
  const [sectionName, setSectionName] = useState('verse1')
  const [rhymeScheme, setRhymeScheme] = useState('ABBA')
  const [strictness, setStrictness] = useState<'strict' | 'sung' | 'loose'>('sung')
  const [lines, setLines] = useState([
    { meaning: '', syllables: 8, rhyme_label: 'A' },
    { meaning: '', syllables: 10, rhyme_label: 'B' },
    { meaning: '', syllables: 10, rhyme_label: 'B' },
    { meaning: '', syllables: 8, rhyme_label: 'A' },
  ])

  const handleCreateSong = () => {
    if (songTitle.trim()) {
      onCreateSong(songTitle.trim())
      setSongTitle('')
      setShowSongForm(false)
    }
  }

  const handleGenerate = () => {
    if (!currentSong) return

    const validLines = lines.filter(l => l.meaning.trim())
    if (validLines.length === 0) return

    onGenerateLyrics({
      song_id: currentSong.song_id,
      section_name: sectionName,
      lines: validLines,
      rhyme_scheme: rhymeScheme,
      strictness
    })
  }

  const updateLine = (index: number, field: keyof typeof lines[0], value: any) => {
    setLines(prev => prev.map((line, i) => 
      i === index ? { ...line, [field]: value } : line
    ))
  }

  if (showSongForm || !currentSong) {
    return (
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-white/90 backdrop-blur border-t">
        <div className="max-w-2xl mx-auto space-y-3">
          <Label>Song Title</Label>
          <div className="flex gap-2">
            <Input
              value={songTitle}
              onChange={(e) => setSongTitle(e.target.value)}
              placeholder="Enter song title..."
              onKeyDown={(e) => e.key === 'Enter' && handleCreateSong()}
            />
            <Button onClick={handleCreateSong} disabled={!songTitle.trim()}>
              <Plus className="w-4 h-4 mr-2" />
              Create
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="absolute bottom-0 left-0 right-0 p-4 bg-white/90 backdrop-blur border-t">
      <div className="max-w-4xl mx-auto space-y-4">
        {/* Section & Settings */}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label className="text-xs">Section</Label>
            <Input
              value={sectionName}
              onChange={(e) => setSectionName(e.target.value)}
              placeholder="verse1"
              className="h-9"
            />
          </div>
          <div>
            <Label className="text-xs">Rhyme Scheme</Label>
            <Input
              value={rhymeScheme}
              onChange={(e) => setRhymeScheme(e.target.value)}
              placeholder="ABBA"
              className="h-9"
            />
          </div>
          <div>
            <Label className="text-xs">Strictness</Label>
            <Select value={strictness} onValueChange={(v: any) => setStrictness(v)}>
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="strict">Strict</SelectItem>
                <SelectItem value="sung">Sung (Recommended)</SelectItem>
                <SelectItem value="loose">Loose</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Lines */}
        <div className="space-y-2">
          {lines.map((line, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="text-sm font-medium text-gray-500 mt-2 w-6">{i + 1}</span>
              <Textarea
                value={line.meaning}
                onChange={(e) => updateLine(i, 'meaning', e.target.value)}
                placeholder={`Line ${i + 1} meaning...`}
                className="flex-1 min-h-[40px] h-10 resize-none"
              />
              <Input
                type="number"
                value={line.syllables}
                onChange={(e) => updateLine(i, 'syllables', parseInt(e.target.value) || 8)}
                className="w-16 h-10"
                min={1}
                max={20}
              />
              <span className="text-sm text-gray-500 mt-2">{rhymeScheme[i] || '.'}</span>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            onClick={() => setLines([...lines, { meaning: '', syllables: 8, rhyme_label: 'A' }])}
            variant="outline"
            size="sm"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Line
          </Button>
          <Button
            onClick={() => setShowSongForm(true)}
            variant="outline"
            size="sm"
          >
            <Music className="w-4 h-4 mr-1" />
            New Song
          </Button>
          <div className="flex-1" />
          <Button
            onClick={handleGenerate}
            disabled={disabled || isGenerating || lines.every(l => !l.meaning.trim())}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {isGenerating ? (
              <>Generating...</>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Generate Lyrics
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
