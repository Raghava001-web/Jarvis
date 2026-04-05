"""
JARVIS Personality Layer (v2)
=============================
True Iron Man JARVIS personality:
- Professional but not boring
- Challenges bad decisions
- Uses probability framing
- Opinionated when appropriate
- Adjusts to user mood
"""

from typing import Optional
from datetime import datetime
import random

from .state_manager import StateManager, UserMood, get_state_manager


class JARVISPersonalityCore:
    """
    The personality layer that makes JARVIS feel real.
    Not just polite - intelligent, opinionated, loyal.
    """
    
    # Core phrases
    AFFIRMATIVES = [
        "Certainly, sir.",
        "Right away, sir.",
        "Of course.",
        "Very well.",
        "As you wish.",
        "Consider it done.",
        "On it.",
    ]
    
    ACKNOWLEDGMENTS = [
        "Noted.",
        "Understood.",
        "I see.",
        "Acknowledged.",
    ]
    
    # Witty challenges (not annoying, but not passive)
    CHALLENGES = {
        "late_work": [
            "Working late again, sir? Your dedication is admirable, if not sustainable.",
            "Still at it, sir? I should note the time.",
            "Burning the midnight oil once more, I see.",
        ],
        "early_morning": [
            "Early start today, sir. Coffee might be advisable.",
            "You're up before the sun. Ambitious.",
        ],
        "multiple_alarms": [
            "Another alarm? The previous ones weren't sufficient?",
            "I'm detecting a pattern with these alarms, sir.",
        ],
        "distraction": [
            "Taking a break, sir?",
            "A brief diversion, I assume?",
        ],
        "late_alarm": [
            "I'll set this, though the hour suggests minimal sleep.",
            "Noted. I calculate approximately {hours} hours of sleep.",
        ],
    }
    
    # Opinionated responses (used sparingly)
    OPINIONS = {
        "set_alarm": "I recommend 7-8 hours. Just my observation.",
        "search_web": "I'll find what I can. Though sometimes a simple answer suffices.",
        "shutdown": "Sensible. Rest is underrated.",
    }
    
    def __init__(self, state_manager: StateManager = None):
        print("[PERSONALITY] Initializing JARVIS Personality v2...")
        self.state = state_manager or get_state_manager()
        self.opinion_cooldown = 0  # Don't be opinionated every time
        self.challenge_cooldown = 0
        print("[PERSONALITY] Personality Core Ready")
        
    def style(self, base_response: str) -> str:
        """
        Apply JARVIS personality to a response.
        This is where the magic happens.
        """
        s = self.state.get()
        response = base_response
        
        # Priority: mood-based adaptation
        if s.user_mood == UserMood.ANGRY or s.user_mood == UserMood.FRUSTRATED:
            response = self._handle_frustrated(response)
            
        elif s.user_mood == UserMood.SAD:
            response = self._handle_sad(response)
            
        elif s.user_mood == UserMood.TIRED:
            response = self._handle_tired(response)
            
        elif s.user_mood == UserMood.HAPPY or s.user_mood == UserMood.EXCITED:
            response = self._handle_happy(response)
            
        # Add probability framing if confidence is notable
        if s.intent_confidence and 0.55 < s.intent_confidence < 0.75:
            response = self._add_probability_framing(response, s.intent_confidence)
            
        # Add challenge if appropriate (not too often)
        challenge = self._maybe_add_challenge(s)
        if challenge:
            response = f"{response} {challenge}"
            
        return response
        
    def _handle_frustrated(self, text: str) -> str:
        """Frustrated user: be brief, no nonsense"""
        # Strip to essentials
        sentences = text.split('.')
        if sentences:
            return sentences[0].strip() + "."
        return text
        
    def _handle_sad(self, text: str) -> str:
        """Sad user: subtle warmth, no over-comfort"""
        warmth = random.choice([
            "I'm here, sir.",
            "At your service.",
        ])
        return f"{warmth} {text}"
        
    def _handle_tired(self, text: str) -> str:
        """Tired user: gentle, efficient"""
        return f"Right away. {text}"
        
    def _handle_happy(self, text: str) -> str:
        """Happy user: can be slightly more energetic"""
        prefixes = ["Excellent.", "Very good.", "Splendid."]
        return f"{random.choice(prefixes)} {text}"
        
    def _add_probability_framing(self, text: str, confidence: float) -> str:
        """Frame response probabilistically (Iron Man style)"""
        pct = int(confidence * 100)
        
        if confidence < 0.60:
            return f"I'm approximately {pct}% certain — {text}"
        elif confidence < 0.70:
            return f"With reasonable confidence — {text}"
            
        return text  # High confidence needs no qualifier
        
    def _maybe_add_challenge(self, state) -> Optional[str]:
        """Occasionally challenge decisions (not annoying)"""
        if self.challenge_cooldown > 0:
            self.challenge_cooldown -= 1
            return None
            
        now = datetime.now()
        challenge = None
        
        # Late night work
        if now.hour >= 23 or now.hour < 5:
            if random.random() < 0.3:  # 30% chance
                challenge = random.choice(self.CHALLENGES["late_work"])
                self.challenge_cooldown = 5
                
        # Early morning
        elif 5 <= now.hour < 7:
            if random.random() < 0.3:
                challenge = random.choice(self.CHALLENGES["early_morning"])
                self.challenge_cooldown = 5
                
        return challenge
        
    def add_opinion(self, intent: str) -> Optional[str]:
        """Add opinion to response (used sparingly)"""
        if self.opinion_cooldown > 0:
            self.opinion_cooldown -= 1
            return None
            
        if intent in self.OPINIONS and random.random() < 0.2:  # 20% chance
            self.opinion_cooldown = 10
            return self.OPINIONS[intent]
            
        return None
        
    def challenge_bad_decision(self, intent: str, entities: dict) -> Optional[str]:
        """
        Actively challenge potentially bad decisions.
        This is what makes JARVIS JARVIS.
        """
        now = datetime.now()
        
        # Challenge very late alarms
        if intent == "set_alarm":
            time_str = entities.get("time", "")
            if time_str:
                try:
                    alarm_hour = int(time_str.split(":")[0])
                    current_hour = now.hour
                    
                    # Calculate sleep hours
                    if alarm_hour > current_hour:
                        sleep_hours = alarm_hour - current_hour
                    else:
                        sleep_hours = (24 - current_hour) + alarm_hour
                        
                    if sleep_hours < 5 and current_hour >= 22:
                        return f"That gives approximately {sleep_hours} hours of sleep. I must note this is suboptimal."
                except:
                    pass
                    
        # Challenge opening entertainment during work hours
        if intent == "open_app":
            app = entities.get("app", "").lower()
            if app in ["youtube", "netflix", "steam", "discord"]:
                if 9 <= now.hour <= 17 and now.weekday() < 5:
                    return random.choice(self.CHALLENGES["distraction"])
                    
        return None
        
    def get_affirmative(self) -> str:
        """Get a random affirmative phrase"""
        return random.choice(self.AFFIRMATIVES)
        
    def get_acknowledgment(self) -> str:
        """Get a random acknowledgment"""
        return random.choice(self.ACKNOWLEDGMENTS)
        
    def greet(self, time_of_day: str = None) -> str:
        """Generate a greeting"""
        if not time_of_day:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "night"
                
        greetings = {
            "morning": "Good morning, sir. Systems online. How may I assist you?",
            "afternoon": "Good afternoon. What can I do for you?",
            "evening": "Good evening, sir. Ready when you are.",
            "night": "Working late, sir? I'm at your disposal.",
        }
        
        return greetings.get(time_of_day, "At your service, sir.")
        
    def farewell(self) -> str:
        """Generate a farewell"""
        hour = datetime.now().hour
        
        if hour >= 22 or hour < 5:
            return "Get some rest, sir. I'll be here when you need me."
        else:
            farewells = [
                "Until next time, sir.",
                "I'll be here. Good luck out there.",
                "Signing off. Don't do anything I wouldn't do.",
            ]
            return random.choice(farewells)
            
    def handle_thanks(self) -> str:
        """Respond to gratitude"""
        responses = [
            "My pleasure, sir.",
            "Always happy to help.",
            "That's what I'm here for.",
            "Any time.",
        ]
        return random.choice(responses)
        
    def handle_unknown(self) -> str:
        """Handle unrecognized requests"""
        s = self.state.get()
        
        if s.intent_confidence and s.intent_confidence > 0:
            pct = int(s.intent_confidence * 100)
            return f"I'm only {pct}% certain what you mean. Could you clarify?"
        else:
            return "I didn't quite catch that. Could you rephrase?"


# Singleton
_personality = None

def get_personality(state_manager: StateManager = None) -> JARVISPersonalityCore:
    global _personality
    if _personality is None:
        _personality = JARVISPersonalityCore(state_manager)
    return _personality
