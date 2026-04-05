"""
WhatsApp Handler - Send messages via WhatsApp Desktop App
Uses pyautogui to automate: open app -> search contact -> type message -> send
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


class WhatsAppHandler:
    """Handles WhatsApp messaging via Desktop app automation"""

    def __init__(self, perception):
        print("[WHATSAPP] Initializing WhatsApp Handler...")
        self.perception = perception
        self.whatsapp_open = False
        print("[WHATSAPP] Handler Ready")

    def _get_title(self):
        return getattr(self.perception, 'user_title', 'sir')

    def _type_text(self, text: str):
        """Type text using clipboard (supports Unicode) or fallback"""
        if PYPERCLIP_AVAILABLE:
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(text, interval=0.02)

    def open_whatsapp(self) -> str:
        """Open WhatsApp Desktop app"""
        title = self._get_title()
        
        try:
            # Try to open WhatsApp Desktop via Windows start menu
            subprocess.Popen(['cmd', '/c', 'start', 'whatsapp:'], 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.whatsapp_open = True
            time.sleep(3)
            return f"Opening WhatsApp, {title}."
        except Exception as e:
            # Fallback: try finding WhatsApp.exe
            try:
                whatsapp_paths = [
                    os.path.expandvars(r'%LOCALAPPDATA%\WhatsApp\WhatsApp.exe'),
                    os.path.expandvars(r'%LOCALAPPDATA%\Programs\whatsapp-desktop\WhatsApp.exe'),
                ]
                for path in whatsapp_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        self.whatsapp_open = True
                        time.sleep(3)
                        return f"Opening WhatsApp, {title}."
            except:
                pass
            
            # Final fallback: WhatsApp Web
            import webbrowser
            webbrowser.open("https://web.whatsapp.com")
            self.whatsapp_open = True
            return f"WhatsApp Desktop not found. Opening WhatsApp Web instead, {title}."

    def send_message(self, contact_name: str = None, message: str = None) -> str:
        """Send a message to a contact via WhatsApp Desktop"""
        title = self._get_title()
        
        if not contact_name:
            return f"Who should I send the message to, {title}?"
        
        if not message:
            return f"What message should I send to {contact_name}, {title}?"
        
        if not PYAUTOGUI_AVAILABLE:
            return f"Screen automation not available, {title}. Install pyautogui."
        
        try:
            # Step 1: Open WhatsApp Desktop
            self.open_whatsapp()
            time.sleep(1.5)  # Give it time to load and steal focus
            
            # Step 2: Open "New Chat" Modal (Bypasses Beta Search Chips)
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1.0)
            
            # Step 3: Type contact name in the New Chat search bar
            self._type_text(contact_name)
            time.sleep(2.0)  # Wait for search results
            
            # Step 4: Select the first contact and open chat
            # 'Down' arrow shifts focus from the input box to the first search result
            pyautogui.press('down')
            time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(1.0)  # Wait for chat to open and message box to gain focus
            
            # Step 5: Type and send message
            self._type_text(message)
            time.sleep(0.2)
            pyautogui.press('enter')
            
            print(f"[WHATSAPP] Message sent to {contact_name}: {message[:50]}...")
            return f"Message sent to {contact_name}, {title}."
            
        except Exception as e:
            print(f"[WHATSAPP] Error: {e}")
            return f"Couldn't send message to {contact_name}, {title}. Error: {str(e)[:50]}"

    def read_messages(self) -> str:
        """Open WhatsApp to view messages"""
        title = self._get_title()
        result = self.open_whatsapp()
        return f"Opening WhatsApp so you can view your messages, {title}."
