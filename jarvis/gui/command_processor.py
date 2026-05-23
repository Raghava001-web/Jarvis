"""
JARVIS Command Processor
========================
Extracted from websocket_server.py — pure text-processing utilities
for command splitting, action inference, and text normalization.

This module must NOT touch websocket transport, audio playback,
or client session state. It is a pure text→text processing layer.
"""

import re
from typing import List


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOUND COMMAND SPLITTING
# ═══════════════════════════════════════════════════════════════════════════════

# Action verbs that indicate a new command
ACTION_VERBS = [
    'set', 'remind', 'open', 'play', 'turn', 'tell', 'search',
    'close', 'enable', 'disable', 'take', 'read', 'send', 'show',
    'check', 'what', 'define', 'sing', 'recite', 'mute', 'unmute',
    'increase', 'decrease', 'lower', 'raise', 'switch', 'launch',
    'stop', 'pause', 'resume', 'start', 'create', 'delete',
    'find', 'download', 'look', 'go', 'navigate', 'make',
]


def split_compound_command(text: str) -> List[str]:
    """Split compound commands like 'set alarm AND open youtube AND search for mrbeast'
    
    Recursively splits on ' and ', ' also ', ' then ' when both sides look like
    separate commands (the part after the split starts with an action verb).
    Avoids false splits like 'search for bread and butter'.
    """
    
    def _is_new_command(part: str) -> bool:
        """Check if this text starts with an action verb"""
        p = part.strip().lower()
        return any(p.startswith(verb + ' ') or p == verb for verb in ACTION_VERBS)
    
    def _recursive_split(text: str) -> list:
        """Recursively split on conjunctions"""
        # Try each split pattern
        for pattern in [' and ', ' also ', ' then ']:
            idx = text.lower().find(pattern)
            if idx == -1:
                continue
            
            left = text[:idx].strip()
            right = text[idx + len(pattern):].strip()
            
            if not left or not right:
                continue
            
            # Only split if the right side starts with an action verb
            if _is_new_command(right):
                # Recursively split the right side too (for 3+ commands)
                right_parts = _recursive_split(right)
                return [left] + right_parts
        
        # No valid split found
        return [text]
    
    commands = _recursive_split(text)
    
    if len(commands) > 1:
        print(f"[CommandProcessor] Split compound command into {len(commands)} parts: {commands}")
    
    return commands


# ═══════════════════════════════════════════════════════════════════════════════
# FAST-PATH PATTERN MATCHING — identifies commands eligible for instant execution
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns that the fast path recognizes (for classification only — execution stays in server)
FAST_PATH_PATTERNS = {
    'close_app': re.compile(r'^close\s+(.+)'),
    'resume_video': ['resume video', 'resume the video', 'play video',
                     'pause video', 'pause the video', 'resume youtube',
                     'play youtube', 'pause youtube'],
    'screenshot': ['screenshot', 'screen capture'],
    'volume': ['volume'],
    'brightness': ['brightness'],
    'youtube_play': re.compile(r'play\s+(.+?)\s+(?:in|on)\s+youtube'),
    'open_app': re.compile(r'^(?:open|launch|start)\s+(.+)'),
    'time': ['time', 'what time is it', 'what is the time', 'tell me the time', "what's the time"],
    'date': ['date', 'what date is it', "what's the date", 'what is the date', "what's today's date"],
    'playback_toggle': ['stop video', 'pause video', 'stop the video', 'pause the video',
                        'resume video', 'resume the video', 'unpause',
                        'stop playing', 'stop music', 'pause music',
                        'play pause', 'play/pause'],
}


def is_fast_path_eligible(text: str) -> bool:
    """Check if a command matches any fast-path pattern.
    
    Pure classification — does not execute anything.
    Returns True if the command can be handled by the fast path.
    """
    cmd = text.lower().strip()
    
    for key, pattern in FAST_PATH_PATTERNS.items():
        if isinstance(pattern, re.Pattern):
            if pattern.search(cmd):
                return True
        elif isinstance(pattern, list):
            if key in ('time', 'date'):
                # Exact match required
                if cmd in pattern:
                    return True
            else:
                # Substring match
                if any(p in cmd for p in pattern):
                    return True
    
    return False
