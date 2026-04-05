"""
Face Recognition Authentication - Owner verification for JARVIS
Recognizes the owner (Raghava) and limits access for outsiders
Now with auto-install and facenet fallback!
"""

import os
import json
import pickle
import threading
import time
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass


class UserType(Enum):
    """Type of user detected"""
    OWNER = "owner"
    KNOWN_GUEST = "known_guest"
    UNKNOWN = "unknown"
    UNVERIFIED = "unverified"


@dataclass
class UserProfile:
    """User profile data"""
    name: str
    user_type: UserType
    access_level: int  # 1 = full, 2 = limited, 3 = minimal
    face_encoding: any = None


class FaceRecognition:
    """Face recognition authentication system for JARVIS"""
    
    def __init__(self, perception=None):
        print("[FACE AUTH] Initializing Face Recognition...")
        self.perception = perception
        
        # Paths
        self.data_dir = Path(__file__).parent.parent / "data" / "faces"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.encodings_file = self.data_dir / "face_encodings.pkl"
        self.profiles_file = self.data_dir / "profiles.json"
        
        # Owner info
        self.owner_name = "Raghava"
        
        # Check for dependencies
        self.face_recognition_available = False
        self.cv2_available = False
        self.facenet_available = False
        
        try:
            import cv2
            self.cv2_available = True
            print("[FACE AUTH] OpenCV available")
        except ImportError:
            print("[FACE AUTH] OpenCV not available - attempting auto-install...")
            self._auto_install("opencv-python")
            try:
                import cv2
                self.cv2_available = True
            except:
                pass
        
        try:
            import face_recognition
            self.face_recognition_available = True
            print("[FACE AUTH] face_recognition available")
        except ImportError:
            print("[FACE AUTH] face_recognition not available - trying facenet fallback...")
            # Try facenet-pytorch as fallback (easier to install)
            try:
                from facenet_pytorch import MTCNN, InceptionResnetV1
                self.facenet_available = True
                self._init_facenet()
                print("[FACE AUTH] Using facenet-pytorch for face recognition")
            except ImportError:
                print("[FACE AUTH] Attempting to install facenet-pytorch...")
                self._auto_install("facenet-pytorch")
                try:
                    from facenet_pytorch import MTCNN, InceptionResnetV1
                    self.facenet_available = True
                    self._init_facenet()
                except:
                    print("[FACE AUTH] Could not initialize face recognition")
        
        # Known faces
        self.known_face_encodings = []
        self.known_face_names = []
        self.profiles: dict = {}
        
        # Current user state
        self.current_user: Optional[UserProfile] = None
        self.is_authenticated = False
        self.last_verification_time = 0
        self.verification_interval = 300  # Re-verify every 5 minutes
        
        # Continuous monitoring
        self.monitoring = False
        self.monitor_thread = None
        
        # Restricted commands for outsiders
        self.restricted_commands = [
            "whatsapp", "message", "email", "calendar", "password",
            "personal", "private", "delete", "shutdown", "restart",
            "settings", "config", "alarm", "reminder", "download"
        ]
        
        # Load saved data
        self._load_data()
        
        print("[FACE AUTH] Face Recognition Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[FACE AUTH] {text}")
    
    def _auto_install(self, package: str):
        """Auto-install missing Python package"""
        try:
            print(f"[FACE AUTH] Auto-installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package, "--user", "-q"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[FACE AUTH] Successfully installed {package}")
        except Exception as e:
            print(f"[FACE AUTH] Failed to install {package}: {e}")
    
    def _init_facenet(self):
        """Initialize facenet-pytorch models for face detection and recognition"""
        try:
            from facenet_pytorch import MTCNN, InceptionResnetV1
            import torch
            
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # Face detector
            self.mtcnn = MTCNN(
                keep_all=False,
                device=device,
                select_largest=True
            )
            
            # Face embedder
            self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
            self.device = device
            
            print("[FACE AUTH] Facenet models initialized")
        except Exception as e:
            print(f"[FACE AUTH] Facenet init error: {e}")
            self.facenet_available = False
    
    def _enhance_low_light(self, frame):
        """Enhance image for better face detection in low light/darkness"""
        import cv2
        import numpy as np
        
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge and convert back
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Apply gamma correction for additional brightness
        gamma = 1.5  # > 1 brightens, < 1 darkens
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                          for i in np.arange(0, 256)]).astype("uint8")
        enhanced = cv2.LUT(enhanced, table)
        
        # Denoise to reduce artifacts
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return enhanced
    
    def _preprocess_for_recognition(self, frame, enhance_light=True):
        """Preprocess frame for face recognition"""
        import cv2
        
        # Check if image is too dark
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = gray.mean()
        
        if enhance_light and avg_brightness < 80:  # Dark image
            print(f"[FACE AUTH] Low light detected (brightness={avg_brightness:.0f}), enhancing...")
            frame = self._enhance_low_light(frame)
        
        return frame

    
    def _load_data(self):
        """Load saved face encodings and profiles"""
        try:
            # Load encodings
            if self.encodings_file.exists():
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get("encodings", [])
                    self.known_face_names = data.get("names", [])
                print(f"[FACE AUTH] Loaded {len(self.known_face_encodings)} face encodings")
            
            # Load profiles
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r') as f:
                    profiles_data = json.load(f)
                    for name, data in profiles_data.items():
                        self.profiles[name] = UserProfile(
                            name=name,
                            user_type=UserType(data.get("user_type", "unknown")),
                            access_level=data.get("access_level", 3)
                        )
        except Exception as e:
            print(f"[FACE AUTH] Error loading data: {e}")
    
    def _save_data(self):
        """Save face encodings and profiles"""
        try:
            # Save encodings
            with open(self.encodings_file, 'wb') as f:
                pickle.dump({
                    "encodings": self.known_face_encodings,
                    "names": self.known_face_names
                }, f)
            
            # Save profiles
            profiles_data = {}
            for name, profile in self.profiles.items():
                profiles_data[name] = {
                    "user_type": profile.user_type.value,
                    "access_level": profile.access_level
                }
            
            with open(self.profiles_file, 'w') as f:
                json.dump(profiles_data, f, indent=2)
                
        except Exception as e:
            print(f"[FACE AUTH] Error saving data: {e}")
    
    def register_owner(self) -> bool:
        """Register the owner's face (Raghava)"""
        if not self.is_available():
            self._speak("Face recognition is not available. Please install the required libraries.")
            return False
        
        self._speak(f"I need to register your face, {self._get_title()}. Please look at the camera.")
        time.sleep(2)
        
        return self._capture_and_register(self.owner_name, UserType.OWNER, access_level=1)
    
    def register_guest(self, name: str) -> bool:
        """Register a known guest"""
        if not self.is_available():
            return False
        
        self._speak(f"Registering {name} as a known guest. Please have them look at the camera.")
        time.sleep(2)
        
        return self._capture_and_register(name, UserType.KNOWN_GUEST, access_level=2)
    
    def _capture_and_register(self, name: str, user_type: UserType, access_level: int) -> bool:
        """Capture face and register - uses facenet as fallback"""
        import cv2
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._speak("Could not access the camera.")
            return False
        
        self._speak("Please hold still for 3 seconds.")
        
        # Capture multiple frames for better encoding
        frames = []
        for _ in range(10):
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            time.sleep(0.2)
        
        cap.release()
        
        # Try face_recognition first
        if self.face_recognition_available:
            try:
                import face_recognition
                return self._register_with_face_recognition(frames, name, user_type, access_level, face_recognition, cv2)
            except Exception as e:
                print(f"[FACE AUTH] face_recognition error: {e}")
        
        # Fallback to facenet
        if self.facenet_available:
            try:
                return self._register_with_facenet(frames, name, user_type, access_level, cv2)
            except Exception as e:
                print(f"[FACE AUTH] facenet error: {e}")
        
        self._speak("Could not process face. Please try again.")
        return False
    
    def _register_with_face_recognition(self, frames, name, user_type, access_level, face_recognition, cv2):
        """Register using face_recognition library"""
        for frame in frames:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                
                # Add to known faces
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                
                # Create profile
                self.profiles[name] = UserProfile(
                    name=name,
                    user_type=user_type,
                    access_level=access_level,
                    face_encoding=face_encoding
                )
                
                # Save
                self._save_data()
                
                # Save face image
                face_img_path = self.data_dir / f"{name.lower().replace(' ', '_')}.jpg"
                cv2.imwrite(str(face_img_path), frame)
                
                self._speak(f"Successfully registered {name}.")
                return True
        
        self._speak("Could not detect a face. Please try again.")
        return False
    
    def _register_with_facenet(self, frames, name, user_type, access_level, cv2):
        """Register using facenet-pytorch (fallback when face_recognition not available)"""
        from PIL import Image
        import torch
        
        for frame in frames:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            
            # Detect face
            face = self.mtcnn(img)
            
            if face is not None:
                # Get embedding
                with torch.no_grad():
                    embedding = self.resnet(face.unsqueeze(0).to(self.device))
                
                face_encoding = embedding.cpu().numpy()[0]
                
                # Add to known faces
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                
                # Create profile
                self.profiles[name] = UserProfile(
                    name=name,
                    user_type=user_type,
                    access_level=access_level,
                    face_encoding=face_encoding
                )
                
                # Save
                self._save_data()
                
                # Save face image
                face_img_path = self.data_dir / f"{name.lower().replace(' ', '_')}.jpg"
                cv2.imwrite(str(face_img_path), frame)
                
                self._speak(f"Successfully registered {name} using deep learning.")
                return True
        
        self._speak("Could not detect a face. Please try again.")
        return False
    
    def verify_user(self) -> Tuple[UserProfile, float]:
        """Verify the current user via webcam - with low-light enhancement"""
        if not self.is_available():
            return UserProfile("Unknown", UserType.UNVERIFIED, 3), 0.0
        
        import cv2
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return UserProfile("Unknown", UserType.UNVERIFIED, 3), 0.0
        
        # Capture multiple frames for better detection
        best_frame = None
        best_brightness = 0
        
        for _ in range(5):
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = gray.mean()
                if brightness > best_brightness:
                    best_brightness = brightness
                    best_frame = frame
        
        cap.release()
        
        if best_frame is None:
            return UserProfile("Unknown", UserType.UNVERIFIED, 3), 0.0
        
        # Apply low-light enhancement if needed
        frame = self._preprocess_for_recognition(best_frame)
        
        # Try face_recognition library first
        if self.face_recognition_available:
            return self._verify_with_face_recognition(frame, cv2)
        
        # Fallback to facenet-pytorch
        if self.facenet_available:
            return self._verify_with_facenet(frame, cv2)
        
        return UserProfile("Unknown", UserType.UNVERIFIED, 3), 0.0
    
    def _verify_with_face_recognition(self, frame, cv2):
        """Verify using face_recognition library"""
        import face_recognition
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        if not face_locations:
            try:
                face_locations = face_recognition.face_locations(rgb_frame, model="cnn")
            except:
                pass
        
        if not face_locations:
            return UserProfile("Unknown", UserType.UNKNOWN, 3), 0.0
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not face_encodings or not self.known_face_encodings:
            return UserProfile("Unknown", UserType.UNKNOWN, 3), 0.0
        
        face_encoding = face_encodings[0]
        face_distances = face_recognition.face_distance(
            self.known_face_encodings, face_encoding
        )
        
        best_match_idx = face_distances.argmin()
        confidence = 1 - face_distances[best_match_idx]
        
        if confidence > 0.6:
            name = self.known_face_names[best_match_idx]
            profile = self.profiles.get(name, UserProfile(name, UserType.KNOWN_GUEST, 2))
            return profile, confidence
        
        return UserProfile("Unknown", UserType.UNKNOWN, 3), confidence
    
    def _verify_with_facenet(self, frame, cv2):
        """Verify using facenet-pytorch (fallback when face_recognition not available)"""
        from PIL import Image
        import torch
        import numpy as np
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        
        # Detect face
        face = self.mtcnn(img)
        
        if face is None:
            return UserProfile("Unknown", UserType.UNKNOWN, 3), 0.0
        
        # Get embedding
        with torch.no_grad():
            embedding = self.resnet(face.unsqueeze(0).to(self.device))
        
        face_encoding = embedding.cpu().numpy()[0]
        
        if not self.known_face_encodings:
            return UserProfile("Unknown", UserType.UNKNOWN, 3), 0.0
        
        # Compare with known encodings using cosine similarity
        best_match_idx = -1
        best_similarity = -1
        
        for i, known_enc in enumerate(self.known_face_encodings):
            # Cosine similarity
            similarity = np.dot(face_encoding, known_enc) / (
                np.linalg.norm(face_encoding) * np.linalg.norm(known_enc)
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = i
        
        # Facenet threshold (cosine similarity > 0.7 is a match)
        if best_similarity > 0.7 and best_match_idx >= 0:
            name = self.known_face_names[best_match_idx]
            profile = self.profiles.get(name, UserProfile(name, UserType.KNOWN_GUEST, 2))
            confidence = float(best_similarity)
            return profile, confidence
        
        return UserProfile("Unknown", UserType.UNKNOWN, 3), float(max(0, best_similarity))
    
    def authenticate(self) -> bool:
        """Authenticate the user and set current user state"""
        if not self.known_face_encodings:
            # No owner registered yet
            self._speak("No owner registered. Would you like to register as the owner?")
            return False
        
        self._speak("Verifying your identity...")
        
        profile, confidence = self.verify_user()
        
        self.current_user = profile
        self.last_verification_time = time.time()
        
        if profile.user_type == UserType.OWNER:
            self.is_authenticated = True
            self._speak(f"Welcome back, {profile.name}. Full access granted.")
            return True
        
        elif profile.user_type == UserType.KNOWN_GUEST:
            self.is_authenticated = True
            self._speak(f"Hello, {profile.name}. You have guest access.")
            return True
        
        else:
            self.is_authenticated = False
            self._speak("I don't recognize you. Access is limited. Only the owner can use full features.")
            return False
    
    def check_command_access(self, command: str) -> Tuple[bool, str]:
        """Check if current user can execute a command
        
        Auto-authenticates by scanning face when restricted command is used.
        
        Returns: (allowed, reason)
        """
        # If already authenticated as owner, allow everything
        if self.current_user and self.current_user.user_type == UserType.OWNER:
            return True, ""
        
        # Check if command is restricted
        command_lower = command.lower()
        
        for restricted in self.restricted_commands:
            if restricted in command_lower:
                # This is a restricted command - need to verify identity
                if not self.is_authenticated:
                    # Auto-authenticate: scan face now
                    self._speak("Let me verify your identity first.")
                    if self.authenticate():
                        # Successfully authenticated
                        if self.current_user and self.current_user.user_type == UserType.OWNER:
                            return True, ""
                        else:
                            return False, f"Sorry, only {self.owner_name} can use this feature."
                    else:
                        return False, "Could not verify your identity."
                
                # Already authenticated but not owner
                if self.current_user and self.current_user.access_level >= 3:
                    return False, f"Sorry, only {self.owner_name} can use this feature."
        
        return True, ""
    
    def get_outsider_response(self, command: str) -> str:
        """Get a response for an outsider trying to use restricted features"""
        # If user is authenticated (face registered), allow the action
        if self.is_authenticated:
            return None  # Allow the action - user is verified
        return (
            f"I need to verify your identity first. Please look at the camera so I can recognize you."
        )
    
    def start_monitoring(self):
        """Start continuous face monitoring"""
        if not self.is_available():
            return
        
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print("[FACE AUTH] Continuous monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous face monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("[FACE AUTH] Continuous monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            # Check if re-verification needed
            if time.time() - self.last_verification_time > self.verification_interval:
                profile, confidence = self.verify_user()
                
                if profile.name != self.current_user.name if self.current_user else True:
                    # User changed
                    old_user = self.current_user.name if self.current_user else "None"
                    self.current_user = profile
                    self.is_authenticated = profile.user_type in [UserType.OWNER, UserType.KNOWN_GUEST]
                    print(f"[FACE AUTH] User changed: {old_user} -> {profile.name}")
                
                self.last_verification_time = time.time()
            
            time.sleep(10)  # Check every 10 seconds
    
    def is_owner(self) -> bool:
        """Check if current user is the owner"""
        return self.current_user and self.current_user.user_type == UserType.OWNER
    
    def is_available(self) -> bool:
        """Check if face recognition is available (with facenet fallback)"""
        return (self.face_recognition_available or self.facenet_available) and self.cv2_available
    
    def remove_user(self, name: str) -> bool:
        """Remove a registered user"""
        if name.lower() == self.owner_name.lower():
            self._speak("Cannot remove the owner profile.")
            return False
        
        if name in self.profiles:
            # Remove from profiles
            del self.profiles[name]
            
            # Remove from encodings
            indices_to_remove = [i for i, n in enumerate(self.known_face_names) if n == name]
            for idx in reversed(indices_to_remove):
                del self.known_face_encodings[idx]
                del self.known_face_names[idx]
            
            self._save_data()
            self._speak(f"Removed {name} from registered users.")
            return True
        
        self._speak(f"{name} is not a registered user.")
        return False
    
    def list_registered_users(self) -> List[str]:
        """List all registered users"""
        return list(self.profiles.keys())
