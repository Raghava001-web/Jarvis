"""
Dictionary Handler - Word definitions with spell correction
Intelligent dictionary with fuzzy matching
"""

import json
from pathlib import Path
from typing import Optional, List, Dict
from difflib import get_close_matches


class DictionaryHandler:
    """Handles word definitions with intelligent spell correction"""
    
    def __init__(self, perception=None):
        print("[DICTIONARY] Initializing Dictionary Handler...")
        self.perception = perception
        
        # Dictionary data path
        self.dict_path = Path(__file__).parent.parent / "data" / "dictionary.json"
        
        # Load dictionary
        self.dictionary = self._load_dictionary()
        
        print(f"[DICTIONARY] Loaded {len(self.dictionary)} words")
        print("[DICTIONARY] Dictionary Handler Ready")
    
    def _get_title(self) -> str:
        """Get user title from perception layer"""
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        """Speak text via perception layer"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[DICTIONARY] {text}")
    
    def _load_dictionary(self) -> Dict:
        """Load dictionary from file or use built-in"""
        try:
            if self.dict_path.exists():
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[DICTIONARY] Could not load dictionary: {e}")
        
        # Built-in mini dictionary
        return {
            "algorithm": "A step-by-step procedure for solving a problem or accomplishing a task.",
            "python": "A high-level programming language known for its simplicity and readability.",
            "jarvis": "Just A Rather Very Intelligent System - your personal AI assistant.",
            "artificial intelligence": "The simulation of human intelligence by machines.",
            "machine learning": "A type of AI that allows systems to learn from data.",
            "neural network": "A computing system inspired by biological neural networks.",
            "debugging": "The process of finding and fixing errors in code.",
            "recursion": "A programming technique where a function calls itself.",
            "api": "Application Programming Interface - a way for programs to communicate.",
            "database": "An organized collection of data stored electronically.",
            "variable": "A named storage location in a program that holds a value.",
            "function": "A reusable block of code that performs a specific task.",
            "loop": "A programming construct that repeats a block of code.",
            "array": "A data structure that stores a collection of elements.",
            "object": "An instance of a class containing data and methods.",
            "class": "A blueprint for creating objects with specific attributes and methods.",
            "inheritance": "A mechanism where a class inherits properties from another class.",
            "polymorphism": "The ability of objects to take on many forms.",
            "encapsulation": "The bundling of data and methods that operate on that data.",
            "abstraction": "Hiding complex implementation details behind a simple interface."
        }
    
    def define_word(self, word: str) -> bool:
        """Look up a word definition with spell correction"""
        title = self._get_title()
        word = word.lower().strip()
        
        # Direct match
        if word in self.dictionary:
            definition = self.dictionary[word]
            self._speak(f"{word.capitalize()}: {definition}")
            return True
        
        # Fuzzy match - find similar words
        close_matches = get_close_matches(word, self.dictionary.keys(), n=3, cutoff=0.6)
        
        if close_matches:
            # Ask if they meant a similar word
            best_match = close_matches[0]
            self._speak(f"I couldn't find '{word}'. Did you mean '{best_match}'?")
            
            # If using perception layer, we could wait for confirmation
            # For now, just provide the closest match
            if len(close_matches) == 1:
                definition = self.dictionary[best_match]
                self._speak(f"{best_match.capitalize()}: {definition}")
                return True
            else:
                alternatives = ", ".join(close_matches)
                self._speak(f"Similar words I found: {alternatives}")
                return True
        
        # Try online dictionary as fallback
        online_def = self._lookup_online(word)
        if online_def:
            self._speak(f"{word.capitalize()}: {online_def}")
            # Cache for future use
            self.dictionary[word] = online_def
            self._save_dictionary()
            return True
        
        self._speak(f"I couldn't find a definition for '{word}', {title}. Please check the spelling.")
        return False
    
    def _lookup_online(self, word: str) -> Optional[str]:
        """Try to look up word online using free dictionary API"""
        try:
            import requests
            
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    meanings = data[0].get("meanings", [])
                    if meanings:
                        definitions = meanings[0].get("definitions", [])
                        if definitions:
                            return definitions[0].get("definition", "")
        except Exception as e:
            print(f"[DICTIONARY] Online lookup error: {e}")
        
        return None
    
    def _save_dictionary(self):
        """Save updated dictionary to file"""
        try:
            self.dict_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dict_path, 'w', encoding='utf-8') as f:
                json.dump(self.dictionary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DICTIONARY] Could not save dictionary: {e}")
    
    def add_word(self, word: str, definition: str) -> bool:
        """Add a new word to the dictionary"""
        title = self._get_title()
        word = word.lower().strip()
        
        self.dictionary[word] = definition
        self._save_dictionary()
        
        self._speak(f"I've added '{word}' to my dictionary, {title}.")
        return True
    
    def synonym(self, word: str) -> bool:
        """Find synonyms for a word"""
        title = self._get_title()
        
        try:
            import requests
            
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    meanings = data[0].get("meanings", [])
                    all_synonyms = []
                    
                    for meaning in meanings:
                        synonyms = meaning.get("synonyms", [])
                        all_synonyms.extend(synonyms[:3])  # Take top 3 from each
                    
                    if all_synonyms:
                        synonym_list = ", ".join(all_synonyms[:5])
                        self._speak(f"Synonyms for {word}: {synonym_list}")
                        return True
        except Exception as e:
            print(f"[DICTIONARY] Synonym lookup error: {e}")
        
        self._speak(f"I couldn't find synonyms for '{word}', {title}.")
        return False
    
    def spell_check(self, text: str) -> List[str]:
        """Check spelling and return suggestions for misspelled words"""
        words = text.lower().split()
        corrections = []
        
        for word in words:
            # Skip short words and numbers
            if len(word) < 3 or word.isdigit():
                continue
            
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalpha())
            
            if clean_word and clean_word not in self.dictionary:
                matches = get_close_matches(clean_word, self.dictionary.keys(), n=1, cutoff=0.8)
                if matches:
                    corrections.append((clean_word, matches[0]))
        
        return corrections
