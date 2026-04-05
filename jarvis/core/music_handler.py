"""
Music Handler - Production Grade
================================
Uses official APIs, real state tracking, no UI automation hacks.

Supports:
- Spotify (via spotipy library with Web API)
- Windows Media Keys (as fallback for any player)
- YouTube (via web for song search)

Requires: pip install spotipy
Spotify Setup: https://developer.spotify.com/dashboard
"""

import os
import subprocess
import webbrowser
import time
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PlaybackState(Enum):
    """Real playback state tracking"""
    UNKNOWN = "unknown"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


class MusicSource(Enum):
    """Music source types"""
    NONE = "none"
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    SYSTEM = "system"  # Any app responding to media keys


@dataclass
class Track:
    """Track information"""
    name: str
    artist: str = ""
    album: str = ""
    duration_ms: int = 0
    source: MusicSource = MusicSource.NONE
    uri: str = ""


@dataclass
class MusicState:
    """Complete music playback state"""
    state: PlaybackState = PlaybackState.UNKNOWN
    current_track: Optional[Track] = None
    source: MusicSource = MusicSource.NONE
    volume: int = 50
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "state": self.state.value,
            "track": self.current_track.__dict__ if self.current_track else None,
            "source": self.source.value,
            "volume": self.volume,
        }


class SpotifyController:
    """
    Spotify control via official Web API.
    Requires spotipy library and Spotify Developer credentials.
    """
    
    def __init__(self):
        self.sp = None
        self.available = False
        self.device_id = None
        self._init_spotify()
        
    def _init_spotify(self):
        """Initialize Spotify API connection"""
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth
            
            # Check for credentials
            client_id = os.environ.get('SPOTIPY_CLIENT_ID')
            client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
            redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI', 'http://localhost:8888/callback')
            
            if not client_id or not client_secret:
                print("[MUSIC] Spotify API credentials not found in environment")
                print("[MUSIC] Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET")
                return
                
            # Initialize with required scopes
            scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
            
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=str(Path(__file__).parent.parent / "data" / ".spotify_cache")
            ))
            
            self.available = True
            print("[MUSIC] Spotify API connected")
            
            # Get active device
            self._refresh_device()
            
        except ImportError:
            print("[MUSIC] spotipy not installed. Run: pip install spotipy")
        except Exception as e:
            print(f"[MUSIC] Spotify init error: {e}")
            
    def _refresh_device(self):
        """Get active Spotify device"""
        if not self.sp:
            return
        try:
            devices = self.sp.devices()
            if devices and devices.get('devices'):
                # Prefer active device, else first available
                for d in devices['devices']:
                    if d['is_active']:
                        self.device_id = d['id']
                        return
                self.device_id = devices['devices'][0]['id']
        except:
            pass
            
    def get_state(self) -> Tuple[PlaybackState, Optional[Track]]:
        """Get current playback state from Spotify API"""
        if not self.sp:
            return PlaybackState.UNKNOWN, None
            
        try:
            playback = self.sp.current_playback()
            if not playback:
                return PlaybackState.STOPPED, None
                
            state = PlaybackState.PLAYING if playback['is_playing'] else PlaybackState.PAUSED
            
            track_info = playback.get('item')
            if track_info:
                track = Track(
                    name=track_info['name'],
                    artist=", ".join(a['name'] for a in track_info.get('artists', [])),
                    album=track_info.get('album', {}).get('name', ''),
                    duration_ms=track_info.get('duration_ms', 0),
                    source=MusicSource.SPOTIFY,
                    uri=track_info.get('uri', '')
                )
                return state, track
                
            return state, None
            
        except Exception as e:
            print(f"[MUSIC] Spotify state error: {e}")
            return PlaybackState.UNKNOWN, None
            
    def play(self, query: str = None) -> Tuple[bool, str]:
        """Play music via Spotify API"""
        if not self.sp:
            return False, "Spotify not connected"
            
        try:
            self._refresh_device()
            
            if query:
                # Search and play
                results = self.sp.search(q=query, type='track', limit=1)
                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    self.sp.start_playback(
                        device_id=self.device_id,
                        uris=[track['uri']]
                    )
                    return True, f"Playing {track['name']} by {track['artists'][0]['name']}"
                return False, f"No results for '{query}'"
            else:
                # Resume playback
                self.sp.start_playback(device_id=self.device_id)
                return True, "Resumed playback"
                
        except Exception as e:
            return False, f"Spotify error: {e}"
            
    def pause(self) -> Tuple[bool, str]:
        """Pause playback"""
        if not self.sp:
            return False, "Spotify not connected"
        try:
            self.sp.pause_playback(device_id=self.device_id)
            return True, "Paused"
        except Exception as e:
            return False, f"Pause error: {e}"
            
    def next_track(self) -> Tuple[bool, str]:
        """Skip to next track"""
        if not self.sp:
            return False, "Spotify not connected"
        try:
            self.sp.next_track(device_id=self.device_id)
            return True, "Next track"
        except Exception as e:
            return False, f"Skip error: {e}"
            
    def previous_track(self) -> Tuple[bool, str]:
        """Go to previous track"""
        if not self.sp:
            return False, "Spotify not connected"
        try:
            self.sp.previous_track(device_id=self.device_id)
            return True, "Previous track"
        except Exception as e:
            return False, f"Previous error: {e}"
            
    def set_volume(self, percent: int) -> Tuple[bool, str]:
        """Set volume (0-100)"""
        if not self.sp:
            return False, "Spotify not connected"
        try:
            percent = max(0, min(100, percent))
            self.sp.volume(percent, device_id=self.device_id)
            return True, f"Volume: {percent}%"
        except Exception as e:
            return False, f"Volume error: {e}"


class MediaKeyController:
    """
    Windows Media Key control - works with ANY media player.
    Uses ctypes for direct key simulation (no pyautogui).
    """
    
    VK_MEDIA_PLAY_PAUSE = 0xB3
    VK_MEDIA_NEXT = 0xB0
    VK_MEDIA_PREV = 0xB1
    VK_VOLUME_UP = 0xAF
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_MUTE = 0xAD
    
    def __init__(self):
        self.available = False
        try:
            import ctypes
            self.user32 = ctypes.windll.user32
            self.available = True
            print("[MUSIC] Media keys available")
        except:
            print("[MUSIC] Media keys not available")
            
    def _press_key(self, vk_code: int):
        """Press and release a virtual key"""
        if not self.available:
            return False
        try:
            self.user32.keybd_event(vk_code, 0, 0, 0)
            self.user32.keybd_event(vk_code, 0, 2, 0)  # Key up
            return True
        except:
            return False
            
    def play_pause(self) -> bool:
        return self._press_key(self.VK_MEDIA_PLAY_PAUSE)
        
    def next_track(self) -> bool:
        return self._press_key(self.VK_MEDIA_NEXT)
        
    def previous_track(self) -> bool:
        return self._press_key(self.VK_MEDIA_PREV)


class MusicHandler:
    """
    Production-grade music handler.
    
    Priority order:
    1. Spotify API (if credentials configured)
    2. Media keys (fallback for any player)
    3. YouTube web search (for specific songs if Spotify unavailable)
    """
    
    def __init__(self, perception=None):
        print("[MUSIC] Initializing Music Handler...")
        self.perception = perception
        
        # Controllers
        self.spotify = SpotifyController()
        self.media_keys = MediaKeyController()
        
        # State tracking
        self.state = MusicState()
        self.state_path = Path(__file__).parent.parent / "data" / "music_state.json"
        self._load_state()
        
        print("[MUSIC] Music Handler Ready")
        print(f"[MUSIC] Spotify: {'Available' if self.spotify.available else 'Not configured'}")
        
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
        
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[MUSIC] {text}")
            
    def _load_state(self):
        """Load persisted state"""
        try:
            if self.state_path.exists():
                with open(self.state_path, 'r') as f:
                    data = json.load(f)
                    self.state.volume = data.get('volume', 50)
        except:
            pass
            
    def _save_state(self):
        """Persist state"""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_path, 'w') as f:
                json.dump(self.state.to_dict(), f)
        except:
            pass
            
    def _update_state(self):
        """Update state from active source"""
        if self.spotify.available:
            state, track = self.spotify.get_state()
            self.state.state = state
            self.state.current_track = track
            self.state.source = MusicSource.SPOTIFY if track else MusicSource.NONE
        self.state.last_updated = datetime.now()
        self._save_state()
        
    def play(self, query: str = None) -> str:
        """
        Play music.
        - If query: search and play that song
        - If no query: resume current playback
        """
        title = self._get_title()
        
        # Try Spotify first
        if self.spotify.available:
            success, message = self.spotify.play(query)
            if success:
                self._update_state()
                return message
            # If Spotify failed with a query, try YouTube
            if query and "No results" in message:
                pass  # Fall through to YouTube
            elif not query:
                # Resume failed, try media keys
                if self.media_keys.play_pause():
                    self.state.state = PlaybackState.PLAYING
                    return "Resumed"
                return message
                
        # Fallback: YouTube search for specific songs
        if query:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            self.state.source = MusicSource.YOUTUBE
            self.state.state = PlaybackState.PLAYING
            self._save_state()
            return f"Searching YouTube for {query}"
            
        # Fallback: Media keys for generic play
        if self.media_keys.play_pause():
            self.state.state = PlaybackState.PLAYING
            return "Playing"
            
        return "Unable to play music"
        
    def pause(self) -> str:
        """Pause current playback"""
        if self.spotify.available:
            success, message = self.spotify.pause()
            if success:
                self.state.state = PlaybackState.PAUSED
                self._save_state()
                return message
                
        # Fallback
        if self.media_keys.play_pause():
            self.state.state = PlaybackState.PAUSED
            return "Paused"
            
        return "Unable to pause"
        
    def next_track(self) -> str:
        """Skip to next track"""
        if self.spotify.available:
            success, message = self.spotify.next_track()
            if success:
                self._update_state()
                return message
                
        if self.media_keys.next_track():
            return "Next track"
            
        return "Unable to skip"
        
    def previous_track(self) -> str:
        """Go to previous track"""
        if self.spotify.available:
            success, message = self.spotify.previous_track()
            if success:
                self._update_state()
                return message
                
        if self.media_keys.previous_track():
            return "Previous track"
            
        return "Unable to go back"
        
    def get_current_track(self) -> Optional[str]:
        """Get info about currently playing track"""
        self._update_state()
        
        if self.state.current_track:
            track = self.state.current_track
            return f"{track.name} by {track.artist}"
            
        return None
        
    def get_state(self) -> MusicState:
        """Get full music state"""
        self._update_state()
        return self.state
        
    def handle_command(self, command: str) -> Optional[str]:
        """
        DETERMINISTIC command handler.
        Uses explicit pattern matching, not fuzzy heuristics.
        """
        cmd = command.lower().strip()
        
        # PLAY commands (most specific first)
        if cmd.startswith("play "):
            query = cmd[5:].strip()
            # Remove common filler words
            for filler in ["some ", "the song ", "song ", "music by ", "track "]:
                if query.startswith(filler):
                    query = query[len(filler):]
            if query:
                return self.play(query)
            return self.play()
            
        if cmd in ["play", "play music", "resume", "resume music"]:
            return self.play()
            
        # PAUSE commands
        if cmd in ["pause", "pause music", "stop", "stop music"]:
            return self.pause()
            
        # NEXT commands
        if cmd in ["next", "next song", "next track", "skip", "skip song"]:
            return self.next_track()
            
        # PREVIOUS commands
        if cmd in ["previous", "previous song", "previous track", "back", "go back"]:
            return self.previous_track()
            
        # WHAT'S PLAYING
        if cmd in ["what's playing", "whats playing", "current song", "what song"]:
            track = self.get_current_track()
            if track:
                return f"Now playing: {track}"
            return "Nothing is playing"
            
        # Not a music command
        return None


# Singleton
_handler = None

def get_music_handler(perception=None) -> MusicHandler:
    global _handler
    if _handler is None:
        _handler = MusicHandler(perception)
    return _handler


# Alias for compatibility
DirectMusicHandler = MusicHandler
