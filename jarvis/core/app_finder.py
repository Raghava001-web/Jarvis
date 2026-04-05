"""
App Finder - Production Grade
=============================
- Proper .lnk shortcut resolution
- Separated Finder and Launcher responsibilities
- Deduplication and ranking
- Clean caching with validation
"""

import os
import subprocess
import winreg
import webbrowser
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class AppType(Enum):
    """Types of applications"""
    SYSTEM = "system"      # Built-in Windows commands
    DESKTOP = "desktop"    # Installed desktop apps
    WEB = "web"            # Web apps (URLs)
    UWP = "uwp"            # Windows Store apps


@dataclass
class AppInfo:
    """Information about an application"""
    name: str
    path: str
    app_type: AppType
    aliases: List[str] = field(default_factory=list)
    score: float = 0.0  # For ranking


class ShortcutResolver:
    """
    Properly resolves Windows .lnk shortcuts.
    Uses Windows Script Host (WSH) for reliable resolution.
    """
    
    @staticmethod
    def resolve_lnk(lnk_path: str) -> Optional[str]:
        """Resolve a .lnk shortcut to its target path"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            return shortcut.TargetPath
        except ImportError:
            # Fallback: use PowerShell
            return ShortcutResolver._resolve_via_powershell(lnk_path)
        except Exception as e:
            print(f"[APP] Error resolving shortcut: {e}")
            return None
            
    @staticmethod
    def _resolve_via_powershell(lnk_path: str) -> Optional[str]:
        """Fallback: resolve shortcut via PowerShell"""
        try:
            ps_script = f'''
                $sh = New-Object -ComObject WScript.Shell
                $sc = $sh.CreateShortcut("{lnk_path}")
                $sc.TargetPath
            '''
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            print(f"[APP] PowerShell resolve error: {e}")
        return None


class AppFinder:
    """
    Finds applications on the system.
    Separated from launching logic.
    """
    
    # System apps (instant access)
    SYSTEM_APPS = {
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "file manager": "explorer.exe",
        "files": "explorer.exe",
        "this pc": "explorer.exe",
        "my computer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "snipping tool": "SnippingTool.exe",
        "control panel": "control.exe",
        "settings": "ms-settings:",
        "device manager": "devmgmt.msc",
        "disk management": "diskmgmt.msc",
        "wifi settings": "ms-settings:network-wifi",
        "wifi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "bluetooth settings": "ms-settings:bluetooth",
        "display settings": "ms-settings:display",
        "sound settings": "ms-settings:sound",
        "apps": "ms-settings:appsfeatures",
        "installed apps": "ms-settings:appsfeatures",
        "photos": "ms-photos:",
        "camera": "microsoft.windows.camera:",
        "store": "ms-windows-store:",
        "microsoft store": "ms-windows-store:",
    }
    
    # Web apps (open in browser) — desktop apps are tried first via aliases
    WEB_APPS = {
        # AI Apps (desktop tried first via ALIASES + app_cache)
        "chatgpt": "https://chat.openai.com",
        "perplexity": "https://perplexity.ai",
        "claude": "https://claude.ai",
        # Messaging (desktop tried first via ALIASES + app_cache)
        "whatsapp": "https://web.whatsapp.com",
        "telegram": "https://web.telegram.org",
        "discord": "https://discord.com/app",
        "slack": "https://app.slack.com",
        # Google & Social
        "gmail": "https://mail.google.com",
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "google drive": "https://drive.google.com",
        "google docs": "https://docs.google.com",
        # Media & Social
        "netflix": "https://netflix.com",
        "spotify": "https://open.spotify.com",
        "github": "https://github.com",
        "linkedin": "https://linkedin.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "instagram": "https://instagram.com",
        "facebook": "https://facebook.com",
        "reddit": "https://reddit.com",
    }
    
    # Common aliases
    ALIASES = {
        "chrome": ["google chrome", "chrome"],
        "firefox": ["mozilla firefox", "firefox"],
        "edge": ["microsoft edge", "edge"],
        "brave": ["brave browser", "brave"],
        "whatsapp": ["whatsapp", "whatsapp desktop", "whatsapp beta"],
        "telegram": ["telegram", "telegram desktop"],
        "discord": ["discord"],
        "slack": ["slack"],
        "vscode": ["visual studio code", "code", "vs code"],
        "spotify": ["spotify"],
        "vlc": ["vlc media player", "vlc"],
        "word": ["microsoft word", "word", "winword"],
        "excel": ["microsoft excel", "excel"],
        "powerpoint": ["microsoft powerpoint", "powerpoint", "pptx"],
        "outlook": ["microsoft outlook", "outlook"],
        "steam": ["steam"],
        "chatgpt": ["chatgpt", "chat gpt", "openai", "chatpgt", "chatgtp", "cahtgpt"],
        "perplexity": ["perplexity", "perplexity ai", "perplexty", "perplxity"],
    }
    
    def __init__(self, perception=None):
        print("[APP FINDER] Initializing...")
        self.perception = perception
        self.resolver = ShortcutResolver()
        
        # Cache setup
        self.cache_path = Path(__file__).parent.parent / "data" / "app_cache.json"
        self.app_cache: Dict[str, AppInfo] = {}
        self._load_cache()
        
        # Scan if cache is stale or empty
        if not self.app_cache or self._is_cache_stale():
            self._scan_apps()
            
        print(f"[APP FINDER] {len(self.app_cache)} apps indexed")
        
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
        
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[APP FINDER] {text}")
            
    def _is_cache_stale(self) -> bool:
        """Check if cache is older than 24 hours"""
        try:
            if self.cache_path.exists():
                mtime = self.cache_path.stat().st_mtime
                age_hours = (Path(__file__).stat().st_mtime - mtime) / 3600
                return age_hours > 24
        except:
            pass
        return True
        
    def _load_cache(self):
        """Load app cache"""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self.app_cache[name] = AppInfo(
                            name=info["name"],
                            path=info["path"],
                            app_type=AppType(info["type"]),
                            aliases=info.get("aliases", []),
                        )
        except Exception as e:
            print(f"[APP FINDER] Cache load error: {e}")
            
    def _save_cache(self):
        """Save app cache"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            for name, info in self.app_cache.items():
                data[name] = {
                    "name": info.name,
                    "path": info.path,
                    "type": info.app_type.value,
                    "aliases": info.aliases,
                }
            with open(self.cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[APP FINDER] Cache save error: {e}")
            
    def _scan_apps(self):
        """Scan system for applications"""
        print("[APP FINDER] Scanning for apps...")
        
        # 1. System apps
        for name, cmd in self.SYSTEM_APPS.items():
            self.app_cache[name] = AppInfo(name=name, path=cmd, app_type=AppType.SYSTEM)
            
        # 2. Web apps
        for name, url in self.WEB_APPS.items():
            self.app_cache[name] = AppInfo(name=name, path=url, app_type=AppType.WEB)
            
        # 3. Start Menu (with proper .lnk resolution)
        self._scan_start_menu()
        
        # 4. Registry
        self._scan_registry()
        
        # 5. Common paths
        self._scan_common_paths()
        
        # Deduplicate and save
        self._deduplicate()
        self._save_cache()
        
    def _scan_start_menu(self):
        """Scan Start Menu with proper .lnk resolution"""
        start_paths = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
            Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs"),
        ]
        
        for start_path in start_paths:
            if not start_path.exists():
                continue
                
            for lnk_file in start_path.rglob("*.lnk"):
                try:
                    name = lnk_file.stem.lower()
                    
                    # Skip uninstallers and help files
                    skip_keywords = ["uninstall", "remove", "help", "readme", "documentation"]
                    if any(kw in name for kw in skip_keywords):
                        continue
                        
                    # Resolve the .lnk to get actual target
                    target = self.resolver.resolve_lnk(str(lnk_file))
                    
                    if target and Path(target).exists():
                        # Use resolved path
                        self.app_cache[name] = AppInfo(
                            name=name,
                            path=target,
                            app_type=AppType.DESKTOP
                        )
                    else:
                        # Store .lnk path if can't resolve
                        self.app_cache[name] = AppInfo(
                            name=name,
                            path=str(lnk_file),
                            app_type=AppType.DESKTOP
                        )
                except Exception as e:
                    pass  # Skip problematic shortcuts
                    
    def _scan_registry(self):
        """Scan registry for installed apps"""
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
        ]
        
        for reg_path in reg_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    i = 0
                    while True:
                        try:
                            app_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_name) as app_key:
                                try:
                                    path, _ = winreg.QueryValueEx(app_key, "")
                                    name = app_name.replace(".exe", "").lower()
                                    if name not in self.app_cache:
                                        self.app_cache[name] = AppInfo(
                                            name=name,
                                            path=path,
                                            app_type=AppType.DESKTOP
                                        )
                                except:
                                    pass
                            i += 1
                        except OSError:
                            break
            except:
                pass
                
    def _scan_common_paths(self):
        """Scan common installation directories"""
        common_dirs = [
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
            Path(os.environ.get("LOCALAPPDATA", "")),
        ]
        
        for base_dir in common_dirs:
            if not base_dir.exists():
                continue
                
            # Only scan one level deep for speed
            for exe in base_dir.glob("*/*.exe"):
                try:
                    name = exe.stem.lower()
                    # Skip common non-app executables
                    skip = ["unins", "setup", "install", "update", "crash"]
                    if any(s in name for s in skip):
                        continue
                    if name not in self.app_cache:
                        self.app_cache[name] = AppInfo(
                            name=name,
                            path=str(exe),
                            app_type=AppType.DESKTOP
                        )
                except:
                    pass
                    
    def _deduplicate(self):
        """Remove duplicates and rank apps"""
        seen_paths = {}
        to_remove = []
        
        for name, info in self.app_cache.items():
            path_key = info.path.lower()
            
            if path_key in seen_paths:
                # Keep the shorter/cleaner name
                existing_name = seen_paths[path_key]
                if len(name) < len(existing_name):
                    to_remove.append(existing_name)
                    seen_paths[path_key] = name
                else:
                    to_remove.append(name)
            else:
                seen_paths[path_key] = name
                
        for name in to_remove:
            if name in self.app_cache:
                del self.app_cache[name]
                
    @staticmethod
    def _edit_distance(s1: str, s2: str) -> int:
        """Simple Levenshtein edit distance for typo correction"""
        if len(s1) < len(s2):
            return AppFinder._edit_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                ins = prev_row[j + 1] + 1
                dele = curr_row[j] + 1
                sub = prev_row[j] + (c1 != c2)
                curr_row.append(min(ins, dele, sub))
            prev_row = curr_row
        return prev_row[-1]
    
    def find(self, query: str, _depth: int = 0) -> Optional[AppInfo]:
        """
        Find an application by name.
        Returns the best match or None.
        Checks: exact -> aliases -> web apps -> system apps -> typo correction -> fuzzy substring
        """
        if _depth > 3:
            return None  # Prevent infinite recursion
            
        query = query.lower().strip()
        
        # 1. Exact match in app cache
        if query in self.app_cache:
            return self.app_cache[query]
            
        # 2. Check aliases (includes typo variants like chatpgt->chatgpt)
        for canonical, aliases in self.ALIASES.items():
            if query in aliases or query == canonical:
                # Try exact match for canonical and all aliases in app_cache
                for alias in [canonical] + aliases:
                    if alias in self.app_cache:
                        return self.app_cache[alias]
                # Try substring match in app_cache (e.g., "whatsapp beta" contains "whatsapp")
                for name, info in self.app_cache.items():
                    if canonical in name or name in canonical:
                        return info
                # If canonical not in cache, check web/system apps
                if canonical in self.WEB_APPS:
                    return AppInfo(name=canonical, path=self.WEB_APPS[canonical], app_type=AppType.WEB)
                if canonical in self.SYSTEM_APPS:
                    return AppInfo(name=canonical, path=self.SYSTEM_APPS[canonical], app_type=AppType.SYSTEM)
        
        # 3. Check WEB_APPS directly (YouTube, Gmail, Netflix, etc.)
        if query in self.WEB_APPS:
            return AppInfo(name=query, path=self.WEB_APPS[query], app_type=AppType.WEB)
        
        # 4. Check SYSTEM_APPS directly
        if query in self.SYSTEM_APPS:
            return AppInfo(name=query, path=self.SYSTEM_APPS[query], app_type=AppType.SYSTEM)
        
        # 5. Typo correction via edit distance (max 2 edits)
        if len(query) >= 3:
            best_match = None
            best_dist = 3  # max allowed distance
            # Check against all known names
            all_names = list(self.app_cache.keys()) + list(self.WEB_APPS.keys()) + list(self.SYSTEM_APPS.keys())
            for canonical, aliases in self.ALIASES.items():
                all_names.extend([canonical] + aliases)
            for name in set(all_names):
                if name == query:
                    continue  # Skip exact same name
                dist = self._edit_distance(query, name)
                if dist < best_dist:
                    best_dist = dist
                    best_match = name
            if best_match:
                print(f"[APP FINDER] Typo corrected: '{query}' -> '{best_match}'")
                return self.find(best_match, _depth + 1)
                        
        # 6. Fuzzy substring match
        matches = []
        for name, info in self.app_cache.items():
            if query in name:
                score = len(query) / len(name)
                matches.append((score, info))
            elif name in query:
                score = len(name) / len(query) * 0.8
                matches.append((score, info))
                
        if matches:
            matches.sort(key=lambda x: -x[0])
            return matches[0][1]
            
        return None
        
    def list_apps(self, filter_type: AppType = None) -> List[str]:
        """List all known apps, optionally filtered by type"""
        apps = []
        for name, info in self.app_cache.items():
            if filter_type is None or info.app_type == filter_type:
                apps.append(name)
        return sorted(apps)
        
    def refresh(self):
        """Refresh the app cache"""
        self.app_cache.clear()
        self._scan_apps()
        self._speak("App cache refreshed.")


class AppLauncher:
    """
    Launches applications.
    Separated from finding logic.
    """
    
    def __init__(self, finder: AppFinder):
        self.finder = finder
        
    def _speak(self, text: str):
        self.finder._speak(text)
        
    def launch(self, app_name: str) -> bool:
        """Launch an app by name"""
        title = self.finder._get_title()
        
        # Find the app
        app = self.finder.find(app_name)
        
        if not app:
            # Try PowerShell search as fallback
            if self._launch_via_powershell(app_name):
                self._speak(f"Opening {app_name}, {title}.")
                return True
            self._speak(f"I couldn't find {app_name}, {title}.")
            return False
            
        # Launch based on type
        try:
            if app.app_type == AppType.SYSTEM:
                return self._launch_system(app, title)
            elif app.app_type == AppType.WEB:
                return self._launch_web(app, title)
            elif app.app_type == AppType.DESKTOP:
                return self._launch_desktop(app, title)
            elif app.app_type == AppType.UWP:
                return self._launch_uwp(app, title)
        except Exception as e:
            print(f"[APP LAUNCHER] Error: {e}")
            self._speak(f"Error opening {app_name}, {title}.")
            return False
            
        return False
        
    def _launch_system(self, app: AppInfo, title: str) -> bool:
        """Launch system app"""
        if app.path.startswith("ms-"):
            os.startfile(app.path)
        else:
            subprocess.Popen(app.path, shell=True)
        self._speak(f"Opening {app.name}, {title}.")
        return True
        
    def _launch_web(self, app: AppInfo, title: str) -> bool:
        """Open web app in browser"""
        webbrowser.open(app.path)
        self._speak(f"Opening {app.name} in your browser, {title}.")
        return True
        
    def _launch_desktop(self, app: AppInfo, title: str) -> bool:
        """Launch desktop app"""
        if app.path.endswith(".lnk"):
            os.startfile(app.path)
        else:
            subprocess.Popen([app.path], shell=True)
        self._speak(f"Opening {app.name}, {title}.")
        return True
        
    def _launch_uwp(self, app: AppInfo, title: str) -> bool:
        """Launch UWP/Store app"""
        subprocess.Popen(["explorer", f"shell:AppsFolder\\{app.path}"], shell=True)
        self._speak(f"Opening {app.name}, {title}.")
        return True
        
    def _launch_via_powershell(self, query: str) -> bool:
        """Fallback: find and launch via PowerShell"""
        try:
            ps_script = f'''
                $app = Get-StartApps | Where-Object {{ $_.Name -like "*{query}*" }} | Select-Object -First 1
                if ($app) {{
                    Start-Process "shell:AppsFolder\\$($app.AppID)"
                    exit 0
                }}
                exit 1
            '''
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False


# Combined interface (backward compatible)
class AppManager:
    """Combined finder and launcher for backward compatibility"""
    
    def __init__(self, perception=None):
        self.finder = AppFinder(perception)
        self.launcher = AppLauncher(self.finder)
        
        # Expose common methods
        self.perception = perception
        self.app_cache = self.finder.app_cache
        self.aliases = self.finder.ALIASES
        self.web_apps = self.finder.WEB_APPS
        self.system_apps = self.finder.SYSTEM_APPS
        
    def find_app(self, name: str) -> Optional[str]:
        """Find app path (backward compatible)"""
        app = self.finder.find(name)
        if not app:
            return None
        if app.app_type == AppType.SYSTEM:
            return f"SYSTEM:{app.path}"
        elif app.app_type == AppType.WEB:
            return f"WEB:{app.path}"
        return app.path
        
    def open_app(self, name: str) -> bool:
        """Open an app (backward compatible)"""
        return self.launcher.launch(name)
        
    def open_anything(self, name: str) -> bool:
        """Open anything (backward compatible)"""
        return self.launcher.launch(name)
        
    def refresh_cache(self):
        """Refresh cache (backward compatible)"""
        self.finder.refresh()
        
    def list_known_apps(self) -> List[str]:
        """List apps (backward compatible)"""
        return self.finder.list_apps()


# Alias for backward compatibility
AppFinder_Legacy = AppManager
