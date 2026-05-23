"""
WhatsApp Handler - Send messages via WhatsApp Desktop App
Uses pyautogui to automate: open app -> search contact -> type message -> send

Fixes applied:
- Window verification via pygetwindow (no blind time.sleep)
- Ctrl+F search (works on all WhatsApp versions, not Ctrl+N)
- _ensure_whatsapp_focused() replaces broken whatsapp_open flag
- Clipboard paste with verification delay
- Relaunch only when not already running
"""

import time
import subprocess
import os

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False


class WhatsAppHandler:
    """Handles WhatsApp messaging via Desktop app automation"""

    def __init__(self, perception):
        print("[WHATSAPP] Initializing WhatsApp Handler...")
        self.perception = perception
        print("[WHATSAPP] Handler Ready")
    
    # m-01: Missing _speak method — routes to perception
    def _speak(self, text: str):
        """Speak via perception layer"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[WHATSAPP] {text}")

    def _get_title(self):
        return getattr(self.perception, 'user_title', 'sir')

    def _paste_text(self, text: str, delay: float = 0.3):
        """Copy text to clipboard and paste with verification delay.
        
        Unlike the old _type_text, this waits after the paste to ensure
        the clipboard content is fully inserted before continuing.
        """
        if PYPERCLIP_AVAILABLE:
            pyperclip.copy(text)
            time.sleep(0.1)  # Let clipboard settle
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(delay)  # Wait for paste to complete
        else:
            pyautogui.write(text, interval=0.02)
            time.sleep(0.2)

    def _ensure_whatsapp_focused(self) -> bool:
        """Bring WhatsApp to foreground, launch if not running.
        
        Replaces the broken open_whatsapp() + whatsapp_open flag:
        - Checks if WhatsApp is already open via pygetwindow
        - If yes, restores and activates (no relaunch)
        - If no, launches and waits for window to actually appear (max 10s)
        - Returns True only when WhatsApp window is confirmed visible
        """
        # Method 1: Use pygetwindow to detect existing window
        if PYGETWINDOW_AVAILABLE:
            windows = gw.getWindowsWithTitle('WhatsApp')
            if windows:
                try:
                    win = windows[0]
                    if win.isMinimized:
                        win.restore()
                    win.activate()
                    time.sleep(0.5)
                    print("[WHATSAPP] Already open — brought to focus")
                    return True
                except Exception:
                    pass  # Window handle stale, will try relaunch
        
        # Method 2: Launch WhatsApp
        launched = False
        try:
            subprocess.Popen(
                ['cmd', '/c', 'start', 'whatsapp:'],
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            launched = True
        except Exception:
            # Fallback: try direct exe paths
            whatsapp_paths = [
                os.path.expandvars(r'%LOCALAPPDATA%\WhatsApp\WhatsApp.exe'),
                os.path.expandvars(r'%LOCALAPPDATA%\Programs\whatsapp-desktop\WhatsApp.exe'),
            ]
            for path in whatsapp_paths:
                if os.path.exists(path):
                    subprocess.Popen([path])
                    launched = True
                    break
        
        if not launched:
            return False
        
        # Wait for the window to actually appear (max 10 seconds)
        if PYGETWINDOW_AVAILABLE:
            for _ in range(20):
                time.sleep(0.5)
                windows = gw.getWindowsWithTitle('WhatsApp')
                if windows:
                    time.sleep(1.5)  # Let UI fully render
                    try:
                        windows[0].activate()
                    except Exception:
                        pass
                    print("[WHATSAPP] Launched and window confirmed")
                    return True
            print("[WHATSAPP] Window never appeared after launch")
            return False
        else:
            # No pygetwindow — fall back to blind wait (best effort)
            time.sleep(4)
            print("[WHATSAPP] Launched (no window verification available)")
            return True

    def open_whatsapp(self) -> str:
        """Open WhatsApp Desktop app (public API, used by intent handlers)"""
        title = self._get_title()
        
        if self._ensure_whatsapp_focused():
            return f"Opening WhatsApp, {title}."
        
        # Final fallback: WhatsApp Web
        import webbrowser
        webbrowser.open("https://web.whatsapp.com")
        return f"WhatsApp Desktop not found. Opening WhatsApp Web instead, {title}."

    def send_message(self, contact_name: str = None, message: str = None) -> str:
        """Send a message to a contact via WhatsApp Desktop.
        
        Flow: ensure focused -> Ctrl+F search -> type contact -> select -> type msg -> enter
        Uses Ctrl+F (universal) instead of Ctrl+N (version-dependent).
        """
        title = self._get_title()
        
        if not contact_name:
            return f"Who should I send the message to, {title}?"
        
        if not message:
            return f"What message should I send to {contact_name}, {title}?"
        
        if not PYAUTOGUI_AVAILABLE:
            return f"Screen automation not available, {title}. Install pyautogui."
        
        try:
            # Step 1: Ensure WhatsApp is open and focused
            if not self._ensure_whatsapp_focused():
                return f"Could not open WhatsApp, {title}."
            
            # Step 2: Open search (Ctrl+F works on ALL versions)
            # Unlike Ctrl+N which was removed in Beta, Ctrl+F is universal
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.8)
            
            # Step 3: Clear search box and type contact name
            pyautogui.hotkey('ctrl', 'a')  # Select all existing text
            time.sleep(0.1)
            self._paste_text(contact_name, delay=1.5)  # Extra delay for search results
            
            # Step 4: Wait for results to load, then select first contact
            time.sleep(2.0)  # Network-dependent search
            pyautogui.press('down')
            time.sleep(0.3)
            # M-03: Auto-press Enter to confirm contact (was asking user to do it)
            pyautogui.press('enter')
            time.sleep(1.0)  # Wait for chat to open
            
            # Step 5: Type and send message
            self._paste_text(message, delay=0.5)
            # M-03: Auto-press Enter to send (was asking user to do it)
            pyautogui.press('enter')
            time.sleep(0.3)
            
            print(f"[WHATSAPP] Message sent to {contact_name}: {message[:50]}...")
            return f"Message sent to {contact_name}, {title}."
            
        except Exception as e:
            print(f"[WHATSAPP] Error: {e}")
            return f"Couldn't send message to {contact_name}, {title}. Error: {str(e)[:50]}"

    def read_messages(self) -> str:
        """Open WhatsApp to view messages"""
        title = self._get_title()
        self.open_whatsapp()
        return f"Opening WhatsApp so you can view your messages, {title}."
