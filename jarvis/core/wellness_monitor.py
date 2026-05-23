"""
Wellness Monitor - Health and wellbeing reminders
JARVIS cares about your health
"""

import datetime
import json
from pathlib import Path
from typing import Optional


class WellnessMonitor:
    """Monitors user wellness and provides health reminders"""
    
    def __init__(self, perception=None):
        print("[WELLNESS] Initializing Wellness Monitor...")
        self.perception = perception
        
        # Session tracking
        self.session_start = datetime.datetime.now()
        self.last_break_reminder = None
        self.last_water_reminder = None
        self.last_posture_reminder = None
        self.last_eye_reminder = None
        
        # Reminder intervals (in minutes)
        self.water_interval = 45  # Every 45 minutes
        self.break_interval = 90  # Every 90 minutes
        self.posture_interval = 60  # Every hour
        self.eye_strain_interval = 20  # 20-20-20 rule
        
        # Activity tracking
        self.commands_count = 0
        self.last_activity = datetime.datetime.now()
        
        # Load preferences
        self.data_path = Path(__file__).parent.parent / "data" / "wellness_data.json"
        self.preferences = self._load_preferences()
        
        print("[WELLNESS] Wellness Monitor Ready")
    
    def _get_title(self) -> str:
        """Get user title from perception layer"""
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _load_preferences(self) -> dict:
        """Load wellness preferences from file"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WELLNESS] Could not load preferences: {e}")
        
        return {
            "water_reminders": True,
            "break_reminders": True,
            "posture_reminders": True,
            "eye_strain_reminders": True,
            "late_night_warnings": True
        }
    
    def _save_preferences(self):
        """Save wellness preferences to file"""
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"[WELLNESS] Could not save preferences: {e}")
    
    def record_activity(self):
        """Record user activity (called on each command)"""
        self.commands_count += 1
        self.last_activity = datetime.datetime.now()
    
    def get_session_duration(self) -> int:
        """Get session duration in minutes"""
        now = datetime.datetime.now()
        return int((now - self.session_start).total_seconds() / 60)
    
    def check_wellness(self) -> Optional[str]:
        """Check if user needs wellness reminder
        
        Returns a reminder message or None
        """
        now = datetime.datetime.now()
        title = self._get_title()
        session_minutes = self.get_session_duration()
        
        # Late night warning (11 PM - 4 AM)
        if self.preferences.get("late_night_warnings", True):
            if 23 <= now.hour or now.hour < 4:
                if self._should_remind("late_night", 30):  # Every 30 min late at night
                    self._mark_reminded("late_night")
                    return f"{title}, it's quite late. Your health is important to me. Perhaps consider resting soon?"
        
        # Water reminder
        if self.preferences.get("water_reminders", True):
            if self._minutes_since(self.last_water_reminder) >= self.water_interval:
                self.last_water_reminder = now
                return f"{title}, you've been working for a while. Perhaps a glass of water?"
        
        # Break reminder (based on session duration)
        if self.preferences.get("break_reminders", True):
            if session_minutes >= self.break_interval:
                if self._minutes_since(self.last_break_reminder) >= self.break_interval:
                    self.last_break_reminder = now
                    hours = session_minutes // 60
                    mins = session_minutes % 60
                    time_str = f"{hours} hour{'s' if hours > 1 else ''}" if hours else f"{mins} minutes"
                    return f"{title}, you've been at it for {time_str}. A short break would do you good."
        
        # Eye strain reminder (20-20-20 rule)
        if self.preferences.get("eye_strain_reminders", True):
            if self._minutes_since(self.last_eye_reminder) >= self.eye_strain_interval:
                # BUG FIX: Only reset timer when reminder is actually sent
                # Old code reset the clock unconditionally, so the window check
                # almost never aligned with the interval check
                if session_minutes > 40:
                    self.last_eye_reminder = now
                    return f"{title}, might I suggest the 20-20-20 rule? Look at something 20 feet away for 20 seconds. Your eyes will thank you."
        
        # Posture reminder
        if self.preferences.get("posture_reminders", True):
            if self._minutes_since(self.last_posture_reminder) >= self.posture_interval:
                self.last_posture_reminder = now
                if session_minutes > 60:  # Only after an hour
                    return f"{title}, a quick posture check - sit up straight, shoulders back. Your body will appreciate it."
        
        return None
    
    def _minutes_since(self, last_time: Optional[datetime.datetime]) -> int:
        """Get minutes since last reminder"""
        if last_time is None:
            # m-06: Return 0 on first check to prevent immediate spam on boot
            # The reminder will fire after the actual interval elapses
            return 0
        now = datetime.datetime.now()
        return int((now - last_time).total_seconds() / 60)
    
    def _should_remind(self, reminder_type: str, interval: int) -> bool:
        """Check if should show a specific reminder type"""
        key = f"_last_{reminder_type}"
        last = getattr(self, key, None)
        if last is None:
            return True
        return self._minutes_since(last) >= interval
    
    def _mark_reminded(self, reminder_type: str):
        """Mark a reminder as shown"""
        key = f"_last_{reminder_type}"
        setattr(self, key, datetime.datetime.now())
    
    def set_preference(self, pref_name: str, value: bool):
        """Set a wellness preference"""
        if pref_name in self.preferences:
            self.preferences[pref_name] = value
            self._save_preferences()
            return True
        return False
    
    def get_wellness_summary(self) -> str:
        """Get a summary of today's wellness"""
        title = self._get_title()
        session = self.get_session_duration()
        
        hours = session // 60
        mins = session % 60
        
        if hours > 0:
            time_str = f"{hours} hour{'s' if hours > 1 else ''} and {mins} minutes"
        else:
            time_str = f"{mins} minutes"
        
        summary = f"{title}, you've been working for {time_str} this session. "
        
        if session > 120:
            summary += "That's quite a stretch. Remember to take breaks!"
        elif session > 60:
            summary += "Good pace. Don't forget to stay hydrated."
        else:
            summary += "You're doing well."
        
        return summary
    
    def reset_session(self):
        """Reset session (e.g., after a break)"""
        self.session_start = datetime.datetime.now()
        self.last_break_reminder = None
        self.last_water_reminder = None
        self.commands_count = 0
