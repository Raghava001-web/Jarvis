"""
Habit Tracker - Daily Habits
Tracks and reminds daily habits
"""

import json
import datetime
import uuid
from pathlib import Path
import re


class HabitTracker:
    """Tracks daily habits and provides reminders"""

    def __init__(self, perception):
        print("[HABITS] Initializing Habit Tracker...")
        self.perception = perception
        
        self.data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.habits_file = self.data_dir / "habits.json"
        self._load_habits()
        
        # Skip first reminder check on boot to prevent startup spam
        self._boot_grace = True
        
        print("[HABITS] Tracker Ready")

    def _load_habits(self):
        """Load habits from file"""
        if self.habits_file.exists():
            try:
                with open(self.habits_file, 'r') as f:
                    self.habits = json.load(f)
            except:
                self.habits = []
        else:
            self.habits = []

    def _save_habits(self):
        """Save habits to file"""
        try:
            with open(self.habits_file, 'w') as f:
                json.dump(self.habits, f, indent=2)
        except Exception as e:
            print(f"ERROR: Save error: {e}")

    def create_habit(self, description: str, interval: str):
        """Create a new habit"""
        # Parse interval
        interval_type = "daily"
        if "hourly" in interval.lower() or "every hour" in interval.lower():
            interval_type = "hourly"
        elif "morning" in interval.lower():
            interval_type = "morning"
        elif "evening" in interval.lower():
            interval_type = "evening"
        elif "night" in interval.lower():
            interval_type = "night"
        
        habit = {
            "id": str(uuid.uuid4()),
            "description": description,
            "interval": interval_type,
            "created": datetime.datetime.now().isoformat(),
            "last_reminder": None,
            "completions": []
        }
        
        self.habits.append(habit)
        self._save_habits()
        self.perception.speak(f"Habit created: {description}, sir.")
        return True

    def check_reminders(self):
        """Check for due habit reminders"""
        now = datetime.datetime.now()
        
        # On first call after boot, silently update timestamps — don't speak
        if self._boot_grace:
            self._boot_grace = False
            for habit in self.habits:
                if not habit.get("last_reminder") or \
                   datetime.datetime.fromisoformat(habit["last_reminder"]).date() < now.date():
                    habit["last_reminder"] = now.isoformat()
            self._save_habits()
            print("[HABITS] Boot grace: silently updated timestamps (no spam)")
            return []
        
        due_reminders = []
        
        for habit in self.habits:
            last_reminder = None
            if habit.get("last_reminder"):
                last_reminder = datetime.datetime.fromisoformat(habit["last_reminder"])
            
            interval = habit.get("interval", "daily")
            should_remind = False
            
            if interval == "hourly":
                if not last_reminder or (now - last_reminder).total_seconds() >= 3600:
                    should_remind = True
            elif interval == "morning":
                if now.hour >= 6 and now.hour < 9:
                    if not last_reminder or last_reminder.date() < now.date():
                        should_remind = True
            elif interval == "evening":
                if now.hour >= 17 and now.hour < 20:
                    if not last_reminder or last_reminder.date() < now.date():
                        should_remind = True
            elif interval == "night":
                if now.hour >= 21 and now.hour < 23:
                    if not last_reminder or last_reminder.date() < now.date():
                        should_remind = True
            elif interval == "daily":
                if not last_reminder or last_reminder.date() < now.date():
                    should_remind = True
            
            if should_remind:
                due_reminders.append(habit)
                habit["last_reminder"] = now.isoformat()
        
        if due_reminders:
            self._save_habits()
            for habit in due_reminders:
                # M-04: Don't speak during Gemini Live — prevents audio clash
                _live = getattr(self.perception, '_gemini_live_active', False)
                if not _live:
                    self.perception.speak(f"Reminder: {habit['description']}, sir.")
                else:
                    print(f"[HABITS] (live mode - suppressed) Reminder: {habit['description']}")
        
        return due_reminders

    def list_habits(self):
        """List all habits"""
        if not self.habits:
            self.perception.speak("No habits tracked, sir.")
            return True
        
        self.perception.speak(f"You have {len(self.habits)} habits, sir.")
        for i, habit in enumerate(self.habits, 1):
            desc = habit.get("description", "Habit")
            interval = habit.get("interval", "daily")
            self.perception.speak(f"Habit {i}: {desc}, reminder: {interval}")
        
        return True

    def complete_habit(self, habit_id: str):
        """Mark a habit as complete"""
        for habit in self.habits:
            if habit.get("id") == habit_id:
                completion = {
                    "timestamp": datetime.datetime.now().isoformat()
                }
                habit["completions"].append(completion)
                self._save_habits()
                self.perception.speak("Habit marked complete, sir.")
                return True
        
        self.perception.speak("Habit not found, sir.")
        return False

    def analyze_patterns(self):
        """Analyze habit completion patterns"""
        if not self.habits:
            return {}
        
        patterns = {}
        for habit in self.habits:
            completions = habit.get("completions", [])
            if completions:
                days_since_created = (datetime.datetime.now() - datetime.datetime.fromisoformat(habit["created"])).days
                patterns[habit["description"]] = {
                    "total_completions": len(completions),
                    "consistency": len(completions) / max(1, days_since_created)
                }
        
        return patterns
