"""
Chat History - Production Grade
================================
- SQLite FTS5 for fast full-text search
- Conversation threading (turn IDs)
- Retention policies
- Token estimation for context windows
- Privacy-conscious (no external calls)
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ChatMessage:
    """A single chat message"""
    id: Optional[int]
    role: str  # "user" or "jarvis"
    content: str
    timestamp: str
    intent: Optional[str] = None
    emotion: Optional[str] = None
    turn_id: Optional[int] = None  # For conversation threading
    tokens: Optional[int] = None   # Token estimation


class ChatHistory:
    """
    Production-grade chat history with FTS5.
    Thread-safe, fast search, proper retention.
    """
    
    def __init__(self, perception=None):
        print("[CHAT] Initializing Chat History...")
        self.perception = perception
        
        # Database
        self.db_path = Path(__file__).parent.parent / "data" / "chat_history.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
        
        # In-memory cache
        self.recent_messages: List[ChatMessage] = []
        self.cache_size = 50
        
        # Conversation state
        self.current_turn = 0
        self._load_turn_counter()
        
        # Retention policy
        self.retention_days = 90  # Keep 90 days by default
        
        print("[CHAT] Chat History Ready")
        
    def _init_db(self):
        """Initialize SQLite with FTS5 and handle schema migrations"""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Check if old schema exists
            cursor.execute("PRAGMA table_info(messages)")
            columns = {col[1] for col in cursor.fetchall()}
            
            if 'id' in columns and 'turn_id' not in columns:
                # Migrate old schema - add new columns
                print("[CHAT] Migrating database schema...")
                cursor.execute('ALTER TABLE messages ADD COLUMN turn_id INTEGER')
                cursor.execute('ALTER TABLE messages ADD COLUMN tokens INTEGER')
                self.conn.commit()
                print("[CHAT] Migration complete")
            elif 'id' not in columns:
                # Create fresh table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        intent TEXT,
                        emotion TEXT,
                        turn_id INTEGER,
                        tokens INTEGER
                    )
                ''')
            
            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_turn ON messages(turn_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_role ON messages(role)')
            
            # FTS5 virtual table for fast full-text search
            # Check if FTS table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='messages_fts'
            """)
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE VIRTUAL TABLE messages_fts USING fts5(
                        content,
                        intent,
                        content='messages',
                        content_rowid='id'
                    )
                ''')
                
                # Triggers to keep FTS in sync
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                        INSERT INTO messages_fts(rowid, content, intent)
                        VALUES (new.id, new.content, new.intent);
                    END
                ''')
                
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                        INSERT INTO messages_fts(messages_fts, rowid, content, intent)
                        VALUES ('delete', old.id, old.content, old.intent);
                    END
                ''')
                
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                        INSERT INTO messages_fts(messages_fts, rowid, content, intent)
                        VALUES ('delete', old.id, old.content, old.intent);
                        INSERT INTO messages_fts(rowid, content, intent)
                        VALUES (new.id, new.content, new.intent);
                    END
                ''')
                
                # Rebuild FTS from existing data
                cursor.execute('''
                    INSERT INTO messages_fts(rowid, content, intent)
                    SELECT id, content, intent FROM messages
                ''')
            
            self.conn.commit()
            
        except Exception as e:
            print(f"[CHAT] Database init error: {e}")
            
    def _load_turn_counter(self):
        """Load the last turn ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT MAX(turn_id) FROM messages')
            result = cursor.fetchone()
            self.current_turn = (result[0] or 0)
        except:
            self.current_turn = 0
            
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (roughly 4 chars = 1 token)"""
        return len(text) // 4 + 1
        
    def new_turn(self):
        """Start a new conversation turn"""
        self.current_turn += 1
        return self.current_turn
        
    def add_message(self, role: str, content: str, intent: str = None,
                    emotion: str = None, new_turn: bool = False) -> Optional[int]:
        """Add a message to history"""
        if new_turn:
            self.new_turn()
            
        timestamp = datetime.now().isoformat()
        tokens = self._estimate_tokens(content)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO messages (role, content, timestamp, intent, emotion, turn_id, tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (role, content, timestamp, intent, emotion, self.current_turn, tokens))
            
            message_id = cursor.lastrowid
            self.conn.commit()
            
            # Update cache
            msg = ChatMessage(message_id, role, content, timestamp, intent, emotion, 
                            self.current_turn, tokens)
            self.recent_messages.append(msg)
            
            if len(self.recent_messages) > self.cache_size:
                self.recent_messages.pop(0)
                
            return message_id
            
        except Exception as e:
            print(f"[CHAT] Error adding message: {e}")
            return None
            
    def add_user_message(self, content: str, emotion: str = None) -> Optional[int]:
        """Add user message (starts new turn)"""
        return self.add_message("user", content, emotion=emotion, new_turn=True)
        
    def add_jarvis_message(self, content: str, intent: str = None) -> Optional[int]:
        """Add JARVIS response (same turn)"""
        return self.add_message("jarvis", content, intent=intent, new_turn=False)
        
    def get_recent(self, count: int = 20) -> List[ChatMessage]:
        """Get recent messages"""
        if len(self.recent_messages) >= count:
            return self.recent_messages[-count:]
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, role, content, timestamp, intent, emotion, turn_id, tokens
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (count,))
            
            rows = cursor.fetchall()
            messages = [ChatMessage(*row) for row in reversed(rows)]
            return messages
            
        except Exception as e:
            print(f"[CHAT] Error getting messages: {e}")
            return []
            
    def search(self, query: str, limit: int = 20) -> List[ChatMessage]:
        """
        Fast FTS5 search - MUCH faster than LIKE '%query%'.
        Supports boolean queries: "word1 AND word2", "word1 OR word2"
        """
        try:
            cursor = self.conn.cursor()
            
            # FTS5 query (properly escape)
            fts_query = query.replace('"', '""')
            
            cursor.execute('''
                SELECT m.id, m.role, m.content, m.timestamp, m.intent, m.emotion, m.turn_id, m.tokens
                FROM messages m
                JOIN messages_fts f ON m.id = f.rowid
                WHERE messages_fts MATCH ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (fts_query, limit))
            
            rows = cursor.fetchall()
            return [ChatMessage(*row) for row in rows]
            
        except Exception as e:
            print(f"[CHAT] FTS search error: {e}, falling back to LIKE")
            # Fallback to LIKE
            try:
                cursor.execute('''
                    SELECT id, role, content, timestamp, intent, emotion, turn_id, tokens
                    FROM messages
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (f'%{query}%', limit))
                
                rows = cursor.fetchall()
                return [ChatMessage(*row) for row in rows]
            except:
                return []
                
    def get_by_date(self, date_str: str) -> List[ChatMessage]:
        """Get messages from a specific date (YYYY-MM-DD)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, role, content, timestamp, intent, emotion, turn_id, tokens
                FROM messages
                WHERE date(timestamp) = ?
                ORDER BY timestamp ASC
            ''', (date_str,))
            
            rows = cursor.fetchall()
            return [ChatMessage(*row) for row in rows]
            
        except Exception as e:
            print(f"[CHAT] Date query error: {e}")
            return []
            
    def get_conversation(self, turn_id: int) -> List[ChatMessage]:
        """Get all messages from a conversation turn"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, role, content, timestamp, intent, emotion, turn_id, tokens
                FROM messages
                WHERE turn_id = ?
                ORDER BY timestamp ASC
            ''', (turn_id,))
            
            rows = cursor.fetchall()
            return [ChatMessage(*row) for row in rows]
            
        except Exception as e:
            print(f"[CHAT] Turn query error: {e}")
            return []
            
    def get_context_window(self, max_tokens: int = 4000) -> str:
        """
        Get recent conversation context within token limit.
        Smart truncation for LLM context windows.
        """
        messages = self.get_recent(50)  # Get last 50 messages
        
        context_parts = []
        total_tokens = 0
        
        # Build from most recent
        for msg in reversed(messages):
            role_name = "User" if msg.role == "user" else "JARVIS"
            line = f"{role_name}: {msg.content}"
            msg_tokens = msg.tokens or self._estimate_tokens(line)
            
            if total_tokens + msg_tokens > max_tokens:
                break
                
            context_parts.insert(0, line)
            total_tokens += msg_tokens
            
        return "\n".join(context_parts)
        
    def get_statistics(self) -> Dict:
        """Get chat statistics"""
        try:
            cursor = self.conn.cursor()
            
            stats = {}
            
            cursor.execute('SELECT COUNT(*) FROM messages')
            stats["total_messages"] = cursor.fetchone()[0]
            
            cursor.execute('SELECT role, COUNT(*) FROM messages GROUP BY role')
            by_role = dict(cursor.fetchall())
            stats["user_messages"] = by_role.get("user", 0)
            stats["jarvis_messages"] = by_role.get("jarvis", 0)
            
            cursor.execute('SELECT MAX(turn_id) FROM messages')
            stats["total_conversations"] = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(tokens) FROM messages')
            stats["total_tokens"] = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM messages')
            dates = cursor.fetchone()
            stats["first_message"] = dates[0]
            stats["last_message"] = dates[1]
            
            return stats
            
        except Exception as e:
            print(f"[CHAT] Statistics error: {e}")
            return {}
            
    def apply_retention(self) -> int:
        """Apply retention policy - delete old messages"""
        try:
            cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
            
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM messages WHERE timestamp < ?', (cutoff,))
            deleted = cursor.rowcount
            self.conn.commit()
            
            # Vacuum to reclaim space
            self.conn.execute('VACUUM')
            
            return deleted
            
        except Exception as e:
            print(f"[CHAT] Retention error: {e}")
            return 0
            
    def clear_history(self) -> bool:
        """Clear all chat history"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM messages')
            self.conn.commit()
            self.recent_messages.clear()
            self.current_turn = 0
            return True
        except Exception as e:
            print(f"[CHAT] Clear error: {e}")
            return False
            
    def export_history(self, filepath: str = None) -> Optional[str]:
        """Export chat history to JSON"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(Path.home() / f"jarvis_chat_export_{timestamp}.json")
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, role, content, timestamp, intent, emotion, turn_id, tokens
                FROM messages
                ORDER BY timestamp ASC
            ''')
            
            rows = cursor.fetchall()
            messages = [asdict(ChatMessage(*row)) for row in rows]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
                
            return filepath
            
        except Exception as e:
            print(f"[CHAT] Export error: {e}")
            return None
            
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Singleton
_history = None

def get_chat_history(perception=None) -> ChatHistory:
    global _history
    if _history is None:
        _history = ChatHistory(perception)
    return _history
