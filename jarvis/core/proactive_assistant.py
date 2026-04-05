"""
Proactive Assistant - Pattern-Based Intelligence
=================================================
Learns user patterns and makes intelligent suggestions.
Not just time-based, but behavior-based.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class UserPattern:
    """A learned user behavior pattern"""
    action: str
    trigger: str  # time, app, sequence
    frequency: int = 0
    last_triggered: Optional[datetime] = None
    confidence: float = 0.5


class PatternLearner:
    """
    Learns user patterns from behavior.
    Tracks: time-based, sequence-based, context-based patterns.
    """
    
    def __init__(self, data_path: Path):
        self.data_path = data_path / "patterns.json"
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Pattern storage
        self.time_patterns: Dict[int, List[str]] = defaultdict(list)  # hour -> actions
        self.sequence_patterns: Dict[str, List[str]] = defaultdict(list)  # action -> next actions
        self.app_patterns: Dict[str, List[str]] = defaultdict(list)  # app -> actions
        
        # Action history
        self.action_history: List[tuple] = []  # (timestamp, action, entities)
        
        self._load()
        
    def _load(self):
        """Load patterns from disk"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    self.time_patterns = defaultdict(list, data.get("time", {}))
                    self.sequence_patterns = defaultdict(list, data.get("sequence", {}))
                    self.app_patterns = defaultdict(list, data.get("app", {}))
        except:
            pass
            
    def _save(self):
        """Save patterns to disk"""
        try:
            data = {
                "time": dict(self.time_patterns),
                "sequence": dict(self.sequence_patterns),
                "app": dict(self.app_patterns),
            }
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
            
    def record_action(self, action: str, entities: Dict = None):
        """Record a user action to learn from"""
        now = datetime.now()
        hour = now.hour
        
        # Time-based pattern
        if action not in self.time_patterns[hour]:
            self.time_patterns[hour].append(action)
        else:
            # Move to end (more recent = more relevant)
            self.time_patterns[hour].remove(action)
            self.time_patterns[hour].append(action)
            
        # Sequence-based pattern
        if self.action_history:
            last_action = self.action_history[-1][1]
            if action not in self.sequence_patterns[last_action]:
                self.sequence_patterns[last_action].append(action)
                
        # App-based pattern
        if entities and "app" in entities:
            app = entities["app"]
            if action not in self.app_patterns[app]:
                self.app_patterns[app].append(action)
                
        # Update history
        self.action_history.append((now, action, entities))
        
        # Keep history bounded
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-100:]
            
        self._save()
        
    def predict_next_action(self, last_action: str = None) -> Optional[str]:
        """Predict what user might do next"""
        now = datetime.now()
        hour = now.hour
        
        candidates = []
        
        # Time-based prediction
        if hour in self.time_patterns:
            time_actions = self.time_patterns[hour]
            if time_actions:
                candidates.extend(time_actions[-3:])  # Last 3 most common
                
        # Sequence-based prediction
        if last_action and last_action in self.sequence_patterns:
            seq_actions = self.sequence_patterns[last_action]
            if seq_actions:
                candidates.extend(seq_actions[-2:])
                
        # Count and return most common
        if candidates:
            from collections import Counter
            counts = Counter(candidates)
            return counts.most_common(1)[0][0]
            
        return None
        
    def get_common_time_actions(self, hour: int) -> List[str]:
        """Get actions commonly done at this hour"""
        return self.time_patterns.get(hour, [])[-3:]
        
    def get_sequence_suggestions(self, action: str) -> List[str]:
        """Get actions that usually follow this one"""
        return self.sequence_patterns.get(action, [])[-2:]


class ProactiveAssistant:
    """
    Pattern-based proactive assistant.
    Learns from user behavior, not just time.
    """
    
    def __init__(self, perception=None, context_memory=None, state_manager=None):
        print("[PROACTIVE] Initializing Pattern-Based Assistant...")
        self.perception = perception
        self.context = context_memory
        self.state = state_manager
        
        # Pattern learner
        data_path = Path(__file__).parent.parent / "data"
        self.patterns = PatternLearner(data_path)
        
        # Suggestion tracking
        self.suggestions_made_today: set = set()
        self.last_suggestion_time: Optional[datetime] = None
        self.min_suggestion_interval = 1800  # 30 min
        
        # Cooldown per suggestion type
        self.suggestion_cooldowns: Dict[str, datetime] = {}
        
        print("[PROACTIVE] Pattern-Based Assistant Ready")
        
    def _get_title(self) -> str:
        if self.perception and hasattr(self.perception, 'user_title'):
            return self.perception.user_title
        return "sir"
        
    def _can_suggest(self, suggestion_type: str) -> bool:
        """Check if we can make this suggestion"""
        now = datetime.now()
        
        # Global cooldown
        if self.last_suggestion_time:
            elapsed = (now - self.last_suggestion_time).total_seconds()
            if elapsed < self.min_suggestion_interval:
                return False
                
        # Per-type cooldown
        if suggestion_type in self.suggestion_cooldowns:
            last = self.suggestion_cooldowns[suggestion_type]
            if (now - last).total_seconds() < 3600:  # 1 hour per type
                return False
                
        return True
        
    def _mark_suggested(self, suggestion_type: str):
        """Mark that a suggestion was made"""
        now = datetime.now()
        self.last_suggestion_time = now
        self.suggestion_cooldowns[suggestion_type] = now
        self.suggestions_made_today.add(suggestion_type)
        
    def record_action(self, action: str, entities: Dict = None):
        """Record user action for pattern learning"""
        self.patterns.record_action(action, entities)
        
    def check_proactive_suggestions(self) -> Optional[str]:
        """
        Check for proactive suggestions based on patterns + time.
        Returns suggestion text or None.
        """
        now = datetime.now()
        title = self._get_title()
        
        # Reset daily suggestions at midnight
        if now.hour == 0:
            self.suggestions_made_today.clear()
            
        # 1. Pattern-based: predict next action
        pattern_suggestion = self._check_pattern_suggestions(now, title)
        if pattern_suggestion:
            return pattern_suggestion
            
        # 2. Time-based: scheduled suggestions
        time_suggestion = self._check_time_suggestions(now, title)
        if time_suggestion:
            return time_suggestion
            
        # 3. Context-based: based on current state
        context_suggestion = self._check_context_suggestions(now, title)
        if context_suggestion:
            return context_suggestion
            
        return None
        
    def _check_pattern_suggestions(self, now: datetime, title: str) -> Optional[str]:
        """Suggestions based on learned patterns"""
        
        # Check if user usually does something at this hour
        hour_actions = self.patterns.get_common_time_actions(now.hour)
        
        if hour_actions:
            action = hour_actions[-1]  # Most recent common action
            
            # Don't suggest if recently suggested
            if not self._can_suggest(f"pattern_{action}"):
                return None
                
            # Generate suggestion based on action type
            suggestion = self._action_to_suggestion(action, title)
            if suggestion:
                self._mark_suggested(f"pattern_{action}")
                return suggestion
                
        return None
        
    def _action_to_suggestion(self, action: str, title: str) -> Optional[str]:
        """Convert a predicted action to a suggestion"""
        suggestions = {
            "play_music": f"{title}, I noticed you often listen to music around this time. Shall I play something?",
            "get_calendar": f"{title}, would you like me to check your schedule?",
            "search_web": f"Shall I look something up for you, {title}?",
            "open_app": None,  # Too generic
        }
        return suggestions.get(action)
        
    def _check_time_suggestions(self, now: datetime, title: str) -> Optional[str]:
        """Classic time-based suggestions"""
        
        # Morning briefing (7-9 AM)
        if 7 <= now.hour < 9:
            if self._can_suggest("morning_briefing"):
                self._mark_suggested("morning_briefing")
                return f"Good morning, {title}. Would you like your morning briefing?"
                
        # Lunch reminder (12-1 PM)
        if 12 <= now.hour < 13:
            if self._can_suggest("lunch_reminder"):
                self._mark_suggested("lunch_reminder")
                return f"{title}, it's around lunch time. Don't forget to take a break."
                
        # Evening summary (6-7 PM)
        if 18 <= now.hour < 19:
            if self._can_suggest("evening_summary"):
                self._mark_suggested("evening_summary")
                return f"{title}, shall I summarize today's activities?"
                
        # Late work warning (10 PM+)
        if now.hour >= 22:
            if self._can_suggest("late_work"):
                self._mark_suggested("late_work")
                return f"{title}, it's getting late. Perhaps consider wrapping up?"
                
        return None
        
    def _check_context_suggestions(self, now: datetime, title: str) -> Optional[str]:
        """Suggestions based on current context"""
        
        if not self.state:
            return None
            
        try:
            s = self.state.get()
            
            # If user has been working for a while, suggest break
            if s.conversation_turns > 20:
                if self._can_suggest("break_reminder"):
                    self._mark_suggested("break_reminder")
                    return f"{title}, you've been working for a while. Consider a short break?"
                    
            # If user seems frustrated, offer help
            if s.user_mood and s.user_mood.value in ["frustrated", "angry"]:
                if self._can_suggest("frustration_help"):
                    self._mark_suggested("frustration_help")
                    return f"Is there something I can help simplify, {title}?"
                    
        except:
            pass
            
        return None
        
    def get_smart_suggestion(self, action: str, entities: Dict = None) -> Optional[str]:
        """
        Get suggestion for what to do after an action.
        Uses learned sequences.
        """
        title = self._get_title()
        
        # Record the action
        self.record_action(action, entities)
        
        # Check learned sequences
        next_actions = self.patterns.get_sequence_suggestions(action)
        
        if next_actions:
            next_action = next_actions[-1]
            return self._sequence_to_suggestion(action, next_action, title)
            
        # Fallback to hardcoded follow-ups
        return self._get_hardcoded_followup(action, entities, title)
        
    def _sequence_to_suggestion(self, action: str, next_action: str, 
                                 title: str) -> Optional[str]:
        """Convert a sequence prediction to suggestion"""
        
        if action == "play_music" and next_action == "volume_up":
            return f"Shall I adjust the volume, {title}?"
            
        if action == "get_calendar" and next_action == "set_alarm":
            return f"Would you like me to set a reminder, {title}?"
            
        return None
        
    def _get_hardcoded_followup(self, action: str, entities: Dict,
                                 title: str) -> Optional[str]:
        """Hardcoded follow-up suggestions"""
        
        if action == "open_app":
            app = entities.get("app", "") if entities else ""
            
            if "chrome" in app.lower() or "brave" in app.lower():
                return f"Would you like me to search for something, {title}?"
            if "whatsapp" in app.lower():
                return f"Shall I send a message, {title}?"
                
        if action == "set_alarm":
            return f"Shall I also add this to your calendar, {title}?"
            
        if action == "search_web":
            return f"Would you like more details on any result, {title}?"
            
        return None
        
    def anticipate_need(self) -> Optional[str]:
        """Predict what user might need right now"""
        
        last_action = None
        if self.patterns.action_history:
            last_action = self.patterns.action_history[-1][1]
            
        predicted = self.patterns.predict_next_action(last_action)
        
        if predicted:
            title = self._get_title()
            return self._action_to_suggestion(predicted, title)
            
        return None
        
    def offer_help(self, failed_command: str) -> str:
        """Offer help when a command fails"""
        title = self._get_title()
        
        return f"I'm not sure what you meant, {title}. You can ask me to play music, set alarms, open apps, search the web, or control your system."


# Factory
def get_proactive_assistant(perception=None, context_memory=None, 
                            state_manager=None) -> ProactiveAssistant:
    return ProactiveAssistant(perception, context_memory, state_manager)
