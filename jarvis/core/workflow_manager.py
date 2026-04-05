"""
Workflow Manager - Hands-Free Multi-Action Workflows
====================================================
Chain multiple actions from a single voice command.
Example: "Open Chrome, search for AI, and take a screenshot"
"""

import time
import re
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class WorkflowAction(Enum):
    """Types of workflow actions"""
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    SEARCH = "search"
    TAKE_SCREENSHOT = "screenshot"
    TYPE_TEXT = "type"
    WAIT = "wait"
    SCROLL = "scroll"
    CLICK = "click"
    SWITCH_APP = "switch_app"
    PLAY_MUSIC = "play_music"
    PAUSE_MUSIC = "pause_music"


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    action: WorkflowAction
    params: Dict[str, Any] = field(default_factory=dict)
    delay: float = 0.5  # Seconds to wait after this step


@dataclass
class Workflow:
    """A complete workflow with multiple steps"""
    name: str
    steps: List[WorkflowStep]
    description: str = ""


class WorkflowManager:
    """
    Execute multi-step workflows from single voice commands.
    
    Example commands:
    - "Open Chrome and search for Python tutorials"
    - "Open Spotify, play music, and minimize"
    - "Take a screenshot and save it"
    """
    
    # Predefined workflow templates
    WORKFLOW_TEMPLATES = {
        "morning routine": [
            WorkflowStep(WorkflowAction.OPEN_APP, {"app": "spotify"}),
            WorkflowStep(WorkflowAction.PLAY_MUSIC, {}),
            WorkflowStep(WorkflowAction.OPEN_APP, {"app": "chrome"}),
            WorkflowStep(WorkflowAction.SEARCH, {"query": "morning news"}),
        ],
        "focus mode": [
            WorkflowStep(WorkflowAction.OPEN_APP, {"app": "spotify"}),
            WorkflowStep(WorkflowAction.PLAY_MUSIC, {}),
            WorkflowStep(WorkflowAction.SWITCH_APP, {"app": "vscode"}),
        ],
        "screenshot workflow": [
            WorkflowStep(WorkflowAction.WAIT, {"seconds": 2}),
            WorkflowStep(WorkflowAction.TAKE_SCREENSHOT, {}),
        ],
    }
    
    def __init__(self, jarvis_core=None, perception=None):
        print("[WORKFLOW] Initializing Workflow Manager...")
        self.jarvis = jarvis_core
        self.perception = perception
        self.current_workflow: Optional[Workflow] = None
        self.is_running = False
        
        print("[WORKFLOW] Workflow Manager Ready")
    
    def _get_title(self) -> str:
        if self.perception and hasattr(self.perception, 'current_title'):
            return self.perception.current_title
        return "sir"
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[WORKFLOW] {text}")
    
    def parse_workflow(self, command: str) -> Optional[Workflow]:
        """
        Parse a multi-action command into a workflow.
        
        Supports patterns like:
        - "open X and do Y"
        - "first X, then Y, and finally Z"
        - "X and then Y"
        """
        command_lower = command.lower()
        steps = []
        
        # Split on conjunctions
        parts = re.split(r'\s+and\s+|\s+then\s+|\s*,\s*', command_lower)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) < 2:
            return None  # Not a multi-step command
        
        for part in parts:
            step = self._parse_single_action(part)
            if step:
                steps.append(step)
        
        if len(steps) >= 2:
            return Workflow(
                name="voice_workflow",
                steps=steps,
                description=command
            )
        
        return None
    
    def _parse_single_action(self, text: str) -> Optional[WorkflowStep]:
        """Parse a single action from text"""
        text = text.strip()
        
        # Open app
        if text.startswith("open "):
            app = text.replace("open ", "").strip()
            return WorkflowStep(WorkflowAction.OPEN_APP, {"app": app})
        
        # Close app
        if text.startswith("close "):
            app = text.replace("close ", "").strip()
            return WorkflowStep(WorkflowAction.CLOSE_APP, {"app": app})
        
        # Search
        if "search for " in text or "search " in text:
            query = re.sub(r'^.*?search\s+(?:for\s+)?', '', text)
            return WorkflowStep(WorkflowAction.SEARCH, {"query": query})
        
        # Screenshot
        if "screenshot" in text or "screen shot" in text:
            return WorkflowStep(WorkflowAction.TAKE_SCREENSHOT, {})
        
        # Type
        if text.startswith("type "):
            content = text.replace("type ", "").strip()
            return WorkflowStep(WorkflowAction.TYPE_TEXT, {"text": content})
        
        # Scroll
        if "scroll down" in text:
            return WorkflowStep(WorkflowAction.SCROLL, {"direction": "down"})
        if "scroll up" in text:
            return WorkflowStep(WorkflowAction.SCROLL, {"direction": "up"})
        
        # Play/Pause music
        if "play music" in text or "play" == text:
            return WorkflowStep(WorkflowAction.PLAY_MUSIC, {})
        if "pause" in text or "stop music" in text:
            return WorkflowStep(WorkflowAction.PAUSE_MUSIC, {})
        
        # Switch app
        if text.startswith("switch to "):
            app = text.replace("switch to ", "").strip()
            return WorkflowStep(WorkflowAction.SWITCH_APP, {"app": app})
        
        # Minimize
        if "minimize" in text:
            return WorkflowStep(WorkflowAction.SCROLL, {"action": "minimize"})
        
        # Wait
        wait_match = re.search(r'wait\s+(\d+)\s*(?:seconds?)?', text)
        if wait_match:
            seconds = int(wait_match.group(1))
            return WorkflowStep(WorkflowAction.WAIT, {"seconds": seconds})
        
        return None
    
    def execute_workflow(self, workflow: Workflow) -> bool:
        """Execute a workflow step by step"""
        title = self._get_title()
        self._speak(f"Starting workflow with {len(workflow.steps)} steps, {title}.")
        
        self.current_workflow = workflow
        self.is_running = True
        
        for i, step in enumerate(workflow.steps, 1):
            if not self.is_running:
                self._speak("Workflow cancelled.")
                return False
            
            print(f"[WORKFLOW] Step {i}/{len(workflow.steps)}: {step.action.value}")
            
            success = self._execute_step(step)
            if not success:
                self._speak(f"Step {i} failed. Stopping workflow.")
                self.is_running = False
                return False
            
            # Delay between steps
            if step.delay > 0 and i < len(workflow.steps):
                time.sleep(step.delay)
        
        self._speak("Workflow complete.")
        self.is_running = False
        return True
    
    def _execute_step(self, step: WorkflowStep) -> bool:
        """Execute a single workflow step"""
        try:
            import pyautogui
            
            if step.action == WorkflowAction.OPEN_APP:
                app = step.params.get("app", "")
                if self.jarvis:
                    self.jarvis.handle_input(f"open {app}")
                else:
                    # Fallback: use Windows Run
                    pyautogui.hotkey('win', 's')
                    time.sleep(0.3)
                    pyautogui.typewrite(app)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                return True
            
            elif step.action == WorkflowAction.CLOSE_APP:
                pyautogui.hotkey('alt', 'f4')
                return True
            
            elif step.action == WorkflowAction.SEARCH:
                query = step.params.get("query", "")
                # Type in search/address bar
                pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                time.sleep(0.2)
                pyautogui.typewrite(query, interval=0.02)
                pyautogui.press('enter')
                return True
            
            elif step.action == WorkflowAction.TAKE_SCREENSHOT:
                if self.jarvis:
                    self.jarvis.handle_input("take a screenshot")
                else:
                    pyautogui.screenshot().save(f"screenshot_{int(time.time())}.png")
                return True
            
            elif step.action == WorkflowAction.TYPE_TEXT:
                text = step.params.get("text", "")
                pyautogui.typewrite(text, interval=0.02)
                return True
            
            elif step.action == WorkflowAction.SCROLL:
                direction = step.params.get("direction", "down")
                amount = 3 if direction == "down" else -3
                pyautogui.scroll(amount)
                return True
            
            elif step.action == WorkflowAction.PLAY_MUSIC:
                pyautogui.press('playpause')
                return True
            
            elif step.action == WorkflowAction.PAUSE_MUSIC:
                pyautogui.press('playpause')
                return True
            
            elif step.action == WorkflowAction.SWITCH_APP:
                app = step.params.get("app", "")
                if self.jarvis:
                    self.jarvis.handle_input(f"switch to {app}")
                else:
                    pyautogui.hotkey('alt', 'tab')
                return True
            
            elif step.action == WorkflowAction.WAIT:
                seconds = step.params.get("seconds", 1)
                time.sleep(seconds)
                return True
            
            return False
            
        except Exception as e:
            print(f"[WORKFLOW] Step error: {e}")
            return False
    
    def stop_workflow(self):
        """Stop the current workflow"""
        self.is_running = False
        self._speak("Workflow stopped.")
    
    def run_template(self, template_name: str) -> bool:
        """Run a predefined workflow template"""
        template_lower = template_name.lower()
        
        if template_lower in self.WORKFLOW_TEMPLATES:
            steps = self.WORKFLOW_TEMPLATES[template_lower]
            workflow = Workflow(
                name=template_lower,
                steps=steps,
                description=f"Template: {template_lower}"
            )
            return self.execute_workflow(workflow)
        
        self._speak(f"I don't know that workflow template.")
        return False
    
    def handle(self, command: str) -> str:
        """Handle workflow commands"""
        command_lower = command.lower()
        
        # Stop workflow
        if "stop workflow" in command_lower or "cancel workflow" in command_lower:
            self.stop_workflow()
            return "Workflow stopped."
        
        # Run template
        if "morning routine" in command_lower:
            self.run_template("morning routine")
            return "Running morning routine."
        
        if "focus mode" in command_lower:
            self.run_template("focus mode")
            return "Entering focus mode."
        
        # Parse and execute custom workflow
        workflow = self.parse_workflow(command)
        if workflow:
            self.execute_workflow(workflow)
            return f"Executed {len(workflow.steps)}-step workflow."
        
        return "I couldn't parse that as a workflow."
    
    def is_workflow_command(self, command: str) -> bool:
        """Check if command looks like a multi-step workflow"""
        command_lower = command.lower()
        
        # Check for templates
        if any(t in command_lower for t in ["morning routine", "focus mode", "workflow"]):
            return True
        
        # Check for multi-action patterns
        multi_action_patterns = [
            r'\band\s+(?:then\s+)?(?:open|close|search|type|scroll)',
            r',\s*(?:then\s+)?(?:open|close|search|type|scroll)',
            r'\bthen\s+(?:open|close|search|type|scroll)',
        ]
        
        for pattern in multi_action_patterns:
            if re.search(pattern, command_lower):
                return True
        
        return False


# Singleton
_workflow_instance = None

def get_workflow_manager(jarvis_core=None, perception=None) -> WorkflowManager:
    """Get or create workflow manager"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = WorkflowManager(jarvis_core, perception)
    return _workflow_instance
