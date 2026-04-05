"""
Learning Layer - Data & Analytics
Tracks interactions and learns patterns
"""

import json
import datetime
from pathlib import Path


class LearningLayer:
    """Learns from interactions and improves"""

    def __init__(self, understanding):
        print("[LEARNING] Initializing Learning Layer...")
        self.understanding = understanding
        
        # Data directory
        self.data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.learning_file = self.data_dir / "learning.json"
        self._load_data()
        
        print("[LEARNING] Layer Ready")

    def _load_data(self):
        """Load learning data from file"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {
                    "command_history": [],
                    "preferences": {},
                    "stats": {
                        "total_commands": 0,
                        "successful_commands": 0,
                        "accuracy": 0.0
                    }
                }
        else:
            self.data = {
                "command_history": [],
                "preferences": {},
                "stats": {
                    "total_commands": 0,
                    "successful_commands": 0,
                    "accuracy": 0.0
                }
            }

    def _save_data(self):
        """Save learning data to file"""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"ERROR: Save error: {e}")

    def log_command(self, command: str, intent: str, confidence: float, success: bool):
        """Log a command interaction"""
        entry = {
            "command": command,
            "intent": intent,
            "confidence": confidence,
            "success": success,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.data["command_history"].append(entry)
        
        # Keep only last 1000 entries
        if len(self.data["command_history"]) > 1000:
            self.data["command_history"] = self.data["command_history"][-1000:]
        
        # Update stats
        self.data["stats"]["total_commands"] += 1
        if success:
            self.data["stats"]["successful_commands"] += 1
        
        total = self.data["stats"]["total_commands"]
        successful = self.data["stats"]["successful_commands"]
        self.data["stats"]["accuracy"] = successful / total if total > 0 else 0.0
        
        # Update preferences
        if intent not in self.data["preferences"]:
            self.data["preferences"][intent] = {"count": 0, "success_rate": 0.0}
        
        self.data["preferences"][intent]["count"] += 1
        
        self._save_data()

    def get_most_used_intents(self, limit: int = 5):
        """Get most frequently used intents"""
        intent_counts = {}
        for entry in self.data["command_history"]:
            intent = entry["intent"]
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_intents[:limit]

    def get_accuracy_by_intent(self):
        """Get success rate by intent"""
        intent_stats = {}
        for entry in self.data["command_history"]:
            intent = entry["intent"]
            if intent not in intent_stats:
                intent_stats[intent] = {"total": 0, "successful": 0}
            
            intent_stats[intent]["total"] += 1
            if entry["success"]:
                intent_stats[intent]["successful"] += 1
        
        accuracy = {}
        for intent, stats in intent_stats.items():
            accuracy[intent] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0.0
        
        return accuracy

    def analyze_patterns(self):
        """Analyze user patterns"""
        if not self.data["command_history"]:
            return {}
        
        # Time-based patterns
        hour_counts = {}
        for entry in self.data["command_history"]:
            timestamp = datetime.datetime.fromisoformat(entry["timestamp"])
            hour = timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        
        return {
            "most_active_hour": most_active_hour,
            "total_interactions": len(self.data["command_history"]),
            "accuracy": self.data["stats"]["accuracy"],
            "top_intents": self.get_most_used_intents(3)
        }
