"""
Context Memory - Unified Memory System
=======================================
- Working Memory: Short-term (last 10-20 turns)
- Long-Term Memory: Semantic (embedding-based recall)
- Entity resolution and pronoun handling
"""

import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import hashlib

# Try embedding support
EMBEDDINGS_AVAILABLE = False
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    pass


@dataclass
class ConversationTurn:
    """A single conversation turn"""
    user_input: str
    jarvis_response: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryFact:
    """A stored fact in long-term memory"""
    fact: str
    category: str
    confidence: float
    timestamp: datetime
    embedding: Optional[Any] = None  # numpy array


class WorkingMemory:
    """
    Short-term conversation memory with auto-summarization.
    Tracks recent turns, current topic, active entities.
    Compresses old context to prevent bloat.
    """
    
    COMPRESS_EVERY = 5  # Summarize every N turns
    
    def __init__(self, max_turns: int = 15):
        self.history: deque = deque(maxlen=max_turns)
        self.current_topic: Optional[str] = None
        self.active_entities: Dict[str, str] = {}  # pronoun -> entity
        self.last_intent: Optional[str] = None
        self.turn_count: int = 0
        
        # Compressed summaries
        self.summaries: List[str] = []
        
    def add_turn(self, user_input: str, jarvis_response: str, 
                 intent: str = None, entities: Dict = None):
        """Add a conversation turn"""
        turn = ConversationTurn(
            user_input=user_input,
            jarvis_response=jarvis_response,
            intent=intent,
            entities=entities or {},
        )
        self.history.append(turn)
        self.turn_count += 1
        
        # Update active entities
        if entities:
            for key, value in entities.items():
                if isinstance(value, str) and len(value) > 2:
                    self.active_entities["it"] = value
                    self.active_entities["that"] = value
                    
        if intent:
            self.last_intent = intent
            self.current_topic = intent.replace("_", " ")
            
        # Auto-compress every N turns
        if self.turn_count > 0 and self.turn_count % self.COMPRESS_EVERY == 0:
            self._compress_context()
            
    def _compress_context(self):
        """Compress old conversation into summary"""
        if len(self.history) < 3:
            return
            
        # Get oldest turns to compress
        old_turns = list(self.history)[:3]
        
        # Simple summarization (no LLM needed)
        summary_parts = []
        intents_seen = set()
        entities_used = []
        
        for turn in old_turns:
            if turn.intent and turn.intent not in intents_seen:
                intents_seen.add(turn.intent)
                
            for k, v in turn.entities.items():
                if isinstance(v, str) and v not in entities_used:
                    entities_used.append(f"{k}:{v}")
                    
        if intents_seen:
            summary_parts.append(f"Discussed: {', '.join(intents_seen)}")
        if entities_used:
            summary_parts.append(f"Mentioned: {', '.join(entities_used[:5])}")
            
        if summary_parts:
            summary = "; ".join(summary_parts)
            self.summaries.append(summary)
            
            # Keep only last 5 summaries
            self.summaries = self.summaries[-5:]
            
        # Remove old turns (keep recent ones)
        while len(self.history) > 5:
            self.history.popleft()
            
    def get_recent(self, n: int = 5) -> List[ConversationTurn]:
        """Get last N turns"""
        return list(self.history)[-n:]
        
    def get_context_prompt(self) -> str:
        """Build context string for LLM, including summaries"""
        parts = []
        
        # Include compressed summaries
        if self.summaries:
            parts.append("Previous context: " + " | ".join(self.summaries[-2:]))
            
        # Recent turns
        recent = self.get_recent(3)
        if recent:
            for turn in recent:
                parts.append(f"User: {turn.user_input}")
                parts.append(f"JARVIS: {turn.jarvis_response}")
                
        return "\n".join(parts)
        
    def get_conversation_summary(self) -> str:
        """Get a full summary of the conversation"""
        summary_parts = []
        
        if self.summaries:
            summary_parts.extend(self.summaries)
            
        # Current context
        if self.current_topic:
            summary_parts.append(f"Current topic: {self.current_topic}")
            
        # Active entities
        if self.active_entities:
            entities = [f"{k}={v}" for k, v in self.active_entities.items()]
            summary_parts.append(f"Active refs: {', '.join(entities)}")
            
        return "; ".join(summary_parts)
        
    def resolve_pronoun(self, text: str) -> str:
        """Resolve pronouns like 'it', 'that' using context"""
        text_lower = text.lower()
        
        for pronoun, entity in self.active_entities.items():
            # Only replace if pronoun is a standalone word
            pattern = rf"\b{pronoun}\b"
            if re.search(pattern, text_lower):
                # Replace carefully
                text = re.sub(pattern, entity, text, flags=re.IGNORECASE)
                break
                
        return text
        
    def clear(self):
        """Clear working memory"""
        self.history.clear()
        self.active_entities.clear()
        self.current_topic = None
        self.summaries.clear()
        self.turn_count = 0


class LongTermMemory:
    """
    Semantic long-term memory.
    Uses embeddings for similarity-based recall.
    Falls back to keyword matching if embeddings unavailable.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print("[MEMORY] Initializing Long-Term Memory...")
        
        # Data path
        self.db_path = Path(__file__).parent.parent / "data" / "long_term_memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Embedding model
        self.model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                print("[MEMORY] Embeddings enabled")
            except:
                print("[MEMORY] Embedding model load failed")
                
        # Initialize database
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()
        
        # In-memory cache for fast lookup
        self._cache: List[MemoryFact] = []
        self._load_cache()
        
        print(f"[MEMORY] {len(self._cache)} facts loaded")
        
    def _init_db(self):
        """Initialize SQLite database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                confidence REAL DEFAULT 1.0,
                timestamp TEXT NOT NULL,
                embedding BLOB,
                keywords TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON facts(category)')
        self.conn.commit()
        
    def _load_cache(self):
        """Load facts into memory cache"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT fact, category, confidence, timestamp, embedding FROM facts')
        
        for row in cursor.fetchall():
            fact, category, confidence, timestamp, emb_blob = row
            
            embedding = None
            if emb_blob and EMBEDDINGS_AVAILABLE:
                try:
                    embedding = np.frombuffer(emb_blob, dtype=np.float32)
                except:
                    pass
                    
            self._cache.append(MemoryFact(
                fact=fact,
                category=category,
                confidence=confidence,
                timestamp=datetime.fromisoformat(timestamp),
                embedding=embedding,
            ))
            
    def remember(self, fact: str, category: str = "general", 
                 confidence: float = 1.0) -> bool:
        """Store a fact in long-term memory"""
        try:
            # Compute embedding
            embedding = None
            emb_blob = None
            if self.model:
                embedding = self.model.encode(fact)
                emb_blob = embedding.astype(np.float32).tobytes()
                
            # Extract keywords for fallback search
            keywords = " ".join(set(re.findall(r"\b\w{4,}\b", fact.lower())))
            
            # Store in database
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO facts (fact, category, confidence, timestamp, embedding, keywords)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (fact, category, confidence, datetime.now().isoformat(), emb_blob, keywords))
            self.conn.commit()
            
            # Add to cache
            self._cache.append(MemoryFact(
                fact=fact,
                category=category,
                confidence=confidence,
                timestamp=datetime.now(),
                embedding=embedding,
            ))
            
            return True
            
        except Exception as e:
            print(f"[MEMORY] Remember error: {e}")
            return False
            
    def recall(self, query: str, top_k: int = 5, 
               category: str = None) -> List[Tuple[str, float]]:
        """
        Recall facts similar to query.
        Returns list of (fact, score) tuples.
        """
        if not self._cache:
            return []
            
        # Filter by category if specified
        candidates = self._cache
        if category:
            candidates = [f for f in self._cache if f.category == category]
            
        if self.model and EMBEDDINGS_AVAILABLE:
            return self._recall_embedding(query, candidates, top_k)
        else:
            return self._recall_keyword(query, candidates, top_k)
            
    def _recall_embedding(self, query: str, candidates: List[MemoryFact], 
                          top_k: int) -> List[Tuple[str, float]]:
        """Recall using cosine similarity"""
        query_emb = self.model.encode(query)
        
        scored = []
        for fact in candidates:
            if fact.embedding is not None:
                score = np.dot(query_emb, fact.embedding) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(fact.embedding)
                )
                scored.append((fact.fact, float(score)))
                
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
        
    def _recall_keyword(self, query: str, candidates: List[MemoryFact],
                        top_k: int) -> List[Tuple[str, float]]:
        """Fallback: keyword-based recall"""
        query_words = set(re.findall(r"\b\w{4,}\b", query.lower()))
        
        scored = []
        for fact in candidates:
            fact_words = set(re.findall(r"\b\w{4,}\b", fact.fact.lower()))
            overlap = len(query_words & fact_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                scored.append((fact.fact, score))
                
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
        
    def forget(self, fact: str) -> bool:
        """Remove a fact from memory"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM facts WHERE fact = ?', (fact,))
            self.conn.commit()
            
            self._cache = [f for f in self._cache if f.fact != fact]
            return True
        except:
            return False
            
    def get_all(self, category: str = None) -> List[str]:
        """Get all stored facts"""
        if category:
            return [f.fact for f in self._cache if f.category == category]
        return [f.fact for f in self._cache]
        
    def clear(self, category: str = None):
        """Clear memory (optionally by category)"""
        cursor = self.conn.cursor()
        if category:
            cursor.execute('DELETE FROM facts WHERE category = ?', (category,))
            self._cache = [f for f in self._cache if f.category != category]
        else:
            cursor.execute('DELETE FROM facts')
            self._cache.clear()
        self.conn.commit()


class ContextMemory:
    """
    Unified memory system combining working and long-term memory.
    This is the main interface other modules should use.
    """
    
    def __init__(self, perception=None):
        print("[CONTEXT] Initializing Context Memory...")
        self.perception = perception
        
        self.working = WorkingMemory()
        self.long_term = LongTermMemory()
        
        # User preferences (weighted, with decay)
        self.preferences: Dict[str, float] = {}
        self._load_preferences()
        
        print("[CONTEXT] Context Memory Ready")
        
    def _load_preferences(self):
        """Load user preferences"""
        pref_path = Path(__file__).parent.parent / "data" / "preferences.json"
        try:
            if pref_path.exists():
                with open(pref_path, 'r') as f:
                    self.preferences = json.load(f)
        except:
            pass
            
    def _save_preferences(self):
        """Save user preferences"""
        pref_path = Path(__file__).parent.parent / "data" / "preferences.json"
        try:
            pref_path.parent.mkdir(parents=True, exist_ok=True)
            with open(pref_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except:
            pass
            
    # Working memory shortcuts
    def add_exchange(self, user_input: str, jarvis_response: str,
                     intent: str = None, entities: Dict = None):
        """Add a conversation exchange"""
        self.working.add_turn(user_input, jarvis_response, intent, entities)
        
    def get_context_prompt(self) -> str:
        """Get context for LLM"""
        return self.working.get_context_prompt()
        
    def resolve_pronoun(self, text: str) -> str:
        """Resolve pronouns using context"""
        return self.working.resolve_pronoun(text)
        
    # Long-term memory shortcuts
    def remember(self, fact: str, category: str = "general") -> bool:
        """Store a fact"""
        return self.long_term.remember(fact, category)
        
    def recall(self, query: str, top_k: int = 5) -> List[str]:
        """Recall relevant facts"""
        results = self.long_term.recall(query, top_k)
        return [fact for fact, score in results]
        
    # Preference tracking
    def set_preference(self, key: str, value: float = 1.0):
        """Set a preference (e.g., 'spotify' -> 0.9)"""
        self.preferences[key] = value
        self._save_preferences()
        
    def get_preference(self, key: str, default: float = 0.0) -> float:
        """Get preference score"""
        return self.preferences.get(key, default)
        
    def learn_preference(self, key: str, positive: bool = True):
        """Learn preference from usage (incremental)"""
        current = self.preferences.get(key, 0.5)
        if positive:
            self.preferences[key] = min(1.0, current + 0.1)
        else:
            self.preferences[key] = max(0.0, current - 0.1)
        self._save_preferences()


# Singleton
_memory = None

def get_context_memory(perception=None) -> ContextMemory:
    global _memory
    if _memory is None:
        _memory = ContextMemory(perception)
    return _memory
