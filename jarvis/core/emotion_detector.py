"""
Emotion Detector - Combined Voice + Face Analysis
Detects user mood for adaptive JARVIS responses
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class EmotionState(Enum):
    """Possible emotional states"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    TIRED = "tired"
    CONFUSED = "confused"
    RUSHED = "rushed"
    CALM = "calm"


@dataclass
class EmotionResult:
    """Result from emotion analysis"""
    emotion: EmotionState
    confidence: float
    voice_emotion: Optional[EmotionState] = None
    face_emotion: Optional[EmotionState] = None
    
    def get_response_style(self) -> dict:
        """Get recommended response parameters based on emotion"""
        styles = {
            EmotionState.ANGRY: {
                "length": "short",
                "rate": 200,  # Faster speech
                "volume": 0.9,
                "tone": "direct"
            },
            EmotionState.RUSHED: {
                "length": "brief",
                "rate": 190,
                "volume": 0.9,
                "tone": "efficient"
            },
            EmotionState.SAD: {
                "length": "supportive",
                "rate": 150,  # Slower
                "volume": 0.7,  # Softer
                "tone": "gentle"
            },
            EmotionState.TIRED: {
                "length": "brief",
                "rate": 145,
                "volume": 0.6,
                "tone": "soft"
            },
            EmotionState.CALM: {
                "length": "normal",
                "rate": 160,
                "volume": 0.75,
                "tone": "relaxed"
            },
            EmotionState.HAPPY: {
                "length": "normal",
                "rate": 175,
                "volume": 0.85,
                "tone": "enthusiastic"
            },
            EmotionState.CONFUSED: {
                "length": "detailed",
                "rate": 155,
                "volume": 0.8,
                "tone": "explanatory"
            },
            EmotionState.NEUTRAL: {
                "length": "normal",
                "rate": 175,
                "volume": 0.9,
                "tone": "normal"
            }
        }
        return styles.get(self.emotion, styles[EmotionState.NEUTRAL])


class VoiceEmotionAnalyzer:
    """Analyzes voice audio for emotional cues"""
    
    def __init__(self):
        print("[EMOTION] Initializing Voice Emotion Analyzer...")
        self.librosa_available = False
        try:
            import librosa
            self.librosa_available = True
            print("[EMOTION] librosa available for voice analysis")
        except ImportError:
            print("[EMOTION] librosa not available - using basic analysis")
    
    def analyze(self, audio_data: bytes = None, text: str = None) -> EmotionState:
        """Analyze voice for emotion
        
        Uses multiple signals:
        - Speech rate (fast = rushed/angry)
        - Volume/intensity (loud = angry, soft = sad/tired)
        - Pitch variation (monotone = tired, varied = excited)
        - Keywords (frustration words like 'again', 'why')
        """
        
        # Keyword-based emotion detection (works without audio processing)
        if text:
            emotion = self._analyze_keywords(text)
            if emotion != EmotionState.NEUTRAL:
                return emotion
        
        # If no librosa, return neutral
        if not self.librosa_available or audio_data is None:
            return EmotionState.NEUTRAL
        
        try:
            return self._analyze_audio_features(audio_data)
        except Exception as e:
            print(f"[EMOTION] Voice analysis error: {e}")
            return EmotionState.NEUTRAL
    
    def _analyze_keywords(self, text: str) -> EmotionState:
        """Detect emotion from keywords in speech"""
        text_lower = text.lower()
        
        # Frustration/anger indicators
        anger_words = ["again", "why isn't", "not working", "stupid", "damn", 
                       "hate", "annoying", "frustrated", "ugh", "come on"]
        if any(word in text_lower for word in anger_words):
            return EmotionState.ANGRY
        
        # Rush indicators
        rush_words = ["quick", "hurry", "fast", "asap", "immediately", "now",
                      "quickly", "urgent"]
        if any(word in text_lower for word in rush_words):
            return EmotionState.RUSHED
        
        # Confusion indicators
        confusion_words = ["what", "how do", "don't understand", "confused",
                           "help me", "explain", "what do you mean"]
        if any(word in text_lower for word in confusion_words):
            return EmotionState.CONFUSED
        
        # Happiness indicators
        happy_words = ["thanks", "great", "awesome", "perfect", "love it",
                       "excellent", "wonderful", "amazing"]
        if any(word in text_lower for word in happy_words):
            return EmotionState.HAPPY
        
        # Sadness indicators
        sad_words = ["sad", "depressed", "lonely", "miss", "hurt", "sorry"]
        if any(word in text_lower for word in sad_words):
            return EmotionState.SAD
        
        return EmotionState.NEUTRAL
    
    def _analyze_audio_features(self, audio_data: bytes) -> EmotionState:
        """Analyze audio features for emotion (requires librosa)"""
        import librosa
        import io
        
        # Convert audio bytes to numpy array
        y, sr = librosa.load(io.BytesIO(audio_data), sr=None)
        
        # Extract features
        # RMS energy (volume)
        rms = np.mean(librosa.feature.rms(y=y))
        
        # Speaking rate (tempo)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Pitch analysis
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
        pitch_std = np.std(pitches[pitches > 0]) if np.any(pitches > 0) else 0
        
        # Classify based on features
        if rms > 0.1 and tempo > 140:
            return EmotionState.ANGRY
        elif rms < 0.02:
            return EmotionState.TIRED
        elif tempo > 130:
            return EmotionState.RUSHED
        elif pitch_std > 50:
            return EmotionState.HAPPY
        elif pitch_std < 20 and rms < 0.05:
            return EmotionState.SAD
        
        return EmotionState.NEUTRAL


class FaceEmotionAnalyzer:
    """Analyzes facial expressions for emotional cues using DeepFace"""
    
    def __init__(self):
        print("[EMOTION] Initializing Face Emotion Analyzer...")
        self.deepface_available = False
        self.fer_available = False
        self.detector = None
        self.frame_count = 0  # Process every 3rd frame for performance
        self.last_emotion = None
        
        # Try DeepFace first (better accuracy)
        try:
            from deepface import DeepFace
            self.DeepFace = DeepFace
            self.deepface_available = True
            print("[EMOTION] DeepFace available for emotion detection")
        except ImportError:
            print("[EMOTION] DeepFace not available, trying FER...")
            # Fallback to FER
            try:
                from fer import FER
                self.detector = FER(mtcnn=True)
                self.fer_available = True
                print("[EMOTION] FER available for face analysis")
            except ImportError:
                print("[EMOTION] FER not available - face emotion disabled")
    
    def analyze(self, frame) -> Optional[EmotionState]:
        """Analyze facial expression in camera frame"""
        if not self.deepface_available and not self.fer_available:
            return None
        
        # Performance optimization: process every 3rd frame
        self.frame_count += 1
        if self.frame_count % 3 != 0:
            return self.last_emotion
        
        try:
            if self.deepface_available:
                return self._analyze_deepface(frame)
            else:
                return self._analyze_fer(frame)
        except Exception as e:
            print(f"[EMOTION] Face analysis error: {e}")
            return None
    
    def _analyze_deepface(self, frame) -> Optional[EmotionState]:
        """Analyze emotion using DeepFace"""
        try:
            # DeepFace analyze - try different parameter names for compatibility
            try:
                # Newer DeepFace versions
                result = self.DeepFace.analyze(
                    frame, 
                    actions=['emotion'],
                    detector_backend='opencv',
                    silent=True
                )
            except TypeError:
                # Older DeepFace versions
                try:
                    result = self.DeepFace.analyze(
                        frame, 
                        actions=['emotion'],
                        enforce_detection=False,
                        silent=True
                    )
                except TypeError:
                    result = self.DeepFace.analyze(
                        frame, 
                        actions=['emotion']
                    )
            
            if not result:
                return None
            
            # Get dominant emotion
            if isinstance(result, list):
                result = result[0]
            
            dominant = result.get('dominant_emotion', 'neutral')
            
            # Map DeepFace emotions to our EmotionState
            emotion_map = {
                "angry": EmotionState.ANGRY,
                "disgust": EmotionState.ANGRY,
                "fear": EmotionState.CONFUSED,
                "happy": EmotionState.HAPPY,
                "sad": EmotionState.SAD,
                "surprise": EmotionState.CONFUSED,
                "neutral": EmotionState.NEUTRAL
            }
            
            self.last_emotion = emotion_map.get(dominant, EmotionState.NEUTRAL)
            return self.last_emotion
            
        except Exception as e:
            # Suppress common errors (no face detected, etc.)
            error_str = str(e)
            if "Face could not be detected" not in error_str and "enforce" not in error_str:
                print(f"[EMOTION] DeepFace error: {e}")
            return None
    
    def _analyze_fer(self, frame) -> Optional[EmotionState]:
        """Fallback to FER for emotion detection"""
        if not self.fer_available or self.detector is None:
            return None
        
        try:
            result = self.detector.detect_emotions(frame)
            
            if not result:
                return None
            
            # Get dominant emotion from first face
            emotions = result[0]["emotions"]
            dominant = max(emotions, key=emotions.get)
            
            # Map FER emotions to our EmotionState
            emotion_map = {
                "angry": EmotionState.ANGRY,
                "disgust": EmotionState.ANGRY,
                "fear": EmotionState.CONFUSED,
                "happy": EmotionState.HAPPY,
                "sad": EmotionState.SAD,
                "surprise": EmotionState.CONFUSED,
                "neutral": EmotionState.NEUTRAL
            }
            
            self.last_emotion = emotion_map.get(dominant, EmotionState.NEUTRAL)
            return self.last_emotion
            
        except Exception as e:
            print(f"[EMOTION] FER error: {e}")
            return None


class EmotionDetector:
    """Combined voice + face emotion detector with temporal smoothing"""
    
    # Smoothing parameters
    HISTORY_SIZE = 10  # Keep last 10 detections
    STABILITY_THRESHOLD = 4  # Need 4 consistent emotions to change stable
    
    def __init__(self):
        print("[EMOTION] Initializing Combined Emotion Detector...")
        self.voice_analyzer = VoiceEmotionAnalyzer()
        self.face_analyzer = FaceEmotionAnalyzer()
        self.last_emotion = EmotionState.NEUTRAL
        
        # Sliding window for emotion smoothing (anti-jitter)
        self.emotion_history: list = []  # List of EmotionState
        self.stable_emotion = EmotionState.NEUTRAL
        self.stable_confidence = 0.5
        
        print("[EMOTION] Emotion Detector Ready")
    
    def detect(self, audio_data: bytes = None, text: str = None, 
               camera_frame = None) -> EmotionResult:
        """Detect emotion from voice and/or face
        
        Weights: 60% face, 40% voice (face is more reliable)
        Falls back to voice-only if no camera
        """
        
        voice_emotion = self.voice_analyzer.analyze(audio_data, text)
        face_emotion = self.face_analyzer.analyze(camera_frame) if camera_frame is not None else None
        
        # Combine emotions
        if face_emotion and voice_emotion:
            # Both available - weight them
            final_emotion = self._combine_emotions(voice_emotion, face_emotion)
            confidence = 0.85
        elif face_emotion:
            final_emotion = face_emotion
            confidence = 0.7
        elif voice_emotion != EmotionState.NEUTRAL:
            final_emotion = voice_emotion
            confidence = 0.6
        else:
            final_emotion = EmotionState.NEUTRAL
            confidence = 0.5
        
        self.last_emotion = final_emotion
        
        return EmotionResult(
            emotion=final_emotion,
            confidence=confidence,
            voice_emotion=voice_emotion,
            face_emotion=face_emotion
        )
    
    def _combine_emotions(self, voice: EmotionState, face: EmotionState) -> EmotionState:
        """Combine voice and face emotions with weighting"""
        
        # If they agree, high confidence
        if voice == face:
            return voice
        
        # If face shows strong emotion, trust it more
        strong_emotions = [EmotionState.ANGRY, EmotionState.HAPPY, EmotionState.SAD]
        if face in strong_emotions:
            return face
        
        # Voice detected strong emotion but face is neutral - could be suppressing
        if voice in strong_emotions and face == EmotionState.NEUTRAL:
            return voice
        
        # Default to face (more reliable)
        return face
    
    def _update_history(self, emotion: EmotionState):
        """Update emotion history buffer"""
        self.emotion_history.append(emotion)
        if len(self.emotion_history) > self.HISTORY_SIZE:
            self.emotion_history.pop(0)
    
    def _get_majority_emotion(self) -> EmotionState:
        """Get most common emotion in history (majority voting)"""
        if not self.emotion_history:
            return EmotionState.NEUTRAL
        
        from collections import Counter
        counts = Counter(self.emotion_history)
        return counts.most_common(1)[0][0]
    
    def detect_stable(self, audio_data: bytes = None, text: str = None,
                      camera_frame = None) -> EmotionResult:
        """
        Detect emotion with temporal smoothing.
        Only changes stable_emotion after consistent detection.
        Use this for UI to prevent jitter.
        
        Returns: EmotionResult with stable emotion
        """
        # Get raw detection
        result = self.detect(audio_data, text, camera_frame)
        
        # Update history
        self._update_history(result.emotion)
        
        # Get majority emotion
        majority = self._get_majority_emotion()
        
        # Count how many times majority appears in recent history
        recent = self.emotion_history[-self.STABILITY_THRESHOLD:] if len(self.emotion_history) >= self.STABILITY_THRESHOLD else []
        majority_count = sum(1 for e in recent if e == majority)
        
        # Update stable emotion only if majority is consistent enough
        if majority_count >= self.STABILITY_THRESHOLD:
            if self.stable_emotion != majority:
                self.stable_emotion = majority
                self.stable_confidence = result.confidence
        
        # Return result with stable emotion
        return EmotionResult(
            emotion=self.stable_emotion,
            confidence=self.stable_confidence,
            voice_emotion=result.voice_emotion,
            face_emotion=result.face_emotion
        )
    
    def get_stable_emotion(self) -> tuple:
        """Get current stable emotion and confidence"""
        return self.stable_emotion, self.stable_confidence
    
    def get_last_emotion(self) -> EmotionState:
        """Get the last detected emotion (raw, may jitter)"""
        return self.last_emotion
    
    def reset_emotion(self):
        """Reset emotion state"""
        self.emotion_history.clear()
        self.stable_emotion = EmotionState.NEUTRAL
        self.stable_confidence = 0.5
        self.last_emotion = EmotionState.NEUTRAL
    
    def get_empathic_response(self, title: str = "sir") -> Optional[str]:
        """Get an empathic response if strong emotion detected"""
        import random
        
        emotion = self.last_emotion
        
        responses = {
            EmotionState.SAD: [
                f"You seem a bit down, {title}. Is everything alright?",
                f"I'm here if you need anything, {title}.",
                f"{title}, you don't seem yourself. Would you like to hear something uplifting?"
            ],
            EmotionState.ANGRY: [
                f"I sense some frustration, {title}. Let me know how I can help.",
                f"Take a breath, {title}. What do you need?"
            ],
            EmotionState.TIRED: [
                f"You look tired, {title}. Perhaps a break would help?",
                f"{title}, it's been a long day. Should I dim the lights?"
            ],
            EmotionState.HAPPY: [
                f"Good to see you in high spirits, {title}!",
                f"You seem cheerful today, {title}."
            ]
        }
        
        if emotion in responses:
            return random.choice(responses[emotion])
        
        return None
