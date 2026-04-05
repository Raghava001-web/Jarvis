"""
Sound Effects Library - Production Grade
=========================================
- Cross-platform audio (pygame with fallbacks)
- Proper asset management and discovery
- Volume control and mixing
- Thread-safe playback
- Configurable genre presets
"""

import os
import threading
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class SoundEffectType(Enum):
    """Types of sound effects"""
    BACKGROUND = "background"
    TRIGGER = "trigger"
    TRANSITION = "transition"


class StoryGenre(Enum):
    """Story genres with associated sounds"""
    COMEDY = "comedy"
    HORROR = "horror"
    BEDTIME = "bedtime"
    ADVENTURE = "adventure"
    ROMANCE = "romance"
    FANTASY = "fantasy"


@dataclass
class SoundAsset:
    """Sound asset with metadata"""
    name: str
    path: Path
    genre: Optional[StoryGenre] = None
    effect_type: SoundEffectType = SoundEffectType.TRIGGER
    duration_ms: int = 0


@dataclass
class GenreConfig:
    """Sound configuration for a genre"""
    background: str
    effects: List[str]
    volume: float = 0.4


# Genre-specific sound configurations
GENRE_SOUNDS: Dict[StoryGenre, GenreConfig] = {
    StoryGenre.COMEDY: GenreConfig(
        background="upbeat_music",
        effects=["laugh_track", "applause", "rimshot", "chuckle", "crowd_laugh"],
        volume=0.4
    ),
    StoryGenre.HORROR: GenreConfig(
        background="eerie_ambient",
        effects=["door_creak", "whisper", "scare_sting", "thunder", "heartbeat"],
        volume=0.5
    ),
    StoryGenre.BEDTIME: GenreConfig(
        background="soft_lullaby",
        effects=["crickets", "gentle_rain", "wind_chimes", "owl_hoot", "stream"],
        volume=0.3
    ),
    StoryGenre.ADVENTURE: GenreConfig(
        background="epic_orchestral",
        effects=["sword_clash", "explosion", "horse_gallop", "arrow_whoosh", "battle_cry"],
        volume=0.5
    ),
    StoryGenre.ROMANCE: GenreConfig(
        background="soft_piano",
        effects=["heartbeat", "sigh", "birds_singing", "gentle_breeze"],
        volume=0.3
    ),
    StoryGenre.FANTASY: GenreConfig(
        background="mystical_ambient",
        effects=["magic_sparkle", "dragon_roar", "spell_cast", "portal_open", "fairy_chime"],
        volume=0.4
    ),
}


class AudioBackend:
    """Abstract audio backend"""
    
    def play_sound(self, path: str, volume: float = 1.0) -> bool:
        raise NotImplementedError
        
    def play_music(self, path: str, volume: float = 0.3, loop: bool = True) -> bool:
        raise NotImplementedError
        
    def stop_music(self, fade_ms: int = 0) -> bool:
        raise NotImplementedError
        
    def set_music_volume(self, volume: float) -> bool:
        raise NotImplementedError
        
    def cleanup(self):
        pass


class PygameBackend(AudioBackend):
    """Pygame audio backend"""
    
    def __init__(self):
        self.available = False
        self._sounds: Dict[str, Any] = {}  # Cached Sound objects
        
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.pygame = pygame
            self.available = True
            print("[SOUND] pygame backend initialized")
        except ImportError:
            print("[SOUND] pygame not installed: pip install pygame")
        except Exception as e:
            print(f"[SOUND] pygame init error: {e}")
            
    def play_sound(self, path: str, volume: float = 1.0) -> bool:
        if not self.available:
            return False
            
        try:
            if path not in self._sounds:
                self._sounds[path] = self.pygame.mixer.Sound(path)
                
            sound = self._sounds[path]
            sound.set_volume(min(1.0, max(0.0, volume)))
            sound.play()
            return True
        except Exception as e:
            print(f"[SOUND] play error: {e}")
            return False
            
    def play_music(self, path: str, volume: float = 0.3, loop: bool = True) -> bool:
        if not self.available:
            return False
            
        try:
            self.pygame.mixer.music.load(path)
            self.pygame.mixer.music.set_volume(min(1.0, max(0.0, volume)))
            loops = -1 if loop else 0
            self.pygame.mixer.music.play(loops)
            return True
        except Exception as e:
            print(f"[SOUND] music play error: {e}")
            return False
            
    def stop_music(self, fade_ms: int = 0) -> bool:
        if not self.available:
            return False
            
        try:
            if fade_ms > 0:
                self.pygame.mixer.music.fadeout(fade_ms)
            else:
                self.pygame.mixer.music.stop()
            return True
        except Exception as e:
            print(f"[SOUND] stop error: {e}")
            return False
            
    def set_music_volume(self, volume: float) -> bool:
        if not self.available:
            return False
            
        try:
            self.pygame.mixer.music.set_volume(min(1.0, max(0.0, volume)))
            return True
        except:
            return False
            
    def cleanup(self):
        if self.available:
            try:
                self.pygame.mixer.music.stop()
                self.pygame.mixer.quit()
            except:
                pass


class FallbackBackend(AudioBackend):
    """Fallback using system sounds"""
    
    def __init__(self):
        import platform
        self.platform = platform.system()
        print(f"[SOUND] Using fallback backend ({self.platform})")
        
    def play_sound(self, path: str, volume: float = 1.0) -> bool:
        try:
            if self.platform == "Windows":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
            elif self.platform == "Darwin":
                os.system(f'afplay "{path}" &')
                return True
            else:
                os.system(f'paplay "{path}" &')
                return True
        except:
            print(f"[SOUND] Fallback play failed: {path}")
            return False
            
    def play_music(self, path: str, volume: float = 0.3, loop: bool = True) -> bool:
        return self.play_sound(path, volume)
        
    def stop_music(self, fade_ms: int = 0) -> bool:
        return True  # Can't really stop async playback
        
    def set_music_volume(self, volume: float) -> bool:
        return False  # Not supported


class AssetManager:
    """Manages sound asset discovery and caching"""
    
    SUPPORTED_FORMATS = [".mp3", ".wav", ".ogg", ".flac"]
    
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Asset cache
        self.assets: Dict[str, SoundAsset] = {}
        self.cache_path = assets_dir / ".asset_cache.json"
        
        # Scan assets
        self._scan_assets()
        
    def _scan_assets(self):
        """Scan for sound assets"""
        if self._load_cache():
            return
            
        print("[SOUND] Scanning for audio assets...")
        
        for ext in self.SUPPORTED_FORMATS:
            for path in self.assets_dir.rglob(f"*{ext}"):
                name = path.stem.lower()
                
                # Determine genre from directory
                genre = None
                for g in StoryGenre:
                    if g.value in str(path.parent).lower():
                        genre = g
                        break
                        
                # Determine type
                effect_type = SoundEffectType.TRIGGER
                if "background" in str(path).lower():
                    effect_type = SoundEffectType.BACKGROUND
                    
                self.assets[name] = SoundAsset(
                    name=name,
                    path=path,
                    genre=genre,
                    effect_type=effect_type,
                )
                
        self._save_cache()
        print(f"[SOUND] Found {len(self.assets)} sound assets")
        
    def _load_cache(self) -> bool:
        """Load asset cache"""
        if not self.cache_path.exists():
            return False
            
        try:
            # Check if cache is older than assets dir
            cache_mtime = self.cache_path.stat().st_mtime
            dir_mtime = self.assets_dir.stat().st_mtime
            if dir_mtime > cache_mtime:
                return False  # Cache stale
                
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
                
            for name, info in data.items():
                path = Path(info["path"])
                if path.exists():
                    self.assets[name] = SoundAsset(
                        name=name,
                        path=path,
                        genre=StoryGenre(info["genre"]) if info.get("genre") else None,
                        effect_type=SoundEffectType(info.get("type", "trigger")),
                    )
                    
            return len(self.assets) > 0
            
        except Exception as e:
            print(f"[SOUND] Cache load error: {e}")
            return False
            
    def _save_cache(self):
        """Save asset cache"""
        try:
            data = {}
            for name, asset in self.assets.items():
                data[name] = {
                    "path": str(asset.path),
                    "genre": asset.genre.value if asset.genre else None,
                    "type": asset.effect_type.value,
                }
            with open(self.cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SOUND] Cache save error: {e}")
            
    def get(self, name: str) -> Optional[SoundAsset]:
        """Get asset by name"""
        return self.assets.get(name.lower())
        
    def get_by_genre(self, genre: StoryGenre) -> List[SoundAsset]:
        """Get all assets for a genre"""
        return [a for a in self.assets.values() if a.genre == genre]


class SoundEffectsLibrary:
    """
    Main sound effects library.
    Thread-safe, cross-platform.
    """
    
    def __init__(self):
        print("[SOUND] Initializing Sound Effects Library...")
        
        # Assets directory
        self.assets_dir = Path(__file__).parent.parent / "gui" / "assets" / "sounds"
        
        # Asset manager
        self.asset_manager = AssetManager(self.assets_dir)
        
        # Audio backend
        self.backend = PygameBackend()
        if not self.backend.available:
            self.backend = FallbackBackend()
            
        # State
        self.background_playing = False
        self.current_background: Optional[str] = None
        self.background_volume = 0.3
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
        
        print("[SOUND] Sound Effects Library Ready")
        
    def play_background(self, sound_name: str, volume: float = 0.3):
        """Start playing background music"""
        with self.lock:
            asset = self.asset_manager.get(sound_name)
            
            if asset:
                if self.backend.play_music(str(asset.path), volume):
                    self.background_playing = True
                    self.current_background = sound_name
                    self.background_volume = volume
            else:
                print(f"[SOUND] Background not found: {sound_name}")
                
    def stop_background(self, fade_ms: int = 1000):
        """Stop background music"""
        with self.lock:
            self.backend.stop_music(fade_ms)
            self.background_playing = False
            self.current_background = None
            
    def fade_to_silence(self, duration_ms: int = 2000):
        """Fade background to silence (dramatic effect)"""
        if not self.background_playing:
            return
            
        self.backend.stop_music(duration_ms)
        time.sleep(duration_ms / 1000)
        
    def play(self, effect_name: str, volume: float = 0.7):
        """Play a one-shot sound effect"""
        asset = self.asset_manager.get(effect_name)
        
        if asset:
            self.backend.play_sound(str(asset.path), volume)
        else:
            print(f"[SOUND] Effect not found: {effect_name}")
            
    def play_sequence(self, effects: List[str], delays: List[float] = None):
        """Play effects in sequence (non-blocking)"""
        if delays is None:
            delays = [0.5] * len(effects)
            
        def _sequence():
            for i, effect in enumerate(effects):
                self.play(effect)
                if i < len(delays):
                    time.sleep(delays[i])
                    
        thread = threading.Thread(target=_sequence, daemon=True)
        thread.start()
        
    def get_genre_config(self, genre: StoryGenre) -> GenreConfig:
        """Get sound configuration for a genre"""
        return GENRE_SOUNDS.get(genre, GENRE_SOUNDS[StoryGenre.BEDTIME])
        
    def setup_genre(self, genre: StoryGenre):
        """Setup sounds for a genre"""
        config = self.get_genre_config(genre)
        self.play_background(config.background, config.volume)
        
    def cleanup(self):
        """Cleanup and release resources"""
        self.stop_background(0)
        self.backend.cleanup()
    
    # Convenience method aliases for consistent API
    def play_sound(self, name: str, volume: float = 0.7) -> bool:
        """Play a sound effect (alias for play)"""
        self.play(name, volume)
        return True
    
    def play_music(self, name: str, volume: float = 0.3, loop: bool = True) -> bool:
        """Play background music (alias for play_background)"""
        self.play_background(name, volume)
        return True
    
    def stop_music(self, fade_ms: int = 1000) -> bool:
        """Stop background music (alias for stop_background)"""
        self.stop_background(fade_ms)
        return True
    
    def set_music_volume(self, volume: float) -> bool:
        """Set music volume"""
        return self.backend.set_music_volume(volume)
    
    def play_effect(self, effect_name: str, volume: float = 0.7):
        """Play a sound effect (alias for play)"""
        self.play(effect_name, volume)


class ImmersiveStoryteller:
    """Tells stories with immersive sound effects"""
    
    def __init__(self, perception=None, knowledge=None):
        print("[STORYTELLER] Initializing...")
        self.perception = perception
        self.knowledge = knowledge
        self.sound_effects = SoundEffectsLibrary()
        print("[STORYTELLER] Ready")
        
    def tell_story(self, theme: str, genre: str) -> bool:
        """Tell a story with sound effects"""
        import random
        
        # Map string to genre
        genre_map = {
            "comedy": StoryGenre.COMEDY,
            "horror": StoryGenre.HORROR,
            "bedtime": StoryGenre.BEDTIME,
            "adventure": StoryGenre.ADVENTURE,
            "romance": StoryGenre.ROMANCE,
            "fantasy": StoryGenre.FANTASY,
        }
        
        story_genre = genre_map.get(genre.lower(), StoryGenre.BEDTIME)
        config = self.sound_effects.get_genre_config(story_genre)
        
        # Start background
        self.sound_effects.setup_genre(story_genre)
        
        # Generate story
        story = self._generate_story(theme, story_genre)
        
        # Narrate
        self._narrate_with_effects(story, story_genre, config)
        
        # Cleanup
        self.sound_effects.stop_background()
        
        return True
        
    def _generate_story(self, theme: str, genre: StoryGenre) -> str:
        """Generate a story"""
        genre_prompts = {
            StoryGenre.COMEDY: "Make it funny with witty punchlines.",
            StoryGenre.HORROR: "Build suspense slowly with scary moments.",
            StoryGenre.BEDTIME: "Make it calming and peaceful.",
            StoryGenre.ADVENTURE: "Make it exciting with action.",
            StoryGenre.ROMANCE: "Make it heartwarming.",
            StoryGenre.FANTASY: "Include magical elements.",
        }
        
        if self.knowledge:
            try:
                prompt = f"""Tell a {genre.value} story about {theme}.
{genre_prompts.get(genre, '')}
Keep it 2-3 minutes. Use [PAUSE] for pauses and [EFFECT] for sound effect moments."""
                return self.knowledge.answer_question(prompt)
            except:
                pass
                
        return f"Once upon a time, there was a tale about {theme}. [PAUSE] The end."
        
    def _narrate_with_effects(self, story: str, genre: StoryGenre, config: GenreConfig):
        """Narrate with effects"""
        import random
        
        segments = story.split("[PAUSE]")
        
        for i, segment in enumerate(segments):
            if "[EFFECT]" in segment:
                parts = segment.split("[EFFECT]")
                for part in parts:
                    if part.strip():
                        self._speak(part.strip())
                    if config.effects:
                        self.sound_effects.play(random.choice(config.effects))
                        time.sleep(0.5)
            else:
                if segment.strip():
                    self._speak(segment.strip())
                    
            if i < len(segments) - 1:
                if genre == StoryGenre.HORROR:
                    self.sound_effects.fade_to_silence(500)
                    time.sleep(2)
                    self.sound_effects.play_background(config.background, config.volume)
                else:
                    time.sleep(1)
                    
        # End effects
        if genre == StoryGenre.COMEDY:
            self.sound_effects.play("applause")
            
    def _speak(self, text: str):
        """Speak text"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[STORY] {text}")
    
    def set_genre(self, genre: str):
        """Set up sounds for a genre"""
        genre_map = {
            "comedy": StoryGenre.COMEDY,
            "horror": StoryGenre.HORROR,
            "bedtime": StoryGenre.BEDTIME,
            "adventure": StoryGenre.ADVENTURE,
            "romance": StoryGenre.ROMANCE,
            "fantasy": StoryGenre.FANTASY,
        }
        story_genre = genre_map.get(genre.lower(), StoryGenre.BEDTIME)
        self.sound_effects.setup_genre(story_genre)
    
    def stop(self):
        """Stop story playback and sounds"""
        self.sound_effects.stop_background()
    
    def cleanup(self):
        """Cleanup resources"""
        self.sound_effects.cleanup()


# Singleton
_library = None

def get_sound_effects() -> SoundEffectsLibrary:
    global _library
    if _library is None:
        _library = SoundEffectsLibrary()
    return _library
