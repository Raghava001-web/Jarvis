"""
Reminder Manager - Intelligent reminder system for JARVIS
Manages reminders, schedules, and recurring tasks
"""

import json
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import re


class ReminderType(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class Reminder:
    """A reminder entry"""
    id: int
    message: str
    remind_at: datetime
    reminder_type: ReminderType
    is_completed: bool = False
    created_at: str = ""


class ReminderManager:
    """Manages reminders and scheduled notifications"""
    
    def __init__(self, perception=None):
        print("[REMINDER] Initializing Reminder Manager...")
        self.perception = perception
        
        # Database — C-02: single persistent connection + lock
        self.db_path = Path(__file__).parent.parent / "data" / "reminders.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()
        
        # Checker thread
        self.running = False
        self.check_thread = None
        
        # Time patterns for parsing
        self.time_patterns = {
            r'in (\d+) minutes?': lambda m: timedelta(minutes=int(m.group(1))),
            r'in (\d+) hours?': lambda m: timedelta(hours=int(m.group(1))),
            r'in (\d+) days?': lambda m: timedelta(days=int(m.group(1))),
            r'at (\d{1,2}):(\d{2})': lambda m: self._parse_time(int(m.group(1)), int(m.group(2))),
            r'at (\d{1,2}) (am|pm)': lambda m: self._parse_time_ampm(int(m.group(1)), m.group(2)),
            r'tomorrow': lambda m: timedelta(days=1),
            r'tonight': lambda m: self._until_tonight(),
        }
        
        print("[REMINDER] Reminder Manager Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[REMINDER] {text}")
    
    def _init_db(self):
        """Initialize database using persistent connection"""
        with self._db_lock:
            cursor = self._conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    remind_at TIMESTAMP NOT NULL,
                    reminder_type TEXT DEFAULT 'once',
                    is_completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self._conn.commit()
    
    def _parse_time(self, hour: int, minute: int) -> timedelta:
        """Parse specific time to timedelta from now"""
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if target <= now:
            target += timedelta(days=1)
        
        return target - now
    
    def _parse_time_ampm(self, hour: int, ampm: str) -> timedelta:
        """Parse time with AM/PM"""
        if ampm.lower() == 'pm' and hour != 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
        
        return self._parse_time(hour, 0)
    
    def _until_tonight(self) -> timedelta:
        """Get timedelta until tonight (9 PM)"""
        now = datetime.now()
        tonight = now.replace(hour=21, minute=0, second=0, microsecond=0)
        
        if tonight <= now:
            tonight += timedelta(days=1)
        
        return tonight - now
    
    def parse_reminder(self, command: str) -> Optional[tuple]:
        """Parse reminder from natural language command
        
        Returns: (message, remind_at datetime, reminder_type) or None
        """
        command_lower = command.lower()
        
        # Extract time
        remind_delta = None
        
        for pattern, extractor in self.time_patterns.items():
            match = re.search(pattern, command_lower)
            if match:
                remind_delta = extractor(match)
                # Remove the time part from message
                command_lower = re.sub(pattern, '', command_lower)
                break
        
        if remind_delta is None:
            # Default to 30 minutes if no time specified
            remind_delta = timedelta(minutes=30)
        
        # Clean up message
        message = command_lower
        for prefix in ['remind me to', 'remind me', 'reminder to', 'reminder']:
            if message.startswith(prefix):
                message = message[len(prefix):].strip()
                break
        
        message = message.strip()
        if not message:
            message = "Reminder"
        
        # Calculate remind time
        if isinstance(remind_delta, timedelta):
            remind_at = datetime.now() + remind_delta
        else:
            remind_at = remind_delta
        
        # Determine type
        reminder_type = ReminderType.ONCE
        if 'daily' in command_lower or 'every day' in command_lower:
            reminder_type = ReminderType.DAILY
        elif 'weekly' in command_lower or 'every week' in command_lower:
            reminder_type = ReminderType.WEEKLY
        
        return (message.title(), remind_at, reminder_type)
    
    def add_reminder(self, message: str, remind_at: datetime, 
                     reminder_type: ReminderType = ReminderType.ONCE,
                     silent: bool = False) -> int:
        """Add a reminder
        
        Args:
            message: The reminder message
            remind_at: When to trigger the reminder
            reminder_type: Type of reminder (once, daily, weekly)
            silent: If True, don't speak the confirmation (for handler-based calls)
        """
        title = self._get_title()
        
        with self._db_lock:
            cursor = self._conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (message, remind_at, reminder_type)
                VALUES (?, ?, ?)
            ''', (message, remind_at.isoformat(), reminder_type.value))
            reminder_id = cursor.lastrowid
            self._conn.commit()
        
        # Format time for speech
        time_str = remind_at.strftime("%I:%M %p")
        if remind_at.date() == datetime.now().date():
            when = f"today at {time_str}"
        elif remind_at.date() == (datetime.now() + timedelta(days=1)).date():
            when = f"tomorrow at {time_str}"
        else:
            when = remind_at.strftime("%B %d at %I:%M %p")
        
        # Only speak if not in silent mode (handler will return response instead)
        if not silent:
            self._speak(f"I'll remind you to {message} {when}, {title}.")
        
        return reminder_id
    
    def set_reminder_from_command(self, command: str) -> bool:
        """Set reminder from natural language command"""
        result = self.parse_reminder(command)
        
        if result:
            message, remind_at, reminder_type = result
            self.add_reminder(message, remind_at, reminder_type)
            return True
        
        self._speak(f"I couldn't understand the reminder. Please specify when to remind you.")
        return False
    
    def get_upcoming_reminders(self, count: int = 5) -> List[Reminder]:
        """Get upcoming reminders"""
        with self._db_lock:
            cursor = self._conn.cursor()
            cursor.execute('''
                SELECT id, message, remind_at, reminder_type, is_completed
                FROM reminders
                WHERE is_completed = 0 AND remind_at > ?
                ORDER BY remind_at ASC
                LIMIT ?
            ''', (datetime.now().isoformat(), count))
            results = cursor.fetchall()
        
        reminders = []
        for row in results:
            reminders.append(Reminder(
                id=row[0],
                message=row[1],
                remind_at=datetime.fromisoformat(row[2]),
                reminder_type=ReminderType(row[3]),
                is_completed=bool(row[4])
            ))
        
        return reminders
    
    def read_reminders(self):
        """Read upcoming reminders aloud"""
        title = self._get_title()
        
        reminders = self.get_upcoming_reminders()
        
        if not reminders:
            self._speak(f"You have no upcoming reminders, {title}.")
            return
        
        self._speak(f"You have {len(reminders)} upcoming reminders, {title}.")
        
        for i, reminder in enumerate(reminders, 1):
            time_str = reminder.remind_at.strftime("%I:%M %p on %B %d")
            self._speak(f"{i}. {reminder.message} at {time_str}")
    
    def _check_due_reminders(self):
        """Check and trigger due reminders — C-02: uses persistent conn + lock"""
        now = datetime.now()
        
        with self._db_lock:
            cursor = self._conn.cursor()
            cursor.execute('''
                SELECT id, message, reminder_type
                FROM reminders
                WHERE is_completed = 0 AND remind_at <= ?
            ''', (now.isoformat(),))
            due_reminders = cursor.fetchall()
        
        for reminder in due_reminders:
            reminder_id, message, reminder_type = reminder
            
            # When Gemini Live owns the audio channel, do NOT auto-speak.
            _live = getattr(self.perception, '_gemini_live_active', False) if self.perception else False
            if _live:
                print(f"[REMINDER] (live mode - suppressed) Reminder: {message}")
            else:
                self._speak(f"Reminder: {message}")
            
            # Mark as complete or reschedule
            with self._db_lock:
                cursor = self._conn.cursor()
                if reminder_type == ReminderType.ONCE.value:
                    cursor.execute('UPDATE reminders SET is_completed = 1 WHERE id = ?', (reminder_id,))
                elif reminder_type == ReminderType.DAILY.value:
                    next_time = now + timedelta(days=1)
                    cursor.execute('UPDATE reminders SET remind_at = ? WHERE id = ?', 
                                  (next_time.isoformat(), reminder_id))
                elif reminder_type == ReminderType.WEEKLY.value:
                    next_time = now + timedelta(weeks=1)
                    cursor.execute('UPDATE reminders SET remind_at = ? WHERE id = ?',
                                  (next_time.isoformat(), reminder_id))
                self._conn.commit()
    
    def _check_loop(self):
        """Background loop to check reminders"""
        while self.running:
            try:
                self._check_due_reminders()
            except Exception as e:
                print(f"[REMINDER] Check error: {e}")
            
            time.sleep(30)  # Check every 30 seconds
    
    def start(self):
        """Start the reminder checker"""
        if self.running:
            return
        
        self.running = True
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()
        print("[REMINDER] Background checker started")
    
    def stop(self):
        """Stop the reminder checker and close DB"""
        self.running = False
        try:
            self._conn.close()
        except Exception:
            pass
        print("[REMINDER] Background checker stopped")
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder — C-02: uses persistent conn + lock"""
        with self._db_lock:
            cursor = self._conn.cursor()
            cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
            deleted = cursor.rowcount > 0
            self._conn.commit()
        
        if deleted:
            self._speak("Reminder deleted.")
        
        return deleted
    
    def clear_completed(self):
        """Clear all completed reminders — C-02: uses persistent conn + lock"""
        with self._db_lock:
            cursor = self._conn.cursor()
            cursor.execute('DELETE FROM reminders WHERE is_completed = 1')
            count = cursor.rowcount
            self._conn.commit()
        
        self._speak(f"Cleared {count} completed reminders.")
