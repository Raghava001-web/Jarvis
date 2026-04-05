"""
Story Sources - Fetch stories from the web
Sources from public domain and open-source story repositories
"""

import random
import requests
from typing import Optional, Dict, List


class WebStoryFetcher:
    """Fetches stories from public web sources"""
    
    def __init__(self):
        print("[STORY] Initializing Web Story Fetcher...")
        
        # Free story APIs and sources
        self.sources = {
            "tales": "https://shortstories-api.onrender.com/stories",
            "random": "https://shortstories-api.onrender.com/stories/random"
        }
        
        # Fallback stories for when web is unavailable
        self.fallback_stories = {
            "bedtime": [
                """Once upon a time, in a forest where the trees whispered secrets to the wind, 
                there lived a little rabbit named Luna. [PAUSE] Every night, she would watch 
                the stars appear one by one, counting them until her eyes grew heavy. [PAUSE]
                The moon would shine a gentle light on her burrow, and the fireflies would 
                dance a lullaby. [EFFECT] "Goodnight, little dreamers," the wind would say, 
                and Luna would drift into peaceful slumber, dreaming of meadows and sunshine.""",
                
                """In a cozy cottage by the sea, an old lighthouse keeper told stories to the waves.
                [PAUSE] Each wave would listen carefully, then carry the story across the ocean.
                [PAUSE] Ships far away would hear the whispers and smile, knowing they were not alone.
                [EFFECT] And so, every night, the lighthouse became a beacon of dreams."""
            ],
            "adventure": [
                """Captain Aria stood at the helm of her ship, the Starbound, as it cut through 
                the stormy seas. [EFFECT] "All hands on deck!" she commanded. [PAUSE]
                The crew had heard legends of the Golden Isle, where treasures beyond imagination 
                awaited the brave. [EFFECT] Lightning cracked across the sky as they pushed forward.
                [PAUSE] After three days, the clouds parted, revealing the mythical island.
                "We made it," Aria whispered, her eyes gleaming with triumph.""",
            ],
            "horror": [
                """The old mansion had been empty for thirty years. [PAUSE] But tonight, 
                someone was watching from the window. [EFFECT] Sarah's flashlight flickered 
                as she pushed open the creaking door. [PAUSE] "Hello?" she called into the darkness. 
                [EFFECT] Something moved in the shadows. [PAUSE] The temperature dropped suddenly. 
                Behind her, a voice whispered: "You shouldn't have come here..." [EFFECT]""",
            ],
            "comedy": [
                """Dave the dragon had a problem - he couldn't breathe fire. [PAUSE] Instead, 
                he sneezed confetti. [EFFECT] "Achoo!" Colorful paper erupted from his nostrils 
                at the worst times. [PAUSE] During the dragon's annual fire-breathing competition, 
                Dave stepped up nervously. [PAUSE] He took a deep breath and... [EFFECT]
                The whole arena was covered in sparkly confetti! The judges laughed so hard, 
                they gave him first place for "Most Entertaining Performance." [EFFECT]"""
            ]
        }
        
        print("[STORY] Story Fetcher Ready")
    
    def fetch_random_story(self) -> Optional[Dict]:
        """Fetch a random story from the web"""
        try:
            response = requests.get(
                self.sources["random"],
                timeout=5,
                headers={"User-Agent": "JARVIS/1.0"}
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", "A Story"),
                    "story": data.get("story", ""),
                    "author": data.get("author", "Unknown"),
                    "genre": self._detect_genre(data.get("story", ""))
                }
        except Exception as e:
            print(f"[STORY] Web fetch error: {e}")
        
        return None
    
    def fetch_story_by_genre(self, genre: str) -> Optional[str]:
        """Fetch a story by genre, with fallback to local stories"""
        
        # Try web first
        web_story = self.fetch_random_story()
        if web_story and web_story.get("story"):
            # Add story markers for sound effects
            return self._add_story_markers(web_story["story"], genre)
        
        # Fallback to local stories
        genre_lower = genre.lower()
        if genre_lower in self.fallback_stories:
            return random.choice(self.fallback_stories[genre_lower])
        
        # Default to bedtime
        return random.choice(self.fallback_stories["bedtime"])
    
    def _detect_genre(self, story: str) -> str:
        """Detect story genre from content"""
        story_lower = story.lower()
        
        if any(word in story_lower for word in ["scary", "dark", "ghost", "shadow", "fear"]):
            return "horror"
        elif any(word in story_lower for word in ["laugh", "funny", "joke", "silly"]):
            return "comedy"
        elif any(word in story_lower for word in ["adventure", "quest", "battle", "hero"]):
            return "adventure"
        elif any(word in story_lower for word in ["night", "sleep", "dream", "star"]):
            return "bedtime"
        
        return "bedtime"
    
    def _add_story_markers(self, story: str, genre: str) -> str:
        """Add [PAUSE] and [EFFECT] markers to a plain story"""
        
        # Split into sentences
        sentences = story.replace(".", ".|").replace("!", "!|").replace("?", "?|").split("|")
        sentences = [s.strip() for s in sentences if s.strip()]
        
        marked_story = []
        effect_frequency = {
            "horror": 4,    # Effect every 4 sentences
            "comedy": 5,
            "adventure": 3,
            "bedtime": 6
        }.get(genre.lower(), 5)
        
        for i, sentence in enumerate(sentences):
            marked_story.append(sentence)
            
            # Add pause every 2-3 sentences
            if i > 0 and i % 2 == 0:
                marked_story.append(" [PAUSE] ")
            
            # Add effect periodically
            if i > 0 and i % effect_frequency == 0:
                marked_story.append(" [EFFECT] ")
        
        return " ".join(marked_story)


# Singleton instance
_fetcher = None

def get_story_fetcher() -> WebStoryFetcher:
    """Get or create story fetcher instance"""
    global _fetcher
    if _fetcher is None:
        _fetcher = WebStoryFetcher()
    return _fetcher
