"""
jarvis/core/cache.py
Minimal, in-memory caching for tool results based on TTL rules.
"""

import time
from typing import Any, Optional

_cache = {}

def get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    return entry["value"] if entry else None

def set(key: str, value: Any):
    _cache[key] = {"value": value, "ts": time.time()}

def is_valid(key: str, ttl_seconds: int) -> bool:
    entry = _cache.get(key)
    if not entry:
        return False
    return (time.time() - entry["ts"]) <= ttl_seconds
