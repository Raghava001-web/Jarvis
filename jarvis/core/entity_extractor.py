"""
Entity Extractor (v2) - Hybrid NLP + Rules
==========================================
Uses spaCy for NER when available, falls back to regex.
Handles complex cases like:
- "Play Blinding Lights by The Weeknd on Spotify"
- "Set an alarm in 10 minutes and another at 7"
- "Open VS Code and then Chrome"
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Try spaCy (optional but recommended)
SPACY_AVAILABLE = False
_NLP = None

def _get_nlp():
    """Lazy load spaCy"""
    global SPACY_AVAILABLE, _NLP
    if _NLP is not None:
        return _NLP
        
    try:
        import spacy
        try:
            _NLP = spacy.load("en_core_web_sm")
            SPACY_AVAILABLE = True
            print("[ENTITY] spaCy loaded")
            return _NLP
        except OSError:
            print("[ENTITY] spaCy model not found (run: python -m spacy download en_core_web_sm)")
            return None
    except ImportError:
        print("[ENTITY] spaCy not installed")
        return None


class EntityExtractor:
    """
    Hybrid entity extraction: spaCy NER + regex patterns.
    Handles compound entities and context.
    """
    
    # Known apps (for better detection)
    KNOWN_APPS = {
        "chrome", "brave", "edge", "firefox", "safari",
        "spotify", "youtube", "netflix", "discord", "slack",
        "vscode", "vs code", "visual studio", "notepad", "sublime",
        "whatsapp", "telegram", "messenger",
        "photoshop", "figma", "canva",
        "terminal", "cmd", "powershell",
        "explorer", "file explorer", "finder",
        "calculator", "calendar", "settings",
        "steam", "epic", "origin",
        "word", "excel", "powerpoint", "outlook",
        "obs", "vlc", "zoom", "teams",
        "perplexity", "chatgpt", "cursor",
    }
    
    # Music app keywords
    MUSIC_APPS = {"spotify", "youtube", "youtube music", "apple music", "soundcloud"}
    
    def __init__(self):
        print("[ENTITY] Initializing Entity Extractor v2...")
        self.nlp = None  # Lazy loaded
        print("[ENTITY] Entity Extractor Ready")
        
    def _ensure_nlp(self):
        """Lazy load NLP"""
        if self.nlp is None:
            self.nlp = _get_nlp()
        return self.nlp is not None
        
    def extract(self, text: str, intent: str) -> Dict[str, Any]:
        """
        Extract entities from text based on intent.
        Returns dict of entity_name -> value.
        """
        text = text.strip()
        entities = {}
        
        # Get spaCy doc if available
        doc = None
        if self._ensure_nlp():
            doc = self.nlp(text)
            
        # Extract based on intent
        if intent in ["play_music", "pause_music", "resume_music", "skip_track"]:
            entities.update(self._extract_music(text, doc))
            
        elif intent in ["set_alarm", "cancel_alarm"]:
            entities.update(self._extract_time(text, doc))
            
        elif intent in ["open_app", "close_app"]:
            entities.update(self._extract_app(text, doc))
            
        elif intent in ["search_web", "ask_question"]:
            entities.update(self._extract_query(text, doc))
            
        elif intent in ["send_whatsapp"]:
            entities.update(self._extract_contact(text, doc))
            
        elif intent in ["play_youtube"]:
            entities.update(self._extract_youtube(text, doc))
            
        elif intent in ["volume_up", "volume_down"]:
            entities.update(self._extract_amount(text))
            
        elif intent in ["create_event"]:
            entities.update(self._extract_event(text, doc))
            
        return entities
        
    def _extract_music(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract song/artist/playlist with NLP support"""
        entities = {}
        text_lower = text.lower()
        
        # Check for app preference
        for app in self.MUSIC_APPS:
            if app in text_lower:
                entities["app"] = app.replace(" ", "_")
                break
                
        # Use spaCy for better entity extraction
        if doc:
            # Find WORK_OF_ART, PERSON, ORG entities
            for ent in doc.ents:
                if ent.label_ == "WORK_OF_ART":
                    entities["song"] = ent.text
                elif ent.label_ == "PERSON":
                    if "artist" not in entities:
                        entities["artist"] = ent.text
                elif ent.label_ == "ORG":
                    # Could be band name
                    if "artist" not in entities and ent.text.lower() not in self.KNOWN_APPS:
                        entities["artist"] = ent.text
                        
        # Fallback/enhance with patterns
        if "song" not in entities:
            patterns = [
                r"play\s+(.+?)\s+by\s+(.+?)(?:\s+on\s+\w+)?$",  # "play X by Y"
                r"play\s+(.+?)(?:\s+on\s+\w+)?$",  # "play X"
                r"(?:listen\s+to|put\s+on)\s+(.+?)(?:\s+on\s+\w+)?$",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    groups = match.groups()
                    song = groups[0].strip()
                    
                    # Clean up
                    song = re.sub(r"\b(some|a|the|song|music)\b", "", song).strip()
                    song = re.sub(r"\s+", " ", song)
                    
                    if song and song not in ["music", "songs"]:
                        entities["song"] = song
                        
                    # Extract artist if present
                    if len(groups) > 1 and groups[1]:
                        artist = groups[1].strip()
                        artist = re.sub(r"\s+(on\s+\w+)$", "", artist)
                        if artist:
                            entities["artist"] = artist
                    break
                    
        return entities
        
    def _extract_time(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract time/duration with NLP support"""
        entities = {}
        text_lower = text.lower()
        
        # Use spaCy TIME entities
        if doc:
            for ent in doc.ents:
                if ent.label_ == "TIME":
                    entities["time_raw"] = ent.text
                    
        # Parse relative time: "in X minutes"
        relative_patterns = [
            r"in\s+(\d+)\s*(minute|min|hour|hr|second|sec)s?",
            r"after\s+(\d+)\s*(minute|min|hour|hr|second|sec)s?",
        ]
        
        for pattern in relative_patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                now = datetime.now()
                if "min" in unit:
                    target = now + timedelta(minutes=amount)
                elif "hour" in unit or "hr" in unit:
                    target = now + timedelta(hours=amount)
                else:
                    target = now + timedelta(seconds=amount)
                    
                entities["time"] = target.strftime("%H:%M")
                entities["relative"] = True
                entities["duration_minutes"] = amount if "min" in unit else amount * 60
                return entities
                
        # Parse absolute time
        time_patterns = [
            r"(?:at|for)\s+(\d{1,2})[:\.](\d{2})\s*(am|pm)?",  # at 7:30 am
            r"(?:at|for)\s+(\d{1,2})\s*(am|pm)",  # at 7 am
            r"(\d{1,2})[:\.](\d{2})\s*(am|pm)",  # 7:30 am
            r"(\d{1,2})\s*(am|pm)\b",  # 7 am
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                
                # Handle minute
                minute = 0
                period = None
                
                if len(groups) >= 2:
                    if groups[1] and groups[1].isdigit():
                        minute = int(groups[1])
                        period = groups[2] if len(groups) > 2 else None
                    else:
                        period = groups[1]
                        
                # Handle AM/PM
                if period:
                    if period.lower() == "pm" and hour < 12:
                        hour += 12
                    elif period.lower() == "am" and hour == 12:
                        hour = 0
                        
                entities["time"] = f"{hour:02d}:{minute:02d}"
                entities["relative"] = False
                return entities
                
        return entities
        
    def _extract_app(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract application name intelligently"""
        entities = {}
        text_lower = text.lower()
        
        # Remove action words
        cleaned = re.sub(
            r"^(please\s+)?(open|launch|start|close|exit|run|quit)\s+",
            "",
            text_lower
        ).strip()
        
        # Remove common suffixes
        cleaned = re.sub(r"\s+(app|application|program)$", "", cleaned)
        
        # Check known apps first (exact match preferred)
        for app in self.KNOWN_APPS:
            if app in cleaned:
                entities["app"] = app.replace(" ", "_")
                return entities
                
        # Use NLP to find proper nouns
        if doc:
            for token in doc:
                if token.pos_ == "PROPN":
                    entities["app"] = token.text.lower()
                    return entities
                    
        # Fallback: use cleaned text
        if cleaned:
            entities["app"] = cleaned.split()[0]  # First word
            
        return entities
        
    def _extract_query(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract search query"""
        entities = {}
        text_lower = text.lower()
        
        # Remove search prefixes
        patterns = [
            r"^(please\s+)?(search|google|look\s+up|find|search\s+for|look\s+for|what\s+is|tell\s+me\s+about|who\s+is|where\s+is|how\s+to)\s+",
        ]
        
        query = text_lower
        for pattern in patterns:
            query = re.sub(pattern, "", query).strip()
            
        if query:
            entities["query"] = query
            
        return entities
        
    def _extract_contact(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract contact name and message"""
        entities = {}
        text_lower = text.lower()
        
        # Use spaCy PERSON entities
        if doc:
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    entities["contact"] = ent.text
                    break
                    
        # Pattern: "message/text X saying Y"
        patterns = [
            r"(?:message|text|whatsapp|send\s+to|send\s+message\s+to)\s+(.+?)(?:\s+saying|\s+that|$)",
            r"(?:tell|ask)\s+(.+?)(?:\s+that|\s+to|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                contact = match.group(1).strip()
                if "contact" not in entities:
                    entities["contact"] = contact
                break
                
        # Extract message content
        msg_patterns = [
            r"(?:saying|that)\s+[\"']?(.+?)[\"']?$",
            r"message\s*[:\s][\"']?(.+?)[\"']?$",
        ]
        
        for pattern in msg_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities["message"] = match.group(1).strip()
                break
                
        return entities
        
    def _extract_youtube(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract YouTube search query"""
        entities = {"app": "youtube"}
        
        # Reuse music extraction for the query
        music_entities = self._extract_music(text, doc)
        if "song" in music_entities:
            entities["query"] = music_entities["song"]
        if "artist" in music_entities:
            entities["artist"] = music_entities["artist"]
            
        # Add query if not from music
        if "query" not in entities:
            text_lower = text.lower()
            query = re.sub(
                r"^(play|open|find|search|watch)\s+(?:on\s+youtube\s+)?",
                "",
                text_lower
            ).strip()
            query = re.sub(r"\s+on\s+youtube$", "", query)
            if query:
                entities["query"] = query
                
        return entities
        
    def _extract_amount(self, text: str) -> Dict[str, Any]:
        """Extract numeric amount"""
        entities = {}
        
        # Look for percentage or number
        match = re.search(r"(\d+)\s*%?", text)
        if match:
            entities["amount"] = int(match.group(1))
        else:
            # Verbal amounts
            verbal = {
                "a bit": 10, "a little": 10,
                "a lot": 30, "much": 30,
                "half": 50, "max": 100, "full": 100,
                "minimum": 10, "maximum": 100,
            }
            for word, amount in verbal.items():
                if word in text.lower():
                    entities["amount"] = amount
                    break
            else:
                entities["amount"] = 10  # Default step
                
        return entities
        
    def _extract_event(self, text: str, doc=None) -> Dict[str, Any]:
        """Extract calendar event details"""
        entities = {}
        text_lower = text.lower()
        
        # Event title
        title_patterns = [
            r"(?:create|add|schedule)\s+(?:a\s+)?(?:meeting|event|appointment)\s+(?:called|named|for)?\s*(.+?)(?:\s+at|\s+on|\s+for|$)",
            r"(?:meeting|event|appointment)\s+(?:with|about)\s+(.+?)(?:\s+at|\s+on|$)",
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities["title"] = match.group(1).strip().title()
                break
                
        # Extract time
        time_entities = self._extract_time(text, doc)
        entities.update(time_entities)
        
        # Use spaCy for additional entities
        if doc:
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    entities["date_raw"] = ent.text
                elif ent.label_ == "PERSON":
                    if "attendee" not in entities:
                        entities["attendee"] = ent.text
                        
        return entities


# Singleton
_extractor = None

def get_entity_extractor() -> EntityExtractor:
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def extract_entities(text: str, intent: str) -> Dict[str, Any]:
    """Convenience function"""
    return get_entity_extractor().extract(text, intent)
