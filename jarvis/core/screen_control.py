"""
Screen Control Handler - Voice-driven mouse and keyboard control
Allows JARVIS to control screen via voice commands
"""

from typing import Dict, Any, Optional, Tuple
import time

# Optional imports
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class ScreenControlHandler:
    """
    Voice-controlled screen interaction.
    Commands: click, double click, right click, scroll, move mouse
    """
    
    def __init__(self):
        print("[SCREEN] Initializing Screen Control...")
        
        self.pyautogui_available = PYAUTOGUI_AVAILABLE
        self.keyboard_available = KEYBOARD_AVAILABLE
        
        if PYAUTOGUI_AVAILABLE:
            print("[SCREEN] pyautogui available")
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            print("[SCREEN] pyautogui not available - screen control disabled")
            self.screen_width, self.screen_height = 1920, 1080
        
        # Named positions for quick navigation
        self.named_positions = {
            "center": (0.5, 0.5),
            "top left": (0.1, 0.1),
            "top right": (0.9, 0.1),
            "bottom left": (0.1, 0.9),
            "bottom right": (0.9, 0.9),
            "top": (0.5, 0.1),
            "bottom": (0.5, 0.9),
            "left": (0.1, 0.5),
            "right": (0.9, 0.5),
        }
        
        print("[SCREEN] Screen Control Ready")
    
    def handle(self, command: str, entities: Dict[str, Any] = None) -> str:
        """Handle screen control commands"""
        if not self.pyautogui_available:
            return "Screen control is not available. Please install pyautogui."
        
        command_lower = command.lower()
        
        # Click commands
        if "double click" in command_lower or "double-click" in command_lower:
            return self._double_click()
        elif "right click" in command_lower or "right-click" in command_lower:
            return self._right_click()
        elif "click" in command_lower:
            position = self._extract_position(command_lower)
            return self._click(position)
        
        # Scroll commands
        elif "scroll down" in command_lower:
            amount = self._extract_amount(command_lower, default=3)
            return self._scroll(-amount)
        elif "scroll up" in command_lower:
            amount = self._extract_amount(command_lower, default=3)
            return self._scroll(amount)
        
        # Move commands
        elif "move mouse" in command_lower or "move cursor" in command_lower:
            position = self._extract_position(command_lower)
            if position:
                return self._move_to(position)
            return "Please specify where to move the cursor."
        
        # Keyboard commands
        elif any(key in command_lower for key in ["press enter", "hit enter", "press escape", "press tab"]):
            return self._press_key(command_lower)
        
        # Type command
        elif "type" in command_lower:
            text = self._extract_text_to_type(command)
            if text:
                return self._type_text(text)
            return "Please specify what to type."
        
        # Hotkey combinations
        elif "copy" in command_lower:
            return self._hotkey("ctrl", "c")
        elif "paste" in command_lower:
            return self._hotkey("ctrl", "v")
        elif "undo" in command_lower:
            return self._hotkey("ctrl", "z")
        elif "redo" in command_lower:
            return self._hotkey("ctrl", "y")
        elif "select all" in command_lower:
            return self._hotkey("ctrl", "a")
        elif "save" in command_lower:
            return self._hotkey("ctrl", "s")
        elif "close" in command_lower and ("window" in command_lower or "tab" in command_lower):
            return self._hotkey("ctrl", "w")
        elif "switch window" in command_lower or "alt tab" in command_lower:
            return self._hotkey("alt", "tab")
        
        # Window management
        elif "minimize" in command_lower:
            return self._hotkey("win", "down")
        elif "maximize" in command_lower:
            return self._hotkey("win", "up")
        elif "restore" in command_lower:
            return self._hotkey("win", "down")
        
        return "I didn't understand that screen control command."
    
    def _click(self, position: Optional[Tuple[int, int]] = None) -> str:
        """Perform a click"""
        if position:
            pyautogui.click(position[0], position[1])
            return f"Clicked at position {position}."
        else:
            pyautogui.click()
            return "Clicked at current cursor position."
    
    def _double_click(self) -> str:
        """Perform a double click"""
        pyautogui.doubleClick()
        return "Double clicked."
    
    def _right_click(self) -> str:
        """Perform a right click"""
        pyautogui.rightClick()
        return "Right clicked."
    
    def _scroll(self, amount: int) -> str:
        """Scroll the mouse wheel"""
        pyautogui.scroll(amount)
        direction = "up" if amount > 0 else "down"
        return f"Scrolled {direction}."
    
    def _move_to(self, position: Tuple[int, int]) -> str:
        """Move cursor to position"""
        pyautogui.moveTo(position[0], position[1], duration=0.3)
        return f"Moved cursor to {position}."
    
    def _press_key(self, command: str) -> str:
        """Press a keyboard key"""
        if "enter" in command:
            pyautogui.press("enter")
            return "Pressed Enter."
        elif "escape" in command or "esc" in command:
            pyautogui.press("escape")
            return "Pressed Escape."
        elif "tab" in command:
            pyautogui.press("tab")
            return "Pressed Tab."
        elif "backspace" in command:
            pyautogui.press("backspace")
            return "Pressed Backspace."
        elif "delete" in command:
            pyautogui.press("delete")
            return "Pressed Delete."
        elif "space" in command:
            pyautogui.press("space")
            return "Pressed Space."
        return "Unknown key."
    
    def _type_text(self, text: str) -> str:
        """Type text"""
        pyautogui.typewrite(text, interval=0.02)
        return f"Typed: {text}"
    
    def _hotkey(self, *keys) -> str:
        """Press a hotkey combination"""
        pyautogui.hotkey(*keys)
        combo = " + ".join(keys)
        return f"Pressed {combo}."
    
    def _extract_position(self, command: str) -> Optional[Tuple[int, int]]:
        """Extract position from command"""
        # Check for named positions
        for name, (rx, ry) in self.named_positions.items():
            if name in command:
                x = int(self.screen_width * rx)
                y = int(self.screen_height * ry)
                return (x, y)
        
        # Try to extract coordinates (e.g., "at 500, 300")
        import re
        coord_match = re.search(r'(\d+)\s*,\s*(\d+)', command)
        if coord_match:
            x = int(coord_match.group(1))
            y = int(coord_match.group(2))
            return (x, y)
        
        return None
    
    def _extract_amount(self, command: str, default: int = 3) -> int:
        """Extract scroll amount from command"""
        import re
        match = re.search(r'(\d+)', command)
        if match:
            return int(match.group(1))
        
        # Word-based amounts
        if "a lot" in command or "much" in command:
            return 10
        elif "a little" in command or "slightly" in command:
            return 1
        
        return default
    
    def _extract_text_to_type(self, command: str) -> Optional[str]:
        """Extract text to type from command"""
        # Try to find quoted text
        import re
        quoted = re.search(r'["\'](.+?)["\']', command)
        if quoted:
            return quoted.group(1)
        
        # Try "type X" pattern
        match = re.search(r'type\s+(.+?)(?:\s*$|\s+and\s+)', command, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def get_current_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        if self.pyautogui_available:
            return pyautogui.position()
        return (0, 0)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions"""
        return (self.screen_width, self.screen_height)
