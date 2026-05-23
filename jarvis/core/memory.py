"""
jarvis/core/memory.py
Lightweight, in-memory storage for conversational context and system state.
"""

from typing import List, Set, Optional, Tuple

class _MemoryStore:
    def __init__(self):
        self._queries: List[str] = []
        self._last_tool: Optional[Tuple[str, dict]] = None
        self._monitored_topics: Set[str] = set()

    def add_query(self, text: str):
        self._queries.append(text)
        if len(self._queries) > 5:
            self._queries.pop(0)

    def get_last_query(self) -> Optional[str]:
        return self._queries[-1] if self._queries else None

    def set_last_tool(self, name: str, args: dict):
        self._last_tool = (name, args)

    def get_last_tool(self) -> Optional[Tuple[str, dict]]:
        return self._last_tool

    def add_monitored_topic(self, topic: str):
        if topic.strip():
            self._monitored_topics.add(topic.strip().lower())

    def get_monitored_topics(self) -> List[str]:
        return sorted(list(self._monitored_topics))


# ── Global Singleton instance ──────────────────────────────────────────────
_memory = _MemoryStore()

# ── Public API ─────────────────────────────────────────────────────────────

def add_query(text: str):
    _memory.add_query(text)

def get_last_query() -> Optional[str]:
    return _memory.get_last_query()

def set_last_tool(name: str, args: dict):
    _memory.set_last_tool(name, args)

def get_last_tool() -> Optional[Tuple[str, dict]]:
    return _memory.get_last_tool()

def add_monitored_topic(topic: str):
    _memory.add_monitored_topic(topic)

def get_monitored_topics() -> List[str]:
    return _memory.get_monitored_topics()
