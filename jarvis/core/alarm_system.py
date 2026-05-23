"""
Alarm System - Production Grade
================================
- Proper event-based scheduling (not polling)
- Cross-platform audio
- Fixed cancel/delete logic
- Recurring alarm support
- Thread-safe operations
"""

import json
import datetime
import uuid
import threading
import time
import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum
import heapq


class AlarmType(Enum):
    """Types of alarms"""
    ONCE = "once"
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"
    CUSTOM = "custom"  # Specific days


@dataclass(order=True)
class Alarm:
    """Alarm with proper ordering for heap"""
    trigger_time: datetime.datetime
    id: str = field(compare=False)
    label: str = field(compare=False, default="Alarm")
    alarm_type: AlarmType = field(compare=False, default=AlarmType.ONCE)
    repeat_days: List[int] = field(compare=False, default_factory=list)  # 0=Mon, 6=Sun
    created: datetime.datetime = field(compare=False, default_factory=datetime.datetime.now)
    snoozed: bool = field(compare=False, default=False)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "trigger_time": self.trigger_time.isoformat(),
            "label": self.label,
            "alarm_type": self.alarm_type.value,
            "repeat_days": self.repeat_days,
            "created": self.created.isoformat(),
            "snoozed": self.snoozed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Alarm':
        return cls(
            id=data["id"],
            trigger_time=datetime.datetime.fromisoformat(data["trigger_time"]),
            label=data.get("label", "Alarm"),
            alarm_type=AlarmType(data.get("alarm_type", "once")),
            repeat_days=data.get("repeat_days", []),
            created=datetime.datetime.fromisoformat(data.get("created", datetime.datetime.now().isoformat())),
            snoozed=data.get("snoozed", False),
        )


class CrossPlatformAudio:
    """Cross-platform audio playback"""
    
    def __init__(self):
        self.platform = platform.system()
        
    def play_alarm_sound(self, duration_seconds: float = 3.0):
        """Play alarm sound on any platform"""
        try:
            if self.platform == "Windows":
                self._play_windows(duration_seconds)
            elif self.platform == "Darwin":  # macOS
                self._play_macos(duration_seconds)
            else:  # Linux
                self._play_linux(duration_seconds)
        except Exception as e:
            print(f"[ALARM] Audio error: {e}")
            self._play_fallback()
            
    def _play_windows(self, duration: float):
        """Windows audio"""
        import winsound
        end_time = time.time() + duration
        while time.time() < end_time:
            winsound.Beep(880, 200)  # A5
            winsound.Beep(988, 200)  # B5
            winsound.Beep(1047, 200) # C6
            time.sleep(0.3)
            
    def _play_macos(self, duration: float):
        """macOS audio"""
        os.system(f'afplay /System/Library/Sounds/Ping.aiff &')
        
    def _play_linux(self, duration: float):
        """Linux audio"""
        # Try paplay (PulseAudio) first
        try:
            os.system('paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga &')
        except:
            # Fallback to speaker-test
            os.system(f'speaker-test -t sine -f 880 -l 1 &')
            
    def _play_fallback(self):
        """Fallback: print bell character"""
        print("\a" * 3)  # Terminal bell


class AlarmScheduler:
    """
    Proper event-based alarm scheduling using heap.
    No polling - sleeps until next alarm.
    """
    
    def __init__(self, on_alarm: Callable[[Alarm], None]):
        self.alarms: List[Alarm] = []  # Min-heap by trigger_time
        self.on_alarm = on_alarm
        self.lock = threading.Lock()
        self.event = threading.Event()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the scheduler"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.event.set()  # Wake up thread
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def add(self, alarm: Alarm):
        """Add alarm to scheduler"""
        with self.lock:
            heapq.heappush(self.alarms, alarm)
        self.event.set()  # Wake up to recalculate wait time
        
    def remove(self, alarm_id: str) -> bool:
        """Remove alarm by ID - properly removes from heap"""
        with self.lock:
            # Find and remove (rebuild heap)
            original_len = len(self.alarms)
            self.alarms = [a for a in self.alarms if a.id != alarm_id]
            heapq.heapify(self.alarms)
            removed = len(self.alarms) < original_len
        if removed:
            self.event.set()  # Wake up to recalculate
        return removed
        
    def get_next(self) -> Optional[Alarm]:
        """Get next alarm without removing"""
        with self.lock:
            return self.alarms[0] if self.alarms else None
            
    def get_all(self) -> List[Alarm]:
        """Get all alarms sorted by time"""
        with self.lock:
            return sorted(self.alarms, key=lambda a: a.trigger_time)
            
    def _run(self):
        """Main scheduler loop - sleeps until next alarm"""
        while self.running:
            next_alarm = self.get_next()
            
            if next_alarm is None:
                # No alarms - wait indefinitely for new alarm
                self.event.wait()
                self.event.clear()
                continue
                
            now = datetime.datetime.now()
            wait_seconds = (next_alarm.trigger_time - now).total_seconds()
            
            if wait_seconds <= 0:
                # Alarm is due - trigger it
                with self.lock:
                    if self.alarms and self.alarms[0].id == next_alarm.id:
                        heapq.heappop(self.alarms)
                        
                # Call handler
                try:
                    self.on_alarm(next_alarm)
                except Exception as e:
                    print(f"[ALARM] Handler error: {e}")
                    
                # Handle recurring alarms
                if next_alarm.alarm_type != AlarmType.ONCE:
                    self._reschedule_recurring(next_alarm)
            else:
                # Wait until alarm time (or until new alarm added)
                self.event.wait(timeout=wait_seconds)
                self.event.clear()
                
    def _reschedule_recurring(self, alarm: Alarm):
        """Reschedule recurring alarm for next occurrence"""
        now = datetime.datetime.now()
        
        if alarm.alarm_type == AlarmType.DAILY:
            # Same time tomorrow
            next_time = alarm.trigger_time + datetime.timedelta(days=1)
        elif alarm.alarm_type == AlarmType.WEEKDAYS:
            # Next weekday
            next_time = alarm.trigger_time + datetime.timedelta(days=1)
            while next_time.weekday() >= 5:  # Skip weekends
                next_time += datetime.timedelta(days=1)
        elif alarm.alarm_type == AlarmType.WEEKENDS:
            # Next weekend day
            next_time = alarm.trigger_time + datetime.timedelta(days=1)
            while next_time.weekday() < 5:  # Skip weekdays
                next_time += datetime.timedelta(days=1)
        else:
            return  # No reschedule for ONCE
            
        new_alarm = Alarm(
            id=str(uuid.uuid4()),
            trigger_time=next_time,
            label=alarm.label,
            alarm_type=alarm.alarm_type,
            repeat_days=alarm.repeat_days,
        )
        self.add(new_alarm)


class AlarmSystem:
    """
    Production-grade alarm system.
    Thread-safe, cross-platform, proper scheduling.
    """
    
    def __init__(self, perception=None):
        print("[ALARMS] Initializing Alarm System...")
        self.perception = perception
        
        # Persistence
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.alarms_file = self.data_dir / "alarms.json"
        
        # Audio
        self.audio = CrossPlatformAudio()
        
        # Scheduler
        self.scheduler = AlarmScheduler(on_alarm=self._on_alarm_triggered)
        self._load_alarms()
        self.scheduler.start()
        
        # Snooze tracking
        self.last_triggered: Optional[Alarm] = None
        self.snooze_minutes = 5
        
        print("[ALARMS] System Ready")
        
    def _speak(self, text: str):
        """Speak via perception or print — with Gemini Live guard"""
        if self.perception:
            # M-06: Don't speak during Gemini Live — prevents audio clash
            _live = getattr(self.perception, '_gemini_live_active', False)
            if _live:
                print(f"[ALARMS] (live mode - suppressed) {text}")
                return
            self.perception.speak(text)
        else:
            print(f"[ALARMS] {text}")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
            
    def _load_alarms(self):
        """Load persisted alarms"""
        if not self.alarms_file.exists():
            return
            
        try:
            with open(self.alarms_file, 'r') as f:
                data = json.load(f)
                
            now = datetime.datetime.now()
            for item in data:
                alarm = Alarm.from_dict(item)
                # Only load future alarms
                if alarm.trigger_time > now:
                    self.scheduler.add(alarm)
                    
        except Exception as e:
            print(f"[ALARMS] Load error: {e}")
            
    def _save_alarms(self):
        """Persist alarms"""
        try:
            alarms = self.scheduler.get_all()
            data = [a.to_dict() for a in alarms]
            with open(self.alarms_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ALARMS] Save error: {e}")
            
    def _on_alarm_triggered(self, alarm: Alarm):
        """Called when alarm triggers"""
        print(f"\n[ALARM] RINGING: {alarm.label}")
        self.last_triggered = alarm
        
        # Play sound
        self.audio.play_alarm_sound(3.0)
        
        # Announce
        self._speak(f"Alarm! {alarm.label}. Say snooze for 5 more minutes.")
        
        # Save updated state
        self._save_alarms()
        
    def set_alarm(self, time_str: str, label: str = "Alarm", 
                  alarm_type: AlarmType = AlarmType.ONCE) -> bool:
        """Set an alarm"""
        title = self._get_title()
        trigger_time = self._parse_time(time_str)
        
        if not trigger_time:
            self._speak(f"I couldn't understand the time, {title}.")
            return False
            
        alarm = Alarm(
            id=str(uuid.uuid4()),
            trigger_time=trigger_time,
            label=label,
            alarm_type=alarm_type,
        )
        
        self.scheduler.add(alarm)
        self._save_alarms()
        
        time_display = trigger_time.strftime("%I:%M %p")
        self._speak(f"Alarm set for {time_display}, {title}.")
        return True
        
    def _parse_time(self, text: str) -> Optional[datetime.datetime]:
        """Parse various time formats"""
        import re
        now = datetime.datetime.now()
        text = text.lower().strip()
        
        # "in X minutes/hours/seconds"
        if match := re.search(r'in\s+(\d+)\s*(?:min|minute)', text):
            return now + datetime.timedelta(minutes=int(match.group(1)))
            
        if match := re.search(r'in\s+(\d+)\s*(?:hour|hr)', text):
            return now + datetime.timedelta(hours=int(match.group(1)))
            
        if match := re.search(r'in\s+(\d+)\s*(?:sec|second)', text):
            return now + datetime.timedelta(seconds=int(match.group(1)))
            
        # "9:30" or "9:30 am/pm"
        if match := re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text):
            hour, minute = int(match.group(1)), int(match.group(2))
            period = match.group(3)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
                
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if alarm_time <= now:
                alarm_time += datetime.timedelta(days=1)
            return alarm_time
            
        # "at 9 am" or just "9 am"
        if match := re.search(r'(?:at\s+)?(\d{1,2})\s*(am|pm)', text):
            hour = int(match.group(1))
            period = match.group(2)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
                
            alarm_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if alarm_time <= now:
                alarm_time += datetime.timedelta(days=1)
            return alarm_time
            
        return None
        
    def list_alarms(self) -> List[Dict]:
        """List all pending alarms"""
        title = self._get_title()
        alarms = self.scheduler.get_all()
        
        if not alarms:
            self._speak(f"No pending alarms, {title}.")
            return []
        
        # Build single TTS string instead of per-alarm calls
        parts = [f"You have {len(alarms)} pending alarm{'s' if len(alarms) > 1 else ''}, {title}. "]
        result = []
        for i, alarm in enumerate(alarms, 1):
            time_str = alarm.trigger_time.strftime("%I:%M %p")
            parts.append(f"{alarm.label} at {time_str}")
            result.append({"index": i, "label": alarm.label, "time": time_str, "id": alarm.id})
        
        self._speak(". ".join(parts) + ".")
        return result
        
    def cancel_alarm(self, index: int = None, alarm_id: str = None) -> bool:
        """
        Cancel an alarm by index or ID.
        FIXED: Properly removes from scheduler, not just marking.
        """
        title = self._get_title()
        if alarm_id:
            # Cancel by ID
            if self.scheduler.remove(alarm_id):
                self._save_alarms()
                self._speak(f"Alarm cancelled, {title}.")
                return True
            self._speak(f"Alarm not found, {title}.")
            return False
            
        # Cancel by index
        alarms = self.scheduler.get_all()
        
        if not alarms:
            self._speak(f"No pending alarms to cancel, {title}.")
            return False
            
        # Default to first alarm
        idx = (index or 1) - 1
        
        if 0 <= idx < len(alarms):
            alarm_to_cancel = alarms[idx]
            if self.scheduler.remove(alarm_to_cancel.id):
                self._save_alarms()
                self._speak(f"Alarm {idx + 1} cancelled, {title}.")
                return True
                
        self._speak(f"Invalid alarm number, {title}.")
        return False
        
    def snooze_alarm(self, minutes: int = None) -> bool:
        """Snooze the last triggered alarm"""
        title = self._get_title()
        if not self.last_triggered:
            self._speak(f"No recent alarm to snooze, {title}.")
            return False
            
        snooze_time = minutes or self.snooze_minutes
        new_time = datetime.datetime.now() + datetime.timedelta(minutes=snooze_time)
        
        snoozed = Alarm(
            id=str(uuid.uuid4()),
            trigger_time=new_time,
            label=f"{self.last_triggered.label} (snoozed)",
            snoozed=True,
        )
        
        self.scheduler.add(snoozed)
        self._save_alarms()
        
        self._speak(f"Alarm snoozed for {snooze_time} minutes, {title}.")
        self.last_triggered = None
        return True
        
    def stop(self):
        """Stop the alarm system"""
        self.scheduler.stop()


# Singleton
_system = None

def get_alarm_system(perception=None) -> AlarmSystem:
    global _system
    if _system is None:
        _system = AlarmSystem(perception)
    return _system
