"""
JARVIS Ultimate - The Central Brain
====================================
Ties together all components into a unified cognitive system.

Pipeline:
User → Perception → Emotion → Intent → State → Router → Personality → Handlers → Memory
"""

from typing import Optional, Dict, Any
from pathlib import Path
import sys
import queue
import threading

# Ensure core is in path
sys.path.insert(0, str(Path(__file__).parent))

# Core AI components
from core.intent_model import IntentModel, get_intent_model
from core.state_manager import StateManager, get_state_manager
from core.context_memory import ContextMemory, get_context_memory
from core.entity_extractor import EntityExtractor, extract_entities
from core.emotion_router import EmotionRouter
from core.personality import JARVISPersonalityCore, get_personality
from core.intent_router import IntentRouter
from core.proactive_assistant import ProactiveAssistant, get_proactive_assistant
from core.decision_engine import DecisionEngine, DecisionType, get_decision_engine
from core.logger import get_logger
from core.input_priority import InputPriorityManager, PrioritizedInput, InputSource
from core.intent_classifier import ClassificationContext

# Multimodal perception (optional)
try:
    from core.unified_perception import UnifiedPerception, get_unified_perception
    from core.gesture_controller import get_gesture_action
    from core.face_auth import get_face_auth
    from core.multimodal_emotion import get_emotion_fusion
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False

# Get logger for this module
logger = get_logger("brain")

# Optional handlers (import safely)
def safe_import(module_path: str, class_name: str):
    """Safely import a handler class"""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except ImportError as e:
        logger.warning(f"Optional module not available: {module_path} - {e}")
        return None
    except Exception as e:
        logger.error(f"Error importing {module_path}: {e}")
        return None


class JARVISUltimate:
    """
    The central JARVIS brain.
    Unified cognitive system with semantic understanding.
    """
    
    def __init__(self, perception=None):
        logger.info("=" * 40)
        logger.info("Booting JARVIS Ultimate...")
        logger.info("=" * 40)
        
        # Store perception
        self.perception = perception
        
        # Core AI components
        logger.info("Loading core AI...")
        self.intent_model = get_intent_model()
        self.state = get_state_manager()
        self.memory = get_context_memory()
        self.entity_extractor = EntityExtractor()
        self.personality = get_personality(self.state)
        
        # Emotion router
        emotion_detector = self._get_emotion_detector()
        self.emotion_router = EmotionRouter(self.state, emotion_detector)
        
        # Proactive assistant (pattern-based)
        self.proactive = get_proactive_assistant(
            perception, self.memory, self.state
        )
        
        # Decision engine (reasoning layer)
        self.decision_engine = get_decision_engine(self.state)
        
        # Priority manager (input arbitration)
        self.priority_manager = InputPriorityManager()
        
        # Source mapping for all input types
        self.source_map = {
            "voice": InputSource.VOICE,
            "gesture": InputSource.GESTURE,
            "ui": InputSource.UI_BUTTON,
            "system": InputSource.SCHEDULED,
            "emergency": InputSource.EMERGENCY
        }
        
        # Load handlers
        logger.info("Loading handlers...")
        self.handlers = self._load_handlers()
        
        # Intent router
        self.router = IntentRouter(
            self.state,
            self.handlers,
            self.personality,
            self._speak
        )
        
        logger.info("=" * 40)
        logger.info("All systems online. Ready to serve.")
        logger.info("=" * 40)
        
        # Multimodal perception (optional)
        self.unified_perception = None
        self.gesture_mode = False
        
        # Vision queue for async processing (CRITICAL: non-blocking)
        self.vision_queue = queue.Queue(maxsize=5)
        self.vision_running = True
        self.vision_thread = None
        
        if MULTIMODAL_AVAILABLE:
            try:
                self.unified_perception = get_unified_perception(self._on_perception_event)
                self.face_auth = get_face_auth()
                self.emotion_fusion = get_emotion_fusion()
                
                # Start vision worker thread
                self.vision_thread = threading.Thread(target=self._vision_worker, daemon=True)
                self.vision_thread.start()
                
                logger.info("Multimodal perception available (async)")
            except Exception as e:
                logger.warning(f"Multimodal perception not loaded: {e}")
        
    def _get_emotion_detector(self):
        """Get emotion detector if available"""
        try:
            from core.emotion_detector import EmotionDetector
            return EmotionDetector()
        except:
            return None
            
    def _load_handlers(self) -> Dict[str, Any]:
        """Load all available handlers"""
        handlers = {}
        
        # Music handler
        try:
            from core.music_handler import DirectMusicHandler
            handlers["music"] = DirectMusicHandler(self.perception)
            print("[JARVIS]   Music handler loaded")
        except Exception as e:
            print(f"[JARVIS]   Music handler not available: {e}")
            
        # Alarm system
        try:
            from core.alarm_system import AlarmSystem
            handlers["alarm"] = AlarmSystem(self.perception)
            print("[JARVIS]   Alarm system loaded")
        except Exception as e:
            print(f"[JARVIS]   Alarm system not available: {e}")
            
        # App finder
        try:
            from core.app_finder import AppManager
            handlers["apps"] = AppManager(self.perception)
            print("[JARVIS]   App finder loaded")
        except Exception as e:
            print(f"[JARVIS]   App finder not available: {e}")
            
        # AI Search
        try:
            from core.ai_search_handler import AISearchHandler
            handlers["search"] = AISearchHandler(self.perception)
            print("[JARVIS]   AI Search loaded")
        except Exception as e:
            print(f"[JARVIS]   AI Search not available: {e}")
            
        # System control
        try:
            from core.system_control import SystemControl
            handlers["system"] = SystemControl(self.perception)
            print("[JARVIS]   System control loaded")
        except Exception as e:
            print(f"[JARVIS]   System control not available: {e}")
            
        # Calendar
        try:
            from core.calendar_integration import CalendarIntegration
            handlers["calendar"] = CalendarIntegration(self.perception)
            print("[JARVIS]   Calendar loaded")
        except Exception as e:
            print(f"[JARVIS]   Calendar not available: {e}")
            
        # WhatsApp
        try:
            from core.whatsapp import WhatsAppHandler
            handlers["whatsapp"] = WhatsAppHandler(self.perception)
            print("[JARVIS]   WhatsApp loaded")
        except Exception as e:
            print(f"[JARVIS]   WhatsApp not available: {e}")
            
        return handlers
        
    def _speak(self, text: str):
        """Speak response"""
        if self.perception and hasattr(self.perception, 'speak'):
            self.perception.speak(text)
        else:
            print(f"[JARVIS] {text}")
            
    # ========== UNIFIED ENTRY POINT ==========
    
    def handle_input(self, text: str = None, frame=None, source: str = "voice") -> dict:
        """
        SINGLE ENTRY POINT FOR ALL INPUTS.
        
        Pipeline: Priority → Context → Intent → Session Check → Router
        
        Args:
            text: User text/voice input
            frame: Camera frame for vision processing (optional)
            source: Input source ("voice", "gesture", "ui", "system", "emergency")
            
        Returns:
            dict with action, response, confidence, intent, entities, should_speak, state
        """
        import time
        
        result = {
            "action": None,
            "response": "",
            "confidence": 0.0,
            "intent": None,
            "entities": {},
            "should_speak": False,
            "state": self.state.to_dict()
        }
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 0: Vision (background, state-only - NEVER triggers actions)
        # ═══════════════════════════════════════════════════════════
        if frame is not None:
            self._process_vision_async(frame)
            
        if not text or not text.strip():
            return result
            
        # ═══════════════════════════════════════════════════════════
        # STAGE 1: Priority Arbitration
        # ═══════════════════════════════════════════════════════════
        input_source = self.source_map.get(source, InputSource.UI_BUTTON)
        self.priority_manager.add(PrioritizedInput(
            source=input_source,
            text=text,
            timestamp=time.time()
        ))
        
        winner = self.priority_manager.get_winner()
        if winner:
            text = winner.text
            logger.debug(f"[PRIORITY] Winner: {winner.source.name} -> {text[:50]}")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 2: Build Context for Classification
        # ═══════════════════════════════════════════════════════════
        s = self.state.get()
        ctx = ClassificationContext(
            active_app=s.active_app,
            last_intent=s.current_intent,
            last_entities=s.entities,
            last_action=s.last_action,
            user_mood=s.user_mood.value if hasattr(s.user_mood, 'value') else str(s.user_mood),
            conversation_topic=s.current_topic
        )
        # Add last gesture for "again" style commands
        if hasattr(s, 'last_gesture'):
            ctx.last_action = ctx.last_action or s.last_gesture
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 3: Process through text pipeline
        # ═══════════════════════════════════════════════════════════
        result = self._process_text_to_result(text, ctx)
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 4: Session Check (AFTER intent, for non-emergency)
        # ═══════════════════════════════════════════════════════════
        session = self.state.get_session()
        if session.is_paused:
            # Allow emergency commands even when paused
            if result.get("intent") not in ["emergency_stop", "cancel", "stop", "wait"]:
                result["action"] = "paused"
                result["response"] = session.pause_reason or "Multiple users detected. Who should I listen to?"
                result["should_speak"] = True
                result["state"] = self.state.to_dict()
                return result
        
        return result
        
    def _process_vision_async(self, frame):
        """
        Queue frame for async vision processing.
        NON-BLOCKING - just puts frame in queue.
        Background worker does heavy processing.
        """
        try:
            # Non-blocking put - drop frame if queue full (better than blocking)
            self.vision_queue.put_nowait(frame)
        except queue.Full:
            pass  # Drop frame rather than block
            
    def _vision_worker(self):
        """
        Background worker thread for vision processing.
        Runs heavy vision ops (gesture, emotion, face) async.
        ONLY updates StateManager - never touches UI.
        
        Rate limiting:
        - Gesture: every frame (fast, MediaPipe is optimized)
        - Emotion: every 10 frames (DeepFace is slow)
        - Face: every 30 frames (recognition is heavy)
        """
        logger.info("[VISION] Background worker started")
        
        frame_count = 0
        EMOTION_RATE = 10  # Process emotion every N frames
        FACE_RATE = 30     # Process face every N frames
        
        while self.vision_running:
            try:
                # Block with timeout so we can check vision_running
                frame = self.vision_queue.get(timeout=0.5)
                frame_count += 1
                
                # === GESTURE: Every frame (fast) ===
                try:
                    from core.gesture_controller import get_gesture_controller
                    gesture_ctrl = get_gesture_controller()
                    if gesture_ctrl.active:
                        gesture, meta = gesture_ctrl.detect(frame)
                        if gesture not in ["idle", "tracking", "disabled"]:
                            self.state.update_gesture(gesture, meta)
                except Exception:
                    pass  # Gesture detection failed, continue
                
                # === EMOTION: Every 10 frames (slow) ===
                if frame_count % EMOTION_RATE == 0:
                    try:
                        if hasattr(self, 'emotion_fusion') and self.emotion_fusion:
                            emotion = self.emotion_fusion.detect_from_frame(frame)
                            if emotion:
                                self.state.update_emotion(emotion)
                    except Exception:
                        pass  # Emotion detection failed, continue
                
                # === FACE: Every 30 frames (heavy) ===
                if frame_count % FACE_RATE == 0:
                    try:
                        if hasattr(self, 'face_auth') and self.face_auth:
                            # Use stable recognition for anti-flicker
                            user, confidence = self.face_auth.recognize_stable(frame)
                            if user and user != "unknown" and confidence > 0.5:
                                self.state.update_recognized_user(user)
                    except Exception:
                        pass  # Face recognition failed, continue
                    
            except queue.Empty:
                continue  # No frame, keep waiting
            except Exception as e:
                logger.warning(f"[VISION] Worker error: {e}")
            
    def _process_text_to_result(self, text: str, ctx: ClassificationContext = None) -> dict:
        """
        Process text input and return structured result.
        Uses context for smart intent classification.
        """
        result = {
            "action": None,
            "response": "",
            "confidence": 0.0,
            "intent": None,
            "entities": {},
            "should_speak": True,
            "state": {}
        }
        
        try:
            # 1. Resolve pronouns
            text = self.memory.resolve_pronoun(text)
            
            # 2. Detect emotion (state update only)
            self.emotion_router.update_mood(text)
            
            # 3. Check if awaiting clarification
            s = self.state.get()
            if s.awaiting_clarification and s.pending_action:
                response = self._handle_clarification(text, s.pending_action)
                result["action"] = "clarification"
                result["response"] = response
                result["confidence"] = 1.0
                result["state"] = self.state.to_dict()
                return result
                
            # 4. Classify intent WITH CONTEXT (two-stage)
            # Stage 4a: Try context-aware classification first (for vague commands)
            from core.intent_classifier import classify_intent
            ctx_intent, ctx_entities = classify_intent(text, ctx)
            
            # Stage 4b: If context gave us a specific intent, use it; else use embedding model
            if ctx_intent and ctx_intent not in ["conversation", "unknown"]:
                intent = ctx_intent
                confidence = 0.85  # Context-resolved commands have good confidence
            else:
                # Fall back to embedding-based model
                intent, confidence = self.intent_model.classify(text)
            
            result["intent"] = intent
            result["confidence"] = confidence
            
            # Handle low confidence (CONFIDENCE GATING)
            if confidence < 0.5 and intent not in [None, "AMBIGUOUS"]:
                result["action"] = "clarify"
                result["response"] = f"I'm not fully confident ({confidence:.0%}). Did you mean: {intent.replace('_', ' ')}?"
                result["should_speak"] = True
                self.state.set_awaiting_clarification(True, intent)
                result["state"] = self.state.to_dict()
                return result
                
            # Handle ambiguous
            if intent == "AMBIGUOUS":
                options = self.intent_model.get_disambiguation_options(text)
                if options:
                    result["response"] = "I detected multiple possibilities:\n" + "\n".join(options) + "\nWhich did you mean?"
                else:
                    result["response"] = "I'm not sure what you meant. Could you be more specific?"
                result["action"] = "clarify"
                result["state"] = self.state.to_dict()
                return result
                
            # Handle no intent
            if not intent:
                result["action"] = "unknown"
                result["response"] = self.personality.handle_unknown()
                result["state"] = self.state.to_dict()
                return result
                
            # 5. Extract entities
            entities = self.entity_extractor.extract(text, intent)
            result["entities"] = entities
            
            # 6. Decision engine
            decision = self.decision_engine.decide(intent, entities, confidence)
            
            if decision.type == DecisionType.CLARIFY:
                self.state.set_awaiting_clarification(True, intent)
                result["action"] = "clarify"
                result["response"] = decision.message
                result["state"] = self.state.to_dict()
                return result
                
            if decision.type == DecisionType.REFUSE_GENTLY:
                result["action"] = "refused"
                result["response"] = decision.message
                result["state"] = self.state.to_dict()
                return result
                
            # Apply entity modifications
            if decision.modified_entities:
                entities.update(decision.modified_entities)
                result["entities"] = entities
                
            # 7. Update state
            self.state.update_intent(intent, confidence, entities)
            
            # 8. Route to handler
            response = self.router.route(intent, entities)
            
            # 9. Apply personality
            response = self.personality.style(response)
            
            # Add warning/challenge if any
            if decision.type == DecisionType.WARN_THEN_PROCEED:
                response = f"{decision.message}\n{response}"
            
            challenge = self.personality.challenge_bad_decision(intent, entities)
            if challenge:
                response = f"{response} {challenge}"
                
            if decision.type == DecisionType.SUGGEST_ALTERNATIVE and decision.suggestion:
                response = f"{response}\n{decision.suggestion}"
                
            # 10. Record turn
            self.memory.add_exchange(text, response, intent, entities)
            self.state.record_turn(text, response)
            
            result["action"] = intent
            result["response"] = response
            result["state"] = self.state.to_dict()
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            result["action"] = "error"
            result["response"] = "I encountered an issue processing that request."
            result["state"] = self.state.to_dict()
            
        return result
            
    def process_command(self, text: str) -> str:
        """
        LEGACY METHOD - Thin wrapper around handle_input().
        
        For new code, use handle_input() directly.
        This exists for backwards compatibility with voice loop.
        
        Speaks automatically based on result.
        Returns the response text.
        """
        if not text or not text.strip():
            return ""
            
        # === USE THE ONE BRAIN ===
        result = self.handle_input(text=text)
        
        # Speak if needed (UI layer responsibility, but kept for legacy)
        if result.get("should_speak", True) and result.get("response"):
            self._speak(result["response"])
            
        # Smart follow-up (proactive layer)
        if result.get("action") and result.get("action") not in ["clarify", "error", "unknown"]:
            try:
                followup = self.proactive.get_smart_suggestion(
                    result.get("intent"), 
                    result.get("entities", {})
                )
                if followup:
                    self._speak(followup)
            except:
                pass
        
        return result.get("response", "")
        
    def _handle_clarification(self, text: str, pending_action: str) -> str:
        """Handle response to clarification request"""
        # Clear the flag
        self.state.set_awaiting_clarification(False)
        
        # Try to process as the pending intent
        intent = pending_action
        entities = self.entity_extractor.extract(text, intent)
        
        # Force confidence since user is clarifying
        self.state.update_intent(intent, 0.90, entities)
        
        return self.router.route(intent, entities)
        
    def _learn_from_interaction(self, text: str, intent: str, entities: Dict):
        """Learn user preferences from interactions"""
        text_lower = text.lower()
        
        # Music app preference
        if intent == "play_music":
            if "spotify" in text_lower:
                self.memory.learn_preference("music_app", True)
                self.memory.set_preference("spotify", 
                    self.memory.get_preference("spotify", 0.5) + 0.1)
            elif "youtube" in text_lower:
                self.memory.set_preference("youtube_music",
                    self.memory.get_preference("youtube_music", 0.5) + 0.1)
                    
        # Remember useful facts
        if intent == "set_alarm":
            time = entities.get("time")
            if time:
                self.memory.remember(f"User set alarm for {time}", "routine")
                
    def start(self):
        """Start interactive JARVIS session"""
        # Greeting
        greeting = self.personality.greet()
        self._speak(greeting)
        
        # Main loop
        while True:
            try:
                # Get input
                if self.perception and hasattr(self.perception, 'listen'):
                    text = self.perception.listen()
                else:
                    text = input("You: ").strip()
                    
                if not text:
                    continue
                    
                # Exit commands
                if text.lower() in ["exit", "quit", "shutdown", "goodbye", "bye"]:
                    farewell = self.personality.farewell()
                    self._speak(farewell)
                    break
                    
                # Process
                self.process_command(text)
                
            except KeyboardInterrupt:
                farewell = self.personality.farewell()
                self._speak(farewell)
                break
            except Exception as e:
                print(f"[JARVIS] Error: {e}")
                
    def shutdown(self):
        """Clean shutdown"""
        farewell = self.personality.farewell()
        self._speak(farewell)
        
        # Stop alarm threads etc.
        if "alarm" in self.handlers:
            try:
                self.handlers["alarm"].stop()
            except:
                pass
                
        # Stop vision worker thread
        self.vision_running = False
        if self.vision_thread and self.vision_thread.is_alive():
            self.vision_thread.join(timeout=1.0)
                
        # Stop multimodal perception
        if self.unified_perception:
            try:
                self.unified_perception.close()
            except:
                pass
                
    # ========== MULTIMODAL PERCEPTION ==========
    
    def _on_perception_event(self, event):
        """Handle perception events from unified perception"""
        if event.event_type == "gesture":
            self._handle_gesture_event(event)
        elif event.event_type == "recognition":
            self._handle_face_recognition(event)
        elif event.event_type == "emotion":
            self._handle_emotion_event(event)
            
    def _handle_gesture_event(self, event):
        """
        Handle gesture events by routing through handle_input().
        
        IMPORTANT: Gestures go through the FULL pipeline:
        Priority → Context → Intent → Session → Router
        
        They do NOT call handlers directly.
        """
        if not self.gesture_mode:
            return
            
        gesture = event.data.get("gesture")
        if not gesture:
            return
            
        # Get active app for context-aware gestures
        active_app = self.state.get().active_app or "default"
        
        # Map gesture to command text
        if MULTIMODAL_AVAILABLE:
            action = get_gesture_action(gesture, active_app)
        else:
            action = gesture
            
        logger.info(f"[GESTURE] {gesture} -> {action}")
        
        # ═══════════════════════════════════════════════════════════
        # ROUTE THROUGH handle_input() - NOT direct handler calls!
        # ═══════════════════════════════════════════════════════════
        # Map gesture actions to command text
        gesture_commands = {
            "next": "next",
            "next_track": "next track",
            "previous": "previous",
            "previous_track": "previous track",
            "play_pause": "play pause",
            "pause": "pause",
            "play": "play",
            "volume_up": "volume up",
            "volume_down": "volume down",
            "scroll_up": "scroll up",
            "scroll_down": "scroll down",
            "cancel": "cancel",
            "stop": "stop",
        }
        
        command_text = gesture_commands.get(action, action)
        
        # Route through the pipeline with gesture source
        result = self.handle_input(text=command_text, source="gesture")
        
        # Speak the response if any
        if result.get("should_speak") and result.get("response"):
            self._speak(result["response"])
            
    def _handle_face_recognition(self, event):
        """Handle face recognition events"""
        user = event.data.get("user")
        if user and user != "unknown":
            # Personalized greeting
            if not self.face_auth.was_seen_recently(user, minutes=30):
                self._speak(f"Welcome back, {user}.")
                
            # Update state
            self.state.recognized_user = user
            
    def _handle_emotion_event(self, event):
        """Handle emotion events from face/voice"""
        emotion = event.data.get("emotion", "neutral")
        
        # Update state manager with detected emotion
        mood_mapping = {
            "happy": "HAPPY",
            "sad": "SAD", 
            "angry": "ANGRY",
            "frustrated": "FRUSTRATED",
            "tired": "TIRED",
            "neutral": "NEUTRAL",
        }
        
        from core.state_manager import UserMood
        mood = getattr(UserMood, mood_mapping.get(emotion, "NEUTRAL"), UserMood.NEUTRAL)
        self.state.update_mood(mood)
        
    def enable_gestures(self):
        """Enable gesture control mode"""
        self.gesture_mode = True
        if self.unified_perception:
            self.unified_perception.enable_gestures()
        self._speak("Gesture control enabled.")
        
    def disable_gestures(self):
        """Disable gesture control mode"""
        self.gesture_mode = False
        if self.unified_perception:
            self.unified_perception.disable_gestures()
        self._speak("Gesture control disabled.")
        
    def start_camera(self):
        """Start camera for visual perception"""
        if self.unified_perception:
            success = self.unified_perception.start_camera()
            if success:
                self._speak("Camera started. Visual perception active.")
            else:
                self._speak("Failed to start camera.")
            return success
        return False
        
    def register_face(self, name: str):
        """Register current face to name"""
        if self.unified_perception:
            success, message = self.unified_perception.register_face(name)
            self._speak(message)
            return success
        return False


# Convenience function
def create_jarvis(perception=None) -> JARVISUltimate:
    """Create a JARVIS instance"""
    return JARVISUltimate(perception)


# Main entry point
if __name__ == "__main__":
    jarvis = JARVISUltimate()
    jarvis.start()
