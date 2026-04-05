"""
Clipboard Memory - Smart Clipboard History
==========================================
- Track copied text history
- Retrieve previous clipboard items
- Paste on command
- Search clipboard history
"""

import threading
import time
from typing import Optional, List
from collections import deque
from dataclasses import dataclass
from datetime import datetime

# Windows clipboard access
try:
    import win32clipboard
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("[CLIPBOARD] win32clipboard not available - install pywin32")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False


@dataclass
class ClipboardItem:
    """A clipboard history item"""
    content: str
    timestamp: datetime
    source: str = "unknown"  # App it was copied from


class ClipboardMemory:
    """
    Voice-controlled clipboard history.
    Commands: save this, what did I copy, paste last copied
    """
    
    def __init__(self, perception=None, max_history: int = 20):
        print("[CLIPBOARD] Initializing Clipboard Memory...")
        self.perception = perception
        self.max_history = max_history
        
        # History storage
        self.history: deque = deque(maxlen=max_history)
        self.last_content: str = ""
        
        # Monitor thread
        self._running = False
        self._monitor_thread = None
        self._clipboard_errors = 0  # Track consecutive errors
        
        # Check availability
        self.win32_available = WIN32_AVAILABLE
        self.pyperclip_available = PYPERCLIP_AVAILABLE
        
        if WIN32_AVAILABLE or PYPERCLIP_AVAILABLE:
            self._start_monitor()
        
        print("[CLIPBOARD] Clipboard Memory Ready")
    
    def _get_title(self) -> str:
        if self.perception and hasattr(self.perception, 'current_title'):
            return self.perception.current_title
        return "sir"
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[CLIPBOARD] {text}")
    
    def _get_clipboard_content(self) -> Optional[str]:
        """Get current clipboard text content"""
        try:
            if WIN32_AVAILABLE:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                        data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        return data
                finally:
                    win32clipboard.CloseClipboard()
            elif PYPERCLIP_AVAILABLE:
                return pyperclip.paste()
        except Exception as e:
            # Only log every 20th error to prevent spam
            self._clipboard_errors = getattr(self, '_clipboard_errors', 0) + 1
            if self._clipboard_errors % 20 == 1:
                print(f"[CLIPBOARD] Read error (x{self._clipboard_errors}): {e}")
        return None
    
    def _set_clipboard_content(self, text: str) -> bool:
        """Set clipboard content"""
        try:
            if WIN32_AVAILABLE:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
                    return True
                finally:
                    win32clipboard.CloseClipboard()
            elif PYPERCLIP_AVAILABLE:
                pyperclip.copy(text)
                return True
        except Exception as e:
            print(f"[CLIPBOARD] Error setting clipboard: {e}")
        return False
    
    def _monitor_loop(self):
        """Background monitor for clipboard changes"""
        consecutive_errors = 0
        while self._running:
            try:
                content = self._get_clipboard_content()
                if content and content != self.last_content and len(content) > 0:
                    # New content detected
                    self.last_content = content
                    item = ClipboardItem(
                        content=content,
                        timestamp=datetime.now()
                    )
                    self.history.append(item)
                    print(f"[CLIPBOARD] Captured: {content[:50]}...")
                    consecutive_errors = 0
                elif content is None:
                    consecutive_errors += 1
            except Exception as e:
                consecutive_errors += 1
            
            # Backoff on repeated errors (Access denied = another process holds clipboard)
            if consecutive_errors > 5:
                time.sleep(5)  # 5s backoff
            else:
                time.sleep(2)  # Poll every 2s (was 0.5s — clipboard doesn't need sub-second polling)
    
    def _start_monitor(self):
        """Start clipboard monitoring"""
        if not self._running:
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            print("[CLIPBOARD] Monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
    
    def save_current(self) -> bool:
        """Explicitly save current clipboard content"""
        content = self._get_clipboard_content()
        if content:
            item = ClipboardItem(
                content=content,
                timestamp=datetime.now()
            )
            self.history.append(item)
            self._speak("Saved to clipboard history.")
            return True
        self._speak("Nothing on clipboard to save.")
        return False
    
    def get_last(self, n: int = 1) -> List[ClipboardItem]:
        """Get last n clipboard items"""
        items = list(self.history)
        return items[-n:] if items else []
    
    def get_history(self, count: int = 5) -> List[ClipboardItem]:
        """Get clipboard history"""
        items = list(self.history)
        return items[-count:][::-1]  # Most recent first
    
    def read_last(self) -> str:
        """Read the last copied item"""
        items = self.get_last(1)
        if items:
            content = items[0].content
            # Truncate for speech
            if len(content) > 100:
                return content[:100] + "..."
            return content
        return ""
    
    def paste_last(self, n: int = 1) -> bool:
        """Paste the nth last item"""
        items = self.get_last(n)
        if items:
            # Paste the oldest of the requested items
            item = items[0]
            self._set_clipboard_content(item.content)
            
            # Simulate Ctrl+V
            try:
                import pyautogui
                pyautogui.hotkey('ctrl', 'v')
                self._speak("Pasted.")
                return True
            except ImportError:
                self._speak("Content copied to clipboard. Please paste manually.")
                return True
        
        self._speak("No clipboard history available.")
        return False
    
    def search_history(self, query: str) -> List[ClipboardItem]:
        """Search clipboard history"""
        query_lower = query.lower()
        return [item for item in self.history if query_lower in item.content.lower()]
    
    def clear_history(self):
        """Clear clipboard history"""
        self.history.clear()
        self._speak("Clipboard history cleared.")
    
    def handle(self, command: str) -> str:
        """Handle clipboard commands"""
        command_lower = command.lower()
        title = self._get_title()
        
        # Save current
        if "save this" in command_lower or "save clipboard" in command_lower:
            self.save_current()
            return "Saved to clipboard history."
        
        # Read last copied
        if "what did i copy" in command_lower or "last copied" in command_lower or "clipboard" in command_lower:
            content = self.read_last()
            if content:
                self._speak(f"You last copied: {content}")
                return f"Last copied: {content}"
            return "Clipboard history is empty."
        
        # Paste last
        if "paste" in command_lower:
            # Extract which one to paste
            if "second last" in command_lower or "previous" in command_lower:
                self.paste_last(2)
                return "Pasted second last item."
            elif "third" in command_lower:
                self.paste_last(3)
                return "Pasted third last item."
            else:
                self.paste_last(1)
                return "Pasted last copied item."
        
        # Clipboard history
        if "clipboard history" in command_lower or "copy history" in command_lower:
            items = self.get_history(5)
            if items:
                response = f"Your last {len(items)} copied items: "
                for i, item in enumerate(items, 1):
                    preview = item.content[:30] + "..." if len(item.content) > 30 else item.content
                    response += f"{i}. {preview}. "
                self._speak(response)
                return response
            return "Clipboard history is empty."
        
        # Clear history
        if "clear clipboard" in command_lower or "clear history" in command_lower:
            self.clear_history()
            return "Clipboard history cleared."
        
        return "I didn't understand that clipboard command."


# Singleton
_clipboard_instance = None

def get_clipboard_memory(perception=None) -> ClipboardMemory:
    """Get or create clipboard memory"""
    global _clipboard_instance
    if _clipboard_instance is None:
        _clipboard_instance = ClipboardMemory(perception)
    return _clipboard_instance
