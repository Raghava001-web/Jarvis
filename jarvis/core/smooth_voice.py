"""
Enhanced Voice Module - Smooth, natural voice synthesis
Uses edge-tts for smoother Microsoft neural voices with pyttsx3 fallback
"""

import asyncio
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional


class SmoothVoice:
    """Enhanced TTS with edge-tts for smoother voices"""
    
    def __init__(self, assistant="jarvis"):
        print("[VOICE] Initializing Smooth Voice Engine...")
        
        self.assistant = assistant
        self.edge_tts_available = False
        self.pygame_available = False
        
        # Check for edge-tts
        try:
            import edge_tts
            self.edge_tts_available = True
            print("[VOICE] edge-tts available (Microsoft Neural voices)")
        except ImportError:
            print("[VOICE] edge-tts not installed. Install with: pip install edge-tts")
        
        # Check for pygame (audio playback)
        try:
            import pygame
            pygame.mixer.init()
            self.pygame_available = True
            print("[VOICE] pygame mixer available for audio playback")
        except ImportError:
            print("[VOICE] pygame not available for audio playback")
        
        # Voice configurations
        self.voices = {
            "jarvis": {
                "voice": "en-GB-RyanNeural",  # British male, sounds sophisticated
                "rate": "+5%",    # Slightly faster than default
                "pitch": "-5Hz",  # Slightly deeper
                "volume": "+0%"
            },
            "friday": {
                "voice": "en-US-JennyNeural",  # American female
                "rate": "+0%",
                "pitch": "+0Hz",
                "volume": "+0%"
            }
        }
        
        # Alternative voices if main ones unavailable
        self.fallback_voices = [
            "en-GB-RyanNeural",
            "en-US-GuyNeural", 
            "en-US-ChristopherNeural",
            "en-AU-WilliamNeural"
        ]
        
        # Audio cache directory
        self.cache_dir = Path(tempfile.gettempdir()) / "jarvis_voice_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Speaking state
        self.is_speaking = False
        self.stop_flag = False
        
        print("[VOICE] Smooth Voice Ready")
    
    def set_assistant(self, name: str):
        """Switch between JARVIS and FRIDAY voice"""
        self.assistant = name.lower()
    
    async def _generate_speech_async(self, text: str, output_file: str):
        """Generate speech audio file using edge-tts"""
        import edge_tts
        
        config = self.voices.get(self.assistant, self.voices["jarvis"])
        
        communicate = edge_tts.Communicate(
            text,
            config["voice"],
            rate=config["rate"],
            pitch=config["pitch"],
            volume=config["volume"]
        )
        
        await communicate.save(output_file)
    
    def speak(self, text: str, callback=None):
        """Speak text with smooth neural voice"""
        if not text:
            return
        
        # Run in thread to not block
        thread = threading.Thread(
            target=self._speak_internal,
            args=(text, callback),
            daemon=True
        )
        thread.start()
    
    def _speak_internal(self, text: str, callback=None):
        """Internal speak implementation"""
        self.is_speaking = True
        self.stop_flag = False
        
        if self.edge_tts_available and self.pygame_available:
            try:
                self._speak_with_edge_tts(text)
            except Exception as e:
                print(f"[VOICE] edge-tts error: {e}, falling back to pyttsx3")
                self._speak_with_pyttsx3(text)
        else:
            self._speak_with_pyttsx3(text)
        
        self.is_speaking = False
        
        if callback:
            callback()
    
    def _speak_with_edge_tts(self, text: str):
        """Speak using edge-tts (smooth neural voice)"""
        import pygame
        import hashlib
        
        # Create cache filename based on text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
        audio_file = self.cache_dir / f"{self.assistant}_{text_hash}.mp3"
        
        # Generate audio if not cached
        if not audio_file.exists():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._generate_speech_async(text, str(audio_file)))
            finally:
                loop.close()
        
        # Play audio
        pygame.mixer.music.load(str(audio_file))
        pygame.mixer.music.play()
        
        # Wait for playback to finish (with stop check)
        while pygame.mixer.music.get_busy() and not self.stop_flag:
            pygame.time.wait(100)
        
        if self.stop_flag:
            pygame.mixer.music.stop()
    
    def _speak_with_pyttsx3(self, text: str):
        """Fallback to pyttsx3 (robotic but reliable)"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 165)  # Slightly slower for clarity
            engine.setProperty('volume', 0.9)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            print(f"[VOICE] pyttsx3 error: {e}")
    
    def stop(self):
        """Stop current speech"""
        self.stop_flag = True
        if self.pygame_available:
            try:
                import pygame
                pygame.mixer.music.stop()
            except:
                pass
    
    def list_available_voices(self):
        """List all available edge-tts voices"""
        if not self.edge_tts_available:
            return []
        
        import asyncio
        import edge_tts
        
        async def get_voices():
            voices = await edge_tts.list_voices()
            return [v for v in voices if v['Locale'].startswith('en-')]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_voices())
        finally:
            loop.close()


# Singleton instance
_voice_engine = None

def get_smooth_voice(assistant="jarvis") -> SmoothVoice:
    """Get or create smooth voice engine"""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = SmoothVoice(assistant)
    return _voice_engine
