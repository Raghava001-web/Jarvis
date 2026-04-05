"""
JARVIS Intent Classifier
Simple keyword-based intent classification
With multi-command support and context-aware disambiguation
"""

from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass, field
try:
    from jarvis.core.intent_router import Intent
except ImportError:
    from core.intent_router import Intent
import re


@dataclass
class ClassificationContext:
    """
    Structured context for intent classification.
    Enables vague commands like "next" or "play it" to resolve correctly.
    
    Example: "next" with active_app="spotify" -> "next_track"
             "next" with active_app="pdf" -> "next_page"
    """
    active_app: Optional[str] = None        # Currently focused app
    last_intent: Optional[str] = None       # Previous intent
    last_entities: Dict[str, Any] = field(default_factory=dict)
    last_action: Optional[str] = None       # What was just done
    user_mood: str = "neutral"              # Current user emotion
    conversation_topic: Optional[str] = None # What we're discussing


# Context-aware vague command mappings
CONTEXT_COMMANDS = {
    # Music app context
    "spotify": {
        "next": "next_track",
        "previous": "previous_track", 
        "back": "previous_track",
        "stop": "pause_music",
        "pause": "pause_music",
        "resume": "play_music",
        "play": "play_music",
    },
    "music": {
        "next": "next_track",
        "previous": "previous_track",
        "back": "previous_track",
        "stop": "pause_music",
        "pause": "pause_music",
        "play": "play_music",
    },
    # PDF context
    "pdf": {
        "next": "next_page",
        "previous": "previous_page",
        "back": "previous_page",
        "close": "close_pdf",
    },
    # Browser context
    "browser": {
        "next": "browser_forward",
        "back": "browser_back",
        "close": "close_tab",
        "new": "new_tab",
    },
    # Video context
    "youtube": {
        "next": "next_video",
        "skip": "skip_ad",
        "pause": "pause_video",
        "play": "play_video",
    },
}


def split_commands(command: str) -> List[str]:
    """
    Split a multi-part command into individual commands.
    Handles: "open brave and search youtube" -> ["open brave", "search youtube"]
    
    Preserves search/query content by checking context.
    """
    cmd = command.strip()
    
    # Don't split if it's a search/query command (the 'and' is part of the query)
    search_indicators = ['search for', 'google', 'look up', 'find', 'what is', 'who is']
    if any(indicator in cmd.lower() for indicator in search_indicators):
        # Only split before the search term
        for indicator in search_indicators:
            if indicator in cmd.lower():
                idx = cmd.lower().find(indicator)
                if idx > 0:
                    # Check if there's an "and" before the search
                    before = cmd[:idx].strip()
                    if before.endswith(' and'):
                        before = before[:-4].strip()
                        after = cmd[idx:].strip()
                        return [before, after] if before else [after]
                break
        return [cmd]
    
    # Split on common conjunctions
    # Order matters - check longer patterns first
    split_patterns = [
        r'\s+and\s+then\s+',  # "and then"
        r'\s+then\s+',        # "then"
        r'\s+after\s+that\s+', # "after that"
    ]
    
    for pattern in split_patterns:
        parts = re.split(pattern, cmd, flags=re.IGNORECASE)
        if len(parts) > 1:
            return [p.strip() for p in parts if p.strip()]
    
    # Split on " and " but be careful with app names
    # Don't split "bread and butter" type phrases
    if ' and ' in cmd.lower():
        parts = cmd.split(' and ', 1)
        # Only split if first part looks like a command
        first_words = ['open', 'close', 'start', 'stop', 'play', 'pause', 'set', 'show', 'tell', 'get']
        if any(parts[0].lower().strip().startswith(w) for w in first_words):
            return [p.strip() for p in parts if p.strip()]
    
    return [cmd]


def classify_intent(command: str, context: ClassificationContext = None) -> Tuple[str, Dict[str, Any]]:
    """
    Classify a command into an intent + extracted entities.
    
    Args:
        command: The user's command text
        context: Optional ClassificationContext for resolving vague commands
    
    Returns:
        Tuple of (intent_name: str, entities: dict)
    """
    cmd = command.lower().strip()
    entities = {}
    
    # ═══════════════════════════════════════════════════════════
    # CONTEXT-AWARE RESOLUTION (check first for vague commands)
    # ═══════════════════════════════════════════════════════════
    if context and context.active_app:
        app = context.active_app.lower()
        # Check if this is a vague command that needs context
        for ctx_app, mappings in CONTEXT_COMMANDS.items():
            if ctx_app in app:
                for vague_cmd, intent in mappings.items():
                    if cmd == vague_cmd or cmd.startswith(f"{vague_cmd} "):
                        # Found context-aware match!
                        return intent, entities
    
    # ═══════════════════════════════════════════════════════════
    # KEYWORD OVERRIDES (common commands that should always work)
    # ═══════════════════════════════════════════════════════════
    # These override even without context
    keyword_overrides = {
        "resume": "play_music",
        "continue playing": "play_music",
        "resume music": "play_music",
        "resume playback": "play_music",
    }
    
    for keyword, intent in keyword_overrides.items():
        if keyword in cmd:
            return intent, entities
    
    # Handle "close X" pattern explicitly
    if cmd.startswith("close ") or cmd == "close":
        app_name = cmd.replace("close ", "").strip() if cmd.startswith("close ") else None
        return "close_app", {"app": app_name} if app_name else {}
    
    # ═══════════════════════════════════════════════════════════
    # VOICE SWITCHING (highest priority)
    # ═══════════════════════════════════════════════════════════
    if 'switch to friday' in cmd or 'activate friday' in cmd:
        return 'switch_to_friday', {}
    if 'switch to jarvis' in cmd or 'activate jarvis' in cmd:
        return 'switch_to_jarvis', {}

    
    # ═══════════════════════════════════════════════════════════
    # GREETINGS & SOCIAL
    # ═══════════════════════════════════════════════════════════
    if any(word in cmd for word in ['hello', 'hi jarvis', 'hi friday', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return 'greeting', {}
    
    if any(word in cmd for word in ['bye', 'goodbye', 'see you', 'goodnight']):
        return 'farewell', {}
    
    if 'thank' in cmd:
        return 'thanks', {}
    
    if 'how are you' in cmd:
        return 'how_are_you', {}
    
    # ═══════════════════════════════════════════════════════════
    # IDENTITY
    # ═══════════════════════════════════════════════════════════
    if 'who are you' in cmd or 'your name' in cmd:
        return 'identity', {}
    
    if any(phrase in cmd for phrase in ['who made you', 'who created you', 'your creator', 'who built you']):
        return 'creator', {}
    
    # ═══════════════════════════════════════════════════════════
    # TIME & DATE
    # ═══════════════════════════════════════════════════════════
    if 'time' in cmd and 'timer' not in cmd:
        return 'time', {}
    
    if 'date' in cmd or ('what' in cmd and 'day' in cmd):
        return 'date', {}
    
    # ═══════════════════════════════════════════════════════════
    # SYSTEM & STATUS
    # ═══════════════════════════════════════════════════════════
    if 'system status' in cmd or 'system report' in cmd:
        return 'system_status', {}
    
    if cmd == 'help' or 'what can you do' in cmd or 'capabilities' in cmd:
        return 'help', {}
    
    # ═══════════════════════════════════════════════════════════
    # WEATHER
    # ═══════════════════════════════════════════════════════════
    if 'weather' in cmd:
        # Try to extract city
        import re
        city_patterns = [
            r'weather (?:in|for|at) (\w+)',
            r'(\w+) weather'
        ]
        for pattern in city_patterns:
            match = re.search(pattern, cmd)
            if match:
                city = match.group(1)
                if city not in ['the', 'today', 'now', 'current']:
                    entities['city'] = city
                    break
        return 'weather', entities
    
    # ═══════════════════════════════════════════════════════════
    # NEWS (Enhanced with Hacker News)
    # ═══════════════════════════════════════════════════════════
    # Search news by keyword
    if 'search news' in cmd or 'news about' in cmd or 'news on' in cmd:
        import re
        keyword = re.sub(r'(search news|news about|news on|for|about)\s*', '', cmd).strip()
        if keyword:
            entities['keyword'] = keyword
            return 'search_news', entities
    
    if 'news' in cmd or 'headline' in cmd or 'hacker news' in cmd:
        # Detect category
        categories = {
            'economics': 'economics',
            'economy': 'economics',
            'business': 'business',
            'politics': 'politics',
            'political': 'politics',
            'tech': 'tech',  # Now maps to Hacker News
            'technology': 'technology',
            'sports': 'sports',
            'sport': 'sports',
            'entertainment': 'entertainment',
            'world': 'world',
            'global': 'world',
            # Hacker News categories
            'hacker': 'hacker',
            'hackernews': 'hackernews',
            'startups': 'startups',
            'ask': 'ask',
            'show': 'show'
        }
        for keyword, category in categories.items():
            if keyword in cmd:
                entities['category'] = category
                break
        return 'news', entities
    
    # ═══════════════════════════════════════════════════════════
    # ENTERTAINMENT
    # ═══════════════════════════════════════════════════════════
    if 'joke' in cmd:
        return 'joke', {}
    
    # IMPORTANT: Check 'chat history' BEFORE 'story' to avoid 'history' matching 'story'
    if 'chat history' in cmd or 'conversation history' in cmd or 'show history' in cmd:
        return 'chat_history', {}
    
    if 'story' in cmd:
        # Extract genre
        if 'horror' in cmd or 'scary' in cmd:
            entities['genre'] = 'horror'
        elif 'funny' in cmd or 'comedy' in cmd:
            entities['genre'] = 'comedy'
        elif 'romance' in cmd:
            entities['genre'] = 'romance'
        elif 'bedtime' in cmd:
            entities['genre'] = 'bedtime'
        return 'story', entities
    
    if 'poem' in cmd or 'recite' in cmd:
        return 'poem', {}
    
    if 'riddle' in cmd:
        return 'riddle', {}
    
    # ═══════════════════════════════════════════════════════════
    # SCREENSHOTS & OCR
    # ═══════════════════════════════════════════════════════════
    if 'screenshot' in cmd or 'screen shot' in cmd or 'capture screen' in cmd:
        return 'screenshot', {}
    
    if any(phrase in cmd for phrase in ['read screen', 'read text', 'extract text', 'ocr',
                                         'what is on my screen', 'what\'s on my screen',
                                         'read my screen', 'screen text']):
        return 'ocr', {}
    
    if 'read clipboard' in cmd:
        return 'read_clipboard', {}
    
    # ═══════════════════════════════════════════════════════════
    # DICTIONARY
    # ═══════════════════════════════════════════════════════════
    if 'define ' in cmd or 'meaning of ' in cmd or 'definition of ' in cmd:
        word = cmd.replace('define ', '').replace('meaning of ', '').replace('definition of ', '').strip()
        entities['word'] = word
        return 'dictionary', entities
    
    if 'synonym' in cmd:
        word = cmd.replace('synonym for ', '').replace('synonym of ', '').replace('synonyms of ', '').replace('synonym', '').strip()
        entities['word'] = word
        return 'synonym', entities
    
    # ═══════════════════════════════════════════════════════════
    # FACE & GESTURE
    # ═══════════════════════════════════════════════════════════
    if any(phrase in cmd for phrase in ['register my face', 'register face', 'register owner']):
        return 'register_face', {}
    
    if any(phrase in cmd for phrase in ['verify me', 'authenticate', 'who am i']):
        return 'verify_face', {}
    
    if any(phrase in cmd for phrase in ['enable gesture', 'start gesture', 'gesture on']):
        return 'enable_gesture', {}
    
    if any(phrase in cmd for phrase in ['disable gesture', 'stop gesture', 'gesture off']):
        return 'disable_gesture', {}
    
    # ═══════════════════════════════════════════════════════════
    # NOTES & ALARMS
    # ═══════════════════════════════════════════════════════════
    if any(phrase in cmd for phrase in ['create note', 'new note', 'add note']):
        content = cmd.replace('create note', '').replace('new note', '').replace('add note', '').strip()
        entities['content'] = content
        return 'create_note', entities
    
    if any(phrase in cmd for phrase in ['list notes', 'show notes', 'my notes']):
        return 'list_notes', {}
    
    if any(phrase in cmd for phrase in ['set alarm', 'alarm for', 'alarm in', 'set an alarm', 'wake me']):
        import re
        # Check for relative time first: "5 min from now", "in 10 minutes"
        relative_match = re.search(r'(\d+)\s*(min|minute|minutes|hour|hours|hr|hrs)', cmd)
        if relative_match:
            entities['relative_amount'] = int(relative_match.group(1))
            entities['relative_unit'] = relative_match.group(2)
            return 'set_alarm', entities
        
        # Absolute time: "7:30 am"
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', cmd)
        if time_match:
            entities['hour'] = int(time_match.group(1))
            entities['minute'] = int(time_match.group(2) or 0)
            entities['period'] = time_match.group(3)
        return 'set_alarm', entities
    
    if any(phrase in cmd for phrase in ['list alarm', 'show alarm', 'my alarm']):
        return 'list_alarms', {}
    
    # ═══════════════════════════════════════════════════════════
    # REMINDERS
    # ═══════════════════════════════════════════════════════════
    if any(phrase in cmd for phrase in ['remind me', 'reminder', 'set reminder']):
        # Pass the full command, ReminderManager will parse the time + message
        entities['raw_command'] = command
        if any(phrase in cmd for phrase in ['list reminder', 'show reminder', 'my reminder']):
            return 'list_reminders', {}
        return 'set_reminder', entities
    
    
    # ═══════════════════════════════════════════════════════════
    # VOLUME & BRIGHTNESS
    # ═══════════════════════════════════════════════════════════
    if 'volume' in cmd:
        if 'up' in cmd or 'increase' in cmd:
            entities['action'] = 'up'
        elif 'down' in cmd or 'decrease' in cmd:
            entities['action'] = 'down'
        elif 'mute' in cmd:
            entities['action'] = 'mute'
        else:
            import re
            match = re.search(r'(\d+)\s*%?', cmd)
            if match:
                entities['level'] = int(match.group(1))
                entities['action'] = 'set'
        return 'volume', entities
    
    # Standalone "mute" without "volume" keyword
    if cmd in ('mute', 'unmute') or 'mute the' in cmd or 'mute audio' in cmd or 'mute sound' in cmd:
        return 'volume', {'action': 'mute'}
    
    if 'brightness' in cmd:
        if 'up' in cmd or 'increase' in cmd:
            entities['action'] = 'up'
        elif 'down' in cmd or 'decrease' in cmd:
            entities['action'] = 'down'
        else:
            import re
            match = re.search(r'(\d+)\s*%?', cmd)
            if match:
                entities['level'] = int(match.group(1))
                entities['action'] = 'set'
        return 'brightness', entities
    
    # ═══════════════════════════════════════════════════════════
    # SCREEN CONTROL
    # ═══════════════════════════════════════════════════════════
    screen_control_triggers = [
        'click', 'double click', 'right click', 
        'scroll up', 'scroll down',
        'move mouse', 'move cursor',
        'type ', 'press enter', 'press escape', 'press tab',
        'copy', 'paste', 'undo', 'redo', 'select all',
        'switch window', 'alt tab', 'close window', 'close tab',
        'new tab', 'new window', 'create tab', 'create new tab',
    ]
    if any(trigger in cmd for trigger in screen_control_triggers):
        entities['raw_text'] = command  # Pass original for parsing
        return 'screen_control', entities
    
    # ═══════════════════════════════════════════════════════════
    # WHATSAPP / COMMUNICATION
    # ═══════════════════════════════════════════════════════════
    # "open whatsapp and text hena saying hi"
    # "send whatsapp to john message what's up"
    if 'whatsapp' in cmd or 'whatsapp to' in cmd or 'send message' in cmd or 'text ' in cmd:
        import re
        
        # Clean up common prefixes that confuse the regex
        clean_cmd = re.sub(r'^(?:open\s+whatsapp\s+and\s+)?(text|send message to|whatsapp)\s+', r'\1 ', cmd, flags=re.I)
        
        # Try to extract contact and message
        # Patterns like: "whatsapp [contact] (saying|message|that) [message]"
        # Or: "text [contact] (saying|message) [message]"
        match = re.search(r'(?:whatsapp|send message to|text)\s+([a-zA-Z0-9\s]+?)(?:\s+(?:saying|message|that)\s+)(.+)', clean_cmd, re.I)
        if match:
            entities['contact'] = match.group(1).strip()
            entities['message'] = match.group(2).strip()
        else:
            # Maybe just contact?
            match2 = re.search(r'(?:whatsapp|send message to|text)\s+([a-zA-Z0-9\s]+)', clean_cmd, re.I)
            if match2:
                entities['contact'] = match2.group(1).strip()
                
        return 'send_message', entities

    # ═══════════════════════════════════════════════════════════
    # APPS & SEARCH
    # ═══════════════════════════════════════════════════════════
    if cmd.startswith('open '):
        app = cmd.replace('open ', '').strip()
        
        # Special case: "open youtube search for X" → should search YouTube, not open app
        if 'youtube' in app and ('search' in app or 'find' in app or 'look' in app):
            import re
            # Extract the search query after youtube + search/find/look keywords
            query_match = re.sub(r'youtube\s*(and\s+)?(search|find|look)\s*(for|up)?\s*', '', app).strip()
            if query_match:
                # Don't open browser here — let the handler do it
                entities['query'] = query_match
                return 'youtube_search', entities
        
        entities['app'] = app
        return 'open_app', entities
    
    # "switch to X" / "go to X" (app switching)
    if cmd.startswith('switch to ') or cmd.startswith('go to '):
        app = cmd.replace('switch to ', '').replace('go to ', '').strip()
        if app and app not in ('friday', 'jarvis'):  # Don't override voice switching
            entities['app'] = app
            return 'open_app', entities
    
    # ═══════════════════════════════════════════════════════════
    # MUSIC CONTROL - Direct responses
    # ═══════════════════════════════════════════════════════════
    # Pause/Stop
    if any(phrase in cmd for phrase in ['pause music', 'pause', 'stop music', 'stop playing']):
        return 'pause_music', {}
    
    # Next track
    if any(phrase in cmd for phrase in ['next song', 'next track', 'skip song', 'skip track', 'skip']):
        return 'next_track', {}
    
    # Previous track
    if any(phrase in cmd for phrase in ['previous song', 'previous track', 'go back', 'last song']):
        return 'previous_track', {}
    
    # Play (must be after pause/next/prev checks)
    if any(phrase in cmd for phrase in ['play music', 'play songs', 'play some music', 'spotify']):
        return 'play_music', {}
    
    # Play specific song — but NOT if YouTube is the target
    if cmd.startswith('play '):
        song = cmd.replace('play ', '').strip()
        # "play X in youtube" / "play X on youtube" → YouTube search, NOT Spotify
        if any(yt in cmd for yt in ['in youtube', 'on youtube', 'youtube', 'in yt', 'on yt']):
            import re
            query = re.sub(r'\s*(in|on)\s*(youtube|yt)\s*$', '', song, flags=re.I).strip()
            entities['query'] = query
            return 'youtube_search', entities
        if len(song) > 2:
            entities['song'] = song
            return 'play_music', entities
    
    # ═══════════════════════════════════════════════════════════
    # AI SEARCH (Perplexica/Scira-inspired)
    # ═══════════════════════════════════════════════════════════
    # Deep research mode
    if any(phrase in cmd for phrase in ['research ', 'deep search', 'investigate']):
        query = cmd.replace('research ', '').replace('deep search', '').replace('investigate', '').strip()
        entities['query'] = query
        entities['mode'] = 'quality'
        return 'ai_search', entities
    
    # Recall facts from memory — MUST be before 'remember' block
    # so "do you remember my X" goes to recall, not remember
    if any(phrase in cmd for phrase in ['recall ', 'what did i tell you about', 'do you remember',
                                         "what's my ", "whats my ", "what is my ", "do you know my"]):
        query = cmd
        for strip in ['recall ', 'what did i tell you about', 'do you remember',
                      "what's my ", "whats my ", "what is my ", "do you know my "]:
            query = query.replace(strip, '')
        entities['query'] = query.strip()
        return 'recall', entities
    
    if any(phrase in cmd for phrase in ['remember that', 'remember this', 'save this',
                                         'remember my', 'remember i', 'remember the']):
        import re
        fact = re.sub(r'(remember that|remember this|save this|remember my|remember i|remember the|remember)\s*', '', cmd).strip()
        entities['fact'] = fact
        return 'remember', entities
    
    # Reddit search
    if 'reddit' in cmd and 'search' in cmd:
        query = cmd.replace('reddit', '').replace('search', '').strip()
        entities['query'] = query
        entities['source'] = 'reddit'
        return 'ai_search', entities
    
    # Regular search (enhanced)
    if 'search' in cmd or 'google' in cmd:
        query = cmd.replace('search for', '').replace('search', '').replace('google', '').strip()
        entities['query'] = query
        return 'search', entities
    
    # ═══════════════════════════════════════════════════════════
    # EMOTION DETECTION
    # ═══════════════════════════════════════════════════════════
    if 'enable emotion' in cmd or 'mood detection' in cmd:
        return 'enable_emotion', {}
    
    if 'disable emotion' in cmd:
        return 'disable_emotion', {}
    
    # ═══════════════════════════════════════════════════════════
    # FEATURES STATUS
    # ═══════════════════════════════════════════════════════════
    if 'features' in cmd or ('status' in cmd and 'system' not in cmd):
        return 'features', {}
    
    # ═══════════════════════════════════════════════════════════
    # GESTURE & FACE HELP (so JARVIS tells user how to use these)
    # ═══════════════════════════════════════════════════════════
    if any(phrase in cmd for phrase in ['hand gesture', 'use gestures', 'gesture control', 'can i use gesture']):
        return 'gesture_help', {}
    
    if any(phrase in cmd for phrase in ['recognize my face', 'face recognition', 'who am i', 'identify me']):
        return 'face_recognition', {}
    
    if any(phrase in cmd for phrase in ['improve you', 'where should i improve', 'what needs improvement', 'improve jarvis']):
        return 'improvement_suggestions', {}
    
    # ═══════════════════════════════════════════════════════════
    # FALLBACK TO CONVERSATION (AI will handle it)
    # ═══════════════════════════════════════════════════════════
    return 'conversation', {}


# Quick test
if __name__ == "__main__":
    test_commands = [
        "hello jarvis",
        "what's the time",
        "tell me a joke",
        "what's the weather in London",
        "tell me a horror story",
        "open chrome",
        "volume up",
        "set alarm for 7:30 am",
        "economics news",
        "who created you"
    ]
    
    for cmd in test_commands:
        intent, entities = classify_intent(cmd)
        print(f"'{cmd}' -> {intent} {entities if entities else ''}")
