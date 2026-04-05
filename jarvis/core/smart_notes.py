"""
Smart Notes - Intelligent note-taking and memory system
JARVIS remembers important information and recalls it when relevant
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
import re


@dataclass
class Note:
    """A single note entry"""
    id: int
    content: str
    tags: List[str]
    created_at: str
    importance: int  # 1-5
    context: str = ""  # Context when note was made


class SmartNotes:
    """Intelligent note-taking and memory recall system"""
    
    def __init__(self, perception=None):
        print("[NOTES] Initializing Smart Notes...")
        self.perception = perception
        
        # Database
        self.db_path = Path(__file__).parent.parent / "data" / "jarvis_memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        
        # Auto-detected tags
        self.tag_patterns = {
            "password": ["password", "pwd", "login", "credential", "account"],
            "meeting": ["meeting", "appointment", "schedule", "call with", "talk to"],
            "idea": ["idea", "thought", "what if", "could we", "imagine"],
            "todo": ["todo", "to do", "need to", "have to", "must", "should"],
            "important": ["important", "critical", "urgent", "don't forget", "remember"],
            "personal": ["birthday", "anniversary", "family", "friend", "mom", "dad"],
            "work": ["work", "office", "project", "deadline", "client", "boss"],
            "learn": ["learn", "study", "course", "tutorial", "read"],
            "buy": ["buy", "purchase", "get", "shop", "order"],
            "health": ["doctor", "medicine", "health", "gym", "workout", "diet"],
        }
        
        print("[NOTES] Smart Notes Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[NOTES] {text}")
    
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance INTEGER DEFAULT 3,
                context TEXT,
                recalled_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _auto_tag(self, content: str) -> List[str]:
        """Automatically detect tags from content"""
        content_lower = content.lower()
        detected_tags = []
        
        for tag, patterns in self.tag_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    detected_tags.append(tag)
                    break
        
        return list(set(detected_tags))
    
    def _detect_importance(self, content: str) -> int:
        """Detect importance level from content"""
        content_lower = content.lower()
        
        # High importance keywords
        if any(word in content_lower for word in ["password", "critical", "urgent", "important", "must", "deadline"]):
            return 5
        elif any(word in content_lower for word in ["need to", "should", "don't forget", "remember"]):
            return 4
        elif any(word in content_lower for word in ["idea", "thought", "could", "might"]):
            return 2
        
        return 3  # Default medium importance
    
    def add_note(self, content: str, tags: List[str] = None) -> int:
        """Add a new note"""
        title = self._get_title()
        
        # Auto-detect tags if not provided
        if not tags:
            tags = self._auto_tag(content)
        
        importance = self._detect_importance(content)
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notes (content, tags, created_at, importance)
            VALUES (?, ?, ?, ?)
        ''', (content, json.dumps(tags), timestamp, importance))
        
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._speak(f"I'll remember that, {title}.")
        return note_id
    
    def remember(self, key: str, value: str, category: str = "general"):
        """Remember a key-value pair"""
        title = self._get_title()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memories (key, value, category, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (key.lower(), value, category, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self._speak(f"I'll remember that {key} is {value}, {title}.")
    
    def recall(self, key: str) -> Optional[str]:
        """Recall a remembered value"""
        title = self._get_title()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM memories WHERE key LIKE ?', (f'%{key.lower()}%',))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self._speak(f"{key} is {result[0]}, {title}.")
            return result[0]
        else:
            self._speak(f"I don't have any information about {key}, {title}.")
            return None
    
    def search_notes(self, query: str) -> List[Note]:
        """Search notes by content or tags"""
        title = self._get_title()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, content, tags, created_at, importance
            FROM notes
            WHERE content LIKE ? OR tags LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT 10
        ''', (f'%{query}%', f'%{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        notes = []
        for row in results:
            notes.append(Note(
                id=row[0],
                content=row[1],
                tags=json.loads(row[2]) if row[2] else [],
                created_at=row[3],
                importance=row[4]
            ))
        
        if notes:
            self._speak(f"I found {len(notes)} notes about '{query}', {title}.")
        else:
            self._speak(f"I couldn't find any notes about '{query}', {title}.")
        
        return notes
    
    def get_by_tag(self, tag: str) -> List[Note]:
        """Get notes by tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, content, tags, created_at, importance
            FROM notes
            WHERE tags LIKE ?
            ORDER BY importance DESC, created_at DESC
        ''', (f'%"{tag}"%',))
        
        results = cursor.fetchall()
        conn.close()
        
        notes = []
        for row in results:
            notes.append(Note(
                id=row[0],
                content=row[1],
                tags=json.loads(row[2]) if row[2] else [],
                created_at=row[3],
                importance=row[4]
            ))
        
        return notes
    
    def get_recent_notes(self, count: int = 5) -> List[Note]:
        """Get recent notes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, content, tags, created_at, importance
            FROM notes
            ORDER BY created_at DESC
            LIMIT ?
        ''', (count,))
        
        results = cursor.fetchall()
        conn.close()
        
        notes = []
        for row in results:
            notes.append(Note(
                id=row[0],
                content=row[1],
                tags=json.loads(row[2]) if row[2] else [],
                created_at=row[3],
                importance=row[4]
            ))
        
        return notes
    
    def read_notes(self, count: int = 5):
        """Read recent notes aloud"""
        title = self._get_title()
        
        notes = self.get_recent_notes(count)
        
        if not notes:
            self._speak(f"You don't have any notes yet, {title}.")
            return
        
        self._speak(f"Here are your recent notes, {title}.")
        
        for i, note in enumerate(notes, 1):
            self._speak(f"Note {i}: {note.content}")
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            self._speak("Note deleted.")
        
        return deleted
    
    def extract_remembrance_from_command(self, command: str) -> bool:
        """Extract and save 'remember that' style commands"""
        command_lower = command.lower()
        
        # Pattern: "remember that [info]"
        if "remember that" in command_lower:
            content = command_lower.split("remember that", 1)[-1].strip()
            if content:
                self.add_note(content)
                return True
        
        # Pattern: "remember [key] is [value]"
        match = re.search(r'remember\s+(.+?)\s+is\s+(.+)', command_lower)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            self.remember(key, value)
            return True
        
        # Pattern: "my [thing] is [value]"
        match = re.search(r'my\s+(.+?)\s+is\s+(.+)', command_lower)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            self.remember(f"your {key}", value)
            return True
        
        return False
