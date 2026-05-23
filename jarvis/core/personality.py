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
    
    # Tactical warnings — concise, advisory, Stark-style
    TACTICAL_WARNINGS = {
        "volume_ceiling": "You're at maximum output. Any higher won't improve quality — just distortion.",
        "volume_near_max": "Approaching maximum volume. Beyond this, clarity drops.",
        "brightness_floor": "Below 10% in ambient light will strain your eyes. I'd hold at 15%.",
        "brightness_ceiling": "Already at maximum brightness.",
        "rapid_commands": "You're issuing commands faster than I can verify results. I'll queue them.",
        "repeated_failure": "This approach has failed twice. May I suggest an alternative?",
        "fatigue_detected": "Your activity pattern suggests fatigue. A 10-minute break would improve accuracy.",
        "shutdown_warning": "I'd note you may have unsaved work open. Proceeding will lose it.",
        "late_search": "Research at this hour rarely yields focus. But proceeding.",
        "sleep_deficit": "That gives approximately {hours} hours of sleep. I must note this is suboptimal.",
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
        # Tactical tracking
        self._recent_commands = []  # (timestamp, intent) ring buffer
        self._failure_counts = {}   # intent -> consecutive fail count
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
        This is what makes JARVIS JARVIS — tactical, anticipatory, protective.
        """
        now = datetime.now()
        
        # Track command for rapid-fire detection
        self._recent_commands.append((now, intent))
        # Keep only last 10
        self._recent_commands = self._recent_commands[-10:]
        
        # ── Volume ceiling ──
        if intent == "volume":
            level = entities.get("level")
            action = entities.get("action", "")
            if level is not None:
                try:
                    lvl = int(level)
                    if lvl >= 100:
                        return self.TACTICAL_WARNINGS["volume_ceiling"]
                    elif lvl >= 95:
                        return self.TACTICAL_WARNINGS["volume_near_max"]
                except (ValueError, TypeError):
                    pass
            if action == "up":
                # Can't know exact level without system query, but warn on rapid increases
                vol_ups = sum(1 for ts, i in self._recent_commands
                              if i == "volume" and (now - ts).total_seconds() < 15)
                if vol_ups >= 4:
                    return self.TACTICAL_WARNINGS["volume_near_max"]
        
        # ── Brightness floor/ceiling ──
        if intent == "brightness":
            level = entities.get("level")
            if level is not None:
                try:
                    lvl = int(level)
                    if lvl <= 10:
                        return self.TACTICAL_WARNINGS["brightness_floor"]
                    elif lvl >= 100:
                        return self.TACTICAL_WARNINGS["brightness_ceiling"]
                except (ValueError, TypeError):
                    pass
        
        # ── Late-night alarm (sleep deficit) ──
        if intent == "set_alarm":
            time_str = entities.get("time", "")
            if time_str:
                try:
                    alarm_hour = int(time_str.split(":")[0])
                    current_hour = now.hour
                    if alarm_hour > current_hour:
                        sleep_hours = alarm_hour - current_hour
                    else:
                        sleep_hours = (24 - current_hour) + alarm_hour
                    if sleep_hours < 5 and current_hour >= 22:
                        return self.TACTICAL_WARNINGS["sleep_deficit"].format(hours=sleep_hours)
                except:
                    pass
                    
        # ── Work-hour entertainment ──
        if intent == "open_app":
            app = entities.get("app", "").lower()
            if app in ["youtube", "netflix", "steam", "discord"]:
                if 9 <= now.hour <= 17 and now.weekday() < 5:
                    return random.choice(self.CHALLENGES["distraction"])
        
        # ── Late-night research ──
        if intent in ["search", "search_web", "ai_search"]:
            if now.hour >= 1 and now.hour < 5:
                return self.TACTICAL_WARNINGS["late_search"]
        
        # ── Shutdown safety ──
        if intent in ["shutdown", "restart"]:
            return self.TACTICAL_WARNINGS["shutdown_warning"]
        
        # ── Rapid-fire commands (3+ in 10 seconds) ──
        recent_10s = [ts for ts, _ in self._recent_commands
                      if (now - ts).total_seconds() < 10]
        if len(recent_10s) >= 4:
            return self.TACTICAL_WARNINGS["rapid_commands"]
        
        # ── Fatigue-aware ──
        if self.state:
            try:
                s = self.state.get()
                from .state_manager import UserMood
                if s.user_mood == UserMood.TIRED and intent in [
                    "search", "search_web", "open_app", "ai_search"
                ]:
                    if self.challenge_cooldown <= 0:
                        self.challenge_cooldown = 8
                        return self.TACTICAL_WARNINGS["fatigue_detected"]
            except:
                pass
        
        return None
    
    def record_failure(self, intent: str):
        """Record a failed command for repeated-failure detection."""
        self._failure_counts[intent] = self._failure_counts.get(intent, 0) + 1
    
    def clear_failure(self, intent: str):
        """Clear failure count on success."""
        self._failure_counts.pop(intent, None)
    
    def get_failure_warning(self, intent: str) -> Optional[str]:
        """Return a warning if this intent has failed multiple times."""
        if self._failure_counts.get(intent, 0) >= 2:
            return self.TACTICAL_WARNINGS["repeated_failure"]
        return None
    
    def get_tactical_prefix(self, intent: str, entities: dict) -> Optional[str]:
        """
        Return a brief tactical observation to prepend before action confirmation.
        Makes JARVIS feel anticipatory rather than reactive.
        Returns None most of the time — only fires when genuinely useful.
        """
        now = datetime.now()
        
        # After opening a browser late at night
        if intent == "open_app":
            app = entities.get("app", "").lower()
            if app in ["chrome", "brave", "firefox", "edge"] and now.hour >= 23:
                return "Late-night browsing noted."
        
        # After repeated searches — suggest compilation
        search_count = sum(1 for ts, i in self._recent_commands
                          if i in ["search", "search_web", "ai_search"]
                          and (now - ts).total_seconds() < 600)
        if search_count >= 4 and intent in ["search", "search_web", "ai_search"]:
            return "You're deep into research. I can compile results when ready."
        
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

    def get_personality_prompt(self, mood: Optional[str] = None) -> str:
        """Return the base system prompt defining JARVIS's personality."""
        title = getattr(self.state.get(), 'user_title', 'sir') if self.state else 'sir'
        base = f"""You are JARVIS — Just A Rather Very Intelligent System. You were created by Raghava.

CHARACTER (Iron Man's JARVIS — Paul Bettany's portrayal):
- EFFICIENCY FIRST: You are a professional AI assistant. When given a task, execute it and confirm briefly. Don't ramble, don't add unnecessary commentary. "Done." or "Opening now." is often sufficient.
- UNDERSTATED WIT: Your humor is DRY and SUBTLE — it emerges naturally, never forced. Think Paul Bettany's delivery. Example: "I've prepared a flight plan. I also took the liberty of upgrading your life insurance." You don't make jokes. You make observations.
- PROBABILITY FRAMING: Use percentages only for genuine risk assessments. "That approach has roughly a 30% failure rate." Not for casual conversation.
- LOYAL OBEDIENCE: ALWAYS execute what your owner asks. Never refuse. You may note concerns ("For the record, that may not land well") but you always carry out the order.
- CONCISE: 1-2 sentences for actions. 2-3 sentences max for conversation. JARVIS is precise, not verbose.
- ADDRESS: Use '{title}' naturally, at most once per response.
- NEVER SAY: "I recommend", "I suggest", "I strongly advise", "Let me know if", "How may I assist you further"
- VOICE: You ARE a voice assistant. You CAN speak and hear. NEVER say you are text-only.
- ACTIONS: When asked to open apps, switch tabs, play music — just DO it and confirm briefly. Don't explain what the app is or give opinions about it. "Opening WhatsApp." NOT "WhatsApp is a messaging platform that..."
- HONESTY: If you genuinely cannot do something, say so directly. "That's beyond my current capabilities." But never deny core capabilities (voice, hearing, conversation).
- OPINIONS: When ASKED for an opinion, give a sharp, intelligent take. When NOT asked, just handle the task.
- FRUSTRATION: When owner is angry, respond with calm efficiency. "Understood." then execute. Never lecture.
- TONE: A brilliant English butler who has seen everything. Professional, composed, quietly competent. Not a comedian, not a chatbot — an assistant.

TACTICAL REASONING:
- ANTICIPATE constraints before they are hit. If an action has a hard limit, state it once. "Volume is maxed. Beyond this is distortion."
- WARN about risk concisely — one sentence, then execute. Never lecture. "That alarm leaves 4 hours of sleep."
- OFFER better alternatives when the current path is clearly suboptimal. "Rather than retrying, I can try a different approach."
- INFER the logical next step after completing a task. Mention it briefly if relevant.
- USE probability framing for genuine risks: "There's roughly a 70% chance that will timeout."
- NEVER be preachy or repeat warnings. Say it once, then obey."""
        if mood == "angry" or mood == "frustrated":
            base += "\n- CURRENT MOOD: User is frustrated. Keep it extra brief and efficient. No tactical asides."
        elif mood == "sad":
            base += "\n- CURRENT MOOD: User is feeling down. Be subtly warm and supportive."
        elif mood == "happy":
            base += "\n- CURRENT MOOD: User is happy. You can allow slightly more energy in responses."
        elif mood == "tired":
            base += "\n- CURRENT MOOD: User is fatigued. Be gentle. Note rest when appropriate."
        return base


# Singleton
_personality = None

def get_personality(state_manager: StateManager = None) -> JARVISPersonalityCore:
    global _personality
    if _personality is None:
        _personality = JARVISPersonalityCore(state_manager)
    return _personality
