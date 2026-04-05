"""
YouTube Downloader - Download videos from YouTube
Uses yt-dlp (actively maintained) as primary engine, pytube as fallback.
"""

import os
import re
from pathlib import Path
from typing import Optional


class YouTubeDownloader:
    """Downloads videos and audio from YouTube"""
    
    def __init__(self, perception=None):
        print("[YOUTUBE] Initializing YouTube Downloader...")
        self.perception = perception
        
        # Download directory
        self.download_dir = Path.home() / "Downloads" / "JARVIS_YouTube"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for yt-dlp (primary - actively maintained, rarely breaks)
        self.ytdlp_available = False
        try:
            import yt_dlp
            self.ytdlp_available = True
            print("[YOUTUBE] yt-dlp available (primary engine)")
        except ImportError:
            print("[YOUTUBE] yt-dlp not available - install with: pip install yt-dlp")
        
        # Check for pytube (fallback)
        self.pytube_available = False
        try:
            from pytube import YouTube
            self.pytube_available = True
            print("[YOUTUBE] pytube available (fallback)")
        except ImportError:
            pass
        
        if not self.ytdlp_available and not self.pytube_available:
            print("[YOUTUBE] WARNING: No download engine available!")
        
        print("[YOUTUBE] YouTube Downloader Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[YOUTUBE] {text}")
    
    def _sanitize_filename(self, title: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '')
        return title[:100]
    
    # ─── yt-dlp Download (Primary) ──────────────────────────────────

    def _ytdlp_download_video(self, url: str, resolution: str = "720p") -> Optional[Path]:
        """Download video using yt-dlp"""
        import yt_dlp
        
        res_num = resolution.replace('p', '')
        
        ydl_opts = {
            'format': f'best[height<={res_num}][ext=mp4]/best[height<={res_num}]/best[ext=mp4]/best',
            'outtmpl': str(self.download_dir / '%(title).100s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return Path(filename)
        except Exception as e:
            print(f"[YOUTUBE] yt-dlp download error: {e}")
            return None

    def _ytdlp_download_audio(self, url: str) -> Optional[Path]:
        """Download audio only using yt-dlp"""
        import yt_dlp
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(self.download_dir / '%(title).100s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if self._ffmpeg_available() else [],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Check if FFmpeg converted to mp3
                mp3_path = Path(filename).with_suffix('.mp3')
                if mp3_path.exists():
                    return mp3_path
                return Path(filename)
        except Exception as e:
            print(f"[YOUTUBE] yt-dlp audio error: {e}")
            return None

    def _ytdlp_get_info(self, url: str) -> Optional[dict]:
        """Get video info using yt-dlp"""
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "author": info.get("uploader", "Unknown"),
                    "length": info.get("duration", 0),
                    "views": info.get("view_count", 0),
                    "description": (info.get("description", "") or "")[:200],
                }
        except Exception as e:
            print(f"[YOUTUBE] yt-dlp info error: {e}")
            return None

    def _ffmpeg_available(self) -> bool:
        """Check if FFmpeg is installed"""
        import shutil
        return shutil.which('ffmpeg') is not None

    # ─── pytube Download (Fallback) ─────────────────────────────────

    def _pytube_download_video(self, url: str, resolution: str = "720p") -> Optional[Path]:
        """Download video using pytube (fallback)"""
        try:
            from pytube import YouTube
            
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, resolution=resolution).first()
            if not stream:
                stream = yt.streams.filter(progressive=True).order_by('resolution').desc().first()
            if not stream:
                return None
            
            output_path = stream.download(output_path=str(self.download_dir))
            return Path(output_path)
        except Exception as e:
            print(f"[YOUTUBE] pytube download error: {e}")
            return None

    def _pytube_download_audio(self, url: str) -> Optional[Path]:
        """Download audio using pytube (fallback)"""
        try:
            from pytube import YouTube
            
            yt = YouTube(url)
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not stream:
                return None
            
            output_path = stream.download(output_path=str(self.download_dir))
            return Path(output_path)
        except Exception as e:
            print(f"[YOUTUBE] pytube audio error: {e}")
            return None

    # ─── Public API ─────────────────────────────────────────────────

    def download_video(self, url: str, resolution: str = "720p") -> Optional[Path]:
        """Download video from YouTube URL (yt-dlp → pytube fallback)"""
        title = self._get_title()
        
        if not self.ytdlp_available and not self.pytube_available:
            self._speak(f"No YouTube download engine available, {title}. Install yt-dlp.")
            return None
        
        self._speak(f"Downloading video, {title}. This may take a moment.")
        
        result = None
        
        # Try yt-dlp first (reliable)
        if self.ytdlp_available:
            result = self._ytdlp_download_video(url, resolution)
        
        # Fallback to pytube
        if not result and self.pytube_available:
            print("[YOUTUBE] yt-dlp failed, falling back to pytube...")
            result = self._pytube_download_video(url, resolution)
        
        if result and result.exists():
            self._speak(f"Download complete, {title}. Video saved to downloads folder.")
            return result
        
        self._speak(f"Failed to download video, {title}. The link may be invalid or restricted.")
        return None
    
    def download_audio(self, url: str) -> Optional[Path]:
        """Download audio only from YouTube URL (yt-dlp → pytube fallback)"""
        title = self._get_title()
        
        if not self.ytdlp_available and not self.pytube_available:
            self._speak(f"No YouTube download engine available, {title}.")
            return None
        
        self._speak(f"Downloading audio, {title}. Please wait.")
        
        result = None
        
        if self.ytdlp_available:
            result = self._ytdlp_download_audio(url)
        
        if not result and self.pytube_available:
            print("[YOUTUBE] yt-dlp failed, falling back to pytube...")
            result = self._pytube_download_audio(url)
        
        if result and result.exists():
            self._speak(f"Download complete, {title}. Audio saved.")
            return result
        
        self._speak(f"Failed to download audio, {title}.")
        return None
    
    def get_video_info(self, url: str) -> Optional[dict]:
        """Get information about a YouTube video"""
        title = self._get_title()
        
        info = None
        
        if self.ytdlp_available:
            info = self._ytdlp_get_info(url)
        
        if not info and self.pytube_available:
            try:
                from pytube import YouTube
                yt = YouTube(url)
                info = {
                    "title": yt.title,
                    "author": yt.author,
                    "length": yt.length,
                    "views": yt.views,
                    "description": (yt.description or "")[:200],
                }
            except Exception:
                pass
        
        if info:
            minutes = info["length"] // 60
            seconds = info["length"] % 60
            self._speak(f"The video '{info['title']}' by {info['author']} is {minutes} minutes and {seconds} seconds long.")
            return info
        
        self._speak(f"Could not get video information, {title}.")
        return None
    
    def extract_url_from_command(self, command: str) -> Optional[str]:
        """Extract YouTube URL from command text"""
        patterns = [
            r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)',
            r'(https?://youtu\.be/[\w-]+)',
            r'(youtube\.com/watch\?v=[\w-]+)',
            r'(youtu\.be/[\w-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                url = match.group(1)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return None
    
    def search_and_play(self, query: str) -> bool:
        """Search YouTube and play the first result immediately."""
        title = self._get_title()
        
        try:
            import urllib.request
            import urllib.parse
            import webbrowser
            
            self._speak(f"Playing {query} on YouTube, {title}.")
            
            # Try yt-dlp search first (more reliable)
            if self.ytdlp_available:
                try:
                    import yt_dlp
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'noplaylist': True,
                        'default_search': 'ytsearch1',
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                        if info and 'entries' in info and info['entries']:
                            video_url = info['entries'][0].get('webpage_url')
                            if video_url:
                                webbrowser.open(video_url)
                                return True
                except Exception as e:
                    print(f"[YOUTUBE] yt-dlp search error: {e}")
            
            # Fallback: scrape YouTube search results
            formatted_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={formatted_query}"
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
            
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            
            if video_ids:
                youtube_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                webbrowser.open(youtube_url)
                return True
            else:
                webbrowser.open(url)
                return False
                
        except Exception as e:
            print(f"[YOUTUBE] Error auto-playing: {e}")
            import urllib.parse
            import webbrowser
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
            return False
            
    def open_downloads_folder(self) -> bool:
        """Open the downloads folder"""
        title = self._get_title()
        try:
            os.startfile(str(self.download_dir))
            self._speak(f"Opening YouTube downloads folder, {title}.")
            return True
        except Exception as e:
            print(f"[YOUTUBE] Error opening folder: {e}")
            return False
