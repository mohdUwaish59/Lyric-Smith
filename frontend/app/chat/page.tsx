import { LyricSmithShell } from "@/components/chat/lyricsmith-shell"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "LyricSmith - AI Songwriting Assistant",
  description: "Generate validated lyrics with precise syllable counts, stress patterns, and rhyme schemes",
}

export default function ChatPage() {
  return <LyricSmithShell />
}
