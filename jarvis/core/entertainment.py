"""
Entertainment Module - Singing, Storytelling, Poems, Jokes
JARVIS entertains and comforts you
"""

import random
from typing import Optional
from enum import Enum


class EntertainmentType(Enum):
    """Types of entertainment"""
    SONG = "song"
    STORY = "story"
    JOKE = "joke"
    POEM = "poem"
    RIDDLE = "riddle"


class JARVISEntertainment:
    """Entertainment capabilities for JARVIS"""
    
    def __init__(self, perception=None, knowledge=None):
        print("[ENTERTAINMENT] Initializing Entertainment Module...")
        self.perception = perception
        self.knowledge = knowledge
        
        # Lazy-load storyteller on first use (prevents init hang from pygame.mixer)
        self._storyteller = None
        self._storyteller_available = True
        
        # Built-in content
        self._init_builtin_content()
        
        print("[ENTERTAINMENT] Entertainment Module Ready")
    
    @property
    def storyteller(self):
        """Lazy-load ImmersiveStoryteller on first use"""
        if self._storyteller is None and self._storyteller_available:
            try:
                from .sound_effects import ImmersiveStoryteller
                self._storyteller = ImmersiveStoryteller(self.perception, self.knowledge)
            except Exception as e:
                print(f"[ENTERTAINMENT] Immersive storytelling not available: {e}")
                self._storyteller_available = False
        return self._storyteller
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[ENTERTAINMENT] {text}")
    
    def _init_builtin_content(self):
        """Initialize built-in songs, poems, etc."""
        
        self.songs = {
            "happy birthday": "Happy birthday to you, Happy birthday to you, Happy birthday dear friend, Happy birthday to you!",
            "twinkle twinkle": "Twinkle, twinkle, little star, How I wonder what you are! Up above the world so high, Like a diamond in the sky.",
            "national anthem": "Jana Gana Mana Adhinayaka Jaya He, Bharata Bhagya Vidhata, Punjab Sindh Gujarat Maratha, Dravida Utkala Banga, Vindhya Himachala Yamuna Ganga, Uchchala Jaladhi Taranga, Tava Shubha Name Jage, Tava Shubha Ashish Maage, Gahe Tava Jaya Gatha, Jana Gana Mangala Dayaka Jaya He, Bharata Bhagya Vidhata, Jaya He, Jaya He, Jaya He, Jaya Jaya Jaya, Jaya He!",
            "abc": "A B C D E F G, H I J K L M N O P, Q R S T U V, W X Y and Z, Now I know my ABCs, Next time won't you sing with me?"
        }
        
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "Why did the developer go broke? Because he used up all his cache.",
            "A SQL query walks into a bar and asks: Can I join you?",
            "There are 10 types of people: those who understand binary and those who don't.",
            "Why do Java developers wear glasses? Because they don't C sharp.",
            "What's a programmer's favorite hangout place? Foo Bar.",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "A programmer's wife tells him: Go to the store and get a loaf of bread. If they have eggs, get a dozen. He returns with 12 loaves of bread.",
            "Why do Python programmers have low self-esteem? They're constantly told they have significant whitespace issues.",
            "What's a computer's least favorite food? Spam.",
            "Why did the programmer quit his job? Because he didn't get arrays.",
            "There's no place like 127.0.0.1.",
            "Why do programmers always mix up Halloween and Christmas? Because Oct 31 equals Dec 25.",
            "What do you call 8 hobbits? A hobbyte.",
            "Why do programmers hate nature? It has too many bugs.",
            "I would tell you a UDP joke, but you might not get it.",
            "A TCP packet walks into a bar and says, 'I'd like a beer.' The bartender replies, 'You want a beer?' The TCP packet says, 'Yes, I want a beer.'",
            "Why do Java programmers have to wear glasses? Because they don't C#.",
            "An SQL statement walks into a bar and sees two tables. It approaches and asks, 'May I join you?'"
        ]
        self.joke_index = 0
        
        self.poems = {
            "default": "In circuits deep and code so bright, I serve you through the day and night. Your loyal JARVIS, ever here, To help you conquer every fear.",
            "morning": "The sun rises on a brand new day, New opportunities come your way. With courage in your heart so true, There's nothing that you cannot do.",
            "night": "The stars are out, the moon shines bright, It's time to rest, to say goodnight. Tomorrow brings another start, But now, let peace fill your heart."
        }
        
        self.riddles = [
            ("What has keys but no locks?", "A keyboard."),
            ("What has a head and a tail but no body?", "A coin."),
            ("What can travel around the world while staying in a corner?", "A stamp."),
            ("What has hands but can't clap?", "A clock."),
            ("What building has the most stories?", "A library."),
        ]
    
    def sing_song(self, song_request: str = None) -> str:
        """Sing a song - returns lyrics string"""
        title = self._get_title()
        
        if song_request:
            song_lower = song_request.lower()
            for song_name, lyrics in self.songs.items():
                if song_name in song_lower or song_lower in song_name:
                    return f"Singing {song_name} for you, {title}. {lyrics}"
            
            if self.knowledge:
                prompt = f"Compose a short 4-line song about {song_request}. Just the lyrics, keep it simple and melodic."
                lyrics = self.knowledge.answer_question(prompt)
                if lyrics:
                    return f"Let me compose something for you, {title}. {lyrics}"
        
        song_name = random.choice(list(self.songs.keys()))
        return f"How about {song_name}, {title}? {self.songs[song_name]}"
    
    def tell_story(self, theme: str = None, genre: str = "bedtime") -> str:
        """Tell a story with immersive narration via Groq AI"""
        title = self._get_title()
        
        if self.storyteller:
            self.storyteller.tell_story(theme or "adventure and friendship", genre)
            return f"I hope you enjoyed that {genre} story, {title}."
        
        if self.knowledge:
            prompt = f"""Tell a {genre} story about {theme or 'adventure'}. 
            Keep it 2-3 paragraphs. Use vivid, dramatic descriptions.
            Vary the tone: suspenseful moments use short tense sentences,
            happy moments use warm flowing language, jokes pause before punchlines.
            Make it cinematic like a movie narrator.
            Genre: comedy=funny, horror=suspenseful, bedtime=calming, adventure=heroic."""
            
            story = self.knowledge.answer_question(prompt)
            if story:
                return f"Let me tell you a {genre} story, {title}. {story}"
        
        return f"I apologize {title}, my storytelling systems are offline."
    
    def tell_joke(self) -> str:
        """Generate a unique joke using AI"""
        if self.knowledge:
            try:
                prompt = """Tell me ONE funny joke. Be creative and original.
                Tech humor, wordplay, or observational comedy.
                Keep it short (1-3 sentences). Just the joke, no intro."""
                joke = self.knowledge.answer_question(prompt)
                if joke and len(joke) > 10:
                    return joke
            except Exception as e:
                print(f"[ENTERTAINMENT] Joke generation error: {e}")
        
        if self.joke_index >= len(self.jokes):
            random.shuffle(self.jokes)
            self.joke_index = 0
        joke = self.jokes[self.joke_index]
        self.joke_index += 1
        return joke
    
    def recite_poem(self, theme: str = None) -> str:
        """Recite a poem"""
        if theme:
            if theme.lower() in self.poems:
                return self.poems[theme.lower()]
            if self.knowledge:
                prompt = f"Write a short 4-line poem about {theme}. Make it thoughtful and meaningful."
                poem = self.knowledge.answer_question(prompt)
                if poem:
                    return poem
        return self.poems["default"]
    
    def tell_riddle(self) -> str:
        """Tell a riddle"""
        title = self._get_title()
        riddle, answer = random.choice(self.riddles)
        return f"Here's a riddle, {title}. {riddle} Think about it... The answer is: {answer}"
    
    def make_laugh(self) -> str:
        """Make the user laugh"""
        return self.tell_joke()
    
    def entertain(self, request: str) -> str:
        """Handle general entertainment requests"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["sing", "song"]):
            song = None
            for keyword in ["sing", "song"]:
                if keyword in request_lower:
                    parts = request_lower.split(f" {keyword} ")
                    if len(parts) > 1 and parts[1].strip():
                        song = parts[1].strip()
            return self.sing_song(song)
        
        elif any(word in request_lower for word in ["story", "tale"]):
            genre = "bedtime"
            theme = None
            for g, kws in [("comedy", ["comedy","funny"]), ("horror", ["horror","scary"]),
                           ("adventure", ["adventure"]), ("romance", ["romance","love"]),
                           ("fantasy", ["fantasy","magic"])]:
                if any(k in request_lower for k in kws):
                    genre = g
                    break
            for keyword in ["about", "story about"]:
                if keyword in request_lower:
                    parts = request_lower.split(f" {keyword} ")
                    if len(parts) > 1:
                        theme = parts[1].strip()
            return self.tell_story(theme, genre)
        
        elif any(word in request_lower for word in ["joke", "laugh", "funny"]):
            return self.tell_joke()
        
        elif any(word in request_lower for word in ["poem", "poetry"]):
            theme = None
            for keyword in ["about", "poem about"]:
                if keyword in request_lower:
                    parts = request_lower.split(f" {keyword} ")
                    if len(parts) > 1:
                        theme = parts[1].strip()
            return self.recite_poem(theme)
        
        elif "riddle" in request_lower:
            return self.tell_riddle()
        
        return self.tell_joke()


# Alias for backward compatibility
EntertainmentEngine = JARVISEntertainment
