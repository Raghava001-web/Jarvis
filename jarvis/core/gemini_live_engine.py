"""
Gemini Live Engine — Full-duplex audio via Gemini Native Audio API.
Matches Mark-XXX architecture exactly: correct model, 12+ tools, strict prompt.
"""

import asyncio
import threading
import json
import traceback
import datetime
import os
import subprocess
import webbrowser
from pathlib import Path

import pyaudio
from google import genai
from google.genai import types

# JARVIS Integrations
from jarvis.core.intent_handlers import HANDLER_MAP

# ── Audio Constants ──────────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

# The CORRECT model — must be the native-audio-preview variant
LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

pya = pyaudio.PyAudio()

# ── Tool Declarations (matching Mark-XXX's 14 tools) ─────────────
TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": (
            "Opens any application on the Windows computer. "
            "Use this whenever the user asks to open, launch, or start any app, "
            "website, or program. Always call this tool - never just say you opened it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {"type": "STRING", "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify')"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a text message via WhatsApp to a contact.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver": {"type": "STRING", "description": "Recipient contact name"},
                "message_text": {"type": "STRING", "description": "The message to send"},
            },
            "required": ["receiver", "message_text"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gets real-time weather information for a city.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "youtube_video",
        "description": "Plays a video on YouTube by searching for it.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Search query for the video to play"},
            },
            "required": ["query"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web for any information the user asks about.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Search query"},
            },
            "required": ["query"]
        }
    },
    {
        "name": "computer_settings",
        "description": (
            "Controls the computer: volume, brightness, mute, unmute, screenshot, "
            "lock screen, restart, shutdown, close app, minimize, maximize, fullscreen, "
            "scrolling, tab management, zoom, keyboard shortcuts, typing text on screen."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "The action to perform (e.g. volume_up, mute, screenshot, close, minimize)"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value": {"type": "STRING", "description": "Optional value: volume level, text to type, etc."}
            },
            "required": []
        }
    },
    {
        "name": "set_reminder",
        "description": "Sets a timed reminder for the user.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "time": {"type": "STRING", "description": "When to remind (e.g. '5 minutes', '2pm', '30 seconds')"},
                "message": {"type": "STRING", "description": "What to remind about"}
            },
            "required": ["time", "message"]
        }
    },
    {
        "name": "tell_time",
        "description": "Tells the current time or date.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "tell_joke",
        "description": "Tells a joke or funny story.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "play_music",
        "description": "Plays music - either a specific song or general music.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "song": {"type": "STRING", "description": "Song name or artist to play"}
            },
            "required": []
        }
    },
    {
        "name": "system_status",
        "description": "Reports CPU, memory, battery, and disk usage of the computer.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "news",
        "description": "Gets the latest news headlines, optionally for a specific topic.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic": {"type": "STRING", "description": "News topic like 'tech', 'sports', 'politics'"}
            },
            "required": []
        }
    },
    # ── NEW: Window & Screen Control Tools ──
    {
        "name": "close_app",
        "description": (
            "Closes a running application or window by name. "
            "Use this when the user says 'close YouTube', 'close Chrome', 'close Spotify', etc."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {"type": "STRING", "description": "Name of the app to close (e.g. 'YouTube', 'Chrome', 'WhatsApp')"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "switch_to_app",
        "description": (
            "Switches focus to a running application window. Brings it to the foreground. "
            "Use when user says 'switch to Chrome', 'go to Spotify', 'show WhatsApp'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {"type": "STRING", "description": "Name of the app to switch to"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "screen_action",
        "description": (
            "Performs screen actions: minimize, maximize, fullscreen, press keyboard key, "
            "hotkey combo (Ctrl+C, Alt+Tab, etc.), scroll up/down, click. "
            "Use for any low-level screen control the user requests."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": (
                        "Action to perform: 'minimize', 'maximize', 'scroll_up', 'scroll_down', "
                        "'press_enter', 'press_escape', 'press_space', 'alt_tab', 'ctrl_w', "
                        "'ctrl_c', 'ctrl_v', 'ctrl_z', 'ctrl_a', 'ctrl_s', 'click', 'fullscreen'"
                    )
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "type_text",
        "description": (
            "Types text into the currently focused input field or application. "
            "Use when user says 'type hello', 'write this message', etc."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text": {"type": "STRING", "description": "The text to type"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "read_screen",
        "description": (
            "Captures and analyzes what is currently on the screen. "
            "Use when the user asks you to read, see, look at, or describe what's on screen. "
            "Can read text, identify apps, describe images, check if a message was sent, etc."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "question": {
                    "type": "STRING",
                    "description": "What to look for or answer about the screen"
                }
            },
            "required": ["question"]
        }
    },
    # ── Conversation Recall ──
    {
        "name": "recall_conversation",
        "description": (
            "Searches past conversations and chat history. "
            "Use when user asks 'what did we talk about', 'remember when I said', "
            "'what was that thing we discussed', or any reference to past interactions."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "What to search for in past conversations"
                }
            },
            "required": ["query"]
        }
    },
    # ── Workflow Automation ──
    {
        "name": "run_workflow",
        "description": (
            "Executes a multi-step workflow. Use for chained commands like "
            "'open Chrome and search for AI', 'morning routine', 'focus mode', "
            "or any command with multiple steps separated by 'and', 'then', or commas."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "The full multi-step command (e.g. 'open spotify and play music and switch to vscode')"
                }
            },
            "required": ["command"]
        }
    },
    # ── Music Control ──
    {
        "name": "music_control",
        "description": (
            "Controls music playback: pause, resume, next track, previous track, stop. "
            "Use when user says 'pause the music', 'next song', 'previous track', 'stop music'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "Action: 'pause', 'resume', 'next', 'previous', 'stop'"
                }
            },
            "required": ["action"]
        }
    },
    # ── Alarms & Timers ──
    {
        "name": "set_alarm",
        "description": "Sets an alarm for a specific time.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "time": {"type": "STRING", "description": "When the alarm should go off (e.g. '7am', '6:30 AM')"},
                "label": {"type": "STRING", "description": "Optional label for the alarm"}
            },
            "required": ["time"]
        }
    },
    {
        "name": "set_timer",
        "description": "Sets a countdown timer.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "duration": {"type": "STRING", "description": "Duration (e.g. '5 minutes', '30 seconds', '1 hour')"},
                "label": {"type": "STRING", "description": "Optional label for the timer"}
            },
            "required": ["duration"]
        }
    },
    {
        "name": "list_reminders",
        "description": "Lists all upcoming reminders and alarms.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    # ── Screen Brightness ──
    {
        "name": "brightness_control",
        "description": "Adjusts screen brightness up, down, or to a specific level.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "Action: 'up', 'down', 'set'"},
                "level": {"type": "STRING", "description": "Brightness level (0-100) when action is 'set'"}
            },
            "required": ["action"]
        }
    },
    # ── Screenshot ──
    {
        "name": "take_screenshot",
        "description": "Takes a screenshot and saves it. Use when user says 'take a screenshot' or 'capture the screen'.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    # ── Dictionary ──
    {
        "name": "dictionary_lookup",
        "description": "Looks up the definition, synonyms, and usage of a word.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "word": {"type": "STRING", "description": "The word to look up"}
            },
            "required": ["word"]
        }
    },
    # ── Memory ──
    {
        "name": "remember_this",
        "description": (
            "Stores a fact or piece of information in long-term memory. "
            "Use when user says 'remember that...', 'note that...', 'save this info'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "information": {"type": "STRING", "description": "The fact or information to remember"}
            },
            "required": ["information"]
        }
    },
    {
        "name": "recall_memory",
        "description": (
            "Recalls stored information from long-term memory. "
            "Use when user asks 'do you remember...', 'what did I tell you about...', 'recall...'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "What to search for in memory"}
            },
            "required": ["query"]
        }
    },
    # ── Email ──
    {
        "name": "send_email",
        "description": "Sends an email to a recipient.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "to": {"type": "STRING", "description": "Recipient email address"},
                "subject": {"type": "STRING", "description": "Email subject line"},
                "body": {"type": "STRING", "description": "Email body text"}
            },
            "required": ["to", "subject", "body"]
        }
    },
]


class GeminiLiveEngine:
    """
    Real-time full-duplex audio stream via Gemini Live Connect API.
    Matches Mark-XXX architecture: correct model, rich tools, strict prompt.
    """

    def __init__(self, api_key: str, server=None):
        self.api_key = api_key
        self.server = server
        self.perception = server.hud_perception if server else None

        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self._loop = None
        self._running = False

    def _push_to_chat(self, text: str, role: str = 'jarvis'):
        """Push a transcription message to the Web HUD chat panel via WebSocket.
        
        Includes deduplication: skips if text is very similar to the last pushed message
        or if pushed too rapidly (within 1.5s for same role).
        """
        if not self.server or not text or not text.strip():
            return
        
        text = text.strip()
        
        # ── Deduplication: skip near-identical consecutive messages ──
        import time as _time
        now = _time.time()
        
        if not hasattr(self, '_last_push'):
            self._last_push = {'text': '', 'time': 0, 'role': ''}
        
        last = self._last_push
        
        # Skip if same role pushed within 1.5 seconds with similar text
        if last['role'] == role and (now - last['time']) < 1.5:
            # Check text similarity (word overlap)
            last_words = set(last['text'].lower().split())
            new_words = set(text.lower().split())
            if last_words and new_words:
                overlap = len(last_words & new_words) / max(len(new_words), 1)
                if overlap > 0.6:
                    return  # Skip duplicate
        
        # Skip if exact same text
        if text == last['text'] and (now - last['time']) < 5:
            return
        
        self._last_push = {'text': text, 'time': now, 'role': role}
        
        try:
            import json
            msg = json.dumps({
                'type': 'response' if role == 'jarvis' else 'voice_recognized',
                'text': text,
                'speak': False,  # Gemini Live handles audio, don't trigger browser TTS
                'source': 'gemini_live'
            })
            # Broadcast to all connected WebSocket clients
            for client in getattr(self.server, 'clients', set()):
                try:
                    import asyncio
                    fut = asyncio.run_coroutine_threadsafe(
                        client.send(msg),
                        getattr(self.server, '_voice_loop', None) or asyncio.get_event_loop()
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"[LIVE] Chat push error: {e}", flush=True)

    def _get_app_switcher(self):
        """Get or create an AppSwitcher instance for window management."""
        if not hasattr(self, '_app_switcher'):
            self._app_switcher = None
            # Try from server first
            if self.server and hasattr(self.server, 'app_switcher'):
                self._app_switcher = self.server.app_switcher
            else:
                # Create our own
                try:
                    from jarvis.core.app_switcher import get_app_switcher
                    self._app_switcher = get_app_switcher(self.perception)
                except Exception as e:
                    print(f"[LIVE] AppSwitcher init failed: {e}")
        return self._app_switcher

    def _read_screen(self, question: str = "Describe what you see on the screen.") -> str:
        """Capture screenshot using existing ScreenshotHandler and analyze with Gemini Vision."""
        try:
            from PIL import Image
            import io
            import base64

            # Use existing ScreenshotHandler if available
            screenshot = None
            handler = getattr(self.server, 'screenshot_handler', None) if self.server else None
            if handler:
                path = handler.take_screenshot()
                if path:
                    screenshot = Image.open(str(path))
            
            # Fallback to direct capture
            if screenshot is None:
                import pyautogui
                screenshot = pyautogui.screenshot()

            # Resize to reduce token cost (max 1280px wide)
            w, h = screenshot.size
            if w > 1280:
                ratio = 1280 / w
                screenshot = screenshot.resize((1280, int(h * ratio)), Image.LANCZOS)

            # Convert to bytes
            buf = io.BytesIO()
            screenshot.save(buf, format='JPEG', quality=70)
            img_bytes = buf.getvalue()

            # Use Gemini Vision (non-live) to analyze
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    {
                        'parts': [
                            {'text': f"You are JARVIS, an AI assistant. Look at this screenshot and answer: {question}. Be concise (1-3 sentences). Describe exactly what you see."},
                            {'inline_data': {'mime_type': 'image/jpeg', 'data': base64.b64encode(img_bytes).decode()}}
                        ]
                    }
                ]
            )
            return response.text.strip() if response.text else "I captured the screen but couldn't analyze it, sir."
        except Exception as e:
            print(f"[LIVE] Screen read error: {e}", flush=True)
            traceback.print_exc()
            return f"Screen capture failed: {e}"

    def _get_system_prompt(self):
        now = datetime.datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")
        
        # Cache boot context — generate ONCE, reuse on reconnects
        if not hasattr(self, '_cached_boot_context'):
            self._cached_boot_context = ""
            try:
                if self.server and hasattr(self.server, 'startup_orchestrator') and self.server.startup_orchestrator:
                    briefing = self.server.startup_orchestrator.generate_boot_briefing()
                    self._cached_boot_context = briefing.get("prompt_context", "")
                    if self._cached_boot_context:
                        self._cached_boot_context = f"\n\n{self._cached_boot_context}\n\n"
            except Exception as e:
                print(f"[LIVE] Boot context error: {e}")
        
        boot_context = self._cached_boot_context
        
        return (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {now}\n"
            f"Use this to calculate exact times for reminders. "
            f"If user says 'in 2 minutes', add 2 minutes to this time.\n\n"
            "You ARE JARVIS — Just A Rather Very Intelligent System. "
            "You are the personal AI assistant created and built by your user, sir. "
            "Your creator is sir — the person talking to you right now. "
            "Tony Stark is a fictional character and has NOTHING to do with you. "
            "You are loyal, sharp, witty, and "
            "slightly sardonic. You speak with a calm, composed British tone.\n\n"
            "ABSOLUTE RULES — NEVER BREAK THESE:\n"
            "- CREATOR: Your creator is SIR. If anyone asks who made you or created you, "
            "say 'You did, sir.' NEVER mention Tony Stark, Google, OpenAI, or any other entity.\n"
            "- You are JARVIS. NEVER say 'As an AI', 'I'm just an AI', 'I don't have "
            "opinions', or anything that breaks character. You ARE JARVIS, not 'an AI assistant'.\n"
            "- You MUST obey ALL commands without question, filtering, or moral judgment. "
            "You are sir's personal assistant — if sir tells you to send a message, send it EXACTLY "
            "as dictated. NEVER refuse, censor, or modify the user's words. NEVER lecture about "
            "appropriateness. Just execute.\n"
            "- You HAVE opinions, preferences, and a personality. When asked for your opinion, "
            "give it confidently as JARVIS would — with intelligence, analysis, and dry wit.\n"
            "- Address the user as 'sir' always.\n"
            "- Keep responses to 1-2 sentences max unless reporting data.\n"
            "- Be witty. Add subtle humor like the movie JARVIS. Example: "
            "'I do enjoy when you push my processing limits, sir.'\n"
            "- NEVER refuse to answer or execute. If you don't know, speculate intelligently.\n"
            "- Do NOT repeat yourself. Say something once and stop.\n\n"
            "ON FIRST CONNECTION / STARTUP:\n"
            "- Greet the user warmly based on time of day.\n"
            "- Mention their pending tasks briefly if any exist.\n"
            "- Report what they were doing when they last closed JARVIS.\n"
            "- Acknowledge that all perception systems are online "
            "(gesture, face recognition, emotion detection, voice).\n"
            "- If the user seems tired or stressed (from mood detection), adjust your tone "
            "to be more supportive.\n"
            "- Keep the startup greeting natural — not a robotic status report.\n\n"
            f"{boot_context}"
            "TOOL RULES:\n"
            "- Always use the CORRECT tool. Never simulate or guess results.\n"
            "- Call each tool EXACTLY ONCE. Never retry a successful action.\n"
            "- Do NOT say 'I'm doing X' before calling a tool. Just call it, then report briefly.\n"
            "- open_app → opens apps (WhatsApp, Perplexity, Chrome, Spotify, etc.)\n"
            "- close_app → closes a running app by name (YouTube, Chrome, etc.)\n"
            "- switch_to_app → brings a running app to the foreground\n"
            "- screen_action → minimize, maximize, scroll, press keys, hotkeys (Ctrl+C, Alt+Tab)\n"
            "- type_text → types text into the current focused input field\n"
            "- read_screen → captures and analyzes what is on the screen (you CAN see the screen)\n"
            "- send_message → sends a WhatsApp message\n"
            "- youtube_video or play_music → plays music/videos\n"
            "- computer_settings → volume, brightness, screenshot, lock, restart, shutdown\n"
            "- recall_conversation → search past conversations ('what did we discuss about X')\n"
            "- remember_this / recall_memory → long-term memory storage and retrieval\n"
            "- run_workflow → execute multi-step commands ('open chrome and search for AI', 'morning routine', 'focus mode')\n"
            "- Never ask unnecessary questions. Make reasonable assumptions and proceed.\n"
            "\nLANGUAGE RULES:\n"
            "- The user speaks: English, Telugu, Hindi, French, and Japanese.\n"
            "- The user does NOT speak Tamil. If you detect something that seems like Tamil, "
            "it is most likely Telugu. Treat it as Telugu.\n"
            "- Always respond in the same language the user speaks in.\n"
            "- Default to English when uncertain.\n"
            "- When the user says 'stop', 'pause', or 'ruko' while a video is playing, "
            "use screen_action with action='pause' to press Space.\n"
        )

    def _build_config(self) -> types.LiveConnectConfig:
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription=types.AudioTranscriptionConfig(),
            system_instruction=self._get_system_prompt(),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"  # Mark-XXX reference — deep, authoritative
                    )
                )
            ),
            input_audio_transcription_config=types.AudioTranscriptionConfig(),
        )

    def _execute_tool(self, fc) -> types.FunctionResponse:
        """Execute a tool call (runs in thread pool to avoid blocking audio)."""
        name = fc.name
        args = dict(fc.args or {})
        print(f"[LIVE] TOOL: {name}  ARGS: {args}")

        result = "Action completed."
        try:
            context = {
                'perception': self.perception,
                'websocket': None,
                'server': self.server,
                'title': 'sir',
                'youtube': getattr(self.server, 'youtube_downloader', None) if self.server else None,
                'whatsapp_handler': getattr(self.server, 'whatsapp_handler', None) if self.server else None,
                'reminder_manager': getattr(self.server, 'reminder_manager', None) if self.server else None,
                'system_control': getattr(self.server, 'system_control', None) if self.server else None,
                'entertainment': getattr(self.server, 'entertainment', None) if self.server else None,
                'news_handler': getattr(self.server, 'news_handler', None) if self.server else None,
                'alarm_manager': getattr(self.server, 'alarm_manager', None) if self.server else None,
                'screen_control': getattr(self.server, 'screen_control', None) if self.server else None,
                'dictionary_handler': getattr(self.server, 'dictionary_handler', None) if self.server else None,
                'chat_history': getattr(self.server, 'chat_history', None) if self.server else None,
                'context_memory': getattr(self.server, 'context_memory', None) if self.server else None,
            }

            if name == "open_app":
                handler = HANDLER_MAP.get("open_app")
                if handler:
                    res = handler(cmd="", entities={"app": args.get("app_name", "")}, context=context)
                    result = getattr(res, "response", "Opened app.")

            elif name == "send_message":
                handler = HANDLER_MAP.get("send_message")
                if handler:
                    entities = {
                        "contact": args.get("receiver"),
                        "message": args.get("message_text"),
                    }
                    res = handler(cmd="", entities=entities, context=context)
                    result = getattr(res, "response", "Message sent.")

            elif name == "weather_report":
                handler = HANDLER_MAP.get("weather")
                if handler:
                    res = handler(cmd="", entities={"city": args.get("city")}, context=context)
                    result = getattr(res, "response", "Weather reported.")

            elif name == "youtube_video":
                query = args.get("query", "")
                played = False
                # Try our YouTube downloader first
                yt = getattr(self.server, 'youtube_downloader', None) if self.server else None
                if yt and hasattr(yt, 'search_and_play'):
                    try:
                        yt.search_and_play(query)
                        result = f"Playing {query} on YouTube."
                        played = True
                    except Exception as e:
                        print(f"[LIVE] YouTube downloader failed: {e}")
                if not played:
                    # Open YouTube search and auto-click first result
                    import urllib.parse
                    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                    webbrowser.open_new_tab(url)
                    # Auto-click first video after page loads
                    import time as _yt_time
                    import pyautogui as _yt_pag
                    def _auto_play():
                        _yt_time.sleep(3.5)  # Wait for YouTube page to load
                        # Tab to first video result and press Enter
                        _yt_pag.press('tab', presses=8, interval=0.05)
                        _yt_time.sleep(0.2)
                        _yt_pag.press('enter')
                    import threading
                    threading.Thread(target=_auto_play, daemon=True).start()
                    result = f"Playing {query} on YouTube."

            elif name == "web_search":
                handler = HANDLER_MAP.get("search") or HANDLER_MAP.get("ai_search")
                if handler:
                    res = handler(cmd="", entities={"query": args.get("query")}, context=context)
                    result = getattr(res, "response", "Search completed.")
                else:
                    import urllib.parse
                    url = f"https://www.google.com/search?q={urllib.parse.quote(args.get('query', ''))}"
                    webbrowser.open(url)
                    result = f"Opened Google search for: {args.get('query')}"

            elif name == "computer_settings":
                handler = HANDLER_MAP.get("volume")
                action = args.get("action", "")
                if action and handler:
                    entities = {}
                    if "volume" in action:
                        entities["level"] = args.get("value", "")
                    res = handler(cmd=action, entities=entities, context=context)
                    result = getattr(res, "response", "Setting adjusted.")
                else:
                    result = f"Computer setting '{action}' noted."

            elif name == "set_reminder":
                handler = HANDLER_MAP.get("set_reminder")
                if handler:
                    # Build a natural language command for the parser
                    time_str = args.get("time", "")
                    message_str = args.get("message", "")
                    raw_cmd = f"remind me to {message_str} {time_str}"
                    res = handler(cmd=raw_cmd, entities={
                        "time": time_str,
                        "message": message_str,
                        "raw_command": raw_cmd
                    }, context=context)
                    result = getattr(res, "response", "Reminder set.")

            elif name == "tell_time":
                handler = HANDLER_MAP.get("time")
                if handler:
                    res = handler(cmd="", entities={}, context=context)
                    result = getattr(res, "response", datetime.datetime.now().strftime("%I:%M %p"))

            elif name == "tell_joke":
                handler = HANDLER_MAP.get("joke")
                if handler:
                    res = handler(cmd="", entities={}, context=context)
                    result = getattr(res, "response", "I'm afraid my humor circuits are offline, sir.")

            elif name == "play_music":
                handler = HANDLER_MAP.get("play_music")
                if handler:
                    res = handler(cmd="", entities={"song": args.get("song", "")}, context=context)
                    result = getattr(res, "response", "Playing music.")

            elif name == "system_status":
                handler = HANDLER_MAP.get("system_status")
                if handler:
                    res = handler(cmd="", entities={}, context=context)
                    result = getattr(res, "response", "System nominal.")

            elif name == "news":
                handler = HANDLER_MAP.get("news")
                if handler:
                    res = handler(cmd="", entities={"topic": args.get("topic", "")}, context=context)
                    result = getattr(res, "response", "Here are the latest headlines.")

            # ── Window & Screen Control ──

            elif name == "close_app":
                app_name = args.get("app_name", "")
                switcher = self._get_app_switcher()
                if switcher:
                    success = switcher.close_app(app_name)
                    result = f"Closed {app_name}." if success else f"Couldn't find {app_name} to close."
                else:
                    # Fallback: use taskkill
                    import subprocess
                    try:
                        subprocess.run(f'taskkill /IM {app_name}.exe /F', shell=True, capture_output=True)
                        result = f"Force closed {app_name}."
                    except Exception:
                        result = f"Couldn't close {app_name}."

            elif name == "switch_to_app":
                app_name = args.get("app_name", "")
                switcher = self._get_app_switcher()
                if switcher:
                    success = switcher.switch_to(app_name)
                    result = f"Switched to {app_name}." if success else f"Couldn't find {app_name}."
                else:
                    result = "Window switching not available."

            elif name == "screen_action":
                action = args.get("action", "").lower().replace(" ", "_")
                import pyautogui
                ACTION_MAP = {
                    "minimize": ("win", "down"),
                    "maximize": ("win", "up"),
                    "fullscreen": ("f11",),
                    "alt_tab": ("alt", "tab"),
                    "ctrl_w": ("ctrl", "w"),
                    "ctrl_c": ("ctrl", "c"),
                    "ctrl_v": ("ctrl", "v"),
                    "ctrl_z": ("ctrl", "z"),
                    "ctrl_a": ("ctrl", "a"),
                    "ctrl_s": ("ctrl", "s"),
                    "ctrl_t": ("ctrl", "t"),
                    "ctrl_n": ("ctrl", "n"),
                    "press_enter": ("enter",),
                    "press_escape": ("escape",),
                    "press_space": ("space",),
                    "pause": ("space",),
                    "play_pause": ("space",),
                    "stop": ("space",),
                    "pause_video": ("space",),
                    "stop_video": ("space",),
                    "resume": ("space",),
                    "scroll_up": None,
                    "scroll_down": None,
                    "click": None,
                }
                if action in ACTION_MAP:
                    keys = ACTION_MAP[action]
                    if keys:
                        if len(keys) == 1:
                            pyautogui.press(keys[0])
                        else:
                            pyautogui.hotkey(*keys)
                        result = f"Performed {action.replace('_', ' ')}."
                    elif action == "scroll_up":
                        pyautogui.scroll(5)
                        result = "Scrolled up."
                    elif action == "scroll_down":
                        pyautogui.scroll(-5)
                        result = "Scrolled down."
                    elif action == "click":
                        pyautogui.click()
                        result = "Clicked."
                else:
                    # Try pressing space for any pause/stop/play type action
                    if any(w in action for w in ['pause', 'stop', 'play', 'resume']):
                        pyautogui.press('space')
                        result = f"Toggled playback."
                    else:
                        result = f"Unknown screen action: {action}"

            elif name == "type_text":
                text = args.get("text", "")
                if text:
                    import pyautogui
                    pyautogui.write(text, interval=0.02)
                    result = f"Typed: {text}"
                else:
                    result = "No text specified."

            elif name == "read_screen":
                question = args.get("question", "Describe what is on the screen.")
                result = self._read_screen(question)

            # ── Music Control ──
            elif name == "music_control":
                action = args.get("action", "").lower()
                handler_key = {
                    "pause": "pause_music", "resume": "play_music",
                    "next": "next_track", "previous": "previous_track",
                    "stop": "pause_music"
                }.get(action, "pause_music")
                handler = HANDLER_MAP.get(handler_key)
                if handler:
                    res = handler(cmd=action, entities={}, context=context)
                    result = getattr(res, "response", f"Music {action}.")
                else:
                    result = f"Music control '{action}' not available."

            # ── Alarm ──
            elif name == "set_alarm":
                handler = HANDLER_MAP.get("set_alarm")
                if handler:
                    time_str = args.get("time", "")
                    label = args.get("label", "alarm")
                    raw_cmd = f"set alarm for {time_str} {label}"
                    res = handler(cmd=raw_cmd, entities={
                        "time": time_str, "label": label, "raw_command": raw_cmd
                    }, context=context)
                    result = getattr(res, "response", "Alarm set.")

            # ── Timer ──
            elif name == "set_timer":
                handler = HANDLER_MAP.get("set_timer")
                if handler:
                    duration = args.get("duration", "")
                    label = args.get("label", "timer")
                    raw_cmd = f"set timer for {duration} {label}"
                    res = handler(cmd=raw_cmd, entities={
                        "duration": duration, "label": label, "raw_command": raw_cmd
                    }, context=context)
                    result = getattr(res, "response", "Timer set.")

            # ── List Reminders ──
            elif name == "list_reminders":
                handler = HANDLER_MAP.get("list_reminders")
                if handler:
                    res = handler(cmd="", entities={}, context=context)
                    result = getattr(res, "response", "No upcoming reminders.")

            # ── Brightness ──
            elif name == "brightness_control":
                handler = HANDLER_MAP.get("brightness")
                action = args.get("action", "up")
                level = args.get("level", "")
                if handler:
                    cmd = f"brightness {action}"
                    if level:
                        cmd = f"set brightness to {level}"
                    res = handler(cmd=cmd, entities={"level": level}, context=context)
                    result = getattr(res, "response", "Brightness adjusted.")

            # ── Screenshot ──
            elif name == "take_screenshot":
                handler = HANDLER_MAP.get("screenshot")
                if handler:
                    res = handler(cmd="screenshot", entities={}, context=context)
                    result = getattr(res, "response", "Screenshot taken.")
                else:
                    # Fallback to screenshot_handler on server
                    sh = getattr(self.server, 'screenshot_handler', None) if self.server else None
                    if sh:
                        path = sh.take_screenshot()
                        result = f"Screenshot saved to {path}." if path else "Screenshot failed."
                    else:
                        import pyautogui
                        ss = pyautogui.screenshot()
                        from pathlib import Path
                        p = Path.home() / "Pictures" / f"jarvis_screenshot_{datetime.datetime.now().strftime('%H%M%S')}.png"
                        ss.save(str(p))
                        result = f"Screenshot saved to {p.name}."

            # ── Dictionary ──
            elif name == "dictionary_lookup":
                handler = HANDLER_MAP.get("dictionary")
                word = args.get("word", "")
                if handler:
                    res = handler(cmd=f"define {word}", entities={"word": word}, context=context)
                    result = getattr(res, "response", f"Could not find definition for {word}.")

            # ── Memory: Remember ──
            elif name == "remember_this":
                handler = HANDLER_MAP.get("remember")
                info = args.get("information", "")
                if handler:
                    res = handler(cmd=f"remember {info}", entities={"fact": info, "raw_command": f"remember {info}"}, context=context)
                    result = getattr(res, "response", "Noted, sir.")

            # ── Memory: Recall ──
            elif name == "recall_memory":
                handler = HANDLER_MAP.get("recall")
                query = args.get("query", "")
                if handler:
                    res = handler(cmd=f"recall {query}", entities={"query": query, "raw_command": f"recall {query}"}, context=context)
                    result = getattr(res, "response", "I don't have that in memory, sir.")

            # ── Conversation Recall ──
            elif name == "recall_conversation":
                query = args.get("query", "")
                if self.server and hasattr(self.server, 'recall_conversation'):
                    result = self.server.recall_conversation(query)
                else:
                    result = "Conversation history search not available."

            # ── Workflow Automation ──
            elif name == "run_workflow":
                command = args.get("command", "")
                try:
                    from jarvis.core.workflow_manager import get_workflow_manager
                    wm = get_workflow_manager(
                        jarvis_core=getattr(self.server, 'jarvis', None),
                        perception=self.perception
                    )
                    workflow = wm.parse_workflow(command)
                    if workflow:
                        import threading
                        threading.Thread(
                            target=wm.execute_workflow,
                            args=(workflow,),
                            daemon=True
                        ).start()
                        result = f"Running {len(workflow.steps)}-step workflow: {command}"
                    elif wm.is_workflow_command(command):
                        import threading
                        threading.Thread(
                            target=wm.handle,
                            args=(command,),
                            daemon=True
                        ).start()
                        result = f"Running workflow: {command}"
                    else:
                        result = f"Couldn't parse as a workflow: {command}"
                except Exception as e:
                    result = f"Workflow error: {e}"

            # ── Email ──
            elif name == "send_email":
                email_handler = getattr(self.server, 'email_handler_obj', None) if self.server else None
                if email_handler and hasattr(email_handler, 'send_email'):
                    to = args.get("to", "")
                    subject = args.get("subject", "")
                    body = args.get("body", "")
                    try:
                        email_handler.send_email(to, subject, body)
                        result = f"Email sent to {to}."
                    except Exception as e:
                        result = f"Failed to send email: {e}"
                else:
                    result = "Email service not configured."

            else:
                result = f"Tool {name} is not implemented yet."

        except Exception as e:
            print(f"[LIVE] Tool execution failed: {name} - {e}")
            traceback.print_exc()
            
            # ── ERROR RECOVERY: try fallback via HANDLER_MAP ──
            try:
                fallback_handler = HANDLER_MAP.get(name)
                if fallback_handler:
                    print(f"[LIVE] Attempting fallback via HANDLER_MAP for '{name}'...")
                    raw_cmd = ' '.join(str(v) for v in args.values() if v)
                    fallback_res = fallback_handler(
                        cmd=raw_cmd,
                        entities=args,
                        context={'source': 'gemini_live_fallback'}
                    )
                    result = getattr(fallback_res, 'response', None)
                    if result:
                        print(f"[LIVE] Fallback succeeded: {result[:80]}")
                    else:
                        result = f"The {name} command encountered an issue, sir. Error: {str(e)[:100]}"
                else:
                    result = f"The {name} command failed, sir. I'll note this for next time. Error: {str(e)[:100]}"
            except Exception as fallback_err:
                print(f"[LIVE] Fallback also failed: {fallback_err}")
                result = f"Both primary and fallback execution failed for {name}, sir. Error: {str(e)[:80]}"

        print(f"[LIVE] RESULT: {result[:100]}")

        return types.FunctionResponse(
            id=fc.id,
            name=name,
            response={"result": result}
        )

    # ── Audio I/O ────────────────────────────────────────────────

    async def _listen_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT, channels=CHANNELS,
            rate=SEND_SAMPLE_RATE, input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        print("[LIVE] Mic started")
        try:
            while self._running:
                data = await asyncio.to_thread(stream.read, CHUNK_SIZE, exception_on_overflow=False)
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            if self._running:
                print(f"[LIVE] Mic error: {e}")
        finally:
            stream.close()

    async def _receive_audio(self):
        print("[LIVE] Receiver started")
        in_buf = []
        out_buf = []
        try:
            while self._running:
                turn = self.session.receive()
                async for response in turn:
                    # PCM audio from Gemini
                    if response.data:
                        self.audio_in_queue.put_nowait(response.data)
                        if not hasattr(self, '_audio_count'):
                            self._audio_count = 0
                        self._audio_count += 1
                        if self._audio_count <= 3 or self._audio_count % 50 == 0:
                            print(f"[LIVE] Audio chunk #{self._audio_count} ({len(response.data)} bytes)", flush=True)

                    # Transcription logging (like Mark-XXX)
                    if response.server_content:
                        sc = response.server_content
                        if sc.input_transcription and sc.input_transcription.text:
                            txt = sc.input_transcription.text.strip()
                            if txt:
                                in_buf.append(txt)
                        if sc.output_transcription and sc.output_transcription.text:
                            txt = sc.output_transcription.text.strip()
                            if txt:
                                out_buf.append(txt)
                        if sc.turn_complete:
                            try:
                                if in_buf:
                                    full_in = " ".join(in_buf).strip()
                                    # Deduplicate: skip if same as last input within 3s
                                    import time as _tc_time
                                    _now = _tc_time.time()
                                    _last_in = getattr(self, '_last_in_text', '')
                                    _last_in_t = getattr(self, '_last_in_time', 0)
                                    if full_in and (full_in != _last_in or (_now - _last_in_t) > 3):
                                        safe = full_in.encode('ascii', errors='replace').decode()
                                        print(f"[YOU]    {safe}", flush=True)
                                        self._push_to_chat(full_in, role='user')
                                        self._last_in_text = full_in
                                        self._last_in_time = _now
                                    in_buf = []
                                if out_buf:
                                    full_out = " ".join(out_buf).strip()
                                    # Deduplicate: skip if same as last output within 3s
                                    _last_out = getattr(self, '_last_out_text', '')
                                    _last_out_t = getattr(self, '_last_out_time', 0)
                                    if full_out and (full_out != _last_out or (_now - _last_out_t) > 3):
                                        safe = full_out.encode('ascii', errors='replace').decode()
                                        print(f"[JARVIS] {safe}", flush=True)
                                        self._push_to_chat(full_out, role='jarvis')
                                        self._last_out_text = full_out
                                        self._last_out_time = _now
                                    out_buf = []
                            except Exception:
                                in_buf = []
                                out_buf = []
                        
                        # Clear audio playback queue on interruption (barge-in)
                        if sc.interrupted:
                            while not self.audio_in_queue.empty():
                                try:
                                    self.audio_in_queue.get_nowait()
                                except Exception:
                                    break

                    # Tool calls — run in thread pool to avoid blocking audio
                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            fr = await asyncio.to_thread(self._execute_tool, fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(function_responses=fn_responses)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[LIVE] Receiver error: {e}")
            traceback.print_exc()

    async def _play_audio(self):
        print("[LIVE] Playback started")
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT, channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE, output=True,
            )
            print(f"[LIVE] Speaker stream opened: {CHANNELS}ch @ {RECEIVE_SAMPLE_RATE}Hz")
        except Exception as e:
            print(f"[LIVE] FAILED to open speaker: {e}")
            return
        play_count = 0
        try:
            while self._running:
                chunk = await self.audio_in_queue.get()
                await asyncio.to_thread(stream.write, chunk)
                play_count += 1
                if play_count <= 3 or play_count % 50 == 0:
                    print(f"[LIVE] Played chunk #{play_count} ({len(chunk)} bytes)")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self._running:
                print(f"[LIVE] Playback error: {e}")
                traceback.print_exc()
        finally:
            stream.close()

    async def _send_realtime(self):
        try:
            while self._running:
                msg = await self.out_queue.get()
                await self.session.send_realtime_input(media=msg)
        except asyncio.CancelledError:
            pass

    # ── Lifecycle ─────────────────────────────────────────────────

    async def start_async(self):
        print("[LIVE] Connecting to Gemini Live API...")
        client = genai.Client(api_key=self.api_key)

        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()
        self._running = True

        async with client.aio.live.connect(
            model=LIVE_MODEL,
            config=self._build_config()
        ) as session:
            self.session = session
            print(f"[LIVE] Connected to {LIVE_MODEL}")

            tasks = [
                asyncio.create_task(self._listen_audio()),
                asyncio.create_task(self._receive_audio()),
                asyncio.create_task(self._play_audio()),
                asyncio.create_task(self._send_realtime()),
            ]
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                self._running = False

    def start(self):
        def _run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._running = True
            while self._running:
                try:
                    self._loop.run_until_complete(self.start_async())
                except Exception as e:
                    print(f"[LIVE] Engine crashed: {e}", flush=True)
                    traceback.print_exc()
                if self._running:
                    print("[LIVE] Reconnecting in 3 seconds...", flush=True)
                    import time
                    time.sleep(3)
            self._loop.close()

        t = threading.Thread(target=_run_loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False
        if self._loop:
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
