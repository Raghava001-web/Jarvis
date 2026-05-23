"""
Task Manager - Tasks & Reminders
"""

import json
import datetime
import uuid
from pathlib import Path
import re


class TaskManager:
    """Manages tasks and basic reminders"""

    def __init__(self, perception):
        print("[TASK MANAGER] Initializing Task Manager...")
        self.perception = perception

        self.data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        self.data_dir.mkdir(exist_ok=True)

        self.tasks_file = self.data_dir / "tasks.json"
        self._load_tasks()

        print("[TASK MANAGER] Ready")

    def _get_title(self):
        return getattr(self.perception, 'user_title', 'sir')

    def _default_data(self):
        return {
            "tasks": [],
            "reminders": []
        }

    def _load_tasks(self):
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r") as f:
                    loaded_data = json.load(f)
                    
                    # Handle old format (list) vs new format (dict)
                    if isinstance(loaded_data, list):
                        # Old format - convert to new format
                        self.data = {
                            "tasks": loaded_data,
                            "reminders": []
                        }
                        self._save()  # Save in new format
                    elif isinstance(loaded_data, dict):
                        # New format - ensure it has required keys
                        if "tasks" not in loaded_data:
                            loaded_data["tasks"] = []
                        if "reminders" not in loaded_data:
                            loaded_data["reminders"] = []
                        self.data = loaded_data
                    else:
                        self.data = self._default_data()
            except Exception as e:
                print(f"ERROR: Failed to load tasks: {e}")
                self.data = self._default_data()
        else:
            self.data = self._default_data()

    def _save(self):
        with open(self.tasks_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_task(self, description: str):
        title = self._get_title()
        if not description or len(description.strip()) < 3:
            self.perception.speak(f"Task description is too short, {title}.")
            return False

        task = {
            "id": str(uuid.uuid4()),
            "description": description.strip(),
            "created": datetime.datetime.now().isoformat(),
            "completed": False
        }

        self.data["tasks"].append(task)
        self._save()
        self.perception.speak(f"Task added: {description}, {title}.")
        return True

    def set_reminder(self, description: str, when: str):
        reminder_time = self._parse_time(when)

        reminder = {
            "id": str(uuid.uuid4()),
            "description": description,
            "time": reminder_time.isoformat(),
            "triggered": False
        }

        self.data["reminders"].append(reminder)
        self._save()
        self.perception.speak(
            f"Reminder set for {reminder_time.strftime('%I:%M %p')}, {self._get_title()}."
        )
        return True

    def _parse_time(self, text: str):
        now = datetime.datetime.now()

        if "tomorrow" in text:
            time_match = re.search(r'(\d{1,2})\s*(am|pm)', text.lower())
            hour = 9
            if time_match:
                hour = int(time_match.group(1))
                if time_match.group(2) == "pm" and hour != 12:
                    hour += 12
            return (now + datetime.timedelta(days=1)).replace(hour=hour, minute=0, second=0)

        hours_match = re.search(r'in\s+(\d+)\s+hour', text.lower())
        if hours_match:
            return now + datetime.timedelta(hours=int(hours_match.group(1)))

        return now + datetime.timedelta(hours=1)

    def check_reminders(self):
        """Call periodically from main loop"""
        try:
            # Ensure data structure is correct
            if not isinstance(self.data, dict):
                self.data = self._default_data()
            
            if "reminders" not in self.data:
                self.data["reminders"] = []
            
            now = datetime.datetime.now()
            reminders_to_save = False

            for reminder in self.data["reminders"]:
                if not isinstance(reminder, dict):
                    continue
                    
                if reminder.get("triggered", False):
                    continue

                try:
                    trigger_time = datetime.datetime.fromisoformat(reminder["time"])
                    if now >= trigger_time:
                        self.perception.speak(
                            f"Reminder: {reminder.get('description', 'Reminder')}, {self._get_title()}."
                        )
                        reminder["triggered"] = True
                        reminders_to_save = True
                except (KeyError, ValueError) as e:
                    # Skip invalid reminders
                    print(f"ERROR: Invalid reminder format: {e}")
                    continue

            if reminders_to_save:
                self._save()
        except Exception as e:
            # Silently handle errors to prevent spam
            pass

    def list_tasks(self):
        title = self._get_title()
        # Filter to valid task dicts that aren't completed
        pending = [t for t in self.data["tasks"] 
                   if isinstance(t, dict) and not t.get("completed", False)]

        if not pending:
            self.perception.speak(f"No pending tasks, {title}.")
            return f"No pending tasks, {title}."

        self.perception.speak(f"You have {len(pending)} pending tasks, {title}.")
        lines = [f"You have {len(pending)} pending tasks, {title}."]
        for i, task in enumerate(pending[:5], 1):
            desc = task.get('description', task.get('title', f'Task {i}'))
            self.perception.speak(f"Task {i}: {desc}")
            lines.append(f"  {i}. {desc}")

        return "\n".join(lines)

    def complete_task_by_index(self, index: int):
        title = self._get_title()
        # BUG FIX: Add isinstance guard to prevent TypeError on corrupted entries
        pending = [t for t in self.data["tasks"] 
                   if isinstance(t, dict) and not t.get("completed", False)]

        if index < 1 or index > len(pending):
            self.perception.speak(f"Invalid task number, {title}.")
            return False

        task = pending[index - 1]
        task["completed"] = True
        task["completed_at"] = datetime.datetime.now().isoformat()
        self._save()
        self.perception.speak(f"Task completed, {title}.")
        return True
