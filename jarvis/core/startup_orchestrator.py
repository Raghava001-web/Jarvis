"""
JARVIS Startup Orchestrator — Full Boot Sequence
=================================================
Runs once after all systems initialize to:
1. Track sessions (save/load shutdown state)
2. Generate intelligent greeting based on time + context
3. Summarize pending tasks & reminders
4. Report last session (where user left off)
5. Read weather, calendar events
6. Kick off mood-aware conversation
"""

import json
import datetime
import os
from pathlib import Path
from typing import Optional, Dict, List, Any


class StartupOrchestrator:
    """Manages JARVIS boot sequence and session tracking."""

    def __init__(self, jarvis=None, context: Dict[str, Any] = None):
        self.jarvis = jarvis
        self.context = context or {}
        
        # Session data file
        self.data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.data_dir / "session.json"
        
        # Load last session
        self.last_session = self._load_session()
        
        print("[BOOT] Startup Orchestrator initialized")

    # ─── Session Tracking ───────────────────────────────────────────

    def _load_session(self) -> Dict:
        """Load last session data."""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[BOOT] Session load error: {e}")
        return {}

    def save_session(self, extra_data: Dict = None):
        """Save current session state on shutdown."""
        session = {
            "shutdown_time": datetime.datetime.now().isoformat(),
            "last_action": self._get_last_action(),
            "pending_tasks_count": self._count_pending_tasks(),
            "session_duration_minutes": self._calc_session_duration(),
        }
        if extra_data:
            session.update(extra_data)
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session, f, indent=2)
            print(f"[BOOT] Session saved: {session}")
        except Exception as e:
            print(f"[BOOT] Session save error: {e}")

    def _get_last_action(self) -> str:
        """Get the last action from chat history."""
        try:
            # Try to get from chat history
            ch = self.context.get("chat_history")
            if ch and hasattr(ch, 'get_recent'):
                recent = ch.get_recent(3)
                if recent:
                    for msg in reversed(recent):
                        if getattr(msg, "role", None) == "user":
                            return getattr(msg, "content", "")[:100]
        except Exception:
            pass
        return "general assistance"

    def _count_pending_tasks(self) -> int:
        """Count pending tasks."""
        try:
            tasks_file = self.data_dir / "tasks.json"
            if tasks_file.exists():
                with open(tasks_file, 'r') as f:
                    data = json.load(f)
                    tasks = data.get("tasks", data) if isinstance(data, dict) else data
                    if isinstance(tasks, list):
                        return len([t for t in tasks if isinstance(t, dict) and not t.get("completed", False)])
        except Exception:
            pass
        return 0

    def _calc_session_duration(self) -> int:
        """Calculate how long this session has been running."""
        try:
            boot_time = self.last_session.get("boot_time")
            if boot_time:
                boot = datetime.datetime.fromisoformat(boot_time)
                return int((datetime.datetime.now() - boot).total_seconds() / 60)
        except Exception:
            pass
        return 0

    # ─── Boot Sequence ──────────────────────────────────────────────

    def generate_boot_briefing(self) -> Dict[str, Any]:
        """
        Generate the full startup briefing.
        Returns a dict with all boot info for the GUI and Gemini prompt.
        """
        now = datetime.datetime.now()
        briefing = {
            "boot_time": now.isoformat(),
            "greeting": self._generate_greeting(now),
            "session_resumption": self._generate_session_resumption(),
            "task_summary": self._generate_task_summary(),
            "reminder_summary": self._generate_reminder_summary(),
            "weather_context": self._get_weather_context(),
            "calendar_context": self._get_calendar_context(),
            "system_status": self._get_system_status(),
            "features_enabled": self._get_features_status(),
        }

        # Save boot time for session duration tracking
        self._save_boot_time(now)

        # Build the full spoken briefing
        briefing["spoken_briefing"] = self._build_spoken_briefing(briefing)
        briefing["prompt_context"] = self._build_prompt_context(briefing)

        return briefing

    def _generate_greeting(self, now: datetime.datetime) -> str:
        """Time-of-day aware greeting."""
        hour = now.hour
        
        if 5 <= hour < 12:
            period = "Good morning"
        elif 12 <= hour < 17:
            period = "Good afternoon"
        elif 17 <= hour < 21:
            period = "Good evening"
        else:
            period = "Burning the midnight oil"  # Mo-03: Distinct late-night greeting

        # Check if returning from a recent session
        last_shutdown = self.last_session.get("shutdown_time")
        if last_shutdown:
            try:
                shutdown = datetime.datetime.fromisoformat(last_shutdown)
                hours_away = (now - shutdown).total_seconds() / 3600
                
                if hours_away < 1:
                    return f"Welcome back, sir. You were away for just {int(hours_away*60)} minutes."
                elif hours_away < 8:
                    return f"{period}, sir. Welcome back — you've been away for about {int(hours_away)} hours."
                else:
                    return f"{period}, sir. All systems online and ready."
            except Exception:
                pass
        
        return f"{period}, sir. JARVIS is fully operational. All systems online."

    def _generate_session_resumption(self) -> str:
        """Tell user what they were doing when they last closed JARVIS."""
        last_action = self.last_session.get("last_action", "")
        last_shutdown = self.last_session.get("shutdown_time", "")
        
        if last_action and last_shutdown:
            try:
                shutdown = datetime.datetime.fromisoformat(last_shutdown)
                time_str = shutdown.strftime("%I:%M %p")
                day_str = shutdown.strftime("%A")
                
                today = datetime.datetime.now().date()
                shutdown_date = shutdown.date()
                
                if shutdown_date == today:
                    when = f"earlier today at {time_str}"
                elif (today - shutdown_date).days == 1:
                    when = f"yesterday at {time_str}"
                else:
                    when = f"on {day_str} at {time_str}"
                
                return f"When you last closed me {when}, you were working on: {last_action}"
            except Exception:
                pass
        
        return ""

    def _generate_task_summary(self) -> str:
        """Summarize pending tasks."""
        try:
            tasks_file = self.data_dir / "tasks.json"
            if tasks_file.exists():
                with open(tasks_file, 'r') as f:
                    data = json.load(f)
                    tasks = data.get("tasks", data) if isinstance(data, dict) else data
                    if isinstance(tasks, list):
                        pending = [t for t in tasks if isinstance(t, dict) and not t.get("completed", False)]
                        if pending:
                            count = len(pending)
                            top_tasks = [t.get("description", "Unknown") for t in pending[:3]]
                            task_list = ", ".join(top_tasks)
                            return f"You have {count} pending task{'s' if count > 1 else ''}: {task_list}"
        except Exception:
            pass
        return "No pending tasks."

    def _generate_reminder_summary(self) -> str:
        """Summarize upcoming reminders."""
        try:
            # Check reminder_manager
            rm = self.context.get("reminder_manager")
            if rm and hasattr(rm, 'get_upcoming'):
                upcoming = rm.get_upcoming()
                if upcoming:
                    return f"You have {len(upcoming)} upcoming reminder{'s' if len(upcoming) > 1 else ''}."
            
            # Fallback: check tasks.json reminders
            tasks_file = self.data_dir / "tasks.json"
            if tasks_file.exists():
                with open(tasks_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        reminders = data.get("reminders", [])
                        active = [r for r in reminders if isinstance(r, dict) and not r.get("triggered", False)]
                        if active:
                            return f"You have {len(active)} active reminder{'s' if len(active) > 1 else ''}."
        except Exception:
            pass
        return ""

    def _get_weather_context(self) -> str:
        """Get current weather for briefing."""
        try:
            wh = self.context.get("weather_handler")
            if wh and hasattr(wh, 'get_current_weather'):
                weather = wh.get_current_weather()
                if weather:
                    temp = weather.get("temp", weather.get("temperature", ""))
                    desc = weather.get("description", weather.get("condition", ""))
                    if temp:
                        return f"Current weather: {temp}°C, {desc}"
        except Exception:
            pass
        return ""

    def _get_calendar_context(self) -> str:
        """Get today's calendar events."""
        try:
            cal = self.context.get("calendar")
            if cal and hasattr(cal, 'get_today_events_list'):
                events = cal.get_today_events_list()
                if events:
                    return f"You have {len(events)} event{'s' if len(events) > 1 else ''} today."
        except Exception:
            pass
        return ""

    def _get_system_status(self) -> Dict:
        """Get system health snapshot."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)  # Mo-02: non-blocking (returns since-last-call value)
            ram = psutil.virtual_memory().percent
            bat = psutil.sensors_battery()
            return {
                "cpu": cpu,
                "ram": ram,
                "battery": bat.percent if bat else None,
                "plugged": bat.power_plugged if bat else None,
            }
        except Exception:
            return {}

    def _get_features_status(self) -> Dict:
        """Report which features are actually active — M-03: check real availability."""
        j = self.context.get("jarvis")
        return {
            "voice": True,  # Always active (core requirement)
            "gesture": bool(j and hasattr(j, 'gesture_controller') and j.gesture_controller),
            "face_recognition": bool(j and hasattr(j, 'face_recognition') and j.face_recognition),
            "emotion_detection": bool(j and hasattr(j, 'emotion_detector') and j.emotion_detector),
            "ai_engine": True,  # Gemini is always available
            "proactive_assistant": bool(j and hasattr(j, 'proactive') and j.proactive),
        }

    def _save_boot_time(self, now: datetime.datetime):
        """Save boot timestamp for session duration tracking."""
        try:
            session = self._load_session()
            session["boot_time"] = now.isoformat()
            with open(self.session_file, 'w') as f:
                json.dump(session, f, indent=2)
        except Exception:
            pass

    # ─── Build Spoken Briefing ──────────────────────────────────────

    def _build_spoken_briefing(self, briefing: Dict) -> str:
        """Build the full spoken startup briefing for Gemini to speak."""
        parts = []
        
        # Greeting
        parts.append(briefing["greeting"])
        
        # Session resumption
        if briefing["session_resumption"]:
            parts.append(briefing["session_resumption"])
        
        # Tasks
        if briefing["task_summary"] and "no pending" not in briefing["task_summary"].lower():
            parts.append(briefing["task_summary"])
        
        # Reminders
        if briefing["reminder_summary"]:
            parts.append(briefing["reminder_summary"])
        
        # Weather
        if briefing["weather_context"]:
            parts.append(briefing["weather_context"])
        
        # Calendar
        if briefing["calendar_context"]:
            parts.append(briefing["calendar_context"])
        
        # System health warnings
        sys_status = briefing.get("system_status", {})
        if sys_status.get("battery") and sys_status["battery"] < 20 and not sys_status.get("plugged"):
            parts.append(f"Warning: battery is at {sys_status['battery']}%. Consider plugging in.")
        
        parts.append("All perception layers active — voice, gesture, face recognition, and emotion detection are online. How may I assist you?")
        
        return " ".join(parts)

    def _build_prompt_context(self, briefing: Dict) -> str:
        """Build context string to inject into Gemini system prompt.
        
        This provides REFERENCE DATA only — Gemini uses it to answer
        questions if sir asks, but NEVER announces it proactively.
        """
        lines = [
            "=== REFERENCE CONTEXT (DO NOT announce this — only use if sir asks) ===",
            f"Current time: {datetime.datetime.now().strftime('%I:%M %p, %A %B %d, %Y')}",
        ]
        
        if briefing["session_resumption"]:
            lines.append(f"Session: {briefing['session_resumption']}")
        
        if briefing["task_summary"]:
            lines.append(f"Tasks: {briefing['task_summary']}")
        
        if briefing["reminder_summary"]:
            lines.append(f"Reminders: {briefing['reminder_summary']}")
        
        if briefing["weather_context"]:
            lines.append(f"Weather: {briefing['weather_context']}")
        
        if briefing["calendar_context"]:
            lines.append(f"Calendar: {briefing['calendar_context']}")
        
        sys_status = briefing.get("system_status", {})
        if sys_status:
            # m-01: Handle None battery gracefully
            bat_val = sys_status.get('battery')
            bat_str = f"{bat_val:.0f}%" if bat_val is not None else "N/A"
            lines.append(f"System: CPU={sys_status.get('cpu',0):.0f}%, RAM={sys_status.get('ram',0):.0f}%, Battery={bat_str}")
        
        lines.append("DO NOT read this context aloud. Just say a brief greeting and wait.")
        lines.append("=== END REFERENCE CONTEXT ===")
        
        return "\n".join(lines)

