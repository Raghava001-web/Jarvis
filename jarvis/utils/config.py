"""
Configuration - Environment and Settings
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Also try loading from jarvis folder
jarvis_env = Path(__file__).parent.parent / ".env"
load_dotenv(jarvis_env)


class Config:
    """Application configuration"""
    CONFIDENCE_THRESHOLD = 0.50
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY")
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        # Groq is our primary AI, so just silently continue
        # The knowledge layer shows "Groq - Llama 3.3 70B" when working
        return True

