"""
Intent Router - Clean Dispatch
==============================
Routes intents to handlers with confidence checking.
Uses dependency injection, respects state.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from .state_manager import StateManager, get_state_manager
from .personality import JARVISPersonalityCore, get_personality


@dataclass
class Intent:
    """Intent classification result"""
    name: str
    confidence: float
    entities: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


@dataclass
class HandlerResult:
    """Result from an intent handler"""
    success: bool
    response: str = ""
    should_speak: bool = True
    action: str = ""
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class IntentRouter:
    """
    Clean intent router with confidence thresholds.
    Routes to handlers, applies personality styling.
    Includes smart fallback strategies for error recovery.
    """
    
    CONFIDENCE_THRESHOLD = 0.55  # Below this, ask for clarification
    HIGH_CONFIDENCE = 0.75       # Above this, execute confidently
    
    # Fallback strategies: if primary intent fails, try alternatives
    FALLBACK_STRATEGIES = {
        "play_music": ["search_web", "open_app"],       # Can't play? Search or open Spotify
        "send_whatsapp": ["search_web"],                 # Can't send? Search contact
        "open_app": ["search_web"],                      # Can't find app? Search for it
        "get_calendar": ["search_web"],                  # Calendar offline? Search
        "weather": ["search_web"],                       # Weather API down? Web search
        "news": ["search_web"],                          # News API down? Web search
    }
    
    def __init__(self, state_manager: StateManager, handlers: Dict[str, Any],
                 personality: JARVISPersonalityCore, speak_func: Callable = None):
        """
        Args:
            state_manager: Central state
            handlers: Dict of handler instances
            personality: Personality layer
            speak_func: Function to speak responses
        """
        print("[ROUTER] Initializing Intent Router...")
        self.state = state_manager
        self.handlers = handlers
        self.personality = personality
        self.speak = speak_func or print
        print("[ROUTER] Intent Router Ready")
        
    def route(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        Route intent to appropriate handler with fallback recovery.
        Returns the response.
        """
        s = self.state.get()
        
        # Check confidence
        if s.intent_confidence < self.CONFIDENCE_THRESHOLD:
            return self._ask_clarification(intent, s.intent_confidence)
            
        # Record action
        self.state.set_topic(intent)
        
        # Try primary intent with fallback recovery
        response = self._dispatch_with_fallback(intent, entities)
        
        # Style with personality
        styled = self.personality.style(response)
        
        # Speak
        self._speak(styled)
        
        return styled
    
    def _dispatch_with_fallback(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        Dispatch to handler with smart fallback on failure.
        If primary intent fails, tries alternatives from FALLBACK_STRATEGIES.
        """
        try:
            response = self._dispatch(intent, entities)
            # Check if response indicates failure
            if response and any(fail in response.lower() for fail in 
                              ["not available", "couldn't", "failed", "error"]):
                raise Exception(response)
            return response
        except Exception as e:
            # Try fallback strategies
            fallbacks = self.FALLBACK_STRATEGIES.get(intent, [])
            for fallback_intent in fallbacks:
                try:
                    print(f"[ROUTER] Primary '{intent}' failed, trying fallback '{fallback_intent}'")
                    return self._dispatch(fallback_intent, entities)
                except Exception:
                    continue
            
            # All fallbacks failed - give graceful error message
            return f"I tried to {intent.replace('_', ' ')}, but ran into issues. Is there another way I can help?"
        
    def _dispatch(self, intent: str, entities: Dict[str, Any]) -> str:
        """Dispatch to specific handler"""
        
        # Music intents
        if intent == "play_music":
            return self._handle_music_play(entities)
        elif intent == "pause_music":
            return self._handle_music_pause()
        elif intent == "resume_music":
            return self._handle_music_resume()
        elif intent == "skip_track":
            return self._handle_music_skip()
        elif intent == "previous_track":
            return self._handle_music_previous()
            
        # Alarm intents
        elif intent == "set_alarm":
            return self._handle_alarm_set(entities)
        elif intent == "list_alarms":
            return self._handle_alarm_list()
        elif intent == "cancel_alarm":
            return self._handle_alarm_cancel(entities)
            
        # App intents
        elif intent == "open_app":
            return self._handle_app_open(entities)
        elif intent == "close_app":
            return self._handle_app_close(entities)
            
        # Search intents
        elif intent == "search_web":
            return self._handle_search(entities)
        elif intent == "ask_question":
            return self._handle_question(entities)
            
        # System intents
        elif intent == "get_time":
            return self._handle_time()
        elif intent == "get_date":
            return self._handle_date()
        elif intent == "volume_up":
            return self._handle_volume(entities, up=True)
        elif intent == "volume_down":
            return self._handle_volume(entities, up=False)
        elif intent == "mute":
            return self._handle_mute()
        elif intent == "brightness_up":
            return self._handle_brightness(entities, up=True)
        elif intent == "brightness_down":
            return self._handle_brightness(entities, up=False)
            
        # Calendar intents
        elif intent == "get_calendar":
            return self._handle_calendar()
        elif intent == "create_event":
            return self._handle_create_event(entities)
            
        # Communication
        elif intent == "send_whatsapp":
            return self._handle_whatsapp(entities)
            
        # Entertainment
        elif intent == "tell_joke":
            return self._handle_joke()
        elif intent == "tell_story":
            return self._handle_story(entities)
        elif intent == "play_youtube":
            return self._handle_youtube(entities)
            
        # Meta intents
        elif intent == "greeting":
            return self.personality.greet()
        elif intent == "goodbye":
            return self.personality.farewell()
        elif intent == "thank_you":
            return self.personality.handle_thanks()
        elif intent == "help":
            return self._handle_help()
        
        # Screen control intents
        elif intent == "screen_control":
            return self._handle_screen_control(entities)
            
        else:
            return self.personality.handle_unknown()
            
    def _ask_clarification(self, intent: str, confidence: float) -> str:
        """Ask for clarification when uncertain"""
        self.state.set_awaiting_clarification(True, intent)
        
        if confidence < 0.3:
            return "I'm not certain what you mean. Could you please rephrase?"
        else:
            pct = int(confidence * 100)
            return f"I'm about {pct}% sure I understand. Could you clarify?"
            
    def _speak(self, text: str):
        """Speak response"""
        if callable(self.speak):
            try:
                self.speak(text)
            except:
                print(f"[JARVIS] {text}")
        else:
            print(f"[JARVIS] {text}")
            
    # Handler implementations
    def _handle_music_play(self, entities: Dict) -> str:
        song = entities.get("song")
        app = entities.get("app", "spotify")
        
        if "music" in self.handlers:
            try:
                self.handlers["music"].play(song)
                self.state.set_last_action(f"play:{song or 'music'}")
                return f"Playing {song}" if song else "Playing music"
            except Exception as e:
                return f"Couldn't play music: {e}"
        return "Music handler not available"
        
    def _handle_music_pause(self) -> str:
        if "music" in self.handlers:
            self.handlers["music"].pause()
            self.state.set_last_action("pause")
            return "Paused"
        return "Music handler not available"
        
    def _handle_music_resume(self) -> str:
        if "music" in self.handlers:
            self.handlers["music"].resume()
            return "Resuming playback"
        return "Music handler not available"
        
    def _handle_music_skip(self) -> str:
        if "music" in self.handlers:
            self.handlers["music"].next_track()
            return "Skipping to next track"
        return "Music handler not available"
        
    def _handle_music_previous(self) -> str:
        if "music" in self.handlers:
            self.handlers["music"].previous_track()
            return "Going back"
        return "Music handler not available"
        
    def _handle_alarm_set(self, entities: Dict) -> str:
        time = entities.get("time")
        if not time:
            return "What time should I set the alarm for?"
            
        if "alarm" in self.handlers:
            self.handlers["alarm"].set_alarm(time)
            self.state.set_last_action(f"alarm:{time}")
            return f"Alarm set for {time}"
        return "Alarm system not available"
        
    def _handle_alarm_list(self) -> str:
        if "alarm" in self.handlers:
            alarms = self.handlers["alarm"].list_alarms()
            if alarms:
                return f"You have {len(alarms)} alarm(s) set"
            return "No alarms set"
        return "Alarm system not available"
        
    def _handle_alarm_cancel(self, entities: Dict) -> str:
        if "alarm" in self.handlers:
            self.handlers["alarm"].cancel_alarm()
            return "Alarm cancelled"
        return "Alarm system not available"
        
    def _handle_app_open(self, entities: Dict) -> str:
        app = entities.get("app")
        if not app:
            return "Which app should I open?"
            
        if "apps" in self.handlers:
            success = self.handlers["apps"].open_app(app)
            if success:
                self.state.set_active_app(app)
                self.state.set_last_action(f"open:{app}")
                return f"Opening {app}"
            return f"Couldn't find {app}"
        return "App finder not available"
        
    def _handle_app_close(self, entities: Dict) -> str:
        app = entities.get("app")
        if "apps" in self.handlers and hasattr(self.handlers["apps"], "close_app"):
            self.handlers["apps"].close_app(app)
            return f"Closing {app}"
        return "Not implemented yet"
        
    def _handle_search(self, entities: Dict) -> str:
        query = entities.get("query")
        if not query:
            return "What should I search for?"
            
        if "search" in self.handlers:
            result = self.handlers["search"].quick_answer(query)
            return result
        return f"Searching for {query}..."
        
    def _handle_question(self, entities: Dict) -> str:
        return self._handle_search(entities)
        
    def _handle_time(self) -> str:
        from datetime import datetime
        now = datetime.now()
        return f"It's {now.strftime('%I:%M %p')}"
        
    def _handle_date(self) -> str:
        from datetime import datetime
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}"
        
    def _handle_volume(self, entities: Dict, up: bool) -> str:
        amount = entities.get("amount", 10)
        if "system" in self.handlers:
            if up:
                self.handlers["system"].volume_up(amount)
                return f"Volume increased"
            else:
                self.handlers["system"].volume_down(amount)
                return f"Volume decreased"
        return "System control not available"
        
    def _handle_mute(self) -> str:
        if "system" in self.handlers:
            self.handlers["system"].mute_volume()
            return "Muted"
        return "System control not available"
        
    def _handle_brightness(self, entities: Dict, up: bool) -> str:
        if "system" in self.handlers:
            if up:
                self.handlers["system"].brightness_up()
                return "Brightness increased"
            else:
                self.handlers["system"].brightness_down()
                return "Brightness decreased"
        return "System control not available"
        
    def _handle_calendar(self) -> str:
        if "calendar" in self.handlers:
            self.handlers["calendar"].get_today_events()
            return ""  # Calendar speaks its own events
        return "Calendar not connected"
        
    def _handle_create_event(self, entities: Dict) -> str:
        if "calendar" in self.handlers:
            title = entities.get("title", "New Event")
            time = entities.get("time")
            # TODO: parse and create
            return "Event creation not fully implemented yet"
        return "Calendar not connected"
        
    def _handle_whatsapp(self, entities: Dict) -> str:
        contact = entities.get("contact")
        message = entities.get("message")
        
        if "whatsapp" in self.handlers:
            self.handlers["whatsapp"].send_message(contact, message)
            return f"Sending message to {contact}"
        return "WhatsApp handler not available"
        
    def _handle_joke(self) -> str:
        if "entertainment" in self.handlers:
            return self.handlers["entertainment"].tell_joke()
        # Fallback jokes
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "There are only 10 types of people: those who understand binary, and those who don't.",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
        ]
        import random
        return random.choice(jokes)
        
    def _handle_story(self, entities: Dict) -> str:
        if "entertainment" in self.handlers:
            return self.handlers["entertainment"].tell_story()
        return "Story telling not available"
        
    def _handle_youtube(self, entities: Dict) -> str:
        query = entities.get("query")
        if "youtube" in self.handlers:
            self.handlers["youtube"].search_and_play(query)
            return f"Playing {query} on YouTube"
        # Fallback to browser
        import webbrowser
        webbrowser.open(f"https://youtube.com/results?search_query={query}")
        return f"Searching YouTube for {query}"
        
    def _handle_help(self) -> str:
        capabilities = [
            "I can play music, set alarms, open apps, search the web,",
            "control volume and brightness, check your calendar,",
            "send WhatsApp messages, tell jokes, control your screen with voice,",
            "click, scroll, type, and much more."
        ]
        return " ".join(capabilities)
    
    def _handle_screen_control(self, entities: Dict) -> str:
        """Handle screen control commands (click, scroll, type, etc.)"""
        if "screen_control" in self.handlers:
            command = entities.get("raw_text", "")
            return self.handlers["screen_control"].handle(command, entities)
        
        # Fallback - try to import and create handler
        try:
            from core.screen_control import ScreenControlHandler
            handler = ScreenControlHandler()
            command = entities.get("raw_text", "")
            return handler.handle(command, entities)
        except Exception as e:
            return f"Screen control not available: {e}"


# Factory function
def get_intent_router(state_manager: StateManager = None,
                      handlers: Dict = None,
                      personality: JARVISPersonalityCore = None,
                      speak_func: Callable = None) -> IntentRouter:
    state_manager = state_manager or get_state_manager()
    personality = personality or get_personality(state_manager)
    handlers = handlers or {}
    return IntentRouter(state_manager, handlers, personality, speak_func)
