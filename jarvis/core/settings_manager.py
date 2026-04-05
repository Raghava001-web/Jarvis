"""
Settings Manager - JARVIS Configuration and Preferences
Handles all user settings and preferences
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class JARVISSettings:
    """All JARVIS settings in one place"""
    
    # Voice settings
    voice_assistant: str = "jarvis"  # "jarvis" or "friday"
    speech_rate: int = 175           # words per minute
    speech_volume: float = 0.9       # 0.0 to 1.0
    user_title: str = "sir"          # "sir" or "mam"
    
    # Wellness settings
    wellness_enabled: bool = True
    water_reminder_interval: int = 30  # minutes
    break_reminder_interval: int = 45  # minutes
    eye_care_reminder: bool = True     # 20-20-20 rule
    posture_reminder: bool = True
    late_night_warning: bool = True
    
    # Interface settings
    globe_enabled: bool = True
    chat_panel_enabled: bool = True
    always_on_top: bool = True
    startup_greeting: bool = True
    
    # Feature toggles
    gesture_control: bool = False    # Requires setup
    face_recognition: bool = False   # Optional security
    emotion_detection: bool = True
    proactive_suggestions: bool = True
    
    # Privacy settings
    save_chat_history: bool = True
    anonymous_mode: bool = False     # Don't log commands
    
    # Sound settings
    sound_effects: bool = True
    notification_sounds: bool = True
    
    # News preferences
    news_country: str = "india"
    news_categories: list = None
    
    def __post_init__(self):
        if self.news_categories is None:
            self.news_categories = ["general", "technology"]


class SettingsManager:
    """Manages JARVIS settings and preferences"""
    
    def __init__(self, perception=None):
        print("[SETTINGS] Initializing Settings Manager...")
        self.perception = perception
        
        # Settings file path
        self.settings_path = Path(__file__).parent.parent / "data" / "settings.json"
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or create settings
        self.settings = self._load_settings()
        
        print("[SETTINGS] Settings Manager Ready")
    
    def _get_title(self) -> str:
        """Get user title from perception layer"""
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        """Speak text via perception layer"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[SETTINGS] {text}")
    
    def _load_settings(self) -> JARVISSettings:
        """Load settings from file"""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return JARVISSettings(**data)
        except Exception as e:
            print(f"[SETTINGS] Could not load settings: {e}")
        
        return JARVISSettings()
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            data = asdict(self.settings)
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print("[SETTINGS] Settings saved")
        except Exception as e:
            print(f"[SETTINGS] Could not save settings: {e}")
    
    def get(self, key: str) -> Any:
        """Get a setting value"""
        return getattr(self.settings, key, None)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self._save_settings()
            return True
        return False
    
    def get_all(self) -> Dict:
        """Get all settings as dictionary"""
        return asdict(self.settings)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        title = self._get_title()
        self.settings = JARVISSettings()
        self._save_settings()
        self._speak(f"Settings reset to defaults, {title}.")
    
    # Voice settings
    def set_speech_rate(self, rate: int):
        """Set speech rate (100-300 WPM)"""
        rate = max(100, min(300, rate))
        self.settings.speech_rate = rate
        self._save_settings()
        
        if self.perception:
            self.perception.set_speech_rate(rate)
    
    def set_speech_volume(self, volume: float):
        """Set speech volume (0.0-1.0)"""
        volume = max(0.0, min(1.0, volume))
        self.settings.speech_volume = volume
        self._save_settings()
        
        if self.perception:
            self.perception.set_speech_volume(volume)
    
    def switch_to_jarvis(self):
        """Switch to JARVIS voice"""
        self.settings.voice_assistant = "jarvis"
        self._save_settings()
        
        if self.perception:
            self.perception.switch_to_jarvis()
    
    def switch_to_friday(self):
        """Switch to FRIDAY voice"""
        self.settings.voice_assistant = "friday"
        self._save_settings()
        
        if self.perception:
            self.perception.switch_to_friday()
    
    # Wellness settings
    def toggle_wellness(self, enabled: bool = None):
        """Toggle wellness reminders"""
        if enabled is None:
            enabled = not self.settings.wellness_enabled
        
        self.settings.wellness_enabled = enabled
        self._save_settings()
        
        status = "enabled" if enabled else "disabled"
        self._speak(f"Wellness reminders {status}.")
    
    def set_water_interval(self, minutes: int):
        """Set water reminder interval"""
        self.settings.water_reminder_interval = max(10, min(120, minutes))
        self._save_settings()
        self._speak(f"Water reminders set to every {minutes} minutes.")
    
    def set_break_interval(self, minutes: int):
        """Set break reminder interval"""
        self.settings.break_reminder_interval = max(20, min(120, minutes))
        self._save_settings()
        self._speak(f"Break reminders set to every {minutes} minutes.")
    
    # Feature toggles
    def toggle_emotion_detection(self, enabled: bool = None):
        """Toggle emotion detection"""
        if enabled is None:
            enabled = not self.settings.emotion_detection
        
        self.settings.emotion_detection = enabled
        self._save_settings()
        
        status = "enabled" if enabled else "disabled"
        self._speak(f"Emotion detection {status}.")
    
    def toggle_proactive(self, enabled: bool = None):
        """Toggle proactive suggestions"""
        if enabled is None:
            enabled = not self.settings.proactive_suggestions
        
        self.settings.proactive_suggestions = enabled
        self._save_settings()
        
        status = "enabled" if enabled else "disabled"
        self._speak(f"Proactive suggestions {status}.")
    
    def toggle_chat_history(self, enabled: bool = None):
        """Toggle chat history saving"""
        if enabled is None:
            enabled = not self.settings.save_chat_history
        
        self.settings.save_chat_history = enabled
        self._save_settings()
        
        status = "enabled" if enabled else "disabled"
        self._speak(f"Chat history saving {status}.")
    
    # Settings report
    def report_settings(self):
        """Report current settings"""
        title = self._get_title()
        s = self.settings
        
        self._speak(f"Here are your current settings, {title}.")
        self._speak(f"Voice: {s.voice_assistant.upper()}, speech rate {s.speech_rate} words per minute.")
        
        wellness_status = "enabled" if s.wellness_enabled else "disabled"
        self._speak(f"Wellness reminders are {wellness_status}.")
        
        emotion_status = "enabled" if s.emotion_detection else "disabled"
        self._speak(f"Emotion detection is {emotion_status}.")
    
    def list_commands(self):
        """List available settings commands"""
        title = self._get_title()
        
        self._speak(f"Here are the settings commands, {title}.")
        self._speak("Say 'switch to Friday' or 'switch to JARVIS' for voice.")
        self._speak("Say 'speak faster' or 'speak slower' for speed.")
        self._speak("Say 'turn off wellness reminders' to disable reminders.")
        self._speak("Say 'reset settings' to restore defaults.")


class HelpSystem:
    """JARVIS help and troubleshooting system"""
    
    def __init__(self, perception=None):
        print("[HELP] Initializing Help System...")
        self.perception = perception
        
        # Help categories
        self.help_topics = {
            "basics": self._help_basics,
            "voice": self._help_voice,
            "apps": self._help_apps,
            "settings": self._help_settings,
            "entertainment": self._help_entertainment,
            "system": self._help_system,
            "troubleshooting": self._help_troubleshooting,
        }
        
        print("[HELP] Help System Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[HELP] {text}")
    
    def get_help(self, topic: str = None):
        """Get help on a topic"""
        title = self._get_title()
        
        if not topic:
            self._general_help()
            return
        
        topic_lower = topic.lower()
        
        # Find matching topic
        for key, func in self.help_topics.items():
            if key in topic_lower:
                func()
                return
        
        # Topic not found
        self._speak(f"I don't have specific help for '{topic}', {title}. Here's general help instead.")
        self._general_help()
    
    def _general_help(self):
        """General help overview"""
        title = self._get_title()
        
        self._speak(f"Here's how to use me, {title}.")
        self._speak("I can help you with: opening apps, playing music, checking weather, news, system status, and more.")
        self._speak("Just speak naturally. For example: 'Open Chrome', 'What's the weather?', or 'Tell me the news'.")
        self._speak("Say 'help with apps' for app commands, or 'help with settings' for settings.")
    
    def _help_basics(self):
        """Basic commands help"""
        self._speak("Here are the basic commands:")
        self._speak("'What time is it?' - Get current time")
        self._speak("'What's the date?' - Get today's date")
        self._speak("'Open [app name]' - Open any application")
        self._speak("'Search for [query]' - Web search")
        self._speak("'Set alarm for [time]' - Set an alarm")
        self._speak("'Exit' or 'Goodbye' - Close JARVIS")
    
    def _help_voice(self):
        """Voice commands help"""
        self._speak("Voice commands:")
        self._speak("'Switch to FRIDAY' - Use female voice")
        self._speak("'Switch to JARVIS' - Use male voice")
        self._speak("'Speak faster' or 'Speak slower' - Adjust speed")
        self._speak("'Stop' or 'Be quiet' - Stop speaking")
        self._speak("You can interrupt me anytime by saying my name.")
    
    def _help_apps(self):
        """App opening help"""
        self._speak("To open apps, say 'Open' followed by the app name:")
        self._speak("'Open Chrome', 'Open Spotify', 'Open WhatsApp'")
        self._speak("For YouTube: 'Play [song name] on YouTube'")
        self._speak("For new browser tabs: 'Open new tab'")
        self._speak("If an app doesn't open, try saying the full name.")
    
    def _help_settings(self):
        """Settings help"""
        self._speak("Settings commands:")
        self._speak("'What are my settings?' - View current settings")
        self._speak("'Turn off wellness reminders' - Disable reminders")
        self._speak("'Reset settings' - Restore defaults")
        self._speak("'Enable emotion detection' - Toggle emotion sensing")
    
    def _help_entertainment(self):
        """Entertainment help"""
        self._speak("Entertainment commands:")
        self._speak("'Tell me a joke' - Hear a joke")
        self._speak("'Sing happy birthday' - JARVIS sings")
        self._speak("'Tell me a horror story' - Scary story with effects")
        self._speak("'Tell me a riddle' - Get a riddle")
        self._speak("'Recite a poem' - Hear poetry")
    
    def _help_system(self):
        """System commands help"""
        self._speak("System commands:")
        self._speak("'Battery status' - Check battery")
        self._speak("'System status' - Full system report")
        self._speak("'Take a screenshot' - Capture screen")
        self._speak("'Volume up/down' - Adjust volume")
        self._speak("'Brightness up/down' - Adjust brightness")
    
    def _help_troubleshooting(self):
        """Troubleshooting help"""
        title = self._get_title()
        
        self._speak(f"Troubleshooting tips, {title}:")
        self._speak("If I don't understand you, try speaking more clearly.")
        self._speak("Make sure your microphone is working and not muted.")
        self._speak("If an app won't open, try the full application name.")
        self._speak("For persistent issues, check the console for error messages.")
        self._speak("You can restart me by saying 'Exit' and running the program again.")
    
    def quick_reference(self):
        """Quick command reference"""
        title = self._get_title()
        
        self._speak(f"Quick reference, {title}:")
        self._speak("Time, Date, Weather, News, Open app, Search, Alarm")
        self._speak("Volume, Brightness, Screenshot, System status")
        self._speak("Joke, Story, Song, Poem, Riddle")
        self._speak("Settings, Help, Exit")
