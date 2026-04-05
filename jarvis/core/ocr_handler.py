"""
OCR Handler - Optical Character Recognition
Extract text from images on screen or from files
"""

import os
from pathlib import Path
from typing import Optional


class OCRHandler:
    """Extracts text from images using OCR"""
    
    def __init__(self, perception=None):
        print("[OCR] Initializing OCR Handler...")
        self.perception = perception
        
        # Check for pytesseract
        self.pytesseract_available = False
        self.tesseract_path = None
        
        try:
            import pytesseract
            self.pytesseract_available = True
            
            # Common Windows installation paths
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Tesseract-OCR\tesseract.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_path = path
                    break
            
            print(f"[OCR] pytesseract available")
            if self.tesseract_path:
                print(f"[OCR] Tesseract found at: {self.tesseract_path}")
        except ImportError:
            print("[OCR] pytesseract not available - install with: pip install pytesseract")
        
        # Check for PIL
        self.pil_available = False
        try:
            from PIL import Image, ImageGrab
            self.pil_available = True
            print("[OCR] PIL available")
        except ImportError:
            print("[OCR] PIL not available")
        
        print("[OCR] OCR Handler Ready")
    
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
            print(f"[OCR] {text}")
    
    def read_screen(self) -> Optional[str]:
        """Read text from current screen"""
        title = self._get_title()
        
        if not self.pytesseract_available or not self.pil_available:
            self._speak(f"OCR is not available, {title}. Please install pytesseract and Tesseract-OCR.")
            return None
        
        try:
            import pytesseract
            from PIL import ImageGrab
            
            self._speak(f"Reading text from screen, {title}.")
            
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Extract text
            text = pytesseract.image_to_string(screenshot)
            
            # Clean up
            text = text.strip()
            
            if text:
                # Limit output length for speech
                if len(text) > 500:
                    spoken_text = text[:500] + "... and more text."
                else:
                    spoken_text = text
                
                self._speak(f"I found the following text: {spoken_text}")
                return text
            else:
                self._speak(f"I couldn't find any readable text on the screen, {title}.")
                return None
                
        except Exception as e:
            print(f"[OCR] Screen read error: {e}")
            self._speak(f"Failed to read screen text, {title}.")
            return None
    
    def read_image(self, image_path: str) -> Optional[str]:
        """Read text from an image file"""
        title = self._get_title()
        
        if not self.pytesseract_available or not self.pil_available:
            self._speak(f"OCR is not available, {title}.")
            return None
        
        try:
            import pytesseract
            from PIL import Image
            
            # Check if file exists
            path = Path(image_path)
            if not path.exists():
                self._speak(f"I couldn't find the image file, {title}.")
                return None
            
            self._speak(f"Reading text from image, {title}.")
            
            # Open and process image
            image = Image.open(str(path))
            
            # Extract text
            text = pytesseract.image_to_string(image)
            text = text.strip()
            
            if text:
                if len(text) > 500:
                    spoken_text = text[:500] + "... and more text."
                else:
                    spoken_text = text
                
                self._speak(f"I found the following text: {spoken_text}")
                return text
            else:
                self._speak(f"I couldn't find any readable text in the image, {title}.")
                return None
                
        except Exception as e:
            print(f"[OCR] Image read error: {e}")
            self._speak(f"Failed to read image text, {title}.")
            return None
    
    def read_region(self, x: int, y: int, width: int, height: int) -> Optional[str]:
        """Read text from a specific screen region"""
        title = self._get_title()
        
        if not self.pytesseract_available or not self.pil_available:
            self._speak(f"OCR is not available, {title}.")
            return None
        
        try:
            import pytesseract
            from PIL import ImageGrab
            
            # Capture region
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)
            
            # Extract text
            text = pytesseract.image_to_string(screenshot)
            text = text.strip()
            
            if text:
                self._speak(f"I found: {text}")
                return text
            else:
                self._speak(f"No readable text in that region, {title}.")
                return None
                
        except Exception as e:
            print(f"[OCR] Region read error: {e}")
            return None
    
    def read_clipboard_image(self) -> Optional[str]:
        """Read text from image in clipboard"""
        title = self._get_title()
        
        if not self.pytesseract_available or not self.pil_available:
            self._speak(f"OCR is not available, {title}.")
            return None
        
        try:
            import pytesseract
            from PIL import ImageGrab
            
            # Get image from clipboard
            image = ImageGrab.grabclipboard()
            
            if image is None:
                self._speak(f"No image found in clipboard, {title}.")
                return None
            
            self._speak(f"Reading text from clipboard image, {title}.")
            
            # Extract text
            text = pytesseract.image_to_string(image)
            text = text.strip()
            
            if text:
                if len(text) > 500:
                    spoken_text = text[:500] + "... and more."
                else:
                    spoken_text = text
                
                self._speak(f"I found: {spoken_text}")
                return text
            else:
                self._speak(f"No readable text in the clipboard image, {title}.")
                return None
                
        except Exception as e:
            print(f"[OCR] Clipboard read error: {e}")
            self._speak(f"Failed to read clipboard image, {title}.")
            return None
    
    def is_available(self) -> bool:
        """Check if OCR is available"""
        return self.pytesseract_available and self.pil_available
