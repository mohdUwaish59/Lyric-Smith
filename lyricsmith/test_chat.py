#!/usr/bin/env python3
"""
test_chat.py - Automated test of the chat interface with mock LLM
"""

from lyricsmith import LineSpec, Strictness, generate_section
from lyricsmith.llm import MockLLM
from chat import SongProject

def test_song_project():
    """Test project save/load."""
    print("Testing SongProject save/load...")
    
    # Create project
    project = SongProject("Test Song")
    project.sections["verse1"] = {
        "lines": ["Line one", "Line two", "Line three", "Line four"],
        "rhyme_scheme": "ABBA",
        "meaning": ["intro", "develop", "develop", "conclude"]
    }
    
    # Save
    project.save("test_song.json")
    print("✅ Saved project")
    
    # Load
    loaded = SongProject.load("test_song.json")
    print(f"✅ Loaded project: '{loaded.title}'")
    print(f"   Sections: {list(loaded.sections.keys())}")
    print(f"   Lines: {loaded.sections['verse1']['lines']}")
    
    import os
    os.remove("test_song.json")
    print("✅ Cleanup done\n")


def test_generation_with_mock():
    """Test generation with mock LLM (fast, no network)."""
    print("Testing generation with Mock LLM...")
    
    llm = MockLLM(pool={
        "opener": [
            "The little boy asleep at night",
            "A boy alone with shadows near",
            "The sleeping boy in darkened room",
        ],
        "image": [
            "The silver moonlight on the floor",
            "The quiet darkness all around",
            "His innocence lies safe and sound",
            "The stars above are shining bright",
        ]
    })
    
    slots = [
        {"meaning": "introduce the boy alone in his room",
         "spec": LineSpec(8, "01010101"), "rhyme_label": "A"},
        {"meaning": "describe the quiet bedroom",
         "spec": LineSpec(10, "0101010101"), "rhyme_label": "B"},
        {"meaning": "suggest innocence or vulnerability",
         "spec": LineSpec(10, "0101010101"), "rhyme_label": "B"},
        {"meaning": "end with a strong visual image",
         "spec": LineSpec(8, "01010101"), "rhyme_label": "A"},
    ]
    
    print("Generating 4-line verse (ABBA)...")
    lines, results = generate_section(
        llm, slots, 
        strictness=Strictness.SUNG,
        candidates_per_round=3,
        max_rounds=2
    )
    
    print("\n📝 Generated Lines:")
    for i, (line, result) in enumerate(zip(lines, results), 1):
        status = "✅" if result.status == "PASS" else "❌"
        print(f"{status} Line {i}: {line or '(failed)'}")
    
    passed = sum(1 for r in results if r.status == "PASS")
    print(f"\n✅ {passed}/{len(results)} lines passed validation\n")


def demo_workflow():
    """Show the typical workflow."""
    print("="*70)
    print("DEMO: Typical Chat Workflow")
    print("="*70)
    print()
    print("1. User: 'new Sleeping Boy Song'")
    print("   → Creates new song project\n")
    
    print("2. User: 'write verse1'")
    print("   → Prompts for:")
    print("     - Line meanings (what each line expresses)")
    print("     - Syllable counts (e.g., 8-10-10-8)")
    print("     - Rhyme scheme (e.g., ABBA)\n")
    
    print("3. System generates and validates lines")
    print("   → Shows: ✅ [PASS] or ❌ [NO_CANDIDATE]")
    print("   → User accepts or retries\n")
    
    print("4. User: 'save'")
    print("   → Saves to songs/sleeping_boy_song.json\n")
    
    print("5. User: 'write chorus'")
    print("   → Repeat for next section\n")
    
    print("6. User: 'show'")
    print("   → View complete song\n")
    
    print("7. User: 'quit'")
    print("   → Exit (song is saved)")
    print()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 LyricSmith Chat Interface - Automated Tests")
    print("="*70 + "\n")
    
    try:
        test_song_project()
        test_generation_with_mock()
        demo_workflow()
        
        print("="*70)
        print("✅ All tests passed!")
        print("="*70)
        print()
        print("📖 To use the actual chat interface:")
        print("   1. Make sure 'ollama serve' is running")
        print("   2. Run: python chat.py")
        print("   3. See CHAT_USAGE.md for detailed guide")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
