"""
JARVIS Unified Launcher - Runs voice assistant with advanced HUD
Combines core JARVIS functionality with the holographic interface
"""

import pygame
import threading
import queue
import time
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.integrated_hud import IntegratedJARVISHUD
from enum import Enum

# Define our own State enum (JARVISState in state_manager is a dataclass, not enum)
class JARVISState(Enum):
    STARTUP = "STARTUP"
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class JARVISWithHUD:
    """JARVIS with integrated HUD interface"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("        INITIALIZING J.A.R.V.I.S. UNIFIED SYSTEM")
        print("="*60 + "\n")
        
        # Command queue for thread communication
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # State
        self.running = False
        self.jarvis_core = None
        
        # HUD
        self.hud = None
        
        # Try to import JARVIS core
        self._init_jarvis_core()
        
        print("[UNIFIED] Initialization Complete")
    
    def _init_jarvis_core(self):
        """Initialize JARVIS core system"""
        try:
            from core.jarvis_ultimate import JARVISUltimate
            self.jarvis_core = JARVISUltimate()
            print("[UNIFIED] JARVIS Core loaded successfully")
        except Exception as e:
            print(f"[UNIFIED] Could not load JARVIS core: {e}")
            print("[UNIFIED] Running in demo mode (HUD only)")
            self.jarvis_core = None
    
    def _voice_thread(self):
        """
        Voice listening thread.
        PURE DISPATCHER - only queues results, never calls UI directly.
        """
        if not self.jarvis_core:
            return
        
        while self.running:
            try:
                # Update HUD to listening state
                self.response_queue.put(("state", JARVISState.LISTENING))
                
                # Listen for command
                command = self.jarvis_core.perception.listen()
                
                if command:
                    # Update HUD to processing
                    self.response_queue.put(("state", JARVISState.PROCESSING))
                    self.response_queue.put(("message", ("user", command)))
                    
                    # === USE UNIFIED ENTRY POINT ===
                    # This returns structured dict, no side effects
                    result = self.jarvis_core.handle_input(text=command)
                    
                    # Queue the result for UI to handle
                    self.response_queue.put(("result", result))
                    
                    # Update state based on result
                    self.response_queue.put(("state", JARVISState.SPEAKING))
                    
                    # Queue the response message
                    if result.get("response"):
                        self.response_queue.put(("message", ("jarvis", result["response"])))
                        
                        # UI will handle speaking via perception
                        if result.get("should_speak") and self.jarvis_core.perception:
                            self.jarvis_core.perception.speak(result["response"])
                    
                    # Check for exit
                    if result.get("action") in ["shutdown", "goodbye", "exit"]:
                        self.running = False
                        break
                
                # Return to idle
                self.response_queue.put(("state", JARVISState.IDLE))
                
            except Exception as e:
                print(f"[VOICE] Error: {e}")
                time.sleep(1)
    
    def _demo_mode_thread(self):
        """Demo mode when JARVIS core not available"""
        states = [JARVISState.IDLE, JARVISState.LISTENING, 
                  JARVISState.PROCESSING, JARVISState.SPEAKING]
        
        demo_messages = [
            ("user", "What's the weather today?"),
            ("jarvis", "Currently 24°C and partly cloudy in Bangalore."),
            ("user", "Set a reminder for 5 PM"),
            ("jarvis", "Reminder set for 5:00 PM, sir."),
            ("user", "Tell me a joke"),
            ("jarvis", "Why don't scientists trust atoms? Because they make up everything!"),
            ("user", "System status"),
            ("jarvis", "All systems operating normally. CPU at 45%, memory at 62%."),
        ]
        
        msg_idx = 0
        state_idx = 0
        
        while self.running:
            time.sleep(3)
            
            # Cycle through demo
            if state_idx < len(states):
                self.response_queue.put(("state", states[state_idx]))
                
                if state_idx == 1:  # Listening
                    self.response_queue.put(("status", ("LISTENING", "Speak now...")))
                elif state_idx == 2:  # Processing
                    self.response_queue.put(("status", ("PROCESSING", "Analyzing...")))
                elif state_idx == 3:  # Speaking
                    self.response_queue.put(("status", ("RESPONDING", "")))
                    if msg_idx < len(demo_messages):
                        self.response_queue.put(("message", demo_messages[msg_idx]))
                        msg_idx = (msg_idx + 1) % len(demo_messages)
                else:
                    self.response_queue.put(("status", ("JARVIS ONLINE", "Awaiting command")))
                
                state_idx = (state_idx + 1) % len(states)
    
    def run(self):
        """Run JARVIS with HUD"""
        pygame.init()
        
        screen = pygame.display.set_mode((1400, 900))
        pygame.display.set_caption("J.A.R.V.I.S. - Just A Rather Very Intelligent System")
        
        clock = pygame.time.Clock()
        self.hud = IntegratedJARVISHUD(1400, 900)
        
        self.running = True
        
        # Start voice thread or demo mode
        if self.jarvis_core:
            voice_thread = threading.Thread(target=self._voice_thread, daemon=True)
            voice_thread.start()
            self.hud.set_status("JARVIS ONLINE", "Voice recognition active")
        else:
            demo_thread = threading.Thread(target=self._demo_mode_thread, daemon=True)
            demo_thread.start()
            self.hud.set_status("DEMO MODE", "JARVIS core not loaded")
        
        # Audio simulation for demo
        audio_phase = 0
        
        while self.running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        # Manual state cycle for testing
                        states = list(JARVISState)
                        current_idx = states.index(self.hud.state)
                        next_idx = (current_idx + 1) % len(states)
                        self.hud.set_state(states[next_idx])
            
            # Process messages from voice thread
            while not self.response_queue.empty():
                try:
                    msg_type, data = self.response_queue.get_nowait()
                    
                    if msg_type == "state":
                        self.hud.set_state(data)
                    elif msg_type == "message":
                        role, text = data
                        self.hud.add_message(role, text)
                    elif msg_type == "status":
                        main_text, sub_text = data
                        self.hud.set_status(main_text, sub_text)
                    elif msg_type == "result":
                        # === HANDLE STRUCTURED RESULT FROM handle_input() ===
                        # This is state data from the brain - update HUD accordingly
                        result = data
                        
                        # Update status based on action
                        action = result.get("action", "unknown")
                        confidence = result.get("confidence", 0)
                        
                        if action == "clarify":
                            self.hud.set_status("CLARIFYING", f"Confidence: {confidence:.0%}")
                        elif action == "error":
                            self.hud.set_status("ERROR", result.get("response", "Unknown error"))
                        elif confidence > 0.8:
                            self.hud.set_status("EXECUTING", f"{action} ({confidence:.0%})")
                        else:
                            self.hud.set_status("PROCESSING", f"{action}")
                            
                except queue.Empty:
                    break
            
            # === OBSERVE STATE MANAGER FOR VISION DATA ===
            # Poll StateManager for gesture, emotion, face updates
            if self.jarvis_core:
                try:
                    from core.state_manager import get_state_manager
                    state = get_state_manager().get()
                    
                    # Update gesture display
                    if hasattr(state, 'last_gesture') and state.last_gesture:
                        gesture = state.last_gesture
                        if gesture not in ['idle', 'tracking', 'disabled']:
                            self.hud.set_status("GESTURE", f"{gesture.upper()}")
                    
                    # Update emotion display
                    if hasattr(state, 'last_emotion') and state.last_emotion:
                        emotion = state.last_emotion
                        if emotion not in ['neutral', None]:
                            # Update HUD emotion indicator if available
                            if hasattr(self.hud, 'set_emotion'):
                                self.hud.set_emotion(emotion)
                    
                    # Update recognized user
                    if hasattr(state, 'recognized_user') and state.recognized_user:
                        user = state.recognized_user
                        if user and user != 'unknown':
                            if hasattr(self.hud, 'set_user'):
                                self.hud.set_user(user)
                except Exception:
                    pass  # State observation failed, continue
            
            # Simulate audio level based on state
            if self.hud.state in [JARVISState.LISTENING, JARVISState.SPEAKING]:
                import math
                import random
                audio_phase += 0.1
                level = 0.3 + 0.3 * math.sin(audio_phase) + random.uniform(0, 0.2)
                self.hud.set_audio_level(level)
            else:
                self.hud.set_audio_level(0)
            
            # Update and render
            self.hud.update()
            self.hud.render(screen)
            
            # FPS
            font = pygame.font.Font(None, 16)
            fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (0, 100, 140))
            screen.blit(fps_text, (10, 880))
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        print("\n[UNIFIED] JARVIS shutdown complete")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("     J.A.R.V.I.S. - Just A Rather Very Intelligent System")
    print("="*60)
    print("\nPress ESC to exit | Press SPACE to cycle states")
    print("-"*60 + "\n")
    
    jarvis = JARVISWithHUD()
    jarvis.run()


if __name__ == "__main__":
    main()
