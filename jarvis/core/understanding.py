"""
Understanding Layer - Intent Classification with Confidence
Extended intents for JARVIS
"""

import re
import numpy as np

# BUG FIX: Top-level import crashes JARVIS if sentence-transformers not installed
# Wrap in try/except so the module can still load with reduced functionality
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[UNDERSTANDING] sentence-transformers not installed — install with: pip install sentence-transformers")


class UnderstandingLayer:
    """Classifies user intent with confidence threshold"""

    CONFIDENCE_THRESHOLD = 0.25  # Lowered for better recognition
    MARGIN_THRESHOLD = 0.05  # difference between top 2 intents

    def __init__(self):
        print("[UNDERSTANDING] Loading Understanding Layer...")
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("[UNDERSTANDING] WARNING: Running without ML model — classification disabled")
            self.model = None
            self.intent_embeddings = {}
            print("[UNDERSTANDING] Layer Ready (degraded)")
            return
            
        from jarvis.core.shared_embeddings import get_shared_embedding_model
        self.model = get_shared_embedding_model("all-MiniLM-L6-v2")

        self.intents = {
            # Basic
            "open_app": [
                "open chrome", "launch notepad", "start calculator",
                "open whatsapp", "open brave", "start spotify",
                "open vs code", "start code editor", "open edge",
                "open file explorer", "open files", "launch youtube",
                "open chatgpt", "open perplexity", "open settings"
            ],
            "time": ["what time", "current time", "time now", "tell me the time"],
            "date": ["what date", "today date", "what day is it", "tell me the date"],
            "joke": ["tell joke", "make me laugh", "say something funny", "tell me a joke"],
            "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
            "thank": ["thank you", "thanks", "appreciate it"],
            "exit": ["exit", "quit", "goodbye", "stop", "bye"],
            
            # Search
            "search": [
                "search for", "google", "find information", "look up",
                "search in brave", "search in chrome", "web search"
            ],
            
            # Questions (for LLM)
            "question": [
                "what is", "who is", "how to", "explain", "define",
                "what does", "how does", "describe", "tell me about",
                "why is", "when was", "where is", "can you explain"
            ],
            
            # Alarms & Reminders - MORE training phrases for better matching
            "set_alarm": [
                "set alarm", "set an alarm", "alarm in", "alarm for", "alarm at",
                "wake me up", "set timer", "timer for", "set alarm for",
                "alarm after", "create alarm", "make an alarm", "put an alarm",
                "remind me at", "wake me at", "alarm 5 minutes", "alarm 10 minutes",
                "set alarm 7", "alarm for 8", "alarm at 9", "alarm for 11"
            ],
            "list_alarms": ["list alarms", "show alarms", "my alarms", "pending alarms", "alarm list", "what alarms"],
            "cancel_alarm": ["cancel alarm", "delete alarm", "remove alarm", "turn off alarm", "cancel the alarm"],
            "snooze_alarm": ["snooze", "snooze alarm", "5 more minutes", "snooze it", "later alarm", "stop alarm"],
            
            # Tasks
            "task": ["add task", "create task", "new task", "task"],
            "reminder": ["remind me", "set reminder", "reminder"],
            "list_tasks": ["list tasks", "show tasks", "my tasks", "pending tasks"],
            
            # News
            "news": [
                "news", "headlines", "headline", "news today",
                "top news", "latest news", "sports news", "tech news"
            ],
            
            # System Control
            "volume_up": ["volume up", "increase volume", "louder", "turn up volume"],
            "volume_down": ["volume down", "decrease volume", "quieter", "turn down volume"],
            "set_volume": ["set volume to", "volume to", "volume at"],
            "mute": ["mute", "mute volume", "unmute", "toggle mute"],
            
            "brightness_up": ["brightness up", "increase brightness", "brighter"],
            "brightness_down": ["brightness down", "decrease brightness", "dimmer"],
            "set_brightness": ["set brightness to", "brightness to", "brightness at"],
            
            "bluetooth_on": ["bluetooth on", "turn on bluetooth", "enable bluetooth"],
            "bluetooth_off": ["bluetooth off", "turn off bluetooth", "disable bluetooth"],
            
            "sleep": ["sleep", "sleep mode", "put to sleep", "sleep computer"],
            "shutdown": [
                "shutdown computer", "shutdown the system", "power off computer",
                "shutdown my pc", "turn off computer", "shutdown system"
            ],
            "restart": ["restart computer", "restart system", "reboot computer", "restart my pc"],
            
            # Stop talking (to prevent confusion with shutdown)
            "stop_talking": [
                "shut up", "shutup", "be quiet", "quiet", "silence",
                "stop talking", "hush", "enough", "okay stop", "stop jarvis"
            ],
            
            # Habits
            "habit": ["remind me to", "create habit", "habit", "every hour", "every day"],
            "list_habits": ["list habits", "show habits", "my habits"],
            
            # Browser control
            "new_tab": ["new tab", "open new tab", "create tab"],
            "close_tab": ["close tab", "close this tab"],
            
            # YouTube
            "youtube_search": [
                "youtube search", "search on youtube", "play on youtube",
                "youtube video", "search youtube for", "find video"
            ],
            
            # Messaging
            "send_message": [
                "send message", "message to", "text to", "whatsapp message",
                "send whatsapp", "message on whatsapp"
            ],
            "read_messages": [
                "read messages", "show messages", "unread messages", 
                "check messages", "my messages"
            ],
            
            # Calendar
            "calendar_events": [
                "calendar", "my events", "upcoming events", "schedule",
                "what's on my calendar", "my meetings"
            ],
            "today_events": [
                "today's events", "events today", "schedule today",
                "meetings today", "what do I have today"
            ],
            
            # Email
            "read_email": [
                "read emails", "check email", "unread emails",
                "my emails", "check my mail", "inbox"
            ],
            "summarize_email": [
                "summarize emails", "email summary", "summarize my emails"
            ],
        }

        self.intent_embeddings = {}
        for intent, examples in self.intents.items():
            vectors = self.model.encode(examples, normalize_embeddings=True)
            self.intent_embeddings[intent] = np.mean(vectors, axis=0)

        print("[UNDERSTANDING] Layer Ready")

    def classify(self, command: str):
        """Return (intent, confidence)"""

        command_vec = self.model.encode(
            [command], normalize_embeddings=True
        )[0]

        scores = []

        for intent, emb in self.intent_embeddings.items():
            score = float(np.dot(command_vec, emb))
            scores.append((intent, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        best_intent, best_score = scores[0]
        second_score = scores[1][1] if len(scores) > 1 else 0.0

        print(f"  Intent: {best_intent} ({best_score:.3f})")

        # Reject low confidence
        if best_score < self.CONFIDENCE_THRESHOLD:
            print("  WARNING: Confidence below threshold")
            return "uncertain", best_score

        # Reject ambiguous matches
        if (best_score - second_score) < self.MARGIN_THRESHOLD:
            print("  WARNING: Ambiguous intent match")
            return "uncertain", best_score

        return best_intent, best_score

    def extract_entities(self, command: str):
        return {
            "numbers": [int(n) for n in re.findall(r"\d+", command)],
            "apps": self._extract_apps(command),
            "raw_text": command
        }

    def _extract_apps(self, command: str):
        apps = [
            "chrome", "notepad", "calculator", "whatsapp",
            "chatgpt", "perplexity", "brave", "edge",
            "code", "vs code", "vscode", "spotify", "youtube",
            "file explorer", "explorer", "files", "settings",
            "word", "excel", "powerpoint", "paint", "terminal",
            "github", "gmail", "netflix", "instagram", "facebook"
        ]
        command_lower = command.lower()
        found = []
        for app in apps:
            if app in command_lower:
                found.append(app)
        return found
