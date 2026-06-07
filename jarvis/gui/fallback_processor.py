import json
import re
import os
import random
import subprocess
import webbrowser
from datetime import datetime
from jarvis.gui.data_providers import maybe_title

class FallbackProcessor:
    """
    Fallback command processing logic extracted from websocket_server.py.
    Used when the main JARVISUltimate system is offline or unavailable.
    """
    def __init__(self, server):
        self.server = server

    async def process(self, command: str, websocket) -> str:
        cmd = command.lower().strip()
        name = self.server.hud_perception.assistant_name
        title = self.server.hud_perception.user_title
        
        # Voice switching (needs WebSocket - handle before router)
        if 'switch to friday' in cmd or 'activate friday' in cmd:
            self.server.hud_perception.switch_to_friday()
            await self.server._send_to(websocket, json.dumps({
                'type': 'assistant_info',
                'name': 'FRIDAY',
                'is_friday': True
            }))
            return "FRIDAY online. Hello, boss. How can I help you today?"
        
        if 'switch to jarvis' in cmd or 'activate jarvis' in cmd:
            self.server.hud_perception.switch_to_jarvis()
            await self.server._send_to(websocket, json.dumps({
                'type': 'assistant_info',
                'name': 'JARVIS',
                'is_friday': False
            }))
            return f"JARVIS back online, {title}. At your service."
        
        # ══════════════════════════════════════════════════════════════════
        # LEGACY HANDLERS: for commands not yet migrated to IntentRouter
        # IntentRouter is now checked FIRST in process_command()
        # ══════════════════════════════════════════════════════════════════
        
        # Greetings - use sir once
        if any(word in cmd for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'good night']):
            hour = datetime.now().hour
            greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Hey there"
            return f"{greeting}, {title}. How may I help?"
        
        # Time - short response, sir once at end
        # Exclude 'bedtime story' — 'time' in 'bedtime' is a false match
        if 'time' in cmd and not any(w in cmd for w in ['story', 'bedtime', 'once upon', 'tale']):
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}, {title}."
        
        # Date - short response, sir once
        if 'date' in cmd or ('what' in cmd and 'day' in cmd):
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}, {title}."
        
        # System status - long response, sir once at the END only
        if 'system status' in cmd or 'system report' in cmd:
            stats = self.server.get_system_stats()
            charge = " and charging" if stats.get('charging') else ""
            return f"All systems operational. CPU at {stats['cpu']}%, " \
                   f"memory at {stats['memory']}%, disk at {stats['disk']}%, " \
                   f"battery at {stats['battery']}%{charge}, {title}."
        
        # How are you - sir once at end
        if 'how are you' in cmd:
            stats = self.server.get_system_stats()
            if stats['cpu'] < 50:
                return f"Operating at peak efficiency, {title}. All systems nominal."
            else:
                return f"Functioning well, {title}. System load is moderate but manageable."
        
        # Weather
        if 'weather' in cmd:
            weather = self.server.get_weather_data()
            return f"Current conditions in {weather['location']}: {weather['temp']}°C, " \
                   f"{weather['condition']}. Humidity at {weather['humidity']}%, " \
                   f"wind {weather['wind']} kilometers per hour."
        
        # General news
        if 'news' in cmd or 'headline' in cmd:
            news = self.server.get_news_data()
            items = news['items'][:3]
            items_text = ". ".join(items)
            return f"Here are the top headlines, {title}: {items_text}"
        
        # Identity
        if 'who are you' in cmd or 'your name' in cmd:
            if self.server.hud_perception.is_friday:
                return "I'm FRIDAY - Female Replacement Intelligent Digital Assistant Youth. " \
                       "Your AI assistant, boss."
            return f"I am {name} - Just A Rather Very Intelligent System. " \
                   f"Your personal AI assistant, created by Raghava."
        
        # Creator
        if 'who made you' in cmd or 'who created you' in cmd or 'creator' in cmd:
            return f"I was created by Raghava, {title}. A brilliant engineer who envisioned " \
                   "the ultimate digital assistant."
        
        # Capabilities
        if 'what can you do' in cmd or 'capabilities' in cmd or cmd == 'help':
            return f"I can assist with many things, {title}: System monitoring, " \
                   "weather updates, news by category (try 'economics news' or 'politics news'), " \
                   "reminders, smart notes, alarms, opening applications, web searches, " \
                   "volume control, and intelligent conversation. Voice to voice mode is active. " \
                   "You can also interact with the globe to get location-specific news."
        
        # STORY - Check BEFORE jokes (so "horror story" doesn't match "joke")
        if 'story' in cmd and 'joke' not in cmd:
            genre = "adventure"
            if 'horror' in cmd or 'scary' in cmd or 'creepy' in cmd:
                genre = "horror"
            elif 'funny' in cmd or 'comedy' in cmd:
                genre = "comedy"
            elif 'romance' in cmd or 'love' in cmd:
                genre = "romance"
            elif 'bedtime' in cmd or 'sleep' in cmd:
                genre = "bedtime"
            elif 'mystery' in cmd or 'detective' in cmd:
                genre = "mystery"
            elif 'sci-fi' in cmd or 'science fiction' in cmd or 'space' in cmd:
                genre = "sci-fi"
            
            # Play ambient sound for horror stories
            if genre == 'horror' and self.server.entertainment and hasattr(self.server.entertainment, 'sound_library'):
                try:
                    self.server.entertainment.sound_library.play('suspense')
                except:
                    pass
            
            if self.server.knowledge and hasattr(self.server.knowledge, 'answer_question'):
                try:
                    prompts = {
                        'horror': """Tell a short, genuinely creepy horror story (3-4 paragraphs).
                            Build suspense slowly, use vivid atmospheric descriptions.
                            Include a twist ending. Make it unsettling but not too graphic.
                            Just tell the story, no intro.""",
                        'comedy': """Tell a short funny story (2-3 paragraphs).
                            Include humor, witty dialogue, and a hilarious punchline.
                            Make it genuinely laugh-out-loud funny.
                            Just tell the story, no intro.""",
                        'romance': """Tell a short, heartwarming romance story (2-3 paragraphs).
                            Make it sweet and touching with vivid emotions.
                            Just tell the story, no intro.""",
                        'mystery': """Tell a short mystery story (3-4 paragraphs).
                            Include clues, suspense, and a satisfying reveal.
                            Just tell the story, no intro.""",
                        'sci-fi': """Tell a short science fiction story (2-3 paragraphs).
                            Include futuristic elements, interesting technology.
                            Just tell the story, no intro.""",
                        'bedtime': """Tell a short, gentle bedtime story (2 paragraphs).
                            Make it calming and peaceful with a happy ending.
                            Just tell the story, no intro.""",
                        'adventure': """Tell a short adventure story (2-3 paragraphs).
                            Include action, excitement, and a triumphant ending.
                            Just tell the story, no intro."""
                    }
                    prompt = prompts.get(genre, prompts['adventure'])
                    story = self.server.knowledge.answer_question(prompt)
                    if story and len(story) > 50:
                        return story
                except Exception as e:
                    print(f"[WebSocket] Story generation error: {e}")
            
            # Fallback stories by genre
            fallback_stories = {
                'horror': "The old house stood silent in the moonlight. Sarah pushed open the door, her flashlight cutting through the darkness. 'Hello?' she called. No answer. But as she turned to leave, she felt cold breath on her neck. And in the mirror across the room, she saw that nothing was standing behind her...",
                'comedy': "Dave tried to impress his date by ordering in French at the Italian restaurant. The waiter, being a good sport, brought him exactly what he ordered: a taxi, three umbrellas, and his mother's phone number. His date still talks about it. They've been married 20 years.",
                'romance': "They met at the coffee shop every morning for a year, never speaking, just exchanging smiles. One day, she found a note on her usual table: 'I've memorized your coffee order. Can I finally learn your name?' She looked up. He was already smiling.",
                'adventure': "The map led to a cave no explorer had entered in centuries. Inside, golden artifacts gleamed in the torchlight. The adventure had only just begun..."
            }
            return fallback_stories.get(genre, fallback_stories['adventure'])
        
        # Jokes - use Gemini AI for unique jokes
        if 'joke' in cmd:
            if self.server.knowledge and hasattr(self.server.knowledge, 'answer_question'):
                try:
                    prompt = """Tell me ONE funny joke. Requirements:
                    - Be creative and original
                    - Can be tech humor, wordplay, or observational comedy
                    - Keep it short (1-3 sentences max)
                    - Just the joke, no intro like "here's a joke"
                    - Make it actually funny, not cringe"""
                    joke = self.server.knowledge.answer_question(prompt)
                    if joke and len(joke) > 10:
                        return joke
                except Exception as e:
                    print(f"[WebSocket] Joke generation error: {e}")
            # Fallback
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "A SQL query walks into a bar and asks: Can I join you?",
                "Why did the developer go broke? Because he used up all his cache."
            ]
            return random.choice(jokes)
        
        # Thank you - no 'sir' every time
        if 'thank' in cmd:
            responses = [
                "You're welcome!",
                "Anytime.",
                "Happy to help.",
                "My pleasure."
            ]
            return random.choice(responses)
        
        # PLAY MUSIC / SPOTIFY / YOUTUBE
        if 'play music' in cmd or 'play song' in cmd or 'spotify' in cmd or 'youtube' in cmd:
            # If YouTube is specifically mentioned
            if 'youtube' in cmd:
                # Extract query: play [query] on youtube
                query_match = re.search(r'(?:play|find|search)\s+(.+?)(?:\s+on|\s+in)?\s*youtube', cmd, re.I)
                # Or: youtube play [query]
                if not query_match:
                    query_match = re.search(r'youtube\s+(?:to\s+)?(?:play|find|search)\s+(.+)', cmd, re.I)
                
                query = query_match.group(1).strip() if query_match else cmd.replace('youtube', '').replace('play', '').strip()
                
                if not query:
                    webbrowser.open("https://youtube.com")
                    return f"Opening YouTube{maybe_title(title)}."
                
                if hasattr(self.server, 'youtube') and hasattr(self.server.youtube, 'search_and_play'):
                    self.server.youtube.search_and_play(query)
                else:
                    from core.youtube_downloader import YouTubeDownloader
                    yt = YouTubeDownloader()
                    yt.search_and_play(query)
                return f"Playing your request on YouTube{maybe_title(title)}."
            
            # Default to Spotify
            try:
                os.startfile('spotify:')
                return f"Opening Spotify for you{maybe_title(title)}."
            except:
                return f"Couldn't open Spotify. Make sure it's installed{maybe_title(title)}."
        
        # Volume - actually control hardware
        if 'volume' in cmd:
            if 'up' in cmd or 'increase' in cmd:
                if self.server.system_control:
                    self.server.system_control.volume_up()
                return f"Volume increased{maybe_title(title)}."
            elif 'down' in cmd or 'decrease' in cmd:
                if self.server.system_control:
                    self.server.system_control.volume_down()
                return f"Volume decreased{maybe_title(title)}."
            elif 'mute' in cmd:
                if self.server.system_control:
                    self.server.system_control.mute_volume()
                return f"Audio muted{maybe_title(title)}."
        
        # SCREEN CONTROL - click, scroll, type, move mouse
        if self.server.screen_control:
            # Click commands
            if 'click' in cmd:
                result = self.server.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Clicked{maybe_title(title)}."
            
            # Scroll commands
            if 'scroll' in cmd:
                result = self.server.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Scrolling{maybe_title(title)}."
            
            # Type text commands
            if 'type ' in cmd or 'write ' in cmd:
                result = self.server.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Typing text{maybe_title(title)}."
            
            # Move mouse
            if 'move mouse' in cmd or 'move cursor' in cmd:
                result = self.server.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Moving cursor{maybe_title(title)}."
            
            # Press key commands
            if 'press ' in cmd and any(k in cmd for k in ['enter', 'escape', 'tab', 'delete', 'backspace', 'space']):
                result = self.server.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Key pressed{maybe_title(title)}."
        
        # WHATSAPP - COORD-FIX: Only fire direct dispatch for commands NOT handled by HANDLER_MAP.
        # The HANDLER_MAP 'send_message' handler already covers "whatsapp" and "send message".
        # This block is now a FALLBACK for commands like "open whatsapp" and "read messages"
        # that aren't covered by the handler.
        if self.server.whatsapp_handler:
            # "open whatsapp" — not in HANDLER_MAP, keep as direct dispatch
            if 'open whatsapp' in cmd:
                result = self.server.whatsapp_handler.open_whatsapp()
                return result if isinstance(result, str) else f"Opening WhatsApp, {title}."
            # "read messages" — not in HANDLER_MAP, keep as direct dispatch
            elif 'read' in cmd and ('message' in cmd or 'whatsapp' in cmd):
                result = self.server.whatsapp_handler.read_messages()
                return result if isinstance(result, str) else f"Opening WhatsApp to view messages, {title}."
        
        # CALENDAR - events, schedule, meetings
        if self.server.calendar:
            # Today's events
            if 'calendar' in cmd or 'event' in cmd or 'schedule' in cmd or 'meeting' in cmd:
                if "today" in cmd or "what's on" in cmd:
                    events = self.server.calendar.get_today_events()
                    if events:
                        event_list = ", ".join([f"{e.summary} at {e.start.strftime('%I:%M %p')}" for e in events[:5]])
                        return f"Today's events, {title}: {event_list}."
                    return f"No events scheduled for today, {title}."
                elif "upcoming" in cmd or "next" in cmd:
                    events = self.server.calendar.get_upcoming_events(5)
                    if events:
                        event_list = ", ".join([f"{e.summary}" for e in events[:5]])
                        return f"Upcoming events, {title}: {event_list}."
                    return f"No upcoming events, {title}."
                elif "create" in cmd or "add" in cmd or "schedule" in cmd:
                    # Quick add: schedule meeting with John tomorrow at 3pm
                    match = re.search(r'(?:create|add|schedule)\s+(?:a\s+)?(?:event|meeting|appointment)?\s*(.+)', cmd, re.I)
                    if match:
                        event_text = match.group(1).strip()
                        result = self.server.calendar.quick_add(event_text)
                        if result:
                            return f"Event created, {title}."
                        return f"Couldn't create event. Please try with more details, {title}."
                return f"Opening calendar, {title}. What would you like to do?"
        
        # EMAIL - read emails, summarize emails
        if self.server.email_handler_obj:
            if 'email' in cmd or 'mail' in cmd or 'gmail' in cmd:
                if 'summarize' in cmd or 'summary' in cmd:
                    self.server.email_handler_obj.summarize_emails()
                    return f"Summarizing your emails, {title}."
                elif 'unread' in cmd or 'read' in cmd or 'check' in cmd:
                    self.server.email_handler_obj.get_unread_emails()
                    return f"Checking your emails, {title}."
                else:
                    self.server.email_handler_obj.get_unread_emails()
                    return f"Checking your inbox, {title}."
        
        # YOUTUBE - download video, download audio
        if self.server.youtube_downloader:
            if 'youtube' in cmd or 'download video' in cmd or 'download audio' in cmd:
                # Extract URL from command
                url = self.server.youtube_downloader.extract_url_from_command(cmd)
                
                if url:
                    if 'audio' in cmd or 'mp3' in cmd or 'music' in cmd:
                        self.server.youtube_downloader.download_audio(url)
                        return f"Downloading audio from YouTube, {title}."
                    else:
                        self.server.youtube_downloader.download_video(url)
                        return f"Downloading video from YouTube, {title}."
                elif 'downloads' in cmd or 'folder' in cmd:
                    self.server.youtube_downloader.open_downloads_folder()
                    return f"Opening YouTube downloads folder, {title}."
                else:
                    return f"Please provide a YouTube URL for me to download, {title}."
        
        # HABITS - create, list, complete habits
        if self.server.habit_tracker:
            if 'habit' in cmd:
                if 'create' in cmd or 'add' in cmd or 'new' in cmd:
                    # Parse: create habit [description] every [interval]
                    match = re.search(r'(?:create|add|new)\s+habit\s+(.+?)(?:\s+every\s+|\s+daily|\s+hourly|\s+morning|\s+evening|$)', cmd, re.I)
                    if match:
                        desc = match.group(1).strip()
                        interval = cmd  # Pass full command for interval parsing
                        self.server.habit_tracker.create_habit(desc, interval)
                        return f"Habit created, {title}."
                elif 'list' in cmd or 'show' in cmd or 'my habits' in cmd:
                    self.server.habit_tracker.list_habits()
                    return f"Listing your habits, {title}."
                elif 'check' in cmd or 'remind' in cmd:
                    reminders = self.server.habit_tracker.check_reminders()
                    if reminders:
                        return f"You have {len(reminders)} habit reminders, {title}."
                    return f"No habit reminders due, {title}."
        
        # TASKS - add, list, complete tasks
        if self.server.task_manager_obj:
            if 'task' in cmd or 'to do' in cmd or 'todo' in cmd:
                if 'add' in cmd or 'create' in cmd or 'new' in cmd:
                    match = re.search(r'(?:add|create|new)\s+(?:a\s+)?task\s+(.+)', cmd, re.I)
                    if match:
                        desc = match.group(1).strip()
                        self.server.task_manager_obj.add_task(desc)
                        return f"Task added, {title}."
                elif 'list' in cmd or 'show' in cmd or 'my tasks' in cmd:
                    self.server.task_manager_obj.list_tasks()
                    return f"Listing your tasks, {title}."
                elif 'complete' in cmd or 'done' in cmd:
                    match = re.search(r'(?:complete|done)\s+task\s+(\d+)', cmd, re.I)
                    if match:
                        index = int(match.group(1))
                        self.server.task_manager_obj.complete_task_by_index(index)
                        return f"Task marked complete, {title}."
        
        # WELLNESS - check wellness, session duration
        if self.server.wellness_monitor:
            if 'wellness' in cmd or 'health' in cmd or 'break' in cmd:
                if 'summary' in cmd or 'status' in cmd:
                    summary = self.server.wellness_monitor.get_wellness_summary()
                    return summary
                elif 'check' in cmd:
                    reminder = self.server.wellness_monitor.check_wellness()
                    if reminder:
                        return reminder
                    return f"You're doing well, {title}."
                elif 'reset' in cmd or 'took a break' in cmd:
                    self.server.wellness_monitor.reset_session()
                    return f"Session reset. Good on you for taking a break, {title}."
        
        # CHAT HISTORY - search conversations, recent chat
        if self.server.chat_history:
            if 'history' in cmd or 'conversation' in cmd or 'what did' in cmd:
                if 'search' in cmd:
                    match = re.search(r'search\s+(?:for\s+)?(.+)', cmd, re.I)
                    if match:
                        query = match.group(1).strip()
                        results = self.server.chat_history.search(query)
                        if results:
                            return f"Found {len(results)} conversations matching '{query}', {title}."
                        return f"No conversations found matching '{query}', {title}."
                elif 'recent' in cmd or 'last' in cmd:
                    messages = self.server.chat_history.get_recent(5)
                    if messages:
                        return f"Here are your last {len(messages)} messages, {title}."
                    return f"No chat history yet, {title}."
                elif 'clear' in cmd or 'delete' in cmd:
                    self.server.chat_history.clear_history()
                    return f"Chat history cleared, {title}."
        
        if ' and search' in cmd and 'open ' in cmd:
            match = re.search(r'open\s+(\w+)\s+and\s+(?:search|look)\s+(?:for\s+)?(.+)', cmd)
            if match:
                browser = match.group(1).lower()
                query = match.group(2).strip()
                
                # Browser command mappings
                browser_cmds = {
                    'edge': 'msedge',
                    'microsoft': 'msedge',
                    'chrome': 'chrome',
                    'brave': 'brave',
                    'firefox': 'firefox',
                }
                
                browser_cmd = browser_cmds.get(browser, 'msedge')
                encoded_query = query.replace(' ', '+')
                
                try:
                    # Open specific browser with search URL
                    search_url = f'https://www.google.com/search?q={encoded_query}'
                    if browser_cmd == 'msedge':
                        subprocess.Popen(['msedge', search_url], shell=True)
                    elif browser_cmd == 'brave':
                        subprocess.Popen(['brave', search_url], shell=True)
                    elif browser_cmd == 'chrome':
                        subprocess.Popen(['chrome', search_url], shell=True)
                    elif browser_cmd == 'firefox':
                        subprocess.Popen(['firefox', search_url], shell=True)
                    else:
                        webbrowser.open(search_url)
                    return f"Opening {browser.capitalize()} and searching for '{query}', {title}."
                except Exception as e:
                    print(f"[WebSocket] Browser search error: {e}")
                    webbrowser.open(f'https://www.google.com/search?q={encoded_query}')
                    return f"Searching for '{query}', {title}."
                    
        # APP SWITCHING — switch to, switch with, go to, alt-tab
        switch_prefixes = ('switch to ', 'switch with ', 'switch tab to ', 'go to ', 'switch tab ')
        if any(cmd.startswith(p) for p in switch_prefixes):
            target = cmd
            for p in switch_prefixes:
                target = target.replace(p, '', 1)
            target = target.strip()
            # Skip assistant personality switches (handled elsewhere)
            if target in ('friday', 'jarvis'):
                pass
            else:
                try:
                    # Try to find the window by title and activate it
                    result = subprocess.run(
                        ['powershell', '-command',
                         f'(Get-Process | Where-Object {{$_.MainWindowTitle -match "{target}"}} | Select-Object -First 1).MainWindowTitle'],
                        capture_output=True, text=True, timeout=3
                    )
                    window_title = result.stdout.strip()
                    if window_title:
                        # Use PowerShell to bring window to front
                        subprocess.run(
                            ['powershell', '-command', f'''
                            $window = Get-Process | Where-Object {{$_.MainWindowTitle -match "{target}"}} | Select-Object -First 1
                            if ($window) {{
                                $hwnd = $window.MainWindowHandle
                                Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class Win32 {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); }}'
                                [Win32]::ShowWindow($hwnd, 9)
                                [Win32]::SetForegroundWindow($hwnd)
                            }}
                            '''],
                            capture_output=True, timeout=3
                        )
                        self.server.state_manager.active_app = target.lower()
                        self.server.state_manager._active_app_time = time.time()
                        return f"Switching to {target}, {title}."
                    else:
                        return f"I can't find {target} running. Would you like me to open it?"
                except Exception as e:
                    print(f"[WebSocket] App switch error: {e}")
                    return f"Couldn't switch to {target}, {title}."
        
        if cmd in ('go back', 'alt tab', 'switch window', 'next window', 'previous window'):
            try:
                import pyautogui
                pyautogui.hotkey('alt', 'tab')
                return f"Switched to the previous window, {title}."
            except Exception as e:
                return f"Couldn't switch windows, {title}."
        
        # Open apps - ACTUALLY open them with fuzzy matching
        if cmd.startswith('open '):
            app = cmd.replace('open ', '').strip()
            app_lower = app.lower()
            
            # Fuzzy matching for common typos
            typo_corrections = {
                'chatpgt': 'chatgpt',
                'chatgtp': 'chatgpt',
                'cahtgpt': 'chatgpt',
                'gpt': 'chatgpt',
                'whatspp': 'whatsapp',
                'whatapp': 'whatsapp',
                'watsapp': 'whatsapp',
                'spotfy': 'spotify',
                'spotofy': 'spotify',
                'perplexty': 'perplexity',
                'perplxity': 'perplexity',
                'telgram': 'telegram',
                'discod': 'discord',
                'edg': 'edge',
                'brav': 'brave',
            }
            app_lower = typo_corrections.get(app_lower, app_lower)
            
            app_paths = {
                # Browsers
                'edge': 'msedge',
                'microsoft edge': 'msedge',
                'brave': 'brave',
                'chrome': 'chrome',
                'firefox': 'firefox',
                # Messaging
                'whatsapp': 'whatsapp:',
                'telegram': 'telegram:',
                'discord': 'discord:',
                # System
                'notepad': 'notepad',
                'calculator': 'calc',
                'file explorer': 'explorer',
                'explorer': 'explorer',
                'settings': 'ms-settings:',
                'cmd': 'cmd',
                'terminal': 'wt',
                'powershell': 'powershell',
                # Development
                'vscode': 'code',
                'vs code': 'code',
                'visual studio code': 'code',
                # Media
                'spotify': 'spotify:',
                # AI Apps - use app_finder or web fallback
                'perplexity': 'perplexity',
                'chatgpt': 'chatgpt',
            }
            
            try:
                # Try using JARVIS app_finder first (most reliable)
                if self.server.jarvis and hasattr(self.server.jarvis, 'app_finder'):
                    try:
                        result = self.server.jarvis.app_finder.open_app(app_lower)
                        if result:
                            return f"Opening {app}, {title}."
                    except Exception as e:
                        print(f"[WebSocket] app_finder error: {e}")
                
                if app_lower in app_paths:
                    target = app_paths[app_lower]
                    
                    # Handle special cases
                    if app_lower == 'perplexity':
                        # Try Start Menu shortcut first
                        shortcut_path = rf'C:\Users\{os.getenv("USERNAME")}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Perplexity.lnk'
                        if os.path.exists(shortcut_path):
                            os.startfile(shortcut_path)
                        else:
                            # Fallback to web
                            webbrowser.open('https://perplexity.ai')
                        return f"Opening Perplexity, {title}."
                    
                    elif app_lower == 'chatgpt':
                        # Try PWA/App first, then web
                        shortcut_path = rf'C:\Users\{os.getenv("USERNAME")}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\ChatGPT.lnk'
                        if os.path.exists(shortcut_path):
                            os.startfile(shortcut_path)
                        else:
                            webbrowser.open('https://chat.openai.com')
                        return f"Opening ChatGPT, {title}."
                    
                    elif target.startswith('http') or target.endswith(':'):
                        os.startfile(target)
                    else:
                        subprocess.Popen(target, shell=True)
                else:
                    # Try to open by name directly
                    os.startfile(app)
                return f"Opening {app}, {title}."
            except Exception as e:
                print(f"[WebSocket] Open app error: {e}")
                # Web fallback for unknown apps
                webbrowser.open(f'https://www.google.com/search?q={app}+download')
                return f"{title}, I couldn't find {app} installed. Let me search for it online."
        
        # Search
        if 'search' in cmd:
            query = cmd.replace('search for', '').replace('search', '').strip()
            return f"Searching for '{query}', {title}."
        
        # Features status
        if 'features' in cmd or 'status' in cmd:
            status = self.server.get_feature_status()
            features = []
            if status['jarvis_full']:
                features.append("full JARVIS integration")
            if status['gesture_available']:
                features.append("gesture control")
            if status['face_available']:
                features.append("face recognition")
            if status['emotion_available']:
                features.append("emotion detection")
            
            if features:
                return f"Available features, {title}: {', '.join(features)}. " \
                       "All can be enabled from the interface."
            return f"Core features active, {title}. Advanced modules loading."
        
        # ══════════════════════════════════════════════════════════════════
        # NEW FEATURE COMMANDS
        # ══════════════════════════════════════════════════════════════════
        
        # SCREENSHOT
        if 'screenshot' in cmd or 'screen shot' in cmd or 'capture screen' in cmd:
            if self.server.screenshot_handler:
                path = self.server.screenshot_handler.take_fullscreen()
                if path:
                    await self.server._send_to(websocket, json.dumps({
                        'type': 'screenshot_taken',
                        'path': str(path),
                        'filename': path.name
                    }))
                    return f"Screenshot saved to {path.name}, {title}."
                return f"Failed to take screenshot, {title}."
            return f"Screenshot feature not available, {title}."
        
        # OCR / READ SCREEN
        if 'read screen' in cmd or 'read text' in cmd or 'extract text' in cmd or 'ocr' in cmd:
            if self.server.ocr_handler:
                text = self.server.ocr_handler.read_screen()
                if text:
                    # Limit for speech
                    short_text = text[:200] + "..." if len(text) > 200 else text
                    await self.server._send_to(websocket, json.dumps({
                        'type': 'ocr_result',
                        'text': text
                    }))
                    return f"I found this text: {short_text}"
                return f"No readable text found on screen, {title}."
            return f"OCR feature not available. Install pytesseract and Tesseract-OCR, {title}."
        
        # READ CLIPBOARD
        if 'read clipboard' in cmd:
            if self.server.ocr_handler:
                text = self.server.ocr_handler.read_clipboard_image()
                if text:
                    return f"Clipboard text: {text[:200]}"
                return f"No text in clipboard image, {title}."
            return f"OCR not available, {title}."
        
        # DICTIONARY
        if 'define ' in cmd or 'meaning of ' in cmd or 'definition of ' in cmd:
            word = cmd.replace('define ', '').replace('meaning of ', '').replace('definition of ', '').strip()
            if self.server.dictionary_handler and word:
                word_lower = word.lower()
                # Get definition directly from dictionary
                if word_lower in self.server.dictionary_handler.dictionary:
                    definition = self.server.dictionary_handler.dictionary[word_lower]
                    return f"{word.capitalize()}: {definition}"
                # Try online lookup
                online_def = self.server.dictionary_handler._lookup_online(word_lower)
                if online_def:
                    return f"{word.capitalize()}: {online_def}"
                return f"I couldn't find a definition for '{word}', {title}."
            return f"Dictionary not available, {title}."
        
        # SYNONYMS
        if 'synonym' in cmd:
            word = cmd.replace('synonym for ', '').replace('synonym of ', '').replace('synonyms of ', '').replace('synonym', '').strip()
            if self.server.dictionary_handler and word:
                import requests
                try:
                    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            meanings = data[0].get("meanings", [])
                            all_synonyms = []
                            for meaning in meanings:
                                synonyms = meaning.get("synonyms", [])
                                all_synonyms.extend(synonyms[:3])
                            if all_synonyms:
                                synonym_list = ", ".join(all_synonyms[:5])
                                return f"Synonyms for {word}: {synonym_list}"
                except:
                    pass
                return f"No synonyms found for '{word}', {title}."
            return f"Dictionary not available, {title}."
        
        # FACE REGISTRATION
        if 'register my face' in cmd or 'register face' in cmd or 'register owner' in cmd:
            if self.server.face_recognition:
                result = self.server.face_recognition.register_owner()
                if result:
                    self.server.current_user = self.server.face_recognition.current_user
                    await self.server._send_to(websocket, json.dumps({
                        'type': 'face_registered',
                        'success': True,
                        'user': 'Raghava'
                    }))
                    return f"Face registered successfully, {title}. You are now the verified owner."
                return f"Face registration failed, {title}. Please try again with better lighting."
            return f"Face recognition is not available, {title}. Install face_recognition and dlib."
        
        # VERIFY FACE
        if 'verify me' in cmd or 'authenticate' in cmd or 'who am i' in cmd:
            if self.server.face_recognition:
                result = self.server.face_recognition.authenticate()
                if result:
                    user = self.server.face_recognition.current_user
                    return f"Welcome, {user.name}. Access level: {user.user_type.value}."
                return f"Face not recognized, {title}."
            return f"Face recognition not available, {title}."
        
        # GESTURE CONTROL
        if 'enable gesture' in cmd or 'start gesture' in cmd or 'gesture on' in cmd:
            if self.server.gesture_controller:
                try:
                    self.server.gesture_controller.enable_tracking()
                    self.server.gesture_enabled = True
                    await self.server._send_to(websocket, json.dumps(self.server.get_feature_status()))
                    return f"Gesture control enabled, {title}. Use hand gestures to control."
                except Exception as e:
                    return f"Failed to start gesture control: {e}"
            return f"Gesture control not available. Install mediapipe, {title}."
        
        if 'disable gesture' in cmd or 'stop gesture' in cmd or 'gesture off' in cmd:
            if self.server.gesture_controller:
                self.server.gesture_controller.disable_tracking()
                self.server.gesture_enabled = False
                return f"Gesture control disabled, {title}."
            return f"Gesture control not active, {title}."
        
        # EMOTION DETECTION
        if 'enable emotion' in cmd or 'mood detection' in cmd:
            self.server.emotion_enabled = True
            await self.server._send_to(websocket, json.dumps(self.server.get_feature_status()))
            return f"Emotion detection enabled, {title}. I'll adapt my responses to your mood."
        
        if 'disable emotion' in cmd:
            self.server.emotion_enabled = False
            return f"Emotion detection disabled, {title}."
        
        # ENTERTAINMENT - POEM
        if 'recite a poem' in cmd or 'poem' in cmd:
            if self.server.entertainment:
                result = self.server.entertainment.recite_poem()
                if isinstance(result, str) and result:
                    return result
            if self.server.knowledge and hasattr(self.server.knowledge, 'answer_question'):
                try:
                    prompt = "Write a short 4-6 line poem. Make it thoughtful and meaningful. Just the poem, no intro."
                    poem = self.server.knowledge.answer_question(prompt)
                    if poem and len(poem) > 20:
                        return poem
                except Exception as e:
                    print(f"[WebSocket] Poem generation error: {e}")
            return f"Roses are red, violets are blue, I'm an AI here to help you."
        
        # ENTERTAINMENT - RIDDLE
        if 'riddle' in cmd:
            if self.server.entertainment:
                result = self.server.entertainment.tell_riddle()
                return result if isinstance(result, str) and result else f"Here's a riddle, {title}: What has keys but no locks? A keyboard!"
            return f"Here's a riddle, {title}: What has keys but no locks, space but no room? A keyboard!"
        
        # SMART NOTES
        if 'create note' in cmd or 'new note' in cmd or 'add note' in cmd:
            content = cmd.replace('create note', '').replace('new note', '').replace('add note', '').strip()
            if self.server.smart_notes and content:
                result = self.server.smart_notes.add_note(content=content)
                return result if isinstance(result, str) else f"Note created, {title}."
            return f"Please specify what to note, {title}. Say 'create note about [topic]'."
        
        if 'list notes' in cmd or 'show notes' in cmd or 'my notes' in cmd:
            if self.server.smart_notes:
                notes = self.server.smart_notes.read_notes()
                return notes if notes else f"You have no notes yet, {title}."
            return f"Notes feature not available, {title}."
        
        # ALARMS
        if 'set alarm' in cmd:
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', cmd)
            if self.server.alarm_system and time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                period = time_match.group(3)
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                self.server.alarm_system.set_alarm(hour, minute)
                return f"Alarm set for {hour:02d}:{minute:02d}, {title}."
            return f"Please specify a time. Say 'set alarm for 7:30 am', {title}."
        
        if 'list alarm' in cmd or 'show alarm' in cmd or 'my alarm' in cmd:
            if self.server.alarm_system:
                alarms = self.server.alarm_system.list_alarms()
                return alarms if alarms else f"No alarms set, {title}."
            return f"Alarm system not available, {title}."
        
        # VOLUME CONTROL (with system control)
        if 'volume' in cmd:
            if self.server.system_control:
                if 'up' in cmd or 'increase' in cmd:
                    self.server.system_control.volume_up()
                    return f"Volume increased, {title}."
                elif 'down' in cmd or 'decrease' in cmd:
                    self.server.system_control.volume_down()
                    return f"Volume decreased, {title}."
                elif 'mute' in cmd:
                    self.server.system_control.mute_volume()
                    return f"Audio muted, {title}."
                
                # Check for specific percentage
                match = re.search(r'(\d+)\s*%?', cmd)
                if match:
                    level = int(match.group(1))
                    self.server.system_control.set_volume(level)
                    return f"Volume set to {level}%, {title}."
            return f"Adjusting volume, {title}."
        
        # BRIGHTNESS CONTROL
        if 'brightness' in cmd:
            if self.server.system_control:
                if 'up' in cmd or 'increase' in cmd:
                    self.server.system_control.brightness_up()
                    return f"Brightness increased, {title}."
                elif 'down' in cmd or 'decrease' in cmd:
                    self.server.system_control.brightness_down()
                    return f"Brightness decreased, {title}."
                
                # Check for specific percentage
                match = re.search(r'(\d+)\s*%?', cmd)
                if match:
                    level = int(match.group(1))
                    self.server.system_control.set_brightness(level)
                    return f"Brightness set to {level}%, {title}."
            return f"Adjusting brightness, {title}."
        
        # WEB SEARCH
        if 'search' in cmd or 'google' in cmd:
            query = cmd.replace('search for', '').replace('search', '').replace('google', '').strip()
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching for '{query}'."
            return "What would you like me to search for?"
        
        # Default fallback - USE GEMINI AI for intelligent responses
        if self.server.knowledge and hasattr(self.server.knowledge, 'answer_question'):
            try:
                response = self.server.knowledge.answer_question(command)
                _err = ['trouble connecting', 'knowledge base', 'currently offline', 'Set GROQ_API_KEY']
                if response and not any(ep in (response or '') for ep in _err):
                    return response
            except Exception as e:
                print(f"[WebSocket] Knowledge error: {e}")
        
        # Gemini Flash fallback for general conversation
        try:
            import google.genai as _genai
            _api_key = getattr(self.server, '_gemini_key', None)
            if not _api_key:
                _api_key = os.getenv('GEMINI_API_KEY', '')
                self.server._gemini_key = _api_key
            if _api_key:
                _client = _genai.Client(api_key=_api_key)
                _resp = _client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=f"You are JARVIS, a witty AI assistant. Keep replies to 1-2 sentences. Address user as 'sir'. Never break character. User says: {command}"
                )
                if _resp and _resp.text:
                    return _resp.text.strip()
        except Exception as e:
            print(f"[WebSocket] Gemini fallback error: {e}")
        
        # Final fallback
        return "I'm not sure about that. Try asking differently or be more specific."
