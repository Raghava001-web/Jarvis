"""
Decision Engine - Reasoning Layer
==================================
Sits above the router. Makes decisions about HOW to handle intents.
Not just dispatch - actual reasoning.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .state_manager import StateManager, UserMood, get_state_manager


class DecisionPriority(Enum):
    """Priority for handling requests"""
    NORMAL = "normal"
    URGENT = "urgent"
    GENTLE = "gentle"
    CAUTIOUS = "cautious"


class DecisionType(Enum):
    """Types of decisions"""
    PROCEED = "proceed"              # Execute as requested
    WARN_THEN_PROCEED = "warn"       # Warn user, then execute
    SUGGEST_ALTERNATIVE = "suggest"  # Offer a better option
    CLARIFY = "clarify"              # Ask for clarification
    REFUSE_GENTLY = "refuse"         # Don't do it, explain why


@dataclass
class Decision:
    """A decision about how to handle a request"""
    type: DecisionType
    priority: DecisionPriority
    message: Optional[str] = None       # Message to add/say
    suggestion: Optional[str] = None    # Alternative suggestion
    modified_entities: Optional[Dict] = None  # Modified parameters


class DecisionEngine:
    """
    Makes intelligent decisions about how to handle requests.
    Considers: user mood, time of day, patterns, safety.
    """
    
    def __init__(self, state_manager: StateManager = None):
        print("[DECISION] Initializing Decision Engine...")
        self.state = state_manager or get_state_manager()
        print("[DECISION] Decision Engine Ready")
        
    def decide(self, intent: str, entities: Dict[str, Any], 
               confidence: float) -> Decision:
        """
        Make a decision about how to handle this request.
        Called before routing.
        """
        s = self.state.get()
        
        # Check for safety concerns
        safety_decision = self._check_safety(intent, entities)
        if safety_decision:
            return safety_decision
            
        # Check for context-based modifications
        context_decision = self._consider_context(intent, entities, s)
        if context_decision:
            return context_decision
            
        # Check confidence-based decisions
        confidence_decision = self._consider_confidence(intent, confidence)
        if confidence_decision:
            return confidence_decision
            
        # Check mood-based priority
        priority = self._get_priority(s.user_mood)
        
        # Default: proceed normally
        return Decision(
            type=DecisionType.PROCEED,
            priority=priority
        )
        
    def _check_safety(self, intent: str, entities: Dict) -> Optional[Decision]:
        """Check for potentially dangerous operations"""
        
        # System shutdown/restart requires confirmation
        if intent in ["shutdown", "restart"]:
            return Decision(
                type=DecisionType.CLARIFY,
                priority=DecisionPriority.CAUTIOUS,
                message="Are you sure you want to do this? This will affect your work."
            )
            
        # Very late night alarms
        if intent == "set_alarm":
            time_str = entities.get("time", "")
            if time_str:
                try:
                    hour = int(time_str.split(":")[0])
                    if 1 <= hour <= 4:
                        return Decision(
                            type=DecisionType.WARN_THEN_PROCEED,
                            priority=DecisionPriority.CAUTIOUS,
                            message=f"Setting alarm for {time_str} - this will severely impact tomorrow's performance."
                        )
                except:
                    pass
                    
        return None
        
    def _consider_context(self, intent: str, entities: Dict, 
                          state) -> Optional[Decision]:
        """Consider context for smarter handling"""
        now = datetime.now()
        
        # Late night work warning
        if now.hour >= 23 or now.hour < 4:
            if intent in ["open_app", "search_web"]:
                return Decision(
                    type=DecisionType.WARN_THEN_PROCEED,
                    priority=DecisionPriority.GENTLE,
                    message="Working late again? I'll proceed, but consider resting soon."
                )
                
        # Morning routine suggestions
        if 6 <= now.hour <= 8:
            if intent == "set_alarm":
                return Decision(
                    type=DecisionType.SUGGEST_ALTERNATIVE,
                    priority=DecisionPriority.NORMAL,
                    suggestion="Since it's morning, shall I also check your calendar for today?"
                )
                
        # If user seems frustrated, be more efficient
        if state.user_mood in [UserMood.FRUSTRATED, UserMood.ANGRY]:
            return Decision(
                type=DecisionType.PROCEED,
                priority=DecisionPriority.URGENT,
                message=None  # Just do it, no extra commentary
            )
            
        # If user is tired, suggest simpler alternatives
        if state.user_mood == UserMood.TIRED:
            if intent == "search_web":
                return Decision(
                    type=DecisionType.SUGGEST_ALTERNATIVE,
                    priority=DecisionPriority.GENTLE,
                    suggestion="You seem tired. Shall I give you a brief answer instead of a detailed search?"
                )
                
        return None
        
    def _consider_confidence(self, intent: str, confidence: float) -> Optional[Decision]:
        """Make decisions based on classification confidence"""
        
        # Very low confidence
        if confidence < 0.50:
            return Decision(
                type=DecisionType.CLARIFY,
                priority=DecisionPriority.NORMAL,
                message="I'm not confident I understood. Could you rephrase that?"
            )
            
        # Moderately low confidence
        if confidence < 0.65:
            pct = int(confidence * 100)
            return Decision(
                type=DecisionType.CLARIFY,
                priority=DecisionPriority.NORMAL,
                message=f"I'm about {pct}% sure I understand. Should I proceed?"
            )
            
        return None
        
    def _get_priority(self, mood: UserMood) -> DecisionPriority:
        """Determine priority based on mood"""
        if mood in [UserMood.FRUSTRATED, UserMood.ANGRY]:
            return DecisionPriority.URGENT  # Be quick
        elif mood in [UserMood.SAD, UserMood.TIRED]:
            return DecisionPriority.GENTLE  # Be soft
        else:
            return DecisionPriority.NORMAL
            
    def challenge_decision(self, intent: str, entities: Dict) -> Optional[str]:
        """
        JARVIS should occasionally challenge bad decisions.
        Returns a challenge question or None.
        """
        now = datetime.now()
        
        # Challenge late-night productivity claims
        if intent == "play_music":
            if now.hour >= 2 and now.hour < 5:
                return "Music at this hour? Perhaps some rest would be more beneficial."
                
        # Challenge setting lots of alarms
        s = self.state.get()
        if intent == "set_alarm":
            if s.last_action and "alarm" in s.last_action:
                return "That's multiple alarms in quick succession. Everything alright?"
                
        # Challenge opening distracting apps during work hours
        if intent == "open_app":
            app = entities.get("app", "").lower()
            if app in ["youtube", "netflix", "discord", "steam"]:
                if 9 <= now.hour <= 17 and now.weekday() < 5:  # Weekday work hours
                    return f"Opening {app} during work hours - taking a break?"
                    
        return None
        
    def get_probability_framing(self, confidence: float) -> str:
        """Frame responses probabilistically (Iron Man style)"""
        if confidence >= 0.90:
            return "I'm highly confident"
        elif confidence >= 0.75:
            return "With reasonable certainty"
        elif confidence >= 0.60:
            return "I believe"
        else:
            return "I'm not entirely certain, but"


# Singleton
_engine = None

def get_decision_engine(state_manager: StateManager = None) -> DecisionEngine:
    global _engine
    if _engine is None:
        _engine = DecisionEngine(state_manager)
    return _engine
