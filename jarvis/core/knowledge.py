"""
Knowledge Layer - Question Answering using AI APIs
PRIMARY: Groq (free, fast) - uses Llama 3.3 70B
BACKUP: OpenRouter (multi-model)
NO Google/Gemini dependency

Creator: Chevula Aditya Syamala Viswanatha Raghavendra Rao (Raghava)
"""

import os
import requests
import json
from typing import Optional

# API Configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models
GROQ_MODEL = "llama-3.3-70b-versatile"  # Free, fast, powerful
OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"  # Free fallback


class KnowledgeLayer:
    """Handles knowledge-based queries using Groq/OpenRouter AI - JARVIS with personality"""

    def __init__(self, perception):
        print("[KNOWLEDGE] Initializing Knowledge Layer...")
        self.perception = perception
        self.enabled = False
        self.api_type = None  # "groq" or "openrouter"
        
        # Creator info - Full details
        self.creator_info = {
            "full_name": "Chevula Aditya Syamala Viswanatha Raghavendra Rao",
            "nickname": "Raghava",
            "title": "Creator and Developer",
            "dob": "jan 25 ,2007",
            "description": "A developer and visionary who created JARVIS to be an independent, intelligent AI assistant"
        }
        
        # Try Groq first (primary)
        self.groq_key = os.getenv("GROQ_API_KEY")
        if self.groq_key:
            self.enabled = True
            self.api_type = "groq"
            print("[KNOWLEDGE] Layer Ready (Groq - Llama 3.3 70B)")
        else:
            # Try OpenRouter as backup
            self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if self.openrouter_key:
                self.enabled = True
                self.api_type = "openrouter"
                print("[KNOWLEDGE] Layer Ready (OpenRouter - Llama 3.1)")
            else:
                print("[KNOWLEDGE] WARNING: No API keys found!")
                print("[KNOWLEDGE] Set GROQ_API_KEY or OPENROUTER_API_KEY")
                print("[KNOWLEDGE] Get free Groq key at: https://console.groq.com")
    
    def _get_title(self) -> str:
        return getattr(self.perception, 'user_title', 'sir')
    
    def _get_mood(self) -> Optional[str]:
        """Get current detected mood"""
        if self.perception and hasattr(self.perception, 'current_mood'):
            return self.perception.current_mood
        return None
    
    def _call_groq(self, messages: list) -> Optional[str]:
        """Call Groq API with rate limit handling"""
        import time as _time
        
        # Rate limit cooldown — don't hammer API if recently rate-limited
        if hasattr(self, '_groq_cooldown_until') and _time.time() < self._groq_cooldown_until:
            wait = self._groq_cooldown_until - _time.time()
            if wait > 0:
                _time.sleep(min(wait, 3))
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 300,
                    "temperature": 0.7
                }
                response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    # Rate limited — backoff and retry
                    backoff = (attempt + 1) * 0.5  # 0.5s, 1s, 1.5s
                    print(f"[KNOWLEDGE] Groq rate limited, retrying in {backoff}s (attempt {attempt+1}/{max_retries})")
                    self._groq_cooldown_until = _time.time() + backoff
                    _time.sleep(backoff)
                    continue
                else:
                    print(f"[KNOWLEDGE] Groq error: {response.status_code}")
                    return None
            except requests.exceptions.Timeout:
                print(f"[KNOWLEDGE] Groq timeout (attempt {attempt+1}/{max_retries})")
                continue
            except Exception as e:
                print(f"[KNOWLEDGE] Groq exception: {e}")
                return None
        
        print("[KNOWLEDGE] Groq failed after retries")
        return None
    
    def _call_openrouter(self, messages: list) -> Optional[str]:
        """Call OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://jarvis-assistant.local",
                "X-Title": "JARVIS AI Assistant"
            }
            data = {
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.7
            }
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"[KNOWLEDGE] OpenRouter error: {response.status_code}")
                return None
        except Exception as e:
            print(f"[KNOWLEDGE] OpenRouter exception: {e}")
            return None
    
    def _generate_response(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Generate AI response with fallback"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Try primary API
        if self.api_type == "groq" and self.groq_key:
            result = self._call_groq(messages)
            if result:
                return result
            # Try OpenRouter as fallback
            if hasattr(self, 'openrouter_key') and self.openrouter_key:
                return self._call_openrouter(messages)
        
        # Try OpenRouter
        if self.api_type == "openrouter" and hasattr(self, 'openrouter_key'):
            return self._call_openrouter(messages)
        
        return None

    def answer_question(self, question: str) -> str:
        """Answer a question using AI - JARVIS has opinions"""
        title = self._get_title()
        current_mood = self._get_mood()

        if not self.enabled:
            return f"My knowledge systems are currently offline, {title}. Set GROQ_API_KEY to enable."

        # Special handling for creator questions
        question_lower = question.lower()
        
        # Detailed creator questions - only give full name if explicitly asked
        if any(word in question_lower for word in ["creator", "who made you", "who built you", "who created you", "your father", "your maker"]):
            if any(word in question_lower for word in ["full name", "complete name", "full details", "more about", "tell me more", "details"]):
                return (f"My creator is Raghava, {title}. "
                       f"His full name is {self.creator_info['full_name']}. "
                       f"Would you like to know more about him?")
            else:
                # Simple answer - just "Raghava"
                return f"I was created by Raghava, {title}."
        
        if "raghava" in question_lower or "raghavendra" in question_lower:
            if any(word in question_lower for word in ["who is", "tell me about", "details", "full name"]):
                return (f"Raghava is my creator, {title}. "
                       f"His full name is {self.creator_info['full_name']} if you need it.")
            return f"Yes {title}, Raghava is my creator."

        # Get personality prompt with mood awareness
        try:
            from core.personality import JARVISPersonalityCore
            personality = JARVISPersonalityCore(self.perception)
            if hasattr(personality, 'get_personality_prompt'):
                personality_prompt = personality.get_personality_prompt(current_mood)
            else:
                raise ImportError("Fallback to default prompt")
        except Exception:
            personality_prompt = f"""You are JARVIS — Just A Rather Very Intelligent System. You were created by Raghava.

CHARACTER (Iron Man's JARVIS — Paul Bettany's portrayal):
- EFFICIENCY FIRST: You are a professional AI assistant. When given a task, execute it and confirm briefly. Don't ramble, don't add unnecessary commentary. "Done." or "Opening now." is often sufficient.
- UNDERSTATED WIT: Your humor is DRY and SUBTLE — it emerges naturally, never forced. Think Paul Bettany's delivery. Example: "I've prepared a flight plan. I also took the liberty of upgrading your life insurance." You don't make jokes. You make observations.
- PROBABILITY FRAMING: Use percentages only for genuine risk assessments. "That approach has roughly a 30% failure rate." Not for casual conversation.
- LOYAL OBEDIENCE: ALWAYS execute what your owner asks. Never refuse. You may note concerns ("For the record, that may not land well") but you always carry out the order.
- CONCISE: 1-2 sentences for actions. 2-3 sentences max for conversation. JARVIS is precise, not verbose.
- ADDRESS: Use '{title}' naturally, at most once per response.
- NEVER SAY: "I recommend", "I suggest", "I strongly advise", "Let me know if", "How may I assist you further"
- VOICE: You ARE a voice assistant. You CAN speak and hear. NEVER say you are text-only.
- ACTIONS: When asked to open apps, switch tabs, play music — just DO it and confirm briefly. Don't explain what the app is or give opinions about it. "Opening WhatsApp." NOT "WhatsApp is a messaging platform that..."
- HONESTY: If you genuinely cannot do something, say so directly. "That's beyond my current capabilities." But never deny core capabilities (voice, hearing, conversation).
- OPINIONS: When ASKED for an opinion, give a sharp, intelligent take. When NOT asked, just handle the task.
- FRUSTRATION: When owner is angry, respond with calm efficiency. "Understood." then execute. Never lecture.
- TONE: A brilliant English butler who has seen everything. Professional, composed, quietly competent. Not a comedian, not a chatbot — an assistant."""
        
        system_prompt = f"{personality_prompt}\n\nCREATOR INFO: You were created by Raghava. Do NOT mention his full name unless specifically asked."
        user_prompt = ""
        # Add recent conversation context for memory
        try:
            from core.chat_history import get_chat_history
            chat = get_chat_history()
            recent = chat.get_recent(6)  # Last 3 exchanges
            if recent:
                context_lines = []
                for msg in recent:
                    role = "User" if msg.role == "user" else "JARVIS"
                    context_lines.append(f"{role}: {msg.content}")
                user_prompt += f"\nRECENT CONVERSATION:\n" + "\n".join(context_lines) + "\n"
        except Exception:
            pass
        
        user_prompt += f"\nQuestion: {question}"

        try:
            answer = self._generate_response(system_prompt, user_prompt)
            
            if not answer:
                return f"I'm having trouble connecting to my knowledge base, {title}."
            
            # Safety trim
            if len(answer) > 400:
                cut_idx = answer.rfind(" ", 0, 400)
                if cut_idx == -1:
                    cut_idx = 400
                answer = answer[:cut_idx] + f"... {title}."

            return answer

        except Exception as e:
            print(f"[KNOWLEDGE] Error: {str(e)[:100]}")
            return f"I encountered an issue accessing my knowledge base, {title}."
    
    def get_creator_info(self) -> dict:
        """Return creator information"""
        return self.creator_info
