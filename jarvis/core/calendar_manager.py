"""
Calendar Manager - Event and Schedule Management
===============================================
- Add calendar events
- Read today's schedule
- Weekly view
- Integration with system calendar (optional)
"""

import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import re


@dataclass
class CalendarEvent:
    """A calendar event"""
    id: int
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_all_day: bool = False
    created_at: str = ""


class CalendarManager:
    """
    Voice-controlled calendar management.
    Commands: add event, what's on my schedule, meetings today
    """
    
    def __init__(self, perception=None):
        print("[CALENDAR] Initializing Calendar Manager...")
        self.perception = perception
        
        # Database
        self.db_path = Path.home() / ".jarvis" / "calendar.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        print("[CALENDAR] Calendar Manager Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return "sir"
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[CALENDAR] {text}")
    
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                description TEXT,
                is_all_day INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def parse_event(self, command: str) -> Optional[Tuple[str, datetime, Optional[datetime]]]:
        """
        Parse event from natural language.
        Returns: (title, start_time, end_time) or None
        """
        command_lower = command.lower()
        
        # Remove trigger phrases
        for phrase in ["add event", "add meeting", "schedule", "create event", "add to calendar"]:
            command_lower = command_lower.replace(phrase, "")
        
        title = None
        start_time = None
        end_time = None
        
        # Parse time patterns
        now = datetime.now()
        
        # "at 3 PM" or "at 15:00"
        time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', command_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if start_time < now:
                start_time += timedelta(days=1)
        
        # "tomorrow at"
        if "tomorrow" in command_lower:
            if start_time:
                start_time += timedelta(days=1)
            else:
                start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Day names
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(days):
            if day in command_lower:
                days_ahead = i - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                if start_time:
                    # Preserve parsed time, shift to target day
                    base = now + timedelta(days=days_ahead)
                    start_time = start_time.replace(
                        year=base.year,
                        month=base.month,
                        day=base.day
                    )
                else:
                    start_time = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0)
                break
        
        # Extract title - what comes before "at" or "tomorrow" or "on"
        title_match = re.search(r'([a-zA-Z\s]+?)(?:\s+(?:at|on|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday))', command_lower)
        if title_match:
            title = title_match.group(1).strip().title()
        else:
            # Fallback: use cleaned command
            title = command_lower.strip().title()
        
        if not start_time:
            start_time = now.replace(hour=9, minute=0) + timedelta(days=1)
        
        if title and len(title) < 3:
            title = "New Event"
        
        return (title, start_time, end_time) if title else None
    
    def add_event(self, title: str, start_time: datetime, 
                  end_time: datetime = None, location: str = None) -> CalendarEvent:
        """Add a calendar event"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO events (title, start_time, end_time, location)
            VALUES (?, ?, ?, ?)
        ''', (
            title,
            start_time.isoformat(),
            end_time.isoformat() if end_time else None,
            location
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Speak confirmation
        time_str = start_time.strftime("%I:%M %p")
        date_str = start_time.strftime("%A, %B %d")
        self._speak(f"Added {title} on {date_str} at {time_str}.")
        
        return CalendarEvent(
            id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location
        )
    
    def add_event_from_command(self, command: str) -> Optional[CalendarEvent]:
        """Add event from natural language"""
        parsed = self.parse_event(command)
        if parsed:
            title, start_time, end_time = parsed
            return self.add_event(title, start_time, end_time)
        
        self._speak("I couldn't understand that event. Try: add meeting team sync at 3 PM tomorrow")
        return None
    
    def get_today_events(self) -> List[CalendarEvent]:
        """Get today's events"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, start_time, end_time, location, description, is_all_day
            FROM events
            WHERE date(start_time) >= ? AND date(start_time) < ?
            ORDER BY start_time
        ''', (today.isoformat(), tomorrow.isoformat()))
        
        events = []
        for row in cursor.fetchall():
            events.append(CalendarEvent(
                id=row[0],
                title=row[1],
                start_time=datetime.fromisoformat(row[2]),
                end_time=datetime.fromisoformat(row[3]) if row[3] else None,
                location=row[4],
                description=row[5],
                is_all_day=bool(row[6])
            ))
        
        conn.close()
        return events
    
    def get_week_events(self) -> List[CalendarEvent]:
        """Get this week's events"""
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, start_time, end_time, location, description, is_all_day
            FROM events
            WHERE date(start_time) >= ? AND date(start_time) < ?
            ORDER BY start_time
        ''', (today.isoformat(), week_end.isoformat()))
        
        events = []
        for row in cursor.fetchall():
            events.append(CalendarEvent(
                id=row[0],
                title=row[1],
                start_time=datetime.fromisoformat(row[2]),
                end_time=datetime.fromisoformat(row[3]) if row[3] else None,
                location=row[4],
                description=row[5],
                is_all_day=bool(row[6])
            ))
        
        conn.close()
        return events
    
    def read_schedule(self, timeframe: str = "today"):
        """Read schedule aloud"""
        title = self._get_title()
        
        if timeframe == "week":
            events = self.get_week_events()
            period = "this week"
        else:
            events = self.get_today_events()
            period = "today"
        
        if not events:
            self._speak(f"You have no events {period}, {title}. Your schedule is clear.")
            return
        
        response = f"You have {len(events)} event{'s' if len(events) > 1 else ''} {period}. "
        
        for event in events[:5]:  # Limit to 5
            time_str = event.start_time.strftime("%I:%M %p")
            if timeframe == "week":
                day_str = event.start_time.strftime("%A")
                response += f"{event.title} on {day_str} at {time_str}. "
            else:
                response += f"{event.title} at {time_str}. "
        
        self._speak(response)
    
    def delete_event(self, event_id: int) -> bool:
        """Delete an event"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            self._speak("Event deleted.")
        
        return deleted
    
    def handle(self, command: str) -> str:
        """Handle calendar commands"""
        command_lower = command.lower()
        
        # Add event
        if any(kw in command_lower for kw in ["add event", "add meeting", "schedule", "create event"]):
            event = self.add_event_from_command(command)
            if event:
                return f"Added {event.title}."
            return "Couldn't add event."
        
        # Read schedule
        if any(kw in command_lower for kw in ["what's on my schedule", "my schedule", "meetings today", "events today", "calendar today"]):
            self.read_schedule("today")
            return "Read today's schedule."
        
        if "this week" in command_lower or "week schedule" in command_lower:
            self.read_schedule("week")
            return "Read week schedule."
        
        return "I didn't understand that calendar command."


# Singleton
_calendar_instance = None

def get_calendar_manager(perception=None) -> CalendarManager:
    """Get or create calendar manager"""
    global _calendar_instance
    if _calendar_instance is None:
        _calendar_instance = CalendarManager(perception)
    return _calendar_instance
