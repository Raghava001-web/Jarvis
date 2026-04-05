"""
Clipboard Intelligence — Monitors clipboard for context-aware actions.
When user copies text, JARVIS can:
1. Auto-detect language and offer translation
2. Summarize long text
3. Detect URLs and offer to open/preview
4. Detect code and offer to explain
5. Detect phone numbers/emails and offer to call/message
"""

import threading
import time
import re
from typing import Optional, Callable


class ClipboardIntelligence:
    """Monitors clipboard and provides intelligent context actions."""

    def __init__(self, perception=None, on_suggestion: Optional[Callable] = None):
        print("[CLIPBOARD] Initializing Clipboard Intelligence...")
        self.perception = perception
        self.on_suggestion = on_suggestion  # Callback to push suggestion to HUD
        
        self._last_text = ""
        self._running = False
        self._thread = None
        self._cooldown = 5  # Seconds between processing same content
        self._last_process_time = 0
        
        try:
            import pyperclip
            self._pyperclip = pyperclip
        except ImportError:
            self._pyperclip = None
            print("[CLIPBOARD] pyperclip not available")
        
        print("[CLIPBOARD] Ready")

    def start(self):
        """Start monitoring clipboard in background."""
        if self._running or not self._pyperclip:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ClipboardMonitor"
        )
        self._thread.start()
        print("[CLIPBOARD] Monitoring started")

    def stop(self):
        """Stop clipboard monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[CLIPBOARD] Monitoring stopped")

    def _monitor_loop(self):
        """Background loop checking clipboard every 2 seconds."""
        while self._running:
            try:
                current = self._pyperclip.paste()
                
                if (current 
                    and current != self._last_text 
                    and len(current.strip()) > 10
                    and time.time() - self._last_process_time > self._cooldown):
                    
                    self._last_text = current
                    self._last_process_time = time.time()
                    
                    suggestion = self._analyze(current)
                    if suggestion:
                        self._push_suggestion(suggestion)
                
            except Exception:
                pass  # Clipboard may be locked by another app
            
            time.sleep(2)

    def _analyze(self, text: str) -> Optional[dict]:
        """Analyze clipboard content and generate a suggestion."""
        text = text.strip()
        
        # 1. URL detection (skip internal/localhost URLs)
        url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
        if url_match and len(text) < 500:
            url = url_match.group()
            # Skip localhost, internal, and JARVIS own URLs
            if any(skip in url for skip in ['localhost', '127.0.0.1', '0.0.0.0', 'ws://']):
                return None
            return {
                "type": "url",
                "content": url,
                "suggestion": f"You copied a link. Want me to open it?",
                "action": "open_url"
            }
        
        # 2. Long text → offer summarization
        word_count = len(text.split())
        if word_count > 100:
            return {
                "type": "long_text",
                "content": text[:200] + "...",
                "word_count": word_count,
                "suggestion": f"You copied {word_count} words. Want me to summarize it?",
                "action": "summarize"
            }
        
        # 3. Code detection (common patterns)
        code_indicators = ['def ', 'function ', 'class ', 'import ', 'const ', 'var ',
                          'return ', 'if (', 'for (', '<?php', '<html', '#!/']
        if any(ind in text for ind in code_indicators):
            return {
                "type": "code",
                "content": text[:200],
                "suggestion": "You copied some code. Want me to explain it?",
                "action": "explain_code"
            }
        
        # 4. Email detection
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        if email_match and len(text) < 200:
            return {
                "type": "email",
                "content": email_match.group(),
                "suggestion": f"You copied an email: {email_match.group()}. Want me to compose a message?",
                "action": "compose_email"
            }
        
        # 5. Phone number detection
        phone_match = re.search(r'[\+]?[0-9]{10,13}', text.replace(' ', '').replace('-', ''))
        if phone_match and len(text) < 50:
            return {
                "type": "phone",
                "content": phone_match.group(),
                "suggestion": f"You copied a phone number. Want me to save it?",
                "action": "save_contact"
            }
        
        # 6. Error/traceback detection
        if 'Traceback' in text or 'Error:' in text or 'Exception' in text:
            return {
                "type": "error",
                "content": text[:300],
                "suggestion": "You copied an error. Want me to help debug it?",
                "action": "debug_error"
            }
        
        return None

    def _push_suggestion(self, suggestion: dict):
        """Push suggestion to HUD silently (don't speak — avoid interrupting user)."""
        msg = suggestion.get("suggestion", "")
        
        if self.on_suggestion:
            self.on_suggestion(suggestion)
        
        # Don't speak — just log and push to HUD
        print(f"[CLIPBOARD] Suggestion: {msg}")
        if suggestion.get("content"):
            content_preview = str(suggestion["content"])[:60]
            print(f"[CLIPBOARD] Captured: {content_preview}...")

    def process_action(self, action: str, content: str) -> str:
        """Process a clipboard action (called when user accepts suggestion)."""
        if action == "open_url":
            import webbrowser
            webbrowser.open(content)
            return f"Opening {content[:50]}..."
        
        elif action == "summarize":
            # Use knowledge layer if available
            return f"Clipboard text ({len(content.split())} words) ready for summarization."
        
        elif action == "explain_code":
            return "Code explanation ready."
        
        elif action == "compose_email":
            return f"Ready to compose email to {content}."
        
        elif action == "debug_error":
            return "Error analysis ready."
        
        return "Action not recognized."
