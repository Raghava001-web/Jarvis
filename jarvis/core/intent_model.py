"""
Intent Model - Embedding-Based Classification (v2)
===================================================
Uses sentence-transformers with:
- kNN + threshold for better accuracy
- Ambiguity detection
- Lazy loading for fast startup
- Domain weighting
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Union
import json

from .intent_definitions import INTENT_EXAMPLES, get_category

# Try to import sentence-transformers (lazy loaded)
EMBEDDINGS_AVAILABLE = False
_ST_MODEL = None

def _get_model():
    """Lazy load sentence-transformers model"""
    global EMBEDDINGS_AVAILABLE, _ST_MODEL
    if _ST_MODEL is not None:
        return _ST_MODEL
        
    try:
        from sentence_transformers import SentenceTransformer
        EMBEDDINGS_AVAILABLE = True
        _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _ST_MODEL
    except ImportError:
        print("[INTENT] sentence-transformers not installed")
        return None


class IntentClassification:
    """Result of intent classification"""
    def __init__(self, intent: str, confidence: float, 
                 is_ambiguous: bool = False, alternatives: List[Tuple[str, float]] = None):
        self.intent = intent
        self.confidence = confidence
        self.is_ambiguous = is_ambiguous
        self.alternatives = alternatives or []
        
    def __repr__(self):
        return f"Intent({self.intent}, {self.confidence:.2f}, ambig={self.is_ambiguous})"


class IntentModel:
    """
    Embedding-based intent classifier with:
    - kNN scoring (not just centroid)
    - Ambiguity detection
    - Confidence thresholds
    - Domain weighting
    - Lazy loading
    """
    
    # Thresholds
    CONFIDENCE_THRESHOLD = 0.55      # Below this = unknown
    AMBIGUITY_MARGIN = 0.08          # If top two within this = ambiguous
    HIGH_CONFIDENCE = 0.75           # Above this = very confident
    
    # Domain weights (some intents are more common)
    DOMAIN_WEIGHTS = {
        "open_app": 1.15,       # Boost app opening
        "play_music": 1.10,
        "search_web": 1.05,
        "greeting": 0.95,      # Slightly lower (less action-oriented)
        "goodbye": 0.95,
    }
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", lazy: bool = True):
        print("[INTENT] Initializing Intent Model...")
        
        self.model_name = model_name
        self.model = None
        self.intent_embeddings: Dict[str, np.ndarray] = {}
        self.example_embeddings: Dict[str, List[np.ndarray]] = {}  # For kNN
        self.cache_path = Path(__file__).parent.parent / "data" / "intent_embeddings_v2.npz"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._loaded = False
        
        if not lazy:
            self._ensure_loaded()
            
        print("[INTENT] Intent Model Ready (lazy mode)")
        
    def _ensure_loaded(self):
        """Ensure model and embeddings are loaded"""
        if self._loaded:
            return True
            
        self.model = _get_model()
        
        if self.model:
            if not self._load_cache():
                self._compute_embeddings()
            self._loaded = True
            return True
            
        return False
        
    def _compute_embeddings(self):
        """Compute embeddings for all intents"""
        print("[INTENT] Computing intent embeddings...")
        
        for intent, examples in INTENT_EXAMPLES.items():
            # Store all example embeddings for kNN
            embeddings = self.model.encode(examples)
            self.example_embeddings[intent] = list(embeddings)
            
            # Also store centroid for fast initial screening
            self.intent_embeddings[intent] = np.mean(embeddings, axis=0)
            
        self._save_cache()
        print(f"[INTENT] Computed {len(self.intent_embeddings)} intent embeddings")
        
    def _load_cache(self) -> bool:
        """Load cached embeddings"""
        try:
            if self.cache_path.exists():
                data = np.load(str(self.cache_path), allow_pickle=True)
                self.intent_embeddings = dict(data['centroids'].item())
                self.example_embeddings = dict(data['examples'].item())
                
                if len(self.intent_embeddings) == len(INTENT_EXAMPLES):
                    print("[INTENT] Loaded cached embeddings")
                    return True
        except:
            pass
        return False
        
    def _save_cache(self):
        """Save embeddings to cache"""
        try:
            np.savez(
                str(self.cache_path), 
                centroids=self.intent_embeddings,
                examples=self.example_embeddings
            )
        except Exception as e:
            print(f"[INTENT] Cache save error: {e}")
            
    def embed(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text"""
        self._ensure_loaded()
        if self.model:
            return self.model.encode(text)
        return None
        
    def classify(self, text: str) -> Tuple[Optional[str], float]:
        """
        Classify intent from text.
        Returns (intent, confidence) or (None, confidence) if below threshold.
        For ambiguous cases, returns ("AMBIGUOUS", confidence).
        """
        if not self._ensure_loaded():
            return self._classify_keyword(text)
            
        # Get all scores
        scores = self._score_all_intents(text)
        
        if not scores:
            return None, 0.0
            
        # Sort by score
        scores.sort(key=lambda x: -x[1])
        
        top_intent, top_score = scores[0]
        second_intent, second_score = scores[1] if len(scores) > 1 else (None, 0)
        
        # Apply domain weight
        top_score_weighted = top_score * self.DOMAIN_WEIGHTS.get(top_intent, 1.0)
        
        # Check thresholds
        if top_score < self.CONFIDENCE_THRESHOLD:
            return None, top_score
            
        # Check for ambiguity
        if len(scores) > 1:
            margin = top_score - second_score
            if margin < self.AMBIGUITY_MARGIN and second_score > self.CONFIDENCE_THRESHOLD:
                # Ambiguous - top two are too close
                return "AMBIGUOUS", top_score
                
        return top_intent, top_score_weighted
        
    def classify_detailed(self, text: str) -> IntentClassification:
        """Get detailed classification with alternatives"""
        if not self._ensure_loaded():
            intent, conf = self._classify_keyword(text)
            return IntentClassification(intent, conf)
            
        scores = self._score_all_intents(text)
        scores.sort(key=lambda x: -x[1])
        
        if not scores:
            return IntentClassification(None, 0.0)
            
        top_intent, top_score = scores[0]
        
        # Check for ambiguity
        is_ambiguous = False
        if len(scores) > 1:
            margin = top_score - scores[1][1]
            is_ambiguous = margin < self.AMBIGUITY_MARGIN and scores[1][1] > self.CONFIDENCE_THRESHOLD
            
        # Get alternatives
        alternatives = scores[1:4]  # Top 3 alternatives
        
        if top_score < self.CONFIDENCE_THRESHOLD:
            return IntentClassification(None, top_score, is_ambiguous, alternatives)
            
        return IntentClassification(top_intent, top_score, is_ambiguous, alternatives)
        
    def _score_all_intents(self, text: str) -> List[Tuple[str, float]]:
        """Score text against all intents using kNN approach"""
        query_vec = self.model.encode(text)
        
        scores = []
        for intent, examples in self.example_embeddings.items():
            # kNN: find similarity to each example
            example_scores = []
            for ex_emb in examples:
                score = np.dot(query_vec, ex_emb) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(ex_emb)
                )
                example_scores.append(score)
                
            # Take mean of top-k examples (k=3)
            example_scores.sort(reverse=True)
            k = min(3, len(example_scores))
            knn_score = np.mean(example_scores[:k])
            
            scores.append((intent, float(knn_score)))
            
        return scores
        
    def _classify_keyword(self, text: str) -> Tuple[Optional[str], float]:
        """Fallback: keyword-based classification"""
        text_lower = text.lower()
        
        keyword_map = {
            "play_music": ["play music", "play song", "start spotify", "listen to", "play"],
            "pause_music": ["pause", "stop music", "stop song"],
            "set_alarm": ["alarm", "wake me", "remind me"],
            "open_app": ["open", "launch", "start", "run"],
            "close_app": ["close", "exit", "quit", "terminate"],
            "search_web": ["search", "google", "look up", "find", "what is"],
            "get_time": ["time", "what time", "clock"],
            "get_date": ["date", "what day", "today"],
            "volume_up": ["volume up", "louder", "increase volume"],
            "volume_down": ["volume down", "quieter", "decrease volume"],
            "greeting": ["hello", "hi ", "hey ", "good morning", "good afternoon"],
            "goodbye": ["bye", "goodbye", "exit", "quit", "shutdown"],
        }
        
        matched = []
        for intent, keywords in keyword_map.items():
            for kw in keywords:
                if kw in text_lower:
                    matched.append((intent, 0.75))
                    break
                    
        if matched:
            return matched[0]
            
        return None, 0.0
        
    def get_top_intents(self, text: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Get top K most likely intents with scores"""
        if not self._ensure_loaded():
            intent, conf = self._classify_keyword(text)
            return [(intent, conf)] if intent else []
            
        scores = self._score_all_intents(text)
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
        
    def add_example(self, intent: str, example: str):
        """Add a new example to an intent (runtime learning)"""
        if not self._ensure_loaded():
            return
            
        if intent not in INTENT_EXAMPLES:
            INTENT_EXAMPLES[intent] = []
            self.example_embeddings[intent] = []
            
        INTENT_EXAMPLES[intent].append(example)
        
        # Add to example embeddings
        new_emb = self.model.encode(example)
        self.example_embeddings[intent].append(new_emb)
        
        # Recompute centroid
        self.intent_embeddings[intent] = np.mean(
            self.example_embeddings[intent], axis=0
        )
        
    def get_disambiguation_options(self, text: str) -> List[str]:
        """Get human-readable options for ambiguous input"""
        result = self.classify_detailed(text)
        
        if not result.is_ambiguous:
            return []
            
        options = []
        intent_descriptions = {
            "play_music": "Play music",
            "open_app": "Open an app",
            "search_web": "Search the web",
            "set_alarm": "Set an alarm",
            # Add more as needed
        }
        
        if result.intent:
            desc = intent_descriptions.get(result.intent, result.intent)
            options.append(f"1. {desc}")
            
        for i, (alt_intent, _) in enumerate(result.alternatives[:2], 2):
            desc = intent_descriptions.get(alt_intent, alt_intent)
            options.append(f"{i}. {desc}")
            
        return options


# Singleton (lazy loaded)
_model = None

def get_intent_model() -> IntentModel:
    global _model
    if _model is None:
        _model = IntentModel(lazy=True)
    return _model
