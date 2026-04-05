"""
Multimodal Emotion Detection
============================
Fuses emotion from 3 sources:
- Face (camera via DeepFace)
- Voice (audio features via librosa)
- Text (semantic via transformers)

Returns unified mood for JARVIS personality adaptation.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import numpy as np

# Try imports for each modality
DEEPFACE_AVAILABLE = False
LIBROSA_AVAILABLE = False
TRANSFORMERS_AVAILABLE = False

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    pass

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    pass

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass


@dataclass
class EmotionSignal:
    """Single emotion reading from one modality"""
    source: str  # "face", "voice", "text"
    emotions: Dict[str, float]  # emotion name -> confidence
    confidence: float  # overall confidence in this reading


class FaceEmotionDetector:
    """Detect emotion from face using DeepFace"""
    
    def __init__(self):
        self.available = DEEPFACE_AVAILABLE
        if self.available:
            print("[EMOTION] Face emotion detector ready")
        else:
            print("[EMOTION] DeepFace not available")
            
    def detect(self, frame) -> Optional[EmotionSignal]:
        """Detect emotion from camera frame"""
        if not self.available:
            return None
            
        try:
            analysis = DeepFace.analyze(
                frame, 
                actions=['emotion'], 
                enforce_detection=False,
                silent=True
            )
            
            if isinstance(analysis, list):
                analysis = analysis[0]
                
            emotions = analysis.get("emotion", {})
            
            # Normalize to 0-1 range
            total = sum(emotions.values())
            if total > 0:
                emotions = {k: v/100.0 for k, v in emotions.items()}
                
            return EmotionSignal(
                source="face",
                emotions=emotions,
                confidence=0.8  # face is usually reliable
            )
            
        except Exception as e:
            return None


class VoiceEmotionDetector:
    """Detect emotion from voice using audio features"""
    
    # Emotion mapping based on pitch/energy
    EMOTION_PROFILES = {
        "angry": {"pitch_high": True, "energy_high": True},
        "happy": {"pitch_high": True, "energy_high": False},
        "sad": {"pitch_high": False, "energy_high": False},
        "neutral": {"pitch_high": False, "energy_high": False},
    }
    
    def __init__(self):
        self.available = LIBROSA_AVAILABLE
        if self.available:
            print("[EMOTION] Voice emotion detector ready")
        else:
            print("[EMOTION] librosa not available")
            
    def detect(self, audio_path: str) -> Optional[EmotionSignal]:
        """Detect emotion from audio file"""
        if not self.available:
            return None
            
        try:
            import librosa
            y, sr = librosa.load(audio_path, duration=5)
            
            # Extract features
            pitch = np.mean(librosa.yin(y, fmin=50, fmax=300))
            energy = np.mean(librosa.feature.rms(y=y))
            
            # Map to emotions
            pitch_high = pitch > 180
            energy_high = energy > 0.05
            
            emotions = {}
            
            if energy_high and pitch_high:
                emotions = {"angry": 0.5, "excited": 0.3, "neutral": 0.2}
            elif energy_high and not pitch_high:
                emotions = {"happy": 0.4, "neutral": 0.4, "excited": 0.2}
            elif not energy_high and pitch_high:
                emotions = {"sad": 0.3, "neutral": 0.5, "tired": 0.2}
            else:
                emotions = {"neutral": 0.6, "tired": 0.2, "sad": 0.2}
                
            return EmotionSignal(
                source="voice",
                emotions=emotions,
                confidence=0.6  # voice is less reliable
            )
            
        except Exception as e:
            return None
            
    def detect_from_features(self, pitch: float, energy: float) -> EmotionSignal:
        """Detect from pre-computed features (for real-time)"""
        pitch_high = pitch > 180
        energy_high = energy > 0.05
        
        if energy_high and pitch_high:
            emotions = {"angry": 0.5, "excited": 0.3}
        elif not energy_high:
            emotions = {"tired": 0.4, "sad": 0.3, "neutral": 0.3}
        else:
            emotions = {"neutral": 0.7, "happy": 0.3}
            
        return EmotionSignal(
            source="voice",
            emotions=emotions,
            confidence=0.6
        )


class TextEmotionDetector:
    """Detect emotion from text using transformers"""
    
    def __init__(self):
        self.model = None
        self.available = TRANSFORMERS_AVAILABLE
        
        if self.available:
            print("[EMOTION] Text emotion detector loading...")
            try:
                # Lazy load - will load on first use
                self._model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
            except:
                self.available = False
                
    def _ensure_model(self):
        """Lazy load the model"""
        if self.model is None and self.available:
            try:
                self.model = pipeline(
                    "text-classification",
                    model=self._model_name,
                    top_k=None
                )
                print("[EMOTION] Text emotion model loaded")
            except:
                self.available = False
                
    def detect(self, text: str) -> Optional[EmotionSignal]:
        """Detect emotion from text"""
        if not self.available:
            return self._keyword_fallback(text)
            
        self._ensure_model()
        
        if self.model is None:
            return self._keyword_fallback(text)
            
        try:
            results = self.model(text[:512])  # limit length
            
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list):
                    results = results[0]
                    
            emotions = {}
            for item in results:
                label = item["label"].lower()
                score = item["score"]
                emotions[label] = score
                
            return EmotionSignal(
                source="text",
                emotions=emotions,
                confidence=0.7
            )
            
        except Exception as e:
            return self._keyword_fallback(text)
            
    def _keyword_fallback(self, text: str) -> EmotionSignal:
        """Simple keyword-based fallback"""
        text_lower = text.lower()
        
        anger_words = ["angry", "frustrated", "annoyed", "hate", "stupid"]
        sad_words = ["sad", "tired", "exhausted", "depressed", "down"]
        happy_words = ["happy", "great", "awesome", "love", "excited"]
        
        emotions = {"neutral": 0.5}
        
        for word in anger_words:
            if word in text_lower:
                emotions = {"angry": 0.6, "frustrated": 0.3}
                break
                
        for word in sad_words:
            if word in text_lower:
                emotions = {"sad": 0.5, "tired": 0.3}
                break
                
        for word in happy_words:
            if word in text_lower:
                emotions = {"happy": 0.6, "excited": 0.2}
                break
                
        return EmotionSignal(
            source="text",
            emotions=emotions,
            confidence=0.4  # keyword is less reliable
        )


class MultimodalEmotionFusion:
    """
    Fuses emotions from multiple modalities.
    Weighted average based on source confidence.
    """
    
    # Standard emotion labels
    EMOTIONS = ["happy", "sad", "angry", "neutral", "tired", 
                "frustrated", "excited", "fearful"]
    
    def __init__(self):
        print("[EMOTION] Initializing Multimodal Emotion Fusion...")
        self.face_detector = FaceEmotionDetector()
        self.voice_detector = VoiceEmotionDetector()
        self.text_detector = TextEmotionDetector()
        self.history: List[str] = []  # recent dominant emotions
        print("[EMOTION] Multimodal Emotion Fusion Ready")
        
    def fuse(self, 
             face_signal: Optional[EmotionSignal] = None,
             voice_signal: Optional[EmotionSignal] = None,
             text_signal: Optional[EmotionSignal] = None) -> str:
        """
        Fuse emotion signals into single dominant emotion.
        Returns emotion string (e.g., "happy", "frustrated").
        """
        signals = [s for s in [face_signal, voice_signal, text_signal] if s]
        
        if not signals:
            return "neutral"
            
        # Weighted fusion
        combined = {}
        total_weight = 0
        
        for signal in signals:
            weight = signal.confidence
            total_weight += weight
            
            for emotion, score in signal.emotions.items():
                emotion_key = self._normalize_emotion(emotion)
                combined[emotion_key] = combined.get(emotion_key, 0) + score * weight
                
        # Normalize
        if total_weight > 0:
            for k in combined:
                combined[k] /= total_weight
                
        # Get dominant
        if not combined:
            return "neutral"
            
        dominant = max(combined, key=combined.get)
        
        # Add to history
        self.history.append(dominant)
        if len(self.history) > 5:
            self.history = self.history[-5:]
            
        return dominant
        
    def _normalize_emotion(self, emotion: str) -> str:
        """Map various labels to standard set"""
        mapping = {
            "anger": "angry",
            "fear": "fearful",
            "surprise": "excited",
            "disgust": "frustrated",
            "joy": "happy",
            "sadness": "sad",
        }
        return mapping.get(emotion.lower(), emotion.lower())
        
    def get_trend(self) -> str:
        """Get the emotional trend (most common recent emotion)"""
        if not self.history:
            return "neutral"
            
        from collections import Counter
        counts = Counter(self.history)
        return counts.most_common(1)[0][0]
        
    def detect_from_text(self, text: str) -> str:
        """Quick text-only emotion detection"""
        signal = self.text_detector.detect(text)
        if signal:
            return self.fuse(text_signal=signal)
        return "neutral"
        
    def detect_from_frame(self, frame) -> str:
        """Quick face-only emotion detection"""
        signal = self.face_detector.detect(frame)
        if signal:
            return self.fuse(face_signal=signal)
        return "neutral"


# Singleton
_fusion = None

def get_emotion_fusion() -> MultimodalEmotionFusion:
    global _fusion
    if _fusion is None:
        _fusion = MultimodalEmotionFusion()
    return _fusion
