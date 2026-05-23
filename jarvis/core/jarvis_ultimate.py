"""
JARVIS - Main Orchestrator
Integrates all layers into a unified system
Enhanced with emotion detection, wellness monitoring, entertainment, and more
"""

import sys
import time
import threading
from pathlib import Path

from core.perception import PerceptionLayer
from core.understanding import UnderstandingLayer
from core.action import ActionLayer
from core.knowledge import KnowledgeLayer
from core.learning import LearningLayer
from core.task_manager import TaskManager
from core.news_handler import NewsHandler
from core.system_control import SystemControl
from core.habit_tracker import HabitTracker
from core.hotkey_system import HotkeySystem
from core.alarm_system import AlarmSystem
from core.whatsapp_handler import WhatsAppHandler
from core.calendar_integration import CalendarIntegration
from core.email_handler import EmailHandler
from core.context_memory import ContextMemory
from core.proactive_assistant import ProactiveAssistant

# New enhanced modules
from core.emotion_detector import EmotionDetector
from core.wellness_monitor import WellnessMonitor
from core.entertainment import JARVISEntertainment
from core.weather_handler import WeatherHandler
from core.dictionary_handler import DictionaryHandler
from core.screenshot_handler import ScreenshotHandler
from core.system_status import SystemStatus
from core.chat_history import ChatHistory
from core.youtube_downloader import YouTubeDownloader
from core.ocr_handler import OCRHandler
from core.pdf_handler import PDFHandler
from core.screen_control import ScreenControlHandler
from core.settings_manager import SettingsManager, HelpSystem
from core.app_finder import AppFinder
from core.app_switcher import AppSwitcher
from core.face_recognition_auth import FaceRecognition, UserType
from core.smart_notes import SmartNotes
from core.reminder_manager import ReminderManager
from core.calendar_manager import CalendarManager
from core.clipboard_memory import ClipboardMemory
from core.workflow_manager import WorkflowManager

# Optional modules (may not be installed)
try:
    from core.gesture_controller import GestureController
    GESTURE_AVAILABLE = True
except ImportError:
    GESTURE_AVAILABLE = False
    print("[JARVIS] Gesture controller not available (install mediapipe opencv-python)")

# GUI components (optional)
try:
    from gui.globe_controller import GlobeController
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("[JARVIS] GUI interface not available")

from utils.config import Config


class JARVISUltimate:
    """Main JARVIS orchestrator - integrates all layers"""

    def __init__(self):
        print("\n" + "="*60)
        print("          JARVIS - ALL SYSTEMS INITIALIZING")
        print("="*60 + "\n")

        # Validate configuration
        if not Config.validate():
            print("ERROR: Configuration validation failed")
            sys.exit(1)

        # Initialize all layers
        print("Initializing Core Layers...")
        self.perception = PerceptionLayer()
        self.understanding = UnderstandingLayer()
        self.learning = LearningLayer(self.understanding)
        self.action = ActionLayer(self.perception)
        self.knowledge = KnowledgeLayer(self.perception)

        print("Initializing Advanced Layers...")
        self.task_manager = TaskManager(self.perception)
        self.news_handler = NewsHandler(self.perception)
        self.system_control = SystemControl(self.perception)
        self.habit_tracker = HabitTracker(self.perception)
        self.hotkey_system = HotkeySystem(self.perception)
        self.alarm_system = AlarmSystem(self.perception)
        self.whatsapp = WhatsAppHandler(self.perception)
        self.calendar = CalendarIntegration(self.perception)
        self.email = EmailHandler(self.perception, self.knowledge)

        # Creator info
        self.creator = "Raghava"
        self.user_title = "sir"
        
        # Context memory for multi-turn conversations
        print("Initializing Intelligence Layers...")
        self._context_memory = None
        self._proactive = None

        # Initialize Enhanced Modules (Deferred to properties)
        print("Initializing Enhanced Modules (Lazy Loading)...")
        self._emotion_detector = None
        self._wellness = None
        self._entertainment = None
        
        # Fast modules
        self.weather = WeatherHandler(self.perception)
        self.dictionary = DictionaryHandler(self.perception)
        self.screenshot = ScreenshotHandler(self.perception)
        self.system_status = SystemStatus(self.perception)
        
        # Deferred heavy modules
        self._chat_history = None
        self._youtube = None
        self._ocr = None
        self._pdf = None
        
        # Fast core modules
        self.screen_control = ScreenControlHandler()
        self.settings = SettingsManager(self.perception)
        self.help_system = HelpSystem(self.perception)
        self.app_finder = AppFinder(self.perception)
        self.app_switcher = AppSwitcher(self.perception)
        
        # Security/Face (Deferred)
        self._face_auth = None
        
        # Planners & Memory
        self._smart_notes = None
        self.smart_reminders = ReminderManager(self.perception)
        self.smart_reminders.start()  # Start background checker
        self.calendar = CalendarManager(self.perception)
        self._clipboard = None
        self.workflow = WorkflowManager(self, self.perception)
        
        # Gesture controller (Deferred)
        self._gesture = None

        # Start background tasks
        self.start_background_tasks()

        print("\n" + "="*60)
        print(f"        ALL SYSTEMS ONLINE - {self.perception.assistant_name} READY")
        print("="*60 + "\n")

    # ================= LAZY PROPERTIES =================

    @property
    def context_memory(self):
        if getattr(self, '_context_memory', None) is None:
            print("[JARVIS] Lazy loading ContextMemory...")
            self._context_memory = ContextMemory()
        return self._context_memory

    @property
    def proactive(self):
        if getattr(self, '_proactive', None) is None:
            self._proactive = ProactiveAssistant(self.perception, self.context_memory)
        return self._proactive

    @property
    def emotion_detector(self):
        if getattr(self, '_emotion_detector', None) is None:
            print("[JARVIS] Lazy loading EmotionDetector...")
            self._emotion_detector = EmotionDetector()
        return self._emotion_detector

    @property
    def wellness(self):
        if getattr(self, '_wellness', None) is None:
            self._wellness = WellnessMonitor(self.perception)
        return self._wellness

    @property
    def entertainment(self):
        if getattr(self, '_entertainment', None) is None:
            self._entertainment = JARVISEntertainment(self.perception, self.knowledge)
        return self._entertainment

    @property
    def chat_history(self):
        if getattr(self, '_chat_history', None) is None:
            print("[JARVIS] Lazy loading ChatHistory...")
            self._chat_history = ChatHistory(self.perception)
        return self._chat_history

    @property
    def youtube(self):
        if getattr(self, '_youtube', None) is None:
            print("[JARVIS] Lazy loading YouTubeDownloader...")
            self._youtube = YouTubeDownloader(self.perception)
        return self._youtube

    @property
    def ocr(self):
        if getattr(self, '_ocr', None) is None:
            print("[JARVIS] Lazy loading OCRHandler...")
            self._ocr = OCRHandler(self.perception)
        return self._ocr

    @property
    def pdf(self):
        if getattr(self, '_pdf', None) is None:
            print("[JARVIS] Lazy loading PDFHandler...")
            self._pdf = PDFHandler(self.perception, self.knowledge)
        return self._pdf

    @property
    def face_auth(self):
        if getattr(self, '_face_auth', None) is None:
            print("[JARVIS] Lazy loading FaceRecognition...")
            self._face_auth = FaceRecognition(self.perception)
            if self._face_auth.is_available():
                print("[JARVIS] Face recognition available")
        return self._face_auth

    @property
    def smart_notes(self):
        if getattr(self, '_smart_notes', None) is None:
            self._smart_notes = SmartNotes(self.perception)
        return self._smart_notes

    @property
    def clipboard(self):
        if getattr(self, '_clipboard', None) is None:
            print("[JARVIS] Lazy loading ClipboardMemory...")
            self._clipboard = ClipboardMemory(self.perception)
        return self._clipboard

    @property
    def gesture(self):
        if getattr(self, '_gesture', None) is None:
            if GESTURE_AVAILABLE:
                try:
                    print("[JARVIS] Lazy loading GestureController...")
                    self._gesture = GestureController(self.perception)
                    print("[JARVIS] Gesture control available")
                except Exception as e:
                    print(f"[JARVIS] Gesture init error: {e}")
        return self._gesture

    def start_background_tasks(self):
        """Start background monitoring tasks"""
        # Habit reminder checker
        def habit_checker():
            while True:
                try:
                    self.habit_tracker.check_reminders()
                    time.sleep(60)  # Check every minute
                except:
                    pass

        habit_thread = threading.Thread(target=habit_checker, daemon=True)
        habit_thread.start()

    def handle_input(self, text: str = None, frame=None) -> dict:
        """
        Single entry point for all input (text or vision).
        Returns structured result dict for UI consumption.
        """
        result = {
            "success": False,
            "action": "unknown",
            "response": "",
            "confidence": 0.0,
            "entities": {}
        }
        
        if text:
            try:
                # Classify intent
                intent, confidence = self.understanding.classify(text)
                entities = self.understanding.extract_entities(text)
                
                result["action"] = intent
                result["confidence"] = confidence
                result["entities"] = entities
                
                # Process command
                success = self.process_command(text)
                result["success"] = success
                result["response"] = f"Processed: {intent}" if success else "Failed to process"
                
            except Exception as e:
                result["response"] = str(e)
                result["success"] = False
        
        return result

    def process_command(self, command: str) -> bool:
        """Process a command through all layers - supports multi-commands"""
        if not command:
            return True  # Continue listening

        # ========== MULTI-COMMAND SUPPORT ==========
        # Split "open brave and search youtube" into separate commands
        from core.intent_classifier import split_commands
        commands = split_commands(command)
        
        if len(commands) > 1:
            print(f"  [MULTI] Split into {len(commands)} commands: {commands}")
            for i, cmd in enumerate(commands):
                print(f"  [MULTI] Executing command {i+1}/{len(commands)}: {cmd}")
                result = self._process_single_command(cmd)
                if not result:
                    return False  # Exit if any command says to stop
                # Small delay between commands
                import time
                time.sleep(0.5)
            return True
        
        return self._process_single_command(command)
    
    def _process_single_command(self, command: str) -> bool:
        """Process a single command through all layers"""
        if not command:
            return True

        # ========== SAVE TO CHAT HISTORY ==========
        self.chat_history.add_message("user", command)

        # ========== CONTEXTUAL UNDERSTANDING ==========
        # Resolve pronouns like "it", "that" to actual entities
        resolved_command = self.context_memory.resolve_pronoun(command)
        if resolved_command != command:
            print(f"  [CONTEXT] Resolved: '{command}' -> '{resolved_command}'")
            command = resolved_command
        
        command_lower = command.lower()

        # Exit commands - use word boundaries to prevent "perplexity" matching "exit"
        exit_words = ["exit jarvis", "quit jarvis", "goodbye jarvis", "bye jarvis", "close jarvis", "stop jarvis", "jarvis stop"]
        if any(phrase in command_lower for phrase in exit_words) or command_lower in ["exit", "quit", "goodbye", "bye", "stop"]:
            self.perception.speak("Goodbye, sir.")
            return False

        # ========== STOP TALKING / STOP STORY ==========
        stop_talking_words = ["stop story", "stop talking", "be quiet", "shut up", "enough", "stop that", "cancel story"]
        if any(phrase in command_lower for phrase in stop_talking_words):
            # Stop any ongoing speech
            if hasattr(self.perception, 'engine') and self.perception.engine:
                try:
                    self.perception.engine.stop()
                except:
                    pass
            self.perception.speak("Okay, stopping.")
            return True

        # ========== FACE RECOGNITION ACCESS CHECK ==========
        # For restricted commands (whatsapp, email, calendar, etc.), scan face and verify owner
        if self.face_auth and self.face_auth.is_available():
            allowed, reason = self.face_auth.check_command_access(command)
            if not allowed:
                self.perception.speak(reason)
                return True  # Command was blocked, but continue listening

        # ========== FACE RECOGNITION COMMANDS ==========
        if "register my face" in command_lower or "register owner" in command_lower:
            self.face_auth.register_owner()
            return True
        
        if "register guest" in command_lower:
            # Extract name
            parts = command_lower.split("register guest")
            if len(parts) > 1:
                guest_name = parts[1].strip()
                if guest_name:
                    self.face_auth.register_guest(guest_name.title())
                    return True
            self.perception.speak("Please specify the guest name.")
            return True
        
        if "who am i" in command_lower or "verify me" in command_lower:
            self.face_auth.authenticate()
            return True
        
        if "list registered users" in command_lower or "who is registered" in command_lower:
            users = self.face_auth.list_registered_users()
            if users:
                self.perception.speak(f"Registered users are: {', '.join(users)}")
            else:
                self.perception.speak("No users are registered yet.")
            return True

        # ========== SECURITY ACCESS CHECK ==========
        # Check if outsider is trying to use restricted commands
        allowed, reason = self.face_auth.check_command_access(command)
        if not allowed:
            self.perception.speak(self.face_auth.get_outsider_response(command))
            return True

        # ========== STOP TALKING (SAFETY - check before shutdown) ==========
        # Intercept "shut up" and similar phrases BEFORE intent classification
        stop_words = ["shut up", "shutup", "be quiet", "stop talking", "hush", "silence"]
        if any(word in command_lower for word in stop_words):
            self.perception.speak("Understood.")
            return True

        # ========== DIRECT ALARM DETECTION (fallback if intent fails) ==========
        if any(phrase in command_lower for phrase in ["set alarm", "set an alarm", "alarm for", "alarm at", "alarm in", "wake me up"]):
            success = self.alarm_system.set_alarm(command, "Alarm")
            return True

        # ========== DIRECT BROWSER TAB CONTROL ==========
        try:
            import pyautogui
            if "new tab" in command_lower or "open tab" in command_lower or "create tab" in command_lower:
                pyautogui.hotkey('ctrl', 't')
                self.perception.speak("New tab opened, sir.")
                return True
            elif "close tab" in command_lower or "close this tab" in command_lower:
                pyautogui.hotkey('ctrl', 'w')
                self.perception.speak("Tab closed, sir.")
                return True
        except ImportError:
            pass

        # ========== SCREEN CONTROL (scroll, click, switch, minimize) ==========
        screen_control_keywords = ["scroll up", "scroll down", "click", "double click", "right click", 
                                   "switch window", "alt tab", "minimize", "maximize", "close window",
                                   "move mouse", "type "]
        if any(kw in command_lower for kw in screen_control_keywords):
            response = self.screen_control.handle(command)
            self.perception.speak(response)
            return True

        # ========== MUSIC CONTROL (play, pause, next, previous) ==========
        try:
            import pyautogui
            music_keywords = ["play music", "pause music", "resume", "next track", "next song", 
                            "previous track", "previous song", "skip", "stop music"]
            if any(kw in command_lower for kw in music_keywords) or command_lower in ["play", "pause", "next", "previous", "skip"]:
                if "pause" in command_lower or "stop" in command_lower:
                    pyautogui.press('playpause')
                    self.perception.speak("Paused.")
                    return True
                elif "play" in command_lower or "resume" in command_lower:
                    pyautogui.press('playpause')
                    self.perception.speak("Playing.")
                    return True
                elif "next" in command_lower or "skip" in command_lower:
                    pyautogui.press('nexttrack')
                    self.perception.speak("Next track.")
                    return True
                elif "previous" in command_lower:
                    pyautogui.press('prevtrack')
                    self.perception.speak("Previous track.")
                    return True
        except ImportError:
            pass

        # ========== APP SWITCHING (switch to, switch back, list windows) ==========
        switch_keywords = ["switch to", "switch back", "go back", "focus", "list windows", "what's open", "running apps"]
        if any(kw in command_lower for kw in switch_keywords):
            response = self.app_switcher.handle(command)
            self.perception.speak(response)
            return True

        # ========== REMINDERS (remind me, set reminder, my reminders) ==========
        reminder_keywords = ["remind me", "set reminder", "set a reminder", "my reminders", "read reminders", "upcoming reminders"]
        if any(kw in command_lower for kw in reminder_keywords):
            if "read" in command_lower or "my reminders" in command_lower or "upcoming" in command_lower:
                self.smart_reminders.read_reminders()
            else:
                self.smart_reminders.set_reminder_from_command(command)
            return True

        # ========== CALENDAR (add event, schedule, my schedule) ==========
        calendar_keywords = ["add event", "add meeting", "schedule meeting", "create event", "my schedule", 
                           "what's on my schedule", "events today", "meetings today", "this week"]
        if any(kw in command_lower for kw in calendar_keywords):
            self.calendar.handle(command)
            return True

        # ========== CLIPBOARD (save this, what did I copy, paste) ==========
        clipboard_keywords = ["save this", "save clipboard", "what did i copy", "last copied", 
                            "clipboard history", "paste last", "clear clipboard"]
        if any(kw in command_lower for kw in clipboard_keywords):
            self.clipboard.handle(command)
            return True

        # ========== WORKFLOWS (multi-action, morning routine, focus mode) ==========
        workflow_triggers = ["morning routine", "focus mode", "and then", "and search"]
        if self.workflow.is_workflow_command(command) or any(t in command_lower for t in workflow_triggers):
            self.workflow.handle(command)
            return True

        # ========== CLOSE APP ==========
        if "close " in command_lower and any(w in command_lower for w in ["close app", "close chrome", "close notepad", "close spotify", "close window"]):
            app_name = command_lower.split("close ")[-1].strip()
            if app_name:
                try:
                    self.app_switcher.close_app(app_name)
                    return True
                except:
                    pass

        # Classify intent
        intent, confidence = self.understanding.classify(command)
        entities = self.understanding.extract_entities(command)

        # Log command
        self.learning.log_command(command, intent, confidence, False)

        success = False
        
        # ========== SMART APP DETECTION ==========
        # Catch app-opening commands even if intent is wrong
        app_keywords = ["open", "launch", "start", "run"]
        is_open_command = any(word in command_lower for word in app_keywords)
        
        if is_open_command and intent not in ["open_app", "youtube_search"]:
            # Force app opening if command starts with open/launch/etc
            for keyword in app_keywords:
                if keyword in command_lower:
                    app_name = command_lower.split(keyword)[-1].strip()
                    if app_name and app_name not in ["jarvis", ""]:
                        # Override intent to open_app
                        intent = "open_app"
                        entities["apps"] = [app_name]
                        print(f"  [OVERRIDE] Detected app open command: {app_name}")
                        break

        # ========== BASIC ACTIONS ==========
        if intent in ["open_app", "time", "date", "joke", "search", "greeting", "thank", "new_tab", "close_tab", "youtube_search"]:
            success = self.action.execute(intent, entities, command)

        # ========== WHATSAPP MESSAGING ==========
        elif intent == "send_message" or "send message" in command_lower or "whatsapp message" in command_lower:
            success = self.whatsapp.send_message()
        
        elif intent == "read_messages" or "read message" in command_lower or "check message" in command_lower:
            success = self.whatsapp.read_messages()

        # ========== CALENDAR ==========
        elif intent == "calendar_events" or "calendar" in command_lower or "my events" in command_lower:
            success = self.calendar.get_upcoming_events()
        
        elif intent == "today_events" or "today's events" in command_lower or "events today" in command_lower:
            success = self.calendar.get_today_events()

        # ========== EMAIL ==========
        elif intent == "read_email" or "check email" in command_lower or "my emails" in command_lower:
            success = self.email.get_unread_emails()
        
        elif intent == "summarize_email" or "summarize email" in command_lower:
            success = self.email.summarize_emails()

        # ========== QUESTIONS (LLM) ==========
        elif intent == "question" or intent == "uncertain":
            # Use knowledge layer for questions
            answer = self.knowledge.answer_question(command)
            self.perception.speak(answer)
            success = True

        # ========== ALARMS ==========
        elif intent == "set_alarm":
            success = self.alarm_system.set_alarm(command, "Alarm")
        
        elif intent == "list_alarms":
            success = self.alarm_system.list_alarms()
        
        elif intent == "cancel_alarm":
            success = self.alarm_system.cancel_alarm()
        
        elif intent == "snooze_alarm" or "snooze" in command_lower:
            success = self.alarm_system.snooze_alarm()

        # ========== TASKS & REMINDERS ==========
        elif intent in ["task", "reminder"] or "task" in command_lower or "remind me" in command_lower:
            if "add" in command_lower or "create" in command_lower:
                task_text = command_lower.replace("add task", "").replace("create task", "").strip()
                if "tomorrow" in command_lower or "in" in command_lower:
                    success = self.task_manager.set_reminder(task_text, command)
                else:
                    success = self.task_manager.add_task(task_text)
            elif "list" in command_lower or "show" in command_lower:
                success = self.task_manager.list_tasks()
            else:
                # Try to add as task
                task_text = command_lower.replace("remind me to", "").replace("remind me", "").strip()
                if task_text:
                    success = self.task_manager.add_task(task_text)

        elif intent == "list_tasks":
            success = self.task_manager.list_tasks()

        # ========== NEWS ==========
        elif intent == "news" or "news" in command_lower or "headline" in command_lower:
            category = "general"
            count = 5
            
            if "sports" in command_lower or "sport" in command_lower:
                category = "sports"
            elif "tech" in command_lower or "technology" in command_lower:
                category = "technology"
            elif "business" in command_lower:
                category = "business"
            elif "entertainment" in command_lower:
                category = "entertainment"
            elif "politic" in command_lower:
                category = "politics"
            elif "econom" in command_lower:  # matches economics, economy, economic
                category = "economics"
            elif "world" in command_lower or "global" in command_lower or "international" in command_lower:
                category = "world"
            
            # Extract count
            numbers = entities.get("numbers", [])
            if numbers:
                count = min(numbers[0], 10)  # Max 10 headlines
            
            success = self.news_handler.get_headlines(count, category)

        # ========== VOLUME CONTROL ==========
        elif intent == "volume_up" or ("volume" in command_lower and "up" in command_lower):
            success = self.system_control.volume_up()

        elif intent == "volume_down" or ("volume" in command_lower and "down" in command_lower):
            success = self.system_control.volume_down()

        elif intent == "set_volume" or ("volume" in command_lower and entities.get("numbers")):
            numbers = entities.get("numbers", [])
            if numbers:
                success = self.system_control.set_volume(numbers[0])
            else:
                self.perception.speak("What volume level, sir?")

        elif intent == "mute" or "mute" in command_lower:
            success = self.system_control.mute_volume()

        # ========== BRIGHTNESS CONTROL ==========
        elif intent == "brightness_up" or ("brightness" in command_lower and ("up" in command_lower or "increase" in command_lower)):
            success = self.system_control.brightness_up()

        elif intent == "brightness_down" or ("brightness" in command_lower and ("down" in command_lower or "decrease" in command_lower)):
            success = self.system_control.brightness_down()

        elif intent == "set_brightness" or ("brightness" in command_lower and entities.get("numbers")):
            numbers = entities.get("numbers", [])
            if numbers:
                success = self.system_control.set_brightness(numbers[0])

        # ========== BLUETOOTH ==========
        elif intent == "bluetooth_on" or ("bluetooth" in command_lower and "on" in command_lower):
            success = self.system_control.bluetooth_on()

        elif intent == "bluetooth_off" or ("bluetooth" in command_lower and "off" in command_lower):
            success = self.system_control.bluetooth_off()

        # ========== STOP TALKING ==========
        elif intent == "stop_talking":
            # Already handled above, but in case it comes through intent
            self.perception.speak("Understood.")
            success = True

        # ========== SYSTEM POWER (with stricter check) ==========
        elif intent == "sleep" or ("sleep" in command_lower and "computer" in command_lower):
            if "confirm" in command_lower or "yes" in command_lower:
                success = self.system_control.sleep_system(confirm=True)
            else:
                self.perception.speak(f"Say 'sleep confirm' to put the system to sleep, sir.")
                success = True

        # STRICT shutdown check - require explicit keywords to prevent "shut up" confusion
        elif intent == "shutdown" or ("shutdown" in command_lower and any(w in command_lower for w in ["computer", "system", "pc", "confirm"])):
            if "confirm" in command_lower or "yes" in command_lower:
                success = self.system_control.shutdown_system(confirm=True)
            else:
                self.perception.speak(f"Say 'shutdown confirm' to shut down, sir.")
                success = True

        elif intent == "restart" or ("restart" in command_lower and any(w in command_lower for w in ["computer", "system", "pc", "confirm"])):
            if "confirm" in command_lower or "yes" in command_lower:
                success = self.system_control.restart_system(confirm=True)
            else:
                self.perception.speak(f"Say 'restart confirm' to restart, sir.")
                success = True

        # ========== HABITS ==========
        elif intent == "habit" or ("remind" in command_lower and "every" in command_lower):
            desc = command_lower.replace("remind me to", "").replace("remind me", "").strip()
            interval = "daily"
            if "hourly" in command_lower or "every hour" in command_lower:
                interval = "hourly"
            elif "morning" in command_lower:
                interval = "morning"
            elif "evening" in command_lower:
                interval = "evening"
            elif "night" in command_lower:
                interval = "night"
            
            if desc:
                success = self.habit_tracker.create_habit(desc, interval)

        elif intent == "list_habits" or ("habits" in command_lower and ("show" in command_lower or "list" in command_lower)):
            success = self.habit_tracker.list_habits()

        # ========== WEATHER ==========
        elif "weather" in command_lower or "temperature" in command_lower:
            # Extract city if mentioned
            city = None
            for phrase in ["in ", "at ", "for "]:
                if phrase in command_lower:
                    city = command_lower.split(phrase)[-1].strip()
            
            if "rain" in command_lower:
                success = self.weather.will_it_rain(city)
            elif "temperature" in command_lower:
                success = self.weather.get_temperature(city)
            else:
                success = self.weather.report_weather(city)

        # ========== ENTERTAINMENT ==========
        elif any(word in command_lower for word in ["sing", "song", "story", "joke", "poem", "riddle", "make me laugh"]):
            success = self.entertainment.entertain(command)

        # ========== DICTIONARY ==========
        elif any(phrase in command_lower for phrase in ["define ", "meaning of ", "what is ", "what does ", "definition"]):
            # Extract word
            word = None
            for phrase in ["define ", "meaning of ", "what is ", "what does ", "definition of "]:
                if phrase in command_lower:
                    word = command_lower.split(phrase)[-1].strip().rstrip("?")
                    break
            if word:
                success = self.dictionary.define_word(word)
        
        elif "synonym" in command_lower:
            word = command_lower.replace("synonym for", "").replace("synonyms for", "").replace("synonym of", "").strip()
            if word:
                success = self.dictionary.synonym(word)

        # ========== SCREENSHOT ==========
        elif "screenshot" in command_lower or "screen capture" in command_lower:
            if "clipboard" in command_lower or "copy" in command_lower:
                success = self.screenshot.copy_to_clipboard()
            else:
                success = self.screenshot.take_fullscreen()

        # ========== SYSTEM STATUS ==========
        elif "system status" in command_lower or "system report" in command_lower:
            success = self.system_status.full_system_report()
        
        elif "cpu" in command_lower and ("usage" in command_lower or "status" in command_lower):
            success = self.system_status.report_cpu()
        
        elif "memory" in command_lower or "ram" in command_lower:
            success = self.system_status.report_memory()
        
        elif "battery" in command_lower and not "save" in command_lower:
            success = self.system_status.report_battery()
        
        elif "disk" in command_lower or "storage" in command_lower:
            success = self.system_status.report_disk()

        # ========== VOICE SWITCHING (JARVIS/FRIDAY) ==========
        elif "switch to friday" in command_lower or "activate friday" in command_lower:
            self.perception.switch_to_friday()
            success = True
        
        elif "switch to jarvis" in command_lower or "activate jarvis" in command_lower:
            self.perception.switch_to_jarvis()
            success = True
        
        elif "who are you" in command_lower or "what's your name" in command_lower:
            name = self.perception.assistant_name
            self.perception.speak(f"I am {name}, your personal AI assistant created by {self.creator}. At your service, {self.perception.user_title}.")
            success = True

        # ========== YOUTUBE DOWNLOAD ==========
        elif "download" in command_lower and ("youtube" in command_lower or "video" in command_lower):
            url = self.youtube.extract_url_from_command(command)
            if url:
                if "audio" in command_lower or "music" in command_lower or "mp3" in command_lower:
                    success = self.youtube.download_audio(url) is not None
                else:
                    success = self.youtube.download_video(url) is not None
            else:
                self.perception.speak(f"Please provide a YouTube URL to download, {self.perception.user_title}.")
                success = True
        
        elif "youtube downloads" in command_lower or "open youtube folder" in command_lower:
            success = self.youtube.open_downloads_folder()

        # ========== OCR (Read Text from Screen/Image) ==========
        elif any(phrase in command_lower for phrase in ["read screen", "read text", "ocr", "extract text"]):
            if "clipboard" in command_lower:
                success = self.ocr.read_clipboard_image() is not None
            elif "screen" in command_lower or "display" in command_lower:
                success = self.ocr.read_screen() is not None
            else:
                # Default to screen reading
                success = self.ocr.read_screen() is not None

        # ========== PDF SUMMARIZATION ==========
        elif any(phrase in command_lower for phrase in ["summarize pdf", "summarize this pdf", "summarize the pdf", "pdf summary", "read pdf"]):
            # Try to find the active PDF or ask user
            import win32gui
            try:
                active_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                if '.pdf' in active_window.lower():
                    # Extract PDF path from window title (common pattern)
                    pdf_name = active_window.split(' - ')[0].strip()
                    # Find this PDF in recent files
                    recent_pdfs = self.pdf.find_pdfs()
                    for pdf_path in recent_pdfs:
                        if pdf_name.lower() in str(pdf_path).lower():
                            summary = self.pdf.summarize(str(pdf_path))
                            self.perception.speak(summary[:1500] if len(summary) > 1500 else summary)
                            success = True
                            break
                    else:
                        self.perception.speak(f"Found PDF window but couldn't locate the file. Try placing a PDF in your Documents folder, {self.perception.user_title}.")
                        success = True
                else:
                    self.perception.speak(f"No PDF is currently open, {self.perception.user_title}. Please open a PDF first.")
                    success = True
            except Exception as e:
                print(f"[PDF] Error detecting active PDF: {e}")
                # Fallback: summarize most recent PDF
                recent_pdfs = self.pdf.find_pdfs()
                if recent_pdfs:
                    self.perception.speak(f"Summarizing most recent PDF, {self.perception.user_title}.")
                    summary = self.pdf.summarize(str(recent_pdfs[0]))
                    self.perception.speak(summary[:1500] if len(summary) > 1500 else summary)
                    success = True
                else:
                    self.perception.speak(f"No PDFs found in your Documents folder, {self.perception.user_title}.")
                    success = True

        # ========== HELP SYSTEM ==========
        elif "help" in command_lower:
            if "app" in command_lower:
                self.help_system.get_help("apps")
            elif "voice" in command_lower:
                self.help_system.get_help("voice")
            elif "setting" in command_lower:
                self.help_system.get_help("settings")
            elif "entertainment" in command_lower or "fun" in command_lower:
                self.help_system.get_help("entertainment")
            elif "system" in command_lower:
                self.help_system.get_help("system")
            elif "troubleshoot" in command_lower or "problem" in command_lower:
                self.help_system.get_help("troubleshooting")
            else:
                self.help_system.get_help()
            success = True
        
        elif "quick reference" in command_lower or "command list" in command_lower:
            self.help_system.quick_reference()
            success = True

        # ========== SMART NOTES & MEMORY ==========
        elif "remember that" in command_lower or "remember my" in command_lower:
            success = self.smart_notes.extract_remembrance_from_command(command)
        
        elif "what is my" in command_lower or "what's my" in command_lower:
            # Recall a memory - extract key
            key = command_lower.replace("what is my", "").replace("what's my", "").strip()
            self.smart_notes.recall(key)
            success = True
        
        elif "take a note" in command_lower or "note that" in command_lower:
            content = command_lower.replace("take a note", "").replace("note that", "").strip()
            if content:
                self.smart_notes.add_note(content)
            success = True
        
        elif "my notes" in command_lower or "read notes" in command_lower:
            self.smart_notes.read_notes()
            success = True
        
        elif "search notes" in command_lower:
            query = command_lower.replace("search notes", "").replace("for", "").strip()
            if query:
                self.smart_notes.search_notes(query)
            success = True

        # ========== SMART REMINDERS ==========
        elif any(phrase in command_lower for phrase in ["remind me", "reminder to", "set a reminder"]):
            success = self.smart_reminders.set_reminder_from_command(command)
        
        elif "my reminders" in command_lower or "show reminders" in command_lower or "list reminders" in command_lower:
            self.smart_reminders.read_reminders()
            success = True

        # ========== SETTINGS COMMANDS ==========
        elif "my settings" in command_lower or "current settings" in command_lower or "what are my settings" in command_lower:
            self.settings.report_settings()
            success = True
        
        elif "reset settings" in command_lower or "restore defaults" in command_lower:
            self.settings.reset_to_defaults()
            success = True
        
        elif "speak faster" in command_lower:
            new_rate = self.settings.get("speech_rate") + 20
            self.settings.set_speech_rate(new_rate)
            self.perception.speak(f"Speaking faster now, {self.perception.user_title}.")
            success = True
        
        elif "speak slower" in command_lower:
            new_rate = self.settings.get("speech_rate") - 20
            self.settings.set_speech_rate(new_rate)
            self.perception.speak(f"Speaking slower now, {self.perception.user_title}.")
            success = True
        
        elif "turn off wellness" in command_lower or "disable wellness" in command_lower:
            self.settings.toggle_wellness(False)
            success = True
        
        elif "turn on wellness" in command_lower or "enable wellness" in command_lower:
            self.settings.toggle_wellness(True)
            success = True
        
        elif "refresh apps" in command_lower or "rescan apps" in command_lower:
            self.app_finder.refresh_cache()
            success = True

        # ========== FALLBACK TO LLM ==========
        if not success:
            # Use context for better LLM responses
            context_prompt = self.context_memory.get_context_prompt()
            answer = self.knowledge.answer_question(command)
            self.perception.speak(answer)
            
            # Log to context memory
            self.context_memory.add_exchange(command, answer, intent)
            success = True
        
        # Log successful commands to context
        if success and intent:
            self.context_memory.add_exchange(command, "Command executed successfully", intent)

        # Update learning with success status
        self.learning.log_command(command, intent, confidence, success)

        return True

    def run(self):
        """Main run loop"""
        name = self.perception.assistant_name
        title = self.perception.user_title
        self.perception.speak(f"Hello {title}. {name} is now online and ready.")

        print("\n" + "="*50)
        print(f"       {name.upper()} IS NOW LISTENING")
        print("="*50)
        print("  Speak clearly into your microphone.")
        print("  Say 'exit' or 'goodbye' to quit.")
        print("="*50 + "\n")

        while True:
            try:
                # Check for proactive suggestions
                try:
                    proactive_msg = self.proactive.check_proactive_suggestions()
                    if proactive_msg:
                        self.perception.speak(proactive_msg)
                except:
                    pass
                
                # Check for wellness reminders
                try:
                    wellness_msg = self.wellness.check_wellness()
                    if wellness_msg:
                        self.perception.speak(wellness_msg)
                except:
                    pass
                
                # Check for reminders in background
                try:
                    self.task_manager.check_reminders()
                except:
                    pass
                
                # Listen for command
                command = self.perception.listen(timeout=15)

                if command:
                    # Log to chat history
                    self.chat_history.add_user_message(command)
                    self.wellness.record_activity()
                    
                    if not self.process_command(command):
                        break  # Exit requested
            except KeyboardInterrupt:
                print("\n\nKeyboard interrupt - Shutting down")
                break
            except Exception as e:
                print(f"ERROR in main loop: {e}")
                continue

        # Cleanup
        self.hotkey_system.stop()
        self.alarm_system.stop()
        if self.gesture:
            self.gesture.stop()
        self.perception.speak(f"{self.perception.assistant_name} offline. Goodbye, {self.perception.user_title}.")

    def on_wake_word(self):
        """Called when wake word is detected"""
        self.perception.speak("Yes, sir?")
        command = self.perception.listen(timeout=10)
        if command:
            self.process_command(command)
