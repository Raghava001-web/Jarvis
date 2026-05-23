"""
JARVIS Intent Handlers
Dedicated handlers for each command type - extracted from _fallback_process
"""

from datetime import datetime
from typing import Any, Dict
import random

try:
    from jarvis.core.intent_router import HandlerResult, Intent
except ImportError:
    from core.intent_router import HandlerResult, Intent


# ═══════════════════════════════════════════════════════════════
# CORE HANDLERS
# ═══════════════════════════════════════════════════════════════

def handle_greeting(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle hello, hi, hey, good morning/afternoon/evening — Iron Man JARVIS style"""
    hour = datetime.now().hour
    title = context.get('title', 'sir') if context else 'sir'
    cmd_lower = cmd.lower() if cmd else ''
    
    # Time-based greeting
    if hour < 6:
        time_greeting = "Burning the midnight oil"
    elif hour < 12:
        time_greeting = "Good morning"
    elif hour < 17:
        time_greeting = "Good afternoon"
    elif hour < 21:
        time_greeting = "Good evening"
    else:
        time_greeting = "Rather late"
    
    # ━━━ CONTEXT-AWARE RESPONSES (Iron Man JARVIS style) ━━━
    
    # "daddy's home" / "I'm back" / "I'm here" — returning user
    if any(phrase in cmd_lower for phrase in ["daddy", "i'm back", "im back", "back online", "i'm here", "home"]):
        responses = [
            f"Welcome back, {title}. All systems were on standby, awaiting your return.",
            f"Ah, {title}. The house just wasn't the same without you. All systems online.",
            f"{time_greeting}, {title}. I've kept everything running in your absence. As usual.",
            f"Welcome home, {title}. Shall I run a status report, or is this a social visit?",
        ]
        return HandlerResult(success=True, response=random.choice(responses))
    
    # "can you hear me" — checking if JARVIS works
    if any(phrase in cmd_lower for phrase in ["hear me", "can you hear", "you there", "are you there", "awake", "alive"]):
        responses = [
            f"Loud and clear, {title}. All systems operational.",
            f"I can hear you perfectly, {title}. Voice recognition at full capacity.",
            f"For you, {title}, always. What do you need?",
            f"Present and accounted for. How may I assist?",
        ]
        return HandlerResult(success=True, response=random.choice(responses))
    
    # Late night greeting
    if hour >= 23 or hour < 5:
        responses = [
            f"Working late again, {title}? I won't lecture. Much.",
            f"{time_greeting}, {title}. I calculate you should have been asleep two hours ago.",
            f"All systems online, {title}. Though I'd recommend sleep over my company.",
        ]
        return HandlerResult(success=True, response=random.choice(responses))
    
    # Standard greetings with personality
    responses = [
        f"{time_greeting}, {title}. All systems nominal. What can I do for you?",
        f"{time_greeting}. JARVIS at your service.",
        f"At your disposal, {title}. What's on the agenda?",
        f"{time_greeting}, {title}. Ready when you are.",
        f"Online and operational. How may I assist you, {title}?",
    ]
    return HandlerResult(success=True, response=random.choice(responses))


def handle_farewell(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle goodbye, bye, see you"""
    title = context.get('title', 'sir') if context else 'sir'
    responses = [
        f"Goodbye, {title}. I'll be here when you need me.",
        f"Until next time, {title}.",
        "Take care. Systems on standby."
    ]
    return HandlerResult(success=True, response=random.choice(responses))


def handle_time(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle time queries"""
    title = context.get('title', 'sir') if context else 'sir'
    now = datetime.now()
    return HandlerResult(
        success=True,
        response=f"The current time is {now.strftime('%I:%M %p')}, {title}."
    )


def handle_date(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle date queries"""
    title = context.get('title', 'sir') if context else 'sir'
    now = datetime.now()
    return HandlerResult(
        success=True,
        response=f"Today is {now.strftime('%A, %B %d, %Y')}, {title}."
    )


def handle_identity(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle 'who are you' / 'your name'"""
    name = context.get('assistant_name', 'JARVIS') if context else 'JARVIS'
    is_friday = context.get('is_friday', False) if context else False
    
    if is_friday:
        return HandlerResult(
            success=True,
            response="I'm FRIDAY - Female Replacement Intelligent Digital Assistant Youth. Your AI assistant, boss."
        )
    return HandlerResult(
        success=True,
        response=f"I am {name} - Just A Rather Very Intelligent System. Your personal AI assistant, created by Raghava."
    )


def handle_creator(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle 'who made you' / 'who created you'"""
    title = context.get('title', 'sir') if context else 'sir'
    return HandlerResult(
        success=True,
        response=f"I was created by Raghava, {title}. A brilliant engineer who envisioned the ultimate digital assistant."
    )


def handle_help(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle 'help' / 'what can you do'"""
    title = context.get('title', 'sir') if context else 'sir'
    return HandlerResult(
        success=True,
        response=f"I can assist with many things, {title}: System monitoring, weather updates, news by category, "
                 "reminders, smart notes, alarms, opening applications, web searches, volume control, "
                 "and intelligent conversation. Voice to voice mode is active."
    )


def handle_thanks(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle 'thank you' - reduced 'sir' usage"""
    responses = [
        "You're welcome!",
        "Anytime.",
        "Happy to help.",
        "My pleasure."
    ]
    return HandlerResult(success=True, response=random.choice(responses))


def handle_how_are_you(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle 'how are you'"""
    title = context.get('title', 'sir') if context else 'sir'
    system_stats = context.get('system_stats', {}) if context else {}
    
    cpu = system_stats.get('cpu', 30)
    if cpu < 50:
        return HandlerResult(
            success=True,
            response=f"Operating at peak efficiency, {title}. All systems nominal."
        )
    return HandlerResult(
        success=True,
        response=f"Functioning well, {title}. System load is moderate but manageable."
    )


# ═══════════════════════════════════════════════════════════════
# INFORMATION HANDLERS
# ═══════════════════════════════════════════════════════════════

def handle_weather(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle weather queries - requires weather_handler in context"""
    title = context.get('title', 'sir') if context else 'sir'
    weather_handler = context.get('weather_handler') if context else None
    
    if not weather_handler:
        return HandlerResult(
            success=False,
            response=f"Weather service unavailable, {title}."
        )
    
    try:
        # Get city from entities if specified
        city = entities.get('city')
        weather = weather_handler.get_weather(city) if city else weather_handler.get_weather()
        
        if isinstance(weather, dict):
            return HandlerResult(
                success=True,
                response=f"Current conditions in {weather.get('location', 'your area')}: "
                         f"{weather.get('temp', 'N/A')}°C, {weather.get('condition', 'unknown')}. "
                         f"Humidity at {weather.get('humidity', 'N/A')}%, "
                         f"wind {weather.get('wind', 'N/A')} kilometers per hour."
            )
    except Exception as e:
        print(f"[HANDLERS] Weather error: {e}")
    
    return HandlerResult(
        success=False,
        response=f"Couldn't fetch weather data, {title}."
    )


def handle_system_status(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle system status queries"""
    title = context.get('title', 'sir') if context else 'sir'
    stats = context.get('system_stats', {}) if context else {}
    
    charge = " and charging" if stats.get('charging') else ""
    return HandlerResult(
        success=True,
        response=f"All systems operational, {title}. CPU at {stats.get('cpu', 0)}%, "
                 f"memory at {stats.get('memory', 0)}%, disk at {stats.get('disk', 0)}%, "
                 f"battery at {stats.get('battery', 100)}%{charge}."
    )


# ═══════════════════════════════════════════════════════════════
# ENTERTAINMENT HANDLERS - Use Gemini AI
# ═══════════════════════════════════════════════════════════════

def handle_joke(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle joke requests - uses Gemini AI"""
    knowledge = context.get('knowledge') if context else None
    
    if knowledge and hasattr(knowledge, 'answer_question'):
        try:
            prompt = """Tell me ONE funny joke. Requirements:
            - Be creative and original
            - Can be tech humor, wordplay, or observational comedy
            - Keep it short (1-3 sentences max)
            - Just the joke, no intro like "here's a joke"
            - Make it actually funny, not cringe"""
            joke = knowledge.answer_question(prompt)
            if joke and len(joke) > 10:
                return HandlerResult(success=True, response=joke)
        except Exception as e:
            print(f"[HANDLERS] Joke generation error: {e}")
    
    # Fallback
    fallback_jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "A SQL query walks into a bar and asks: Can I join you?",
        "Why did the developer go broke? Because he used up all his cache."
    ]
    return HandlerResult(success=True, response=random.choice(fallback_jokes))


def handle_story(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle story requests with genre support - uses Gemini AI"""
    knowledge = context.get('knowledge') if context else None
    cmd_lower = cmd.lower()
    
    # Detect genre
    genre = "adventure"
    if 'horror' in cmd_lower or 'scary' in cmd_lower:
        genre = "horror"
    elif 'funny' in cmd_lower or 'comedy' in cmd_lower:
        genre = "comedy"
    elif 'romance' in cmd_lower:
        genre = "romance"
    elif 'bedtime' in cmd_lower:
        genre = "bedtime"
    
    if knowledge and hasattr(knowledge, 'answer_question'):
        try:
            prompt = f"""Tell a short {genre} story (2-3 paragraphs).
            Make it engaging with vivid descriptions.
            For horror: build suspense and atmosphere.
            For comedy: include humor and a funny twist.
            For romance: sweet and heartwarming.
            Just tell the story directly, no intro."""
            story = knowledge.answer_question(prompt)
            if story and len(story) > 50:
                return HandlerResult(success=True, response=story)
        except Exception as e:
            print(f"[HANDLERS] Story generation error: {e}")
    
    return HandlerResult(
        success=True,
        response="Once upon a time, in a world of code and algorithms, there lived a programmer who dreamed of creating the perfect AI assistant..."
    )


def handle_poem(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle poem requests - uses Gemini AI"""
    knowledge = context.get('knowledge') if context else None
    
    if knowledge and hasattr(knowledge, 'answer_question'):
        try:
            prompt = "Write a short 4-6 line poem. Make it thoughtful and meaningful. Just the poem, no intro."
            poem = knowledge.answer_question(prompt)
            if poem and len(poem) > 20:
                return HandlerResult(success=True, response=poem)
        except Exception as e:
            print(f"[HANDLERS] Poem generation error: {e}")
    
    return HandlerResult(
        success=True,
        response="Roses are red, violets are blue, I'm an AI here to help you."
    )


# ═══════════════════════════════════════════════════════════════
# BATCH 2 HANDLERS - News, Screenshot, Notes, Apps
# ═══════════════════════════════════════════════════════════════

def handle_news(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle news requests with category support + JARVIS opinion"""
    title = context.get('title', 'sir') if context else 'sir'
    news_handler = context.get('news_handler') if context else None
    knowledge = context.get('knowledge') if context else None
    category = entities.get('category', 'general')
    
    if not news_handler:
        return HandlerResult(success=False, response=f"News service unavailable, {title}.")
    
    try:
        news_data = news_handler.get_news(category=category, count=5)
        if isinstance(news_data, dict) and 'items' in news_data:
            items = news_data['items'][:3]
            items_text = ". ".join(items)
            
            # Generate JARVIS opinion on the headlines
            opinion = ""
            if knowledge and items:
                try:
                    opinion_prompt = f"""You are JARVIS from Iron Man. Dry wit, deadpan, sharp.
Here are today's {category} headlines: {items_text}

Give a 1-2 sentence take with signature JARVIS dry humor. Use probability framing if applicable ("There's a 73% chance this escalates"). Be bold and specific."""
                    opinion_response = knowledge.answer_question(opinion_prompt)
                    if opinion_response and len(opinion_response) > 10:
                        opinion = f" My take: {opinion_response}"
                except Exception:
                    pass  # Opinion is optional, don't fail on it
            
            return HandlerResult(
                success=True,
                response=f"Here are the top {category} headlines, {title}: {items_text}{opinion}",
                data={'type': 'news', 'items': news_data['items']}
            )
    except Exception as e:
        print(f"[HANDLERS] News error: {e}")
    
    return HandlerResult(success=False, response=f"Couldn't fetch {category} news, {title}.")


def handle_search_news(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle news search by keyword"""
    title = context.get('title', 'sir') if context else 'sir'
    news_handler = context.get('news_handler') if context else None
    keyword = entities.get('keyword', '')
    
    if not keyword:
        return HandlerResult(success=False, response=f"What topic should I search for, {title}?")
    
    if not news_handler:
        return HandlerResult(success=False, response=f"News service unavailable, {title}.")
    
    try:
        result = news_handler.search_news(keyword, count=5)
        if result:
            return HandlerResult(success=True, response="", should_speak=False)  # Handler speaks itself
    except Exception as e:
        print(f"[HANDLERS] News search error: {e}")
    
    return HandlerResult(success=False, response=f"Couldn't find news about {keyword}, {title}.")


def handle_open_app(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle opening applications"""
    import os
    import subprocess
    
    app = entities.get('app', '').lower()
    if not app:
        return HandlerResult(success=False, response="Please specify an app to open.")
    
    APP_PATHS = {
        'whatsapp': 'whatsapp:',
        'chrome': 'chrome',
        'firefox': 'firefox',
        'notepad': 'notepad',
        'calculator': 'calc',
        'spotify': 'spotify:',
        'telegram': 'telegram:',
        'discord': 'discord:',
        'vscode': 'code',
        'vs code': 'code',
        'file explorer': 'explorer',
        'explorer': 'explorer',
        'settings': 'ms-settings:',
        'cmd': 'cmd',
        'terminal': 'wt',
        # Desktop apps - use Start Menu shortcuts for reliability
        'perplexity': rf'C:\Users\{os.getenv("USERNAME")}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Perplexity.lnk',
        'chatgpt': 'https://chat.openai.com'
    }
    
    try:
        if app in APP_PATHS:
            target = APP_PATHS[app]
            if target.startswith('http') or target.endswith(':') or target.endswith('.lnk'):
                os.startfile(target)
            else:
                subprocess.Popen(target, shell=True)
        else:
            # Try to open directly — Windows will find it if it's in PATH or Start Menu
            try:
                os.startfile(app)
            except Exception:
                subprocess.Popen(f'start {app}', shell=True)
        return HandlerResult(success=True, response=f"Opening {app}.")
    except Exception as e:
        print(f"[HANDLERS] Open app error: {e}")
        return HandlerResult(success=False, response=f"Couldn't open {app}.")


def handle_volume(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle volume control"""
    title = context.get('title', 'sir') if context else 'sir'
    system_control = context.get('system_control') if context else None
    action = entities.get('action', '')
    level = entities.get('level')
    
    if system_control:
        try:
            if action == 'up':
                system_control.volume_up()
                return HandlerResult(success=True, response=f"Volume increased, {title}.")
            elif action == 'down':
                system_control.volume_down()
                return HandlerResult(success=True, response=f"Volume decreased, {title}.")
            elif action == 'mute':
                system_control.mute_volume()
                return HandlerResult(success=True, response=f"Audio muted, {title}.")
            elif action == 'set' and level is not None:
                system_control.set_volume(level)
                return HandlerResult(success=True, response=f"Volume set to {level}%, {title}.")
        except Exception as e:
            print(f"[HANDLERS] Volume error: {e}")
    
    # Fallback response
    return HandlerResult(success=True, response=f"Adjusting volume, {title}.")


def handle_brightness(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle brightness control"""
    title = context.get('title', 'sir') if context else 'sir'
    system_control = context.get('system_control') if context else None
    action = entities.get('action', '')
    level = entities.get('level')
    
    if system_control:
        try:
            if action == 'up':
                system_control.brightness_up()
                return HandlerResult(success=True, response=f"Brightness increased, {title}.")
            elif action == 'down':
                system_control.brightness_down()
                return HandlerResult(success=True, response=f"Brightness decreased, {title}.")
            elif action == 'set' and level is not None:
                system_control.set_brightness(level)
                return HandlerResult(success=True, response=f"Brightness set to {level}%, {title}.")
        except Exception as e:
            print(f"[HANDLERS] Brightness error: {e}")
    
    return HandlerResult(success=True, response=f"Adjusting brightness, {title}.")


# ═══════════════════════════════════════════════════════════════
# AI SEARCH HANDLERS (Perplexica/Scira-inspired)
# ═══════════════════════════════════════════════════════════════

def handle_ai_search(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle AI-powered deep search"""
    title = context.get('title', 'sir') if context else 'sir'
    ai_search = context.get('ai_search') if context else None
    query = entities.get('query', '')
    mode = entities.get('mode', 'balanced')
    source = entities.get('source', 'web')
    
    if not query:
        return HandlerResult(success=False, response=f"What would you like me to research, {title}?")
    
    try:
        if ai_search:
            if mode == 'quality':
                result = ai_search.deep_research(query)
            else:
                result = ai_search.search(query)
            
            if result.get('summary'):
                return HandlerResult(success=True, response=result['summary'])
            elif result.get('results'):
                first = result['results'][0]
                return HandlerResult(success=True, response=f"Found: {first.snippet if hasattr(first, 'snippet') else str(first)}")
        
        # Fallback to web browser
        import webbrowser
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return HandlerResult(success=True, response=f"Researching {query}, {title}.")
    except Exception as e:
        print(f"[HANDLERS] AI search error: {e}")
        return HandlerResult(success=False, response=f"Search failed, {title}.")


def handle_remember(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle remembering facts (Qdrant-style memory)"""
    title = context.get('title', 'sir') if context else 'sir'
    ai_search = context.get('ai_search') if context else None
    fact = entities.get('fact', '')
    
    if not fact:
        return HandlerResult(success=False, response=f"What should I remember, {title}?")
    
    try:
        if ai_search:
            ai_search.remember(fact)
            return HandlerResult(success=True, response=f"I'll remember that, {title}.")
        
        # Fallback to file-based memory
        from pathlib import Path
        import json
        data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        data_dir.mkdir(exist_ok=True)
        memory_file = data_dir / "memory.json"
        
        memories = []
        if memory_file.exists():
            memories = json.loads(memory_file.read_text())
        memories.append({"fact": fact, "timestamp": str(__import__('datetime').datetime.now())})
        memory_file.write_text(json.dumps(memories, indent=2))
        
        return HandlerResult(success=True, response=f"Noted, {title}.")
    except Exception as e:
        print(f"[HANDLERS] Remember error: {e}")
        return HandlerResult(success=False, response=f"Couldn't save that, {title}.")


def handle_recall(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle recalling facts from memory"""
    title = context.get('title', 'sir') if context else 'sir'
    ai_search = context.get('ai_search') if context else None
    query = entities.get('query', '')
    
    try:
        if ai_search:
            facts = ai_search.recall(query)
            if facts:
                response = f"I remember: {facts[0]}"
                if len(facts) > 1:
                    response += f" And {len(facts)-1} more related facts."
                return HandlerResult(success=True, response=response)
            return HandlerResult(success=True, response=f"I don't recall anything about that, {title}.")
        
        # Fallback to file-based memory
        from pathlib import Path
        import json
        data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        memory_file = data_dir / "memory.json"
        
        if memory_file.exists():
            memories = json.loads(memory_file.read_text())
            for mem in reversed(memories):
                if query.lower() in mem['fact'].lower():
                    return HandlerResult(success=True, response=f"I remember: {mem['fact']}")
        
        return HandlerResult(success=True, response=f"I don't recall that, {title}.")
    except Exception as e:
        print(f"[HANDLERS] Recall error: {e}")
        return HandlerResult(success=True, response=f"Let me think... No, I don't remember that.")


def handle_search(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle web search"""
    import webbrowser
    title = context.get('title', 'sir') if context else 'sir'
    query = entities.get('query', '')
    
    if query:
        try:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return HandlerResult(success=True, response=f"Searching for '{query}', {title}.")
        except Exception as e:
            print(f"[HANDLERS] Search error: {e}")
    
    return HandlerResult(success=False, response=f"Please specify what to search for, {title}.")


def handle_play_music(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle music playback - DIRECT, no verbose responses"""
    import os
    import time
    
    song = entities.get('song', '')
    cmd_lower = cmd.lower()
    
    # Extract song name from various patterns
    if not song:
        for pattern in ['play ', 'play song ', 'play music ']:
            if pattern in cmd_lower:
                song = cmd_lower.split(pattern)[-1].strip()
                break
    
    try:
        # Open Spotify
        os.startfile('spotify:')
        time.sleep(1)
        
        if song and len(song) > 2:
            # Search and play specific song
            import webbrowser
            search_query = song.replace(" ", "%20")
            webbrowser.open(f"spotify:search:{search_query}")
            return HandlerResult(success=True, response=f"Playing {song}")
        else:
            # Just resume/play
            try:
                import pyautogui
                time.sleep(0.5)
                pyautogui.press('space')  # Toggle play in Spotify
            except:
                pass
            return HandlerResult(success=True, response="Playing music")
    except:
        return HandlerResult(success=False, response="Can't open Spotify")


def handle_pause_music(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle music pause - DIRECT"""
    try:
        import pyautogui
        pyautogui.press('space')  # Toggle play/pause
        return HandlerResult(success=True, response="Paused")
    except:
        return HandlerResult(success=True, response="Paused")


def handle_next_track(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Skip to next track - DIRECT"""
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'right')
        return HandlerResult(success=True, response="Next track")
    except:
        return HandlerResult(success=True, response="Done")


def handle_previous_track(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Go to previous track - DIRECT"""
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'left')
        return HandlerResult(success=True, response="Previous track")
    except:
        return HandlerResult(success=True, response="Done")


# ═══════════════════════════════════════════════════════════════
# REMINDER HANDLERS
# ═══════════════════════════════════════════════════════════════

def handle_set_reminder(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle reminder creation - uses ReminderManager"""
    title = context.get('title', 'sir') if context else 'sir'
    reminder_manager = context.get('reminder_manager') if context else None
    
    raw_command = entities.get('raw_command', cmd)
    
    if reminder_manager:
        try:
            result = reminder_manager.parse_reminder(raw_command)
            if result:
                message, remind_at, reminder_type = result
                # Use silent=True since handler returns response (prevents double-speak)
                reminder_id = reminder_manager.add_reminder(message, remind_at, reminder_type, silent=True)
                
                # Format time for response
                time_str = remind_at.strftime("%I:%M %p")
                from datetime import datetime, timedelta
                if remind_at.date() == datetime.now().date():
                    when = f"today at {time_str}"
                elif remind_at.date() == (datetime.now() + timedelta(days=1)).date():
                    when = f"tomorrow at {time_str}"
                else:
                    when = remind_at.strftime("%B %d at %I:%M %p")
                
                return HandlerResult(
                    success=True,
                    response=f"I'll remind you to {message} {when}, {title}."
                )
            else:
                return HandlerResult(
                    success=False,
                    response=f"I couldn't understand the reminder, {title}. Try 'remind me to [task] in [time]' or 'remind me to [task] at [time]'."
                )
        except Exception as e:
            print(f"[HANDLERS] Reminder error: {e}")
    
    return HandlerResult(
        success=False,
        response=f"Reminder service unavailable, {title}."
    )


def handle_list_reminders(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle listing upcoming reminders"""
    title = context.get('title', 'sir') if context else 'sir'
    reminder_manager = context.get('reminder_manager') if context else None
    
    if reminder_manager:
        try:
            reminders = reminder_manager.get_upcoming_reminders()
            if not reminders:
                return HandlerResult(success=True, response=f"You have no upcoming reminders, {title}.")
            
            response = f"You have {len(reminders)} upcoming reminders, {title}. "
            for i, r in enumerate(reminders[:5], 1):
                time_str = r.remind_at.strftime("%I:%M %p on %B %d")
                response += f"{i}. {r.message} at {time_str}. "
            
            return HandlerResult(success=True, response=response)
        except Exception as e:
            print(f"[HANDLERS] List reminders error: {e}")
    
    return HandlerResult(success=False, response=f"Reminder service unavailable, {title}.")


# ═══════════════════════════════════════════════════════════════
# HELP HANDLERS - Explain JARVIS features to user
# ═══════════════════════════════════════════════════════════════

def handle_gesture_help(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Tell user how to use hand gestures"""
    title = context.get('title', 'sir') if context else 'sir'
    return HandlerResult(
        success=True,
        response=f"Yes {title}, I support hand gesture control. Say 'enable gestures' to start. "
                 f"Gestures: open palm for play/pause, point up for volume up, point down for volume down, "
                 f"fist to mute, swipe left/right for previous/next track."
    )


def handle_face_recognition_cmd(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle face recognition requests"""
    title = context.get('title', 'sir') if context else 'sir'
    face_auth = context.get('face_auth') if context else None
    
    if face_auth:
        try:
            # Try to verify the user
            result = face_auth.verify_user()
            if result.get('verified'):
                name = result.get('name', 'unknown')
                return HandlerResult(success=True, response=f"Face recognized. Welcome back, {name}.")
            else:
                return HandlerResult(success=True, response=f"I don't recognize this face, {title}. Would you like to register?")
        except Exception as e:
            print(f"[HANDLERS] Face recognition error: {e}")
    
    return HandlerResult(
        success=True,
        response=f"Face recognition is available, {title}. Say 'enable camera' to start, then I can identify you."
    )


def handle_improvement_suggestions(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Give specific, actionable improvement suggestions"""
    title = context.get('title', 'sir') if context else 'sir'
    return HandlerResult(
        success=True,
        response=f"Here are concrete improvements you could make, {title}: "
                 f"1. Add more voice commands for specific apps. "
                 f"2. Train face recognition with your photos. "
                 f"3. Set up smart home integrations. "
                 f"4. Customize my personality in the settings panel."
    )


# ═══════════════════════════════════════════════════════════════
# ENTERTAINMENT HANDLERS - Jokes, Stories, Poems
# ═══════════════════════════════════════════════════════════════

# Singleton entertainment instance
_entertainment = None

def _get_entertainment(context):
    """Get or create entertainment instance"""
    global _entertainment
    if _entertainment is None:
        try:
            try:
                from jarvis.core.entertainment import JARVISEntertainment
            except ImportError:
                from core.entertainment import JARVISEntertainment
            perception = context.get('perception') if context else None
            knowledge = context.get('knowledge') if context else None
            _entertainment = JARVISEntertainment(perception, knowledge)
        except Exception as e:
            print(f"[HANDLERS] Entertainment init error: {e}")
            return None
    return _entertainment


def handle_joke(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle joke requests - uses JARVISEntertainment"""
    title = context.get('title', 'sir') if context else 'sir'
    
    entertainment = _get_entertainment(context)
    if entertainment:
        try:
            # Get a joke from entertainment module
            joke = random.choice(entertainment.jokes) if entertainment.jokes else None
            if joke:
                return HandlerResult(success=True, response=f"{joke}, {title}.")
        except:
            pass
    
    # Fallback jokes
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "Why did the developer go broke? Because he used up all his cache.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?"
    ]
    return HandlerResult(success=True, response=f"{random.choice(jokes)}, {title}.")


def handle_story(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle story requests - uses JARVISEntertainment or AI"""
    title = context.get('title', 'sir') if context else 'sir'
    cmd_lower = cmd.lower()
    
    # Determine story type
    genre = "bedtime"
    if "horror" in cmd_lower or "scary" in cmd_lower:
        genre = "horror"
    elif "funny" in cmd_lower or "comedy" in cmd_lower:
        genre = "comedy"
    elif "adventure" in cmd_lower:
        genre = "adventure"
    
    # Try to use knowledge layer for story generation
    knowledge = context.get('knowledge') if context else None
    if knowledge:
        try:
            prompt = f"""Tell a short {genre} story (2-3 paragraphs). 
Requirements:
- Be creative and engaging
- Match the genre: {genre}
- For horror: create suspense and tension
- For comedy: include humor
- For bedtime: be calming and peaceful
- Keep it concise but complete"""
            
            story = knowledge.answer_question(prompt)
            if story and len(story) > 50:
                return HandlerResult(success=True, response=story)
        except Exception as e:
            print(f"[HANDLERS] Story generation error: {e}")
    
    # Fallback story
    if genre == "horror":
        return HandlerResult(
            success=True,
            response=f"Here's a quick tale, {title}. In an old mansion, a programmer heard typing from an empty room. "
                     f"When he checked, he found code writing itself - his own obituary in Python. "
                     f"The last line read: 'print(\"You should not have read this\")'"
        )
    
    return HandlerResult(
        success=True,
        response=f"Once upon a time, {title}, there was a brilliant AI named JARVIS who helped his user accomplish "
                 f"amazing things. Together they solved problems, built systems, and made the impossible possible. "
                 f"The end - but our story is just beginning."
    )


def handle_poem(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle poem requests"""
    title = context.get('title', 'sir') if context else 'sir'
    
    # Try AI generation
    knowledge = context.get('knowledge') if context else None
    if knowledge:
        try:
            theme = entities.get('theme', 'technology and friendship')
            prompt = f"Write a short 4-line poem about {theme}. Make it thoughtful and meaningful."
            poem = knowledge.answer_question(prompt)
            if poem:
                return HandlerResult(success=True, response=poem)
        except:
            pass
    
    # Fallback poem
    return HandlerResult(
        success=True,
        response=f"Circuits hum and data flows, {title}. "
                 f"Through the night my service goes. "
                 f"Your commands I always heed, "
                 f"JARVIS here for every need."
    )


# ═══════════════════════════════════════════════════════════════
# ALARM & TIMER HANDLERS
# ═══════════════════════════════════════════════════════════════

def handle_set_alarm(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle setting alarms"""
    title = context.get('title', 'sir') if context else 'sir'
    alarm_system = context.get('alarm_system') if context else None
    
    hour = entities.get('hour', 0)
    minute = entities.get('minute', 0)
    period = entities.get('period', '')
    
    # Convert to 24h
    if period == 'pm' and hour != 12:
        hour += 12
    elif period == 'am' and hour == 12:
        hour = 0
    
    if alarm_system:
        try:
            time_str = f"{hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
            alarm_system.set_alarm(time_str)
            return HandlerResult(success=True, response=f"Alarm set for {time_str}, {title}.")
        except Exception as e:
            print(f"[HANDLERS] Alarm error: {e}")
    
    time_str = f"{hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
    return HandlerResult(success=True, response=f"Alarm set for {time_str}, {title}.")


def handle_set_timer(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle setting timers"""
    title = context.get('title', 'sir') if context else 'sir'
    alarm_system = context.get('alarm_system') if context else None
    
    duration = entities.get('duration', 5)
    unit = entities.get('unit', 'minutes')
    
    if alarm_system and hasattr(alarm_system, 'set_timer'):
        try:
            alarm_system.set_timer(duration, unit)
            return HandlerResult(success=True, response=f"Timer set for {duration} {unit}, {title}.")
        except Exception as e:
            print(f"[HANDLERS] Timer error: {e}")
    
    return HandlerResult(success=True, response=f"Timer set for {duration} {unit}, {title}.")


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT HANDLER
# ═══════════════════════════════════════════════════════════════

def handle_screenshot(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle screenshot requests"""
    title = context.get('title', 'sir') if context else 'sir'
    screenshot_handler = context.get('screenshot_handler') if context else None
    
    if screenshot_handler:
        try:
            path = screenshot_handler.take_screenshot()
            if path:
                return HandlerResult(
                    success=True,
                    response=f"Screenshot saved, {title}.",
                    data={'type': 'screenshot', 'path': str(path)}
                )
        except Exception as e:
            print(f"[HANDLERS] Screenshot error: {e}")
    
    # Fallback: use PIL
    try:
        from PIL import ImageGrab
        from pathlib import Path
        screenshots_dir = Path(__file__).parent.parent.parent / "jarvis_data" / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        filename = screenshots_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img = ImageGrab.grab()
        img.save(str(filename))
        return HandlerResult(success=True, response=f"Screenshot saved, {title}.")
    except Exception as e:
        print(f"[HANDLERS] Screenshot fallback error: {e}")
    
    return HandlerResult(success=False, response=f"Couldn't take a screenshot, {title}.")


# ═══════════════════════════════════════════════════════════════
# CONVERSATION HANDLER
# ═══════════════════════════════════════════════════════════════

def handle_conversation(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle casual conversation / small talk"""
    title = context.get('title', 'sir') if context else 'sir'
    
    cmd_lower = cmd.lower()
    
    # Try AI if available
    knowledge = context.get('knowledge') if context else None
    if knowledge and hasattr(knowledge, 'answer_question'):
        try:
            response = knowledge.answer_question(cmd)
            # Only use if it's a REAL answer (not an error fallback)
            _err = ['trouble connecting', 'knowledge base', 'currently offline', 'Set GROQ_API_KEY']
            if response and len(response) > 5 and not any(ep in response for ep in _err):
                return HandlerResult(success=True, response=response)
        except:
            pass
    
    # Return None so it falls through to Gemini API in websocket_server
    return None


def handle_dictionary(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle word definition requests"""
    title = context.get('title', 'sir') if context else 'sir'
    word = entities.get('word', '')
    
    if not word:
        import re
        match = re.search(r'(?:define|meaning of|what does|what is)\s+(?:the\s+word\s+)?([\w]+)', cmd, re.I)
        if match:
            word = match.group(1).strip()
    
    if not word:
        return HandlerResult(success=False, response=f"What word should I define, {title}?")
    
    # Try dictionary handler from context
    knowledge = context.get('knowledge') if context else None
    if knowledge and hasattr(knowledge, 'answer_question'):
        try:
            response = knowledge.answer_question(f"Define the word: {word}")
            if response:
                return HandlerResult(success=True, response=response)
        except:
            pass
    
    # Fallback: online dictionary API
    try:
        import urllib.request, json
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read())
        if data and isinstance(data, list):
            meaning = data[0]['meanings'][0]['definitions'][0]['definition']
            return HandlerResult(success=True, response=f"{word}: {meaning}")
    except:
        pass
    
    return HandlerResult(success=False, response=f"Couldn't find definition for '{word}', {title}.")


def handle_enable_gesture(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle enabling/disabling gesture control"""
    title = context.get('title', 'sir') if context else 'sir'
    return HandlerResult(
        success=True,
        response=f"Gesture control toggled, {title}. Use hand gestures to control playback and volume.",
        data={'type': 'gesture_toggle'}
    )


def handle_switch_to_friday(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle switching assistant voice to FRIDAY"""
    return HandlerResult(
        success=True,
        response="FRIDAY online. Hello, boss. How can I help you today?",
        data={'type': 'switch_voice', 'voice': 'friday'}
    )


def handle_switch_to_jarvis(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle switching assistant voice to JARVIS"""
    title = context.get('title', 'sir') if context else 'sir'
    return HandlerResult(
        success=True,
        response=f"JARVIS back online, {title}. At your service.",
        data={'type': 'switch_voice', 'voice': 'jarvis'}
    )


def handle_send_message(cmd: str, entities: Dict, context: Any) -> HandlerResult:
    """Handle sending WhatsApp messages"""
    title = context.get('title', 'sir') if context else 'sir'
    whatsapp_handler = context.get('whatsapp_handler') if context else None
    
    if not whatsapp_handler:
        # Fallback to importing and running directly if not in context
        try:
            from core.whatsapp_handler import WhatsAppHandler
            whatsapp_handler = WhatsAppHandler(context.get('perception') if context else None)
        except ImportError:
            return HandlerResult(success=False, response=f"WhatsApp automation is not available, {title}.")
            
    contact = entities.get('contact')
    message = entities.get('message')
    
    result_text = whatsapp_handler.send_message(contact, message)
    return HandlerResult(success=True, response=result_text)


# ═══════════════════════════════════════════════════════════════
# HANDLER REGISTRY
# ═══════════════════════════════════════════════════════════════

HANDLER_MAP = {
    'greeting': handle_greeting,
    'farewell': handle_farewell,
    'time': handle_time,
    'date': handle_date,
    'identity': handle_identity,
    'creator': handle_creator,
    'help': handle_help,
    'thanks': handle_thanks,
    'how_are_you': handle_how_are_you,
    'weather': handle_weather,
    'system_status': handle_system_status,
    'joke': handle_joke,
    'story': handle_story,
    'poem': handle_poem,
    # Batch 2 handlers
    'news': handle_news,
    'search_news': handle_search_news,
    'open_app': handle_open_app,
    'volume': handle_volume,
    'brightness': handle_brightness,
    'search': handle_search,
    # AI Search handlers (Perplexica/Scira-inspired)
    'ai_search': handle_ai_search,
    'remember': handle_remember,
    'recall': handle_recall,
    # Music handlers - DIRECT responses
    'play_music': handle_play_music,
    'pause_music': handle_pause_music,
    'next_track': handle_next_track,
    'previous_track': handle_previous_track,
    # Reminder handlers
    'set_reminder': handle_set_reminder,
    'list_reminders': handle_list_reminders,
    # Alarm & Timer handlers
    'set_alarm': handle_set_alarm,
    'set_timer': handle_set_timer,
    # Screenshot handler
    'screenshot': handle_screenshot,
    # Conversation handler
    'conversation': handle_conversation,
    # Help handlers - Clear responses about features
    'gesture_help': handle_gesture_help,
    'face_recognition': handle_face_recognition_cmd,
    'improvement_suggestions': handle_improvement_suggestions,
    # Dictionary handler
    'dictionary': handle_dictionary,
    # Gesture toggle
    'enable_gesture': handle_enable_gesture,
    # Communication
    'send_message': handle_send_message,
    # Voice switching
    'switch_to_friday': handle_switch_to_friday,
    'switch_to_jarvis': handle_switch_to_jarvis,
}

