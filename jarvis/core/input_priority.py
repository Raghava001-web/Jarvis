"""
JARVIS Input Priority Manager
==============================
Handles input contention when voice, gesture, UI, scheduled tasks conflict.

Priority hierarchy:
    EMERGENCY (100): "Stop!", "Cancel!", system alerts
    VOICE (80):      Spoken commands
    GESTURE (60):    Hand gestures
    UI_BUTTON (40):  HUD button clicks
    SCHEDULED (20):  Timers, alarms, reminders
"""

import time
from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class InputSource(IntEnum):
    """Priority levels for input sources"""
    EMERGENCY = 100   # "Stop!", "Cancel!", etc.
    VOICE = 80        # Spoken commands
    GESTURE = 60      # Hand gestures
    UI_BUTTON = 40    # HUD interactions
    SCHEDULED = 20    # Timers/alarms/reminders


# Commands that should be treated as emergency (highest priority)
EMERGENCY_COMMANDS = frozenset([
    "stop", "cancel", "wait", "hold on", "never mind",
    "abort", "halt", "pause everything", "emergency"
])


@dataclass
class PrioritizedInput:
    """An input with priority metadata"""
    source: InputSource
    text: str
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For sorting - higher priority first, then newer timestamp"""
        if self.source != other.source:
            return self.source > other.source  # Higher priority first
        return self.timestamp > other.timestamp  # Newer first


class InputPriorityManager:
    """
    Manages input arbitration when multiple inputs arrive simultaneously.
    
    Usage:
        manager = InputPriorityManager()
        manager.add(PrioritizedInput(InputSource.VOICE, "play music"))
        manager.add(PrioritizedInput(InputSource.GESTURE, "next"))
        winner = manager.get_winner()  # Returns VOICE input (higher priority)
    """
    
    def __init__(self, debounce_ms: int = 300, window_ms: int = 500):
        """
        Args:
            debounce_ms: Ignore duplicate inputs within this window
            window_ms: Collect inputs for this long before picking winner
        """
        self.debounce_ms = debounce_ms
        self.window_ms = window_ms
        self.pending: List[PrioritizedInput] = []
        self.last_text: Optional[str] = None
        self.last_text_time: float = 0
    
    def add(self, inp: PrioritizedInput) -> bool:
        """
        Add an input to the pending queue.
        Returns True if added, False if debounced (duplicate).
        """
        now = time.time()
        
        # Check for emergency commands - upgrade priority
        if any(cmd in inp.text.lower() for cmd in EMERGENCY_COMMANDS):
            inp = PrioritizedInput(
                source=InputSource.EMERGENCY,
                text=inp.text,
                timestamp=inp.timestamp,
                confidence=inp.confidence,
                metadata=inp.metadata
            )
        
        # Debounce: ignore if same text within window
        if (inp.text.lower() == self.last_text and 
            now - self.last_text_time < self.debounce_ms / 1000):
            return False
        
        self.pending.append(inp)
        self.last_text = inp.text.lower()
        self.last_text_time = now
        return True
    
    def get_winner(self) -> Optional[PrioritizedInput]:
        """
        Get the highest priority input and clear the queue.
        Uses (source priority, timestamp) as the sorting key.
        """
        if not self.pending:
            return None
        
        # Sort by priority (higher first), then by timestamp (newer first)
        # The __lt__ method on PrioritizedInput handles this
        winner = sorted(self.pending)[0]
        self.pending.clear()
        return winner
    
    def peek_winner(self) -> Optional[PrioritizedInput]:
        """Peek at winner without clearing queue"""
        if not self.pending:
            return None
        return sorted(self.pending)[0]
    
    def has_pending(self) -> bool:
        """Check if there are pending inputs"""
        return len(self.pending) > 0
    
    def clear(self):
        """Clear all pending inputs"""
        self.pending.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get debug stats"""
        return {
            "pending_count": len(self.pending),
            "pending_by_source": {
                source.name: sum(1 for p in self.pending if p.source == source)
                for source in InputSource
            }
        }


# Singleton instance
_manager: Optional[InputPriorityManager] = None

def get_priority_manager() -> InputPriorityManager:
    """Get the global priority manager instance"""
    global _manager
    if _manager is None:
        _manager = InputPriorityManager()
    return _manager
