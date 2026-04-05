"""
Face Authentication System
==========================
Proper face recognition with:
- Embedding-based comparison
- User registration
- Secure matching with tolerance
- Fallback to OpenCV if face_recognition unavailable
"""

import cv2
import numpy as np
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Try to import face_recognition (requires dlib)
FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print("[FACE] face_recognition not installed - using OpenCV fallback")


class FaceAuth:
    """
    Face-based user authentication.
    Stores face embeddings for recognition.
    
    Features:
    - Rolling confirmation (requires N consistent detections)
    - Anti-flicker (stable_user only changes with confidence)
    - Temporal smoothing for UI stability
    """
    
    TOLERANCE = 0.5  # Lower = stricter matching
    CONFIRMATION_THRESHOLD = 3  # Consistent detections before confirming
    HISTORY_SIZE = 10  # Recognition history buffer size
    
    def __init__(self, data_dir: Path = None):
        print("[FACE] Initializing Face Authentication...")
        
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_file = self.data_dir / "face_embeddings.json"
        
        # Known users: {name: [list of embeddings]}
        self.known_users: Dict[str, List[List[float]]] = {}
        self._load_embeddings()
        
        # OpenCV face detector fallback
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        self.available = FACE_RECOGNITION_AVAILABLE
        self.last_seen: Dict[str, datetime] = {}
        
        # Rolling confirmation (anti-flicker)
        self.recognition_history: List[str] = []  # Last N recognitions
        self.stable_user: Optional[str] = None  # Confirmed stable user
        self.stable_confidence: float = 0.0
        self.consecutive_matches: int = 0
        self.last_raw_user: Optional[str] = None
        
        user_count = len(self.known_users)
        print(f"[FACE] Face Auth Ready ({user_count} users registered)")
        
    def _load_embeddings(self):
        """Load saved face embeddings"""
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'r') as f:
                    self.known_users = json.load(f)
            except:
                self.known_users = {}
                
    def _save_embeddings(self):
        """Save face embeddings to disk"""
        try:
            with open(self.embeddings_file, 'w') as f:
                json.dump(self.known_users, f)
        except Exception as e:
            print(f"[FACE] Failed to save embeddings: {e}")
            
    def register(self, frame: np.ndarray, name: str) -> Tuple[bool, str]:
        """
        Register a new user's face.
        Takes multiple samples for better recognition.
        
        Returns: (success, message)
        """
        if not self.available:
            return False, "Face recognition not available (dlib not installed)"
            
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces
        locations = face_recognition.face_locations(rgb)
        
        if not locations:
            return False, "No face detected. Please face the camera."
            
        if len(locations) > 1:
            return False, "Multiple faces detected. Please ensure only one face is visible."
            
        # Get embedding
        encodings = face_recognition.face_encodings(rgb, locations)
        
        if not encodings:
            return False, "Couldn't extract face features. Please try again."
            
        encoding = encodings[0].tolist()
        
        # Add to known users
        if name not in self.known_users:
            self.known_users[name] = []
            
        self.known_users[name].append(encoding)
        
        # Keep max 5 embeddings per user
        if len(self.known_users[name]) > 5:
            self.known_users[name] = self.known_users[name][-5:]
            
        self._save_embeddings()
        
        sample_count = len(self.known_users[name])
        return True, f"Registered {name} (sample {sample_count}/5)"
        
    def recognize(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Recognize a face in the frame.
        
        Returns: (name or None, confidence)
        """
        if not self.available:
            return self._opencv_fallback(frame)
            
        if not self.known_users:
            return None, 0.0
            
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces
        locations = face_recognition.face_locations(rgb)
        
        if not locations:
            return None, 0.0
            
        # Get encoding for first face
        encodings = face_recognition.face_encodings(rgb, locations[:1])
        
        if not encodings:
            return None, 0.0
            
        unknown_encoding = encodings[0]
        
        # Compare to all known users
        best_match = None
        best_distance = float('inf')
        
        for name, user_encodings in self.known_users.items():
            for known_enc in user_encodings:
                distance = face_recognition.face_distance(
                    [np.array(known_enc)], 
                    unknown_encoding
                )[0]
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = name
                    
        # Check threshold
        if best_distance <= self.TOLERANCE:
            confidence = 1 - best_distance
            self.last_seen[best_match] = datetime.now()
            return best_match, float(confidence)
            
        return "unknown", float(1 - best_distance)
        
    def _opencv_fallback(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """Fallback: just detect if a face is present"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            return "user", 0.5  # Generic detection
        return None, 0.0
        
    def get_users(self) -> List[str]:
        """Get list of registered users"""
        return list(self.known_users.keys())
        
    def remove_user(self, name: str) -> bool:
        """Remove a registered user"""
        if name in self.known_users:
            del self.known_users[name]
            self._save_embeddings()
            return True
        return False
        
    def was_seen_recently(self, name: str, minutes: int = 5) -> bool:
        """Check if user was seen recently"""
        if name not in self.last_seen:
            return False
            
        elapsed = datetime.now() - self.last_seen[name]
        return elapsed.total_seconds() < minutes * 60
        
    def recognize_stable(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Recognize face with rolling confirmation.
        Only updates stable_user after N consistent detections.
        Use this instead of recognize() for UI to prevent flicker.
        
        Returns: (stable_user, stable_confidence)
        """
        # Get raw recognition
        raw_user, raw_confidence = self.recognize(frame)
        self.last_raw_user = raw_user
        
        # Update history
        if raw_user:
            self.recognition_history.append(raw_user)
            if len(self.recognition_history) > self.HISTORY_SIZE:
                self.recognition_history.pop(0)
        else:
            # No face - reset after enough empty frames
            self.recognition_history.append("__none__")
            if len(self.recognition_history) > self.HISTORY_SIZE:
                self.recognition_history.pop(0)
        
        # Check for consecutive matches
        if raw_user and raw_user != "unknown":
            if raw_user == self.last_raw_user:
                self.consecutive_matches += 1
            else:
                self.consecutive_matches = 1
                
            # Confirm user after threshold
            if self.consecutive_matches >= self.CONFIRMATION_THRESHOLD:
                if self.stable_user != raw_user:
                    self.stable_user = raw_user
                    self.stable_confidence = raw_confidence
        else:
            self.consecutive_matches = 0
            
        # Check if stable user should be cleared (no detections)
        recent = self.recognition_history[-self.CONFIRMATION_THRESHOLD:] if len(self.recognition_history) >= self.CONFIRMATION_THRESHOLD else []
        if all(u == "__none__" for u in recent):
            self.stable_user = None
            self.stable_confidence = 0.0
            
        return self.stable_user, self.stable_confidence
        
    def get_stable_user(self) -> Tuple[Optional[str], float]:
        """Get currently confirmed stable user without processing frame"""
        return self.stable_user, self.stable_confidence
        
    def reset_identity(self):
        """Reset recognition state (e.g., when user leaves)"""
        self.recognition_history.clear()
        self.stable_user = None
        self.stable_confidence = 0.0
        self.consecutive_matches = 0
        self.last_raw_user = None


# Singleton
_face_auth = None

def get_face_auth() -> FaceAuth:
    global _face_auth
    if _face_auth is None:
        _face_auth = FaceAuth()
    return _face_auth
