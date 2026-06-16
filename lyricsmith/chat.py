#!/usr/bin/env python3
"""
chat.py - Simple CLI chat interface for LyricSmith

A conversational interface for generating validated song lyrics.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from lyricsmith import LineSpec, Strictness, generate_section
from lyricsmith.llm import OllamaClient, HuggingFaceClient


class SongProject:
    """Manages a song project with sections and metadata."""
    
    def __init__(self, title="Untitled Song"):
        self.title = title
        self.created = datetime.now().isoformat()
        self.sections = {}  # {section_name: {"lines": [...], "specs": [...], "rhyme": "..."}}
        self.current_section = None
    
    def to_dict(self):
        return {
            "title": self.title,
            "created": self.created,
            "sections": self.sections,
            "current_section": self.current_section
        }
    
    @classmethod
    def from_dict(cls, data):
        project = cls(data["title"])
        project.created = data["created"]
        project.sections = data["sections"]
        project.current_section = data.get("current_section")
        return project
    
    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as f:
            return cls.from_dict(json.load(f))


class LyricSmithChat:
    """Simple CLI chat interface."""
    
    def __init__(self):
        self.project = None
        self.llm = None
        self.strictness = Strictness.SUNG
        self.projects_dir = Path("songs")
        self.projects_dir.mkdir(exist_ok=True)
        
    def print_header(self):
        print("\n" + "="*70)
        print("🎵 LyricSmith - AI Songwriting Assistant")
        print("="*70)
        print("A conversational tool that generates lyrics with validated")
        print("syllable counts, stress patterns, and rhyme schemes.\n")
        
    def print_help(self):
        print("\n📋 Available Commands:")
        print("  new <song title>          - Start a new song project")
        print("  load <filename>           - Load existing song")
        print("  save                      - Save current song")
        print("  list                      - List all saved songs")
        print("  write <section>           - Generate lyrics for a section")
        print("  show                      - Show current song")
        print("  settings                  - Show/change settings")
        print("  help                      - Show this help")
        print("  quit/exit                 - Exit the program")
        print()
        
    def setup_llm(self):
        """Initialize LLM connection."""
        print("\n🔧 Setting up LLM connection...")
        print("\nChoose backend:")
        print("  1. Ollama (local, free, private)")
        print("  2. HuggingFace API (cloud, free tier, requires token)")
        
        choice = input("\nBackend [1/2]: ").strip() or "1"
        
        if choice == "2":
            self._setup_huggingface()
        else:
            self._setup_ollama()
    
    def _setup_ollama(self):
        """Setup Ollama backend."""
        print("\n📦 Using Ollama (local)...")
        print("Connecting to http://localhost:11434...")
        
        model = input("Model name [llama3.1]: ").strip() or "llama3.1"
        
        try:
            self.llm = OllamaClient(model=model)
            print(f"✅ Connected to Ollama with model: {model}\n")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            print("Make sure 'ollama serve' is running and the model is pulled.")
            sys.exit(1)
    
    def _setup_huggingface(self):
        """Setup HuggingFace API backend."""
        print("\n🤗 Using HuggingFace Inference API...")
        print("\nPopular free models:")
        print("  1. Qwen/Qwen2.5-7B-Instruct (recommended)")
        print("  2. meta-llama/Llama-3.1-8B-Instruct")
        print("  3. mistralai/Mistral-7B-Instruct-v0.3")
        print("  4. Custom model")
        
        model_choice = input("\nModel [1/2/3/4]: ").strip() or "1"
        
        models = {
            "1": "Qwen/Qwen2.5-7B-Instruct",
            "2": "meta-llama/Llama-3.1-8B-Instruct",
            "3": "mistralai/Mistral-7B-Instruct-v0.3",
        }
        
        if model_choice == "4":
            model = input("Enter model name (e.g., org/model-name): ").strip()
        else:
            model = models.get(model_choice, models["1"])
        
        print(f"\n🔑 Get your FREE API token from:")
        print("   https://huggingface.co/settings/tokens")
        print("   (Click 'New token' → Type: Read)")
        
        api_token = input("\nAPI token: ").strip()
        
        if not api_token or not api_token.startswith("hf_"):
            print("❌ Invalid token. Token should start with 'hf_'")
            sys.exit(1)
        
        try:
            self.llm = HuggingFaceClient(model=model, api_token=api_token)
            print(f"✅ Connected to HuggingFace with model: {model}")
            print("⚠️  Note: First request may be slow (model loading)\n")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            sys.exit(1)
    
    def cmd_new(self, args):
        """Create a new song project."""
        title = " ".join(args) if args else "Untitled Song"
        self.project = SongProject(title)
        print(f"\n✨ Created new song: '{title}'")
        print("Use 'write <section>' to start generating lyrics.")
        
    def cmd_save(self, args):
        """Save current project."""
        if not self.project:
            print("❌ No active project. Use 'new' to create one.")
            return
        
        filename = self.projects_dir / f"{self.project.title.lower().replace(' ', '_')}.json"
        self.project.save(filename)
        print(f"💾 Saved to: {filename}")
        
    def cmd_load(self, args):
        """Load a project."""
        if not args:
            print("❌ Usage: load <filename>")
            return
        
        filename = self.projects_dir / args[0]
        if not filename.exists():
            filename = Path(args[0])  # Try absolute path
        
        if not filename.exists():
            print(f"❌ File not found: {filename}")
            return
        
        self.project = SongProject.load(filename)
        print(f"📂 Loaded: '{self.project.title}'")
        self.cmd_show([])
        
    def cmd_list(self, args):
        """List saved songs."""
        songs = list(self.projects_dir.glob("*.json"))
        if not songs:
            print("📁 No saved songs yet.")
            return
        
        print("\n📁 Saved Songs:")
        for song in songs:
            print(f"  - {song.stem}")
        print()
        
    def cmd_show(self, args):
        """Show current song."""
        if not self.project:
            print("❌ No active project.")
            return
        
        print(f"\n🎵 Song: {self.project.title}")
        print(f"📅 Created: {self.project.created}")
        
        if not self.project.sections:
            print("   (No sections written yet)")
        else:
            for section_name, section_data in self.project.sections.items():
                print(f"\n  [{section_name.upper()}]")
                for i, line in enumerate(section_data["lines"], 1):
                    print(f"    {i}. {line}")
        print()
        
    def cmd_write(self, args):
        """Generate lyrics for a section."""
        if not self.project:
            print("❌ No active project. Use 'new' to create one.")
            return
        
        if not args:
            print("❌ Usage: write <section> (e.g., 'write verse1')")
            return
        
        section_name = args[0]
        print(f"\n✍️  Writing section: {section_name}")
        print("="*70)
        
        # Get section structure from user
        meaning = self.get_section_meaning()
        specs = self.get_section_specs()
        rhyme_scheme = self.get_rhyme_scheme(len(specs))
        
        # Build slots
        slots = []
        for i, (spec, rhyme_label) in enumerate(zip(specs, rhyme_scheme)):
            slots.append({
                "meaning": meaning[i] if i < len(meaning) else f"line {i+1}",
                "spec": spec,
                "rhyme_label": rhyme_label
            })
        
        # Generate
        print(f"\n🤖 Generating with {self.strictness.value} strictness...")
        print("This may take a minute...\n")
        
        lines, results = generate_section(
            self.llm, 
            slots, 
            strictness=self.strictness,
            candidates_per_round=8,
            max_rounds=6
        )
        
        # Show results
        print("\n📝 Results:")
        print("="*70)
        for i, (line, result) in enumerate(zip(lines, results), 1):
            status_icon = "✅" if result.status == "PASS" else "❌"
            print(f"{status_icon} Line {i} [{result.status}] ({result.attempts} attempts)")
            if line:
                print(f"   {line}")
            else:
                print(f"   ❌ Could not generate valid line")
                if result.best_near_miss:
                    print(f"   Closest: {result.best_near_miss.line}")
                    print(f"   Issues: {result.best_near_miss.problems}")
            print()
        
        # Ask to save
        if any(lines):
            save = input("💾 Save these lines to the song? (y/n): ").strip().lower()
            if save == 'y':
                self.project.sections[section_name] = {
                    "lines": lines,
                    "rhyme_scheme": rhyme_scheme,
                    "meaning": meaning
                }
                print(f"✅ Section '{section_name}' saved!")
                
                auto_save = input("Save project to file? (y/n): ").strip().lower()
                if auto_save == 'y':
                    self.cmd_save([])
    
    def get_section_meaning(self):
        """Get line meanings from user."""
        print("\n📖 Describe what each line should express:")
        print("   (Press Enter with empty line when done)")
        meanings = []
        i = 1
        while True:
            meaning = input(f"  Line {i}: ").strip()
            if not meaning:
                break
            meanings.append(meaning)
            i += 1
        return meanings
    
    def get_section_specs(self):
        """Get syllable counts and stress patterns."""
        print("\n📏 Define syllable counts and stress patterns:")
        print("   Example: '8 01010101' or just '8' (uses iambic)")
        print("   (Press Enter with empty line when done)")
        
        specs = []
        i = 1
        while True:
            spec_input = input(f"  Line {i} [syllables stress]: ").strip()
            if not spec_input:
                break
            
            parts = spec_input.split()
            syllables = int(parts[0])
            
            if len(parts) > 1:
                stress = parts[1]
            else:
                # Default: iambic (alternating 01)
                stress = "01" * (syllables // 2) + ("0" if syllables % 2 else "")
            
            specs.append(LineSpec(syllables, stress))
            i += 1
        
        return specs
    
    def get_rhyme_scheme(self, num_lines):
        """Get rhyme scheme from user."""
        print(f"\n🎭 Rhyme scheme for {num_lines} lines:")
        print("   Examples: ABBA, AABB, ABCB, AAAA, or '----' for no rhyme")
        
        while True:
            scheme = input("  Rhyme scheme: ").strip().upper()
            if len(scheme) == num_lines or not scheme:
                return scheme or "-" * num_lines
            print(f"   ⚠️  Need exactly {num_lines} letters")
    
    def cmd_settings(self, args):
        """Show/change settings."""
        print("\n⚙️  Current Settings:")
        print(f"  Strictness: {self.strictness.value}")
        print(f"  LLM Model: {self.llm.model if self.llm else 'Not set'}")
        print()
        
        change = input("Change strictness? (strict/sung/loose/n): ").strip().lower()
        if change in ["strict", "sung", "loose"]:
            self.strictness = Strictness(change)
            print(f"✅ Strictness set to: {change}")
        
    def run(self):
        """Main chat loop."""
        self.print_header()
        self.setup_llm()
        self.print_help()
        
        print("💡 Tip: Start with 'new My Song Title'\n")
        
        while True:
            try:
                user_input = input("🎵 > ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd in ["quit", "exit"]:
                    print("\n👋 Goodbye!")
                    break
                elif cmd == "help":
                    self.print_help()
                elif cmd == "new":
                    self.cmd_new(args)
                elif cmd == "save":
                    self.cmd_save(args)
                elif cmd == "load":
                    self.cmd_load(args)
                elif cmd == "list":
                    self.cmd_list(args)
                elif cmd == "show":
                    self.cmd_show(args)
                elif cmd == "write":
                    self.cmd_write(args)
                elif cmd == "settings":
                    self.cmd_settings(args)
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("   Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    chat = LyricSmithChat()
    chat.run()
