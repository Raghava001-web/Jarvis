"""
App Switcher - Hands-Free Window Control
========================================
- List running windows
- Switch to specific apps  
- Track most recently used apps (MRU)
- Minimize/maximize/close windows
"""

import time
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from collections import deque

# Windows-specific imports
try:
    import win32gui
    import win32con
    import win32process
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("[APP_SWITCHER] win32gui not available - install pywin32")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


@dataclass
class WindowInfo:
    """Information about a window"""
    hwnd: int
    title: str
    process_name: str
    is_visible: bool = True
    is_minimized: bool = False


class AppSwitcher:
    """
    Voice-controlled window switching.
    Commands: switch to X, switch back, list windows, close X
    """
    
    # App name aliases for common apps
    APP_ALIASES = {
        "chrome": ["google chrome", "chrome"],
        "firefox": ["mozilla firefox", "firefox"],
        "edge": ["microsoft edge", "edge"],
        "spotify": ["spotify"],
        "vscode": ["visual studio code", "vs code", "code"],
        "notepad": ["notepad", "untitled - notepad"],
        "explorer": ["file explorer", "explorer"],
        "terminal": ["windows terminal", "powershell", "cmd"],
        "discord": ["discord"],
        "slack": ["slack"],
        "teams": ["microsoft teams", "teams"],
        "word": ["microsoft word", "word"],
        "excel": ["microsoft excel", "excel"],
        "powerpoint": ["microsoft powerpoint", "powerpoint"],
        # Added for JARVIS
        "whatsapp": ["whatsapp"],
        "perplexity": ["perplexity"],
        "youtube": ["youtube", "youtube.com"],
        "chatgpt": ["chatgpt", "chat.openai"],
        "settings": ["settings"],
        "task manager": ["task manager", "taskmgr"],
        "calculator": ["calculator", "calc"],
    }
    
    def __init__(self, perception=None, max_history: int = 10):
        print("[APP_SWITCHER] Initializing App Switcher...")
        self.perception = perception
        self.max_history = max_history
        
        # MRU tracking
        self.app_history: deque = deque(maxlen=max_history)
        self.active_app: Optional[str] = None
        self.active_hwnd: Optional[int] = None
        
        self.win32_available = WIN32_AVAILABLE
        
        if WIN32_AVAILABLE:
            # Track initial focused window
            self._update_active_window()
        
        print("[APP_SWITCHER] App Switcher Ready")
    
    def _get_title(self) -> str:
        """Get user title"""
        if self.perception and hasattr(self.perception, 'current_title'):
            return self.perception.current_title
        return "sir"
    
    def _speak(self, text: str):
        """Speak via perception"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[APP_SWITCHER] {text}")
    
    def _update_active_window(self):
        """Update the currently active window"""
        if not WIN32_AVAILABLE:
            return
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                if title:
                    # Add to history if different from last
                    if not self.app_history or self.app_history[-1] != title:
                        self.app_history.append(title)
                    self.active_app = title
                    self.active_hwnd = hwnd
        except Exception as e:
            print(f"[APP_SWITCHER] Error getting active window: {e}")
    
    def get_windows(self) -> List[WindowInfo]:
        """Get list of all visible windows"""
        if not WIN32_AVAILABLE:
            return []
        
        windows = []
        
        def enum_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 1:  # Skip empty/single char titles
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except:
                        process_name = "unknown"
                    
                    is_minimized = win32gui.IsIconic(hwnd)
                    
                    windows.append(WindowInfo(
                        hwnd=hwnd,
                        title=title,
                        process_name=process_name,
                        is_visible=True,
                        is_minimized=is_minimized
                    ))
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, windows)
        except Exception as e:
            print(f"[APP_SWITCHER] Error enumerating windows: {e}")
        
        return windows
    
    def find_window(self, query: str) -> Optional[WindowInfo]:
        """Find a window matching the query"""
        query_lower = query.lower().strip()
        windows = self.get_windows()
        
        best_match = None
        best_score = 0
        
        for window in windows:
            title_lower = window.title.lower()
            process_lower = window.process_name.lower()
            
            # Exact title match
            if query_lower == title_lower:
                return window
            
            # Check aliases
            for app_key, aliases in self.APP_ALIASES.items():
                if query_lower in aliases or query_lower == app_key:
                    for alias in aliases:
                        if alias in title_lower or alias in process_lower:
                            return window
            
            # Partial match scoring
            score = 0
            if query_lower in title_lower:
                score = len(query_lower) / len(title_lower) * 100
            elif query_lower in process_lower:
                score = len(query_lower) / len(process_lower) * 80
            
            if score > best_score:
                best_score = score
                best_match = window
        
        return best_match if best_score > 30 else None
    
    def switch_to(self, app_name: str) -> bool:
        """Switch to a specific app/window"""
        if not WIN32_AVAILABLE:
            self._speak("Window switching not available.")
            return False
        
        title = self._get_title()
        window = self.find_window(app_name)
        
        if not window:
            self._speak(f"I couldn't find {app_name}, {title}.")
            return False
        
        try:
            hwnd = window.hwnd
            
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            
            self._update_active_window()
            self._speak(f"Switched to {app_name}.")
            return True
            
        except Exception as e:
            print(f"[APP_SWITCHER] Error switching: {e}")
            self._speak(f"Couldn't switch to {app_name}, {title}.")
            return False
    
    def switch_back(self) -> bool:
        """Switch to the previous app"""
        if len(self.app_history) < 2:
            self._speak("No previous window to switch back to.")
            return False
        
        # Get second-to-last window
        previous = list(self.app_history)[-2]
        return self.switch_to(previous)
    
    def minimize_current(self) -> bool:
        """Minimize the current window"""
        if not WIN32_AVAILABLE:
            return False
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            self._speak("Minimized.")
            return True
        except Exception as e:
            print(f"[APP_SWITCHER] Error minimizing: {e}")
            return False
    
    def maximize_current(self) -> bool:
        """Maximize the current window"""
        if not WIN32_AVAILABLE:
            return False
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            self._speak("Maximized.")
            return True
        except Exception as e:
            print(f"[APP_SWITCHER] Error maximizing: {e}")
            return False
    
    def close_app(self, app_name: str) -> bool:
        """Close a specific app/window"""
        if not WIN32_AVAILABLE:
            return False
        
        window = self.find_window(app_name)
        if not window:
            self._speak(f"Couldn't find {app_name}.")
            return False
        
        try:
            win32gui.PostMessage(window.hwnd, win32con.WM_CLOSE, 0, 0)
            self._speak(f"Closing {app_name}.")
            return True
        except Exception as e:
            print(f"[APP_SWITCHER] Error closing: {e}")
            return False
    
    def list_windows(self) -> List[str]:
        """Get list of window names"""
        windows = self.get_windows()
        return [w.title for w in windows[:10]]  # Top 10
    
    def handle(self, command: str) -> str:
        """Handle app switching commands"""
        command_lower = command.lower()
        
        # Switch back
        if "switch back" in command_lower or "go back" in command_lower:
            success = self.switch_back()
            return "Switched back." if success else "No previous window."
        
        # Switch to specific app
        if "switch to" in command_lower:
            app_name = command_lower.split("switch to")[-1].strip()
            success = self.switch_to(app_name)
            return f"Switched to {app_name}." if success else f"Couldn't find {app_name}."
        
        # Focus specific app
        if "focus" in command_lower:
            app_name = command_lower.split("focus")[-1].strip()
            if app_name:
                success = self.switch_to(app_name)
                return f"Focused {app_name}." if success else f"Couldn't find {app_name}."
        
        # Close app
        if "close" in command_lower:
            # Extract app name
            for keyword in ["close", "quit", "exit"]:
                if keyword in command_lower:
                    app_name = command_lower.split(keyword)[-1].strip()
                    if app_name and app_name not in ["window", "this", "it", ""]:
                        success = self.close_app(app_name)
                        return f"Closed {app_name}." if success else f"Couldn't close {app_name}."
        
        # List windows
        if "list windows" in command_lower or "what's open" in command_lower or "running apps" in command_lower:
            windows = self.list_windows()
            if windows:
                return f"Open windows: {', '.join(windows[:5])}"
            return "No windows found."
        
        return "I didn't understand that window command."
    
    def get_active_app(self) -> Optional[str]:
        """Get the currently active app name"""
        self._update_active_window()
        return self.active_app
    
    def get_last_apps(self, count: int = 5) -> List[str]:
        """Get recently used apps"""
        return list(self.app_history)[-count:]


# Singleton instance
_switcher_instance = None

def get_app_switcher(perception=None) -> AppSwitcher:
    """Get or create app switcher instance"""
    global _switcher_instance
    if _switcher_instance is None:
        _switcher_instance = AppSwitcher(perception)
    return _switcher_instance
