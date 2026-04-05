"""
Action Layer - Command Execution
Handles: Opening apps, time/date, jokes, web search, browser control, YouTube
"""

import os
import webbrowser
from datetime import datetime
import random
import subprocess
import time
import urllib.parse

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class ActionLayer:
    """Executes actions based on intent"""

    def __init__(self, perception):
        print("[ACTION] Initializing Action Layer...")
        self.perception = perception

        username = os.getenv("USERNAME")

        # Comprehensive app paths
        self.app_paths = {
            # Browsers
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            
            # Productivity
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "files": "explorer.exe",
            
            # Development
            "code": rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "vs code": rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "vscode": rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            
            # Microsoft Office
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            
            # Entertainment
            "spotify": rf"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
            
            # Communication - Desktop apps
            "whatsapp": rf"C:\Users\{username}\AppData\Local\WhatsApp\WhatsApp.exe",
            
            # System
            "settings": "ms-settings:",
            "control panel": "control.exe",
            "task manager": "taskmgr.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "paint": "mspaint.exe",
            "alarm": "ms-clock:",  # Windows Alarms app
            "clock": "ms-clock:",
            
            # Special apps with custom paths
            "perplexity": rf"C:\Users\{username}\AppData\Local\Programs\Perplexity\Perplexity.exe",
            
            # Messages
            "messages": rf"C:\Users\{username}\AppData\Local\WhatsApp\WhatsApp.exe",
        }
        
        # Web-based apps (open in browser if no desktop app)
        self.web_apps = {
            "youtube": "https://youtube.com",
            "whatsapp": "https://web.whatsapp.com",
            "chatgpt": "https://chat.openai.com",
            "perplexity": "https://perplexity.ai",
            "github": "https://github.com",
            "gmail": "https://mail.google.com",
            "google": "https://google.com",
            "twitter": "https://twitter.com",
            "x": "https://twitter.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "linkedin": "https://linkedin.com",
            "reddit": "https://reddit.com",
            "netflix": "https://netflix.com",
            "amazon": "https://amazon.in",
            "messages": "https://web.whatsapp.com",
        }

        # More jokes variety
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "Why did the developer go broke? Because he used up all his cache.",
            "A SQL query walks into a bar and asks: Can I join you?",
            "There are 10 types of people: those who understand binary and those who don't.",
            "Why do Java developers wear glasses? Because they don't C sharp.",
            "What's a programmer's favorite hangout place? Foo Bar.",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "A programmer's wife tells him: Go to the store and get a loaf of bread. If they have eggs, get a dozen. He returns with 12 loaves of bread.",
            "Why do Python programmers have low self-esteem? They're constantly told they have significant whitespace issues.",
            "What's a computer's least favorite food? Spam.",
            "Why did the programmer quit his job? Because he didn't get arrays.",
            "There's no place like 127.0.0.1.",
            "Why do programmers always mix up Halloween and Christmas? Because Oct 31 equals Dec 25.",
            "What do you call 8 hobbits? A hobbyte.",
        ]
        
        self.joke_index = 0

        print("[ACTION] Layer Ready")

    def execute(self, intent, entities, raw_text):
        """Central dispatcher - executes action based on intent"""
        
        # Get user title from perception layer
        title = getattr(self.perception, 'user_title', 'sir')
        
        if intent == "time":
            return self.get_time(title)

        if intent == "date":
            return self.get_date(title)

        if intent == "joke":
            return self.tell_joke(title)

        if intent == "open_app":
            apps = entities.get("apps", [])
            if apps:
                return self.open_app(apps[0], title)
            app_name = self._extract_app_name(raw_text)
            if app_name:
                return self.open_app(app_name, title)
            self.perception.speak(f"Which application should I open, {title}?")
            return False

        if intent == "search":
            return self.search_web(raw_text, title)
        
        if intent == "youtube_search":
            return self.youtube_search(raw_text, title)
        
        if intent == "new_tab":
            return self.new_tab(title)
        
        if intent == "close_tab":
            return self.close_tab(title)
        
        if intent == "greeting":
            self.perception.speak(f"Hello {title}, how may I assist you?")
            return True
        
        if intent == "thank":
            self.perception.speak(f"You are welcome, {title}.")
            return True

        return False
    
    def _extract_app_name(self, text):
        """Extract app name from raw text"""
        text = text.lower()
        for prefix in ["open", "launch", "start", "run"]:
            text = text.replace(prefix, "")
        text = text.strip()
        
        for app in list(self.app_paths.keys()) + list(self.web_apps.keys()):
            if app in text:
                return app
        
        return text if text else None

    def get_time(self, title="sir"):
        now = datetime.now().strftime("%I:%M %p")
        self.perception.speak(f"The time is {now}, {title}.")
        return True

    def get_date(self, title="sir"):
        today = datetime.now().strftime("%A, %B %d, %Y")
        self.perception.speak(f"Today is {today}, {title}.")
        return True

    def tell_joke(self, title="sir"):
        """Tell a joke without repeating"""
        if self.joke_index >= len(self.jokes):
            random.shuffle(self.jokes)
            self.joke_index = 0
        
        joke = self.jokes[self.joke_index]
        self.joke_index += 1
        self.perception.speak(f"{joke}, {title}.")
        return True

    def open_app(self, app_name, title="sir"):
        """Open an application - tries desktop app first, then web"""
        app_name = app_name.lower().strip()
        
        # Handle common misrecognitions
        app_name = app_name.replace("what's app", "whatsapp")
        app_name = app_name.replace("whats app", "whatsapp")
        
        print(f"[ACTION] Attempting to open: {app_name}")

        try:
            # Check desktop apps first
            if app_name in self.app_paths:
                path = self.app_paths[app_name]
                
                # Handle special URIs (ms-settings:, etc.)
                if path.startswith("ms-") or path.startswith("http"):
                    os.startfile(path)
                    self.perception.speak(f"Opening {app_name}, {title}.")
                    return True
                
                # For simple system commands like calc.exe, notepad.exe - try directly first
                if path.endswith(".exe") and not os.path.sep in path:
                    try:
                        subprocess.Popen(path, shell=True)
                        self.perception.speak(f"Opening {app_name}, {title}.")
                        return True
                    except Exception as e:
                        print(f"[ACTION] Direct command failed: {e}")
                
                # Check if full path file exists
                if os.path.exists(path):
                    subprocess.Popen(path, shell=True)
                    self.perception.speak(f"Opening {app_name}, {title}.")
                    return True
            
            # Check web apps
            if app_name in self.web_apps:
                url = self.web_apps[app_name]
                webbrowser.open(url)
                self.perception.speak(f"Opening {app_name} in browser, {title}.")
                return True
            
            # Try as system command (for apps in PATH)
            try:
                os.startfile(app_name)
                self.perception.speak(f"Opening {app_name}, {title}.")
                return True
            except:
                pass
            
            # App not found - search for it online
            self.perception.speak(f"{title}, it seems you don't have {app_name} installed. Let me search for it online.")
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(app_name)}+download"
            webbrowser.open(search_url)
            return True

        except Exception as e:
            print(f"ERROR: Open app error: {e}")
            self.perception.speak(f"I could not open {app_name}, {title}.")
            return False

    def search_web(self, text, title="sir", browser=None):
        """Search the web"""
        query = text.lower()
        for word in ["search", "search for", "google", "look up", "find", "in brave", "in chrome", "in edge"]:
            query = query.replace(word, "")
        query = query.strip()

        if not query:
            self.perception.speak(f"What should I search for, {title}?")
            return False

        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        if "brave" in text.lower():
            self._open_url_in_browser(url, "brave")
        elif "chrome" in text.lower():
            self._open_url_in_browser(url, "chrome")
        elif "edge" in text.lower():
            self._open_url_in_browser(url, "edge")
        else:
            webbrowser.open(url)
        
        self.perception.speak(f"Searching for {query}, {title}.")
        return True
    
    def youtube_search(self, text, title="sir"):
        """Search on YouTube"""
        query = text.lower()
        for word in ["youtube", "search", "for", "on", "videos", "video", "play"]:
            query = query.replace(word, "")
        query = query.strip()
        
        if not query:
            # Just open YouTube
            webbrowser.open("https://youtube.com")
            self.perception.speak(f"Opening YouTube, {title}.")
            return True
        
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)
        self.perception.speak(f"Searching YouTube for {query}, {title}.")
        return True
    
    def _open_url_in_browser(self, url, browser):
        """Open URL in specific browser"""
        if browser in self.app_paths:
            path = self.app_paths[browser]
            if os.path.exists(path):
                subprocess.Popen([path, url])
                return True
        webbrowser.open(url)
        return True
    
    def new_tab(self, title="sir"):
        """Open a new browser tab"""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey('ctrl', 't')
            self.perception.speak(f"New tab opened, {title}.")
            return True
        else:
            self.perception.speak(f"Tab control requires pyautogui, {title}.")
            return False
    
    def close_tab(self, title="sir"):
        """Close current browser tab"""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey('ctrl', 'w')
            self.perception.speak(f"Tab closed, {title}.")
            return True
        else:
            self.perception.speak(f"Tab control requires pyautogui, {title}.")
            return False
