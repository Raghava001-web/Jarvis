"""
Screenshot Handler - Screen capture capabilities
Captures full screen or specific regions
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class ScreenshotHandler:
    """Handles screenshot capture and management"""
    
    def __init__(self, perception=None):
        print("[SCREENSHOT] Initializing Screenshot Handler...")
        self.perception = perception
        
        # Screenshot save directory
        self.save_dir = Path.home() / "Pictures" / "JARVIS_Screenshots"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for pyautogui
        self.pyautogui_available = False
        try:
            import pyautogui
            self.pyautogui_available = True
            print("[SCREENSHOT] pyautogui available")
        except ImportError:
            print("[SCREENSHOT] pyautogui not available")
        
        # Check for PIL
        self.pil_available = False
        try:
            from PIL import ImageGrab
            self.pil_available = True
            print("[SCREENSHOT] PIL available")
        except ImportError:
            print("[SCREENSHOT] PIL not available")
        
        print("[SCREENSHOT] Screenshot Handler Ready")
    
    def _get_title(self) -> str:
        """Get user title from perception layer"""
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        """Speak text via perception layer"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[SCREENSHOT] {text}")
    
    def _generate_filename(self, prefix: str = "screenshot") -> Path:
        """Generate a unique filename for screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        return self.save_dir / filename
    
    def take_screenshot(self, region: tuple = None, filename: str = None) -> Optional[Path]:
        """Take a screenshot of the full screen or a specific region
        
        Args:
            region: Optional tuple (x, y, width, height) for specific region
            filename: Optional custom filename
            
        Returns:
            Path to saved screenshot or None
        """
        title = self._get_title()
        
        if not self.pyautogui_available and not self.pil_available:
            self._speak(f"Screenshot capability is not available, {title}. Please install pyautogui or Pillow.")
            return None
        
        try:
            self._speak(f"Taking screenshot, {title}.")
            
            # Generate save path
            save_path = Path(filename) if filename else self._generate_filename()
            if not save_path.suffix:
                save_path = save_path.with_suffix('.png')
            
            # Take screenshot using pyautogui (preferred)
            if self.pyautogui_available:
                import pyautogui
                
                if region:
                    screenshot = pyautogui.screenshot(region=region)
                else:
                    screenshot = pyautogui.screenshot()
                
                screenshot.save(str(save_path))
            
            # Fallback to PIL
            elif self.pil_available:
                from PIL import ImageGrab
                
                if region:
                    # Convert (x, y, w, h) to (x1, y1, x2, y2)
                    x, y, w, h = region
                    bbox = (x, y, x + w, y + h)
                    screenshot = ImageGrab.grab(bbox=bbox)
                else:
                    screenshot = ImageGrab.grab()
                
                screenshot.save(str(save_path))
            
            self._speak(f"Done, {title}. Screenshot saved.")
            return save_path
            
        except Exception as e:
            print(f"[SCREENSHOT] Error: {e}")
            self._speak(f"Failed to take screenshot, {title}.")
            return None
    
    def take_fullscreen(self) -> Optional[Path]:
        """Take a full screen screenshot"""
        return self.take_screenshot()
    
    def take_region(self, x: int, y: int, width: int, height: int) -> Optional[Path]:
        """Take a screenshot of a specific region"""
        return self.take_screenshot(region=(x, y, width, height))
    
    def copy_to_clipboard(self) -> bool:
        """Take screenshot and copy to clipboard"""
        title = self._get_title()
        
        try:
            if self.pil_available:
                from PIL import ImageGrab
                import io
                
                screenshot = ImageGrab.grab()
                
                # Copy to clipboard using win32clipboard
                try:
                    import win32clipboard
                    from io import BytesIO
                    
                    output = BytesIO()
                    screenshot.convert('RGB').save(output, 'BMP')
                    data = output.getvalue()[14:]  # Remove BMP header
                    output.close()
                    
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                    win32clipboard.CloseClipboard()
                    
                    self._speak(f"Screenshot copied to clipboard, {title}.")
                    return True
                except ImportError:
                    # Fallback: save and notify
                    path = self.take_screenshot()
                    self._speak(f"Clipboard access not available. Screenshot saved to {path.name}.")
                    return True
            
            self._speak(f"Could not copy screenshot to clipboard, {title}.")
            return False
            
        except Exception as e:
            print(f"[SCREENSHOT] Clipboard error: {e}")
            self._speak(f"Failed to copy screenshot, {title}.")
            return False
    
    def get_recent_screenshots(self, count: int = 5) -> list:
        """Get list of recent screenshots"""
        try:
            screenshots = sorted(
                self.save_dir.glob("*.png"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            return screenshots[:count]
        except Exception as e:
            print(f"[SCREENSHOT] Error listing screenshots: {e}")
            return []
    
    def open_screenshot_folder(self) -> bool:
        """Open the screenshot save folder"""
        title = self._get_title()
        
        try:
            os.startfile(str(self.save_dir))
            self._speak(f"Opening screenshot folder, {title}.")
            return True
        except Exception as e:
            print(f"[SCREENSHOT] Error opening folder: {e}")
            self._speak(f"Could not open screenshot folder, {title}.")
            return False
