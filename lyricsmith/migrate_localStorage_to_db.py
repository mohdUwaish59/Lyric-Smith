#!/usr/bin/env python3
"""
migrate_localStorage_to_db.py - Helper script to migrate localStorage data to database

This is a template for users to manually migrate their localStorage data
if they have important conversations they want to preserve.
"""

import uuid
from datetime import datetime
from database import SessionLocal
from models import Session as DBSession, Message as DBMessage, Song as DBSong, generate_session_name

def create_migration_session(session_name: str = None):
    """
    Create a new session for migrated data.
    
    Args:
        session_name: Optional custom name, otherwise generates random name
    
    Returns:
        Session ID for use in migration
    """
    db = SessionLocal()
    try:
        session_id = str(uuid.uuid4())
        session = DBSession(
            id=session_id,
            name=session_name or f"Migrated - {generate_session_name()}",
            created_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        
        print(f"✅ Created migration session: {session.name}")
        print(f"   Session ID: {session_id}")
        return session_id
        
    finally:
        db.close()


def add_message_to_session(session_id: str, role: str, content: str, **kwargs):
    """
    Add a message to a session.
    
    Args:
        session_id: Target session ID
        role: "user", "assistant", or "system"
        content: Message content
        **kwargs: Optional fields (lyrics, results, generation_request)
    """
    db = SessionLocal()
    try:
        message = DBMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            lyrics=kwargs.get('lyrics'),
            results=kwargs.get('results'),
            generation_request=kwargs.get('generation_request'),
            created_at=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        print(f"   ✓ Added {role} message")
        
    finally:
        db.close()


def add_song_to_session(session_id: str, title: str, sections: dict = None):
    """
    Add a song to a session.
    
    Args:
        session_id: Target session ID
        title: Song title
        sections: Optional song sections dictionary
    """
    db = SessionLocal()
    try:
        song_id = str(uuid.uuid4())
        song = DBSong(
            id=song_id,
            session_id=session_id,
            title=title,
            sections=sections or {},
            created_at=datetime.utcnow()
        )
        db.add(song)
        
        # Update session's current_song_id
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if session:
            session.current_song_id = song_id
        
        db.commit()
        print(f"   ✓ Added song: {title}")
        return song_id
        
    finally:
        db.close()


# ============================================================================
# Example Migration Script
# ============================================================================

def example_migration():
    """
    Example showing how to migrate data.
    Users should customize this based on their localStorage data.
    """
    print("Example Migration Script")
    print("=" * 60)
    
    # Step 1: Create a new session
    session_id = create_migration_session("My Old Conversations")
    
    # Step 2: Add messages (customize with your data)
    print("\nMigrating messages...")
    
    add_message_to_session(
        session_id,
        role="system",
        content="✅ LLM configured: ollama with model qwen2.5:7b"
    )
    
    add_message_to_session(
        session_id,
        role="user",
        content="Generate verse1 with 4 lines (AABB)"
    )
    
    add_message_to_session(
        session_id,
        role="assistant",
        content="✅ Lyrics generated successfully!",
        lyrics=["Line 1 text", "Line 2 text", None, "Line 4 text"],
        results=[
            {"line": "Line 1 text", "status": "PASS", "attempts": 5, "problems": []},
            {"line": "Line 2 text", "status": "PASS", "attempts": 2, "problems": []},
            {"line": None, "status": "FAIL", "attempts": 32, "problems": ["syllable_count"]},
            {"line": "Line 4 text", "status": "PASS", "attempts": 10, "problems": []}
        ]
    )
    
    # Step 3: Add songs (if any)
    print("\nMigrating songs...")
    song_id = add_song_to_session(
        session_id,
        title="My Old Song",
        sections={
            "verse1": {
                "lines": ["Line 1", "Line 2", "Line 3", "Line 4"],
                "rhyme_scheme": "AABB",
                "created": datetime.utcnow().isoformat()
            }
        }
    )
    
    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print(f"\nYou can now access this session in the app.")
    print(f"Session ID: {session_id}")


# ============================================================================
# Manual Migration Template
# ============================================================================

def manual_migration():
    """
    Template for manual migration.
    Copy your localStorage JSON data here and adapt as needed.
    """
    
    # TODO: Paste your localStorage data here
    # Example: localStorage_messages = [...your messages...]
    # Example: localStorage_song = {...your song data...}
    
    print("Manual Migration Template")
    print("=" * 60)
    print("\n⚠️  This is a template. You need to:")
    print("1. Export your localStorage data from browser console:")
    print("   localStorage.getItem('lyricsmith-messages')")
    print("   localStorage.getItem('lyricsmith-current-song')")
    print("2. Paste the JSON data into this script")
    print("3. Adapt the migration logic to your data structure")
    print("4. Run this script")
    print("\nFor help, see the example_migration() function above.")


if __name__ == "__main__":
    import sys
    
    print("LyricSmith Data Migration Tool")
    print("=" * 60)
    print("\nOptions:")
    print("1. Run example migration")
    print("2. Use manual migration template")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        if input("\nThis will create test data. Continue? (y/n): ").lower() == 'y':
            example_migration()
    elif choice == "2":
        print("\n⚠️  Edit this script and add your data to manual_migration() function")
        manual_migration()
    else:
        print("Exiting...")
