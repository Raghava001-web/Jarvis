"""
Integrated JARVIS HUD - Combines all visual elements with JARVIS core
Full holographic interface with real-time voice integration
"""

import pygame
import threading
import queue
import time
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.advanced_hud import HUD, State as JARVISState, Theme as HUDColors
from gui.waveform_visualizer import AudioWaveformVisualizer, CircularWaveform, VoiceActivityIndicator


class IntegratedJARVISHUD:
    """Integrated JARVIS HUD with all visual elements"""
    
    def __init__(self, width: int = 1400, height: int = 900):
        print("[INTEGRATED HUD] Initializing...")
        
        self.width = width
        self.height = height
        
        # Main HUD (now using new reactive HUD class)
        self.hud = HUD()
        
        # Waveform visualizers
        self.linear_waveform = AudioWaveformVisualizer(300, 60)
        self.circular_waveform = CircularWaveform(
            width // 2, height // 2, 
            150  # Fixed radius since HUD globe may vary
        )
        self.voice_indicator = VoiceActivityIndicator(width // 2 - 25, height // 2 + 280)
        
        # State
        self.state = JARVISState.IDLE
        self.audio_level = 0
        
        # Message queue for communication with JARVIS core
        self.message_queue = queue.Queue()
        
        # Chat messages
        self.chat_messages = []
        self.max_messages = 8
        
        # Status text
        self.status_text = "JARVIS ONLINE"
        self.sub_status = "Ready to assist"
        
        # Emotion and user recognition state (for vision feedback display)
        self.current_emotion = "neutral"
        self.recognized_user = None
        self.emotion_colors = {
            "happy": (0, 255, 120),      # Green
            "sad": (100, 150, 255),      # Blue
            "angry": (255, 80, 80),      # Red
            "surprised": (255, 200, 0),  # Yellow
            "fear": (180, 100, 255),     # Purple
            "disgust": (150, 100, 50),   # Brown
            "neutral": (0, 200, 240),    # Cyan (default)
        }
        
        print("[INTEGRATED HUD] Ready")
    
    def set_emotion(self, emotion: str):
        """Set current detected emotion for display"""
        self.current_emotion = emotion.lower() if emotion else "neutral"
    
    def set_user(self, user: str):
        """Set recognized user for display"""
        self.recognized_user = user
    
    def set_state(self, state: JARVISState):
        """Set JARVIS state (Note: In new architecture, state is set via StateManager)"""
        self.state = state
        # self.hud.set_state(state)  # HUD is now reactive - reads from StateManager
        
        # Update waveform states
        if state == JARVISState.LISTENING:
            self.linear_waveform.set_listening(True)
            self.circular_waveform.set_active(True)
            self.voice_indicator.set_active(True)
        elif state == JARVISState.SPEAKING:
            self.linear_waveform.set_speaking(True)
            self.circular_waveform.set_active(True)
            self.voice_indicator.set_active(True)
        elif state == JARVISState.PROCESSING:
            self.linear_waveform.set_processing(True)
            self.circular_waveform.set_active(False)
            self.voice_indicator.set_active(False)
        else:
            self.linear_waveform.set_listening(False)
            self.linear_waveform.set_speaking(False)
            self.linear_waveform.set_processing(False)
            self.circular_waveform.set_active(False)
            self.voice_indicator.set_active(False)
    
    def set_audio_level(self, level: float):
        """Set current audio input level"""
        self.audio_level = level
        self.linear_waveform.set_audio_level(level)
        self.circular_waveform.set_audio_level(level)
    
    def set_status(self, main_text: str, sub_text: str = ""):
        """Set status text"""
        self.status_text = main_text
        self.sub_status = sub_text
    
    def add_message(self, role: str, text: str):
        """Add a chat message"""
        self.chat_messages.append({
            "role": role,
            "text": text,
            "time": time.strftime("%H:%M")
        })
        
        # Limit messages
        while len(self.chat_messages) > self.max_messages:
            self.chat_messages.pop(0)
    
    def _draw_status_display(self, screen):
        """Draw main status display below globe"""
        cx = self.width // 2
        cy = self.height // 2 + 150 + 220  # Using fixed globe radius estimate
        
        # Main status
        font = pygame.font.Font(None, 32)
        status_surf = font.render(self.status_text, True, HUDColors.PRIMARY)
        screen.blit(status_surf, (cx - status_surf.get_width() // 2, cy))
        
        # Sub status
        small_font = pygame.font.Font(None, 20)
        sub_surf = small_font.render(self.sub_status, True, HUDColors.TEXT_DIM)
        screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, cy + 30))
    
    def _draw_chat_panel(self, screen):
        """Draw compact chat history panel"""
        panel_x = 20
        panel_y = self.height - 280
        panel_width = 280
        panel_height = 260
        
        # Panel background
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (10, 25, 40, 200), (0, 0, panel_width, panel_height))
        pygame.draw.rect(panel_surf, HUDColors.SECONDARY, (0, 0, panel_width, panel_height), 1)
        screen.blit(panel_surf, (panel_x, panel_y))
        
        # Title
        font = pygame.font.Font(None, 18)
        title_surf = font.render("CONVERSATION_LOG", True, HUDColors.ACCENT)
        screen.blit(title_surf, (panel_x + 10, panel_y + 8))
        
        # Separator
        pygame.draw.line(screen, HUDColors.SECONDARY,
                        (panel_x + 5, panel_y + 25),
                        (panel_x + panel_width - 5, panel_y + 25), 1)
        
        # Messages
        small_font = pygame.font.Font(None, 16)
        y = panel_y + 35
        
        for msg in self.chat_messages[-6:]:
            is_user = msg["role"].lower() == "user"
            
            # Role indicator
            role_color = HUDColors.ACCENT if is_user else HUDColors.PRIMARY
            role_text = "YOU" if is_user else "JARVIS"
            role_surf = small_font.render(f"[{role_text}]", True, role_color)
            screen.blit(role_surf, (panel_x + 10, y))
            
            # Message text (truncate if too long)
            text = msg["text"]
            if len(text) > 35:
                text = text[:32] + "..."
            
            text_surf = small_font.render(text, True, HUDColors.TEXT)
            screen.blit(text_surf, (panel_x + 60, y))
            
            y += 18
    
    def _draw_command_suggestions(self, screen):
        """Draw command suggestions panel"""
        panel_x = self.width - 220
        panel_y = self.height - 200
        
        suggestions = [
            "Try saying:",
            "\"What's the weather?\"",
            "\"Tell me a joke\"",
            "\"Set a reminder\"",
            "\"Help\"",
        ]
        
        font = pygame.font.Font(None, 16)
        
        for i, text in enumerate(suggestions):
            color = HUDColors.ACCENT if i == 0 else HUDColors.TEXT_DIM
            text_surf = font.render(text, True, color)
            screen.blit(text_surf, (panel_x, panel_y + i * 18))
    
    def update(self):
        """Update all components"""
        self.hud.update()
        self.linear_waveform.update()
        self.circular_waveform.update()
        self.voice_indicator.update()
    
    def render(self, screen):
        """Render everything"""
        # Main HUD
        self.hud.render(screen)
        
        # Circular waveform around globe
        self.circular_waveform.render(screen)
        
        # Voice activity indicator
        self.voice_indicator.render(screen)
        
        # Linear waveform at bottom
        waveform_x = self.width // 2 - 150
        waveform_y = self.height - 100
        self.linear_waveform.render(screen, waveform_x, waveform_y)
        
        # Status display
        self._draw_status_display(screen)
        
        # Chat panel
        self._draw_chat_panel(screen)
        
        # Command suggestions
        self._draw_command_suggestions(screen)
        
        # Vision status panel (emotion + user recognition)
        self._draw_vision_panel(screen)
    
    def _draw_vision_panel(self, screen):
        """Draw emotion and user recognition panel"""
        panel_x = self.width - 220
        panel_y = 20
        panel_width = 200
        panel_height = 100
        
        # Panel background
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (10, 25, 40, 200), (0, 0, panel_width, panel_height))
        pygame.draw.rect(panel_surf, HUDColors.SECONDARY, (0, 0, panel_width, panel_height), 1)
        screen.blit(panel_surf, (panel_x, panel_y))
        
        # Title
        font = pygame.font.Font(None, 18)
        title_surf = font.render("VISION_STATUS", True, HUDColors.ACCENT)
        screen.blit(title_surf, (panel_x + 10, panel_y + 8))
        
        # Separator
        pygame.draw.line(screen, HUDColors.SECONDARY,
                        (panel_x + 5, panel_y + 25),
                        (panel_x + panel_width - 5, panel_y + 25), 1)
        
        small_font = pygame.font.Font(None, 16)
        
        # User display
        user_text = self.recognized_user if self.recognized_user else "Unknown"
        user_color = HUDColors.PRIMARY if self.recognized_user else HUDColors.TEXT_DIM
        user_surf = small_font.render(f"User: {user_text}", True, user_color)
        screen.blit(user_surf, (panel_x + 10, panel_y + 35))
        
        # Emotion display with colored indicator
        emotion_color = self.emotion_colors.get(self.current_emotion, HUDColors.PRIMARY)
        
        # Emotion indicator circle
        pygame.draw.circle(screen, emotion_color, (panel_x + 20, panel_y + 62), 8)
        pygame.draw.circle(screen, HUDColors.PRIMARY, (panel_x + 20, panel_y + 62), 8, 1)
        
        emotion_text = self.current_emotion.upper()
        emotion_surf = small_font.render(f"Mood: {emotion_text}", True, emotion_color)
        screen.blit(emotion_surf, (panel_x + 35, panel_y + 55))
        
        # Status indicator (pulsing dot)
        import math
        import time as time_module
        pulse = (math.sin(time_module.time() * 3) + 1) / 2  # 0-1 pulsing
        dot_size = int(3 + pulse * 3)
        pygame.draw.circle(screen, HUDColors.INDICATOR_ACTIVE, 
                          (panel_x + panel_width - 15, panel_y + 12), dot_size)


def run_integrated_hud():
    """Run the integrated HUD"""
    pygame.init()
    
    # Get screen info for fullscreen option
    info = pygame.display.Info()
    
    # Window mode
    screen = pygame.display.set_mode((1400, 900))
    pygame.display.set_caption("J.A.R.V.I.S. - Advanced Interface")
    
    clock = pygame.time.Clock()
    hud = IntegratedJARVISHUD(1400, 900)
    
    # Demo messages
    hud.add_message("user", "What's the weather today?")
    hud.add_message("jarvis", "Currently 24°C and partly cloudy in your area.")
    hud.add_message("user", "Set a reminder for 5 PM")
    hud.add_message("jarvis", "Reminder set for 5:00 PM, sir.")
    
    running = True
    state_idx = 0
    states = list(JARVISState)
    
    # Simulated audio level
    audio_phase = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    state_idx = (state_idx + 1) % len(states)
                    hud.set_state(states[state_idx])
                    hud.set_status(f"STATE: {states[state_idx].value.upper()}", "Press SPACE to change")
                elif event.key == pygame.K_1:
                    hud.set_state(JARVISState.IDLE)
                    hud.set_status("JARVIS ONLINE", "Awaiting command")
                elif event.key == pygame.K_2:
                    hud.set_state(JARVISState.LISTENING)
                    hud.set_status("LISTENING", "Speak now...")
                elif event.key == pygame.K_3:
                    hud.set_state(JARVISState.PROCESSING)
                    hud.set_status("PROCESSING", "Analyzing request...")
                elif event.key == pygame.K_4:
                    hud.set_state(JARVISState.SPEAKING)
                    hud.set_status("SPEAKING", "Responding...")
        
        # Simulate audio level when in listening/speaking state
        if hud.state in [JARVISState.LISTENING, JARVISState.SPEAKING]:
            import math
            import random
            audio_phase += 0.1
            level = 0.3 + 0.3 * math.sin(audio_phase) + random.uniform(0, 0.2)
            hud.set_audio_level(level)
        else:
            hud.set_audio_level(0)
        
        hud.update()
        hud.render(screen)
        
        # FPS display
        font = pygame.font.Font(None, 16)
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, HUDColors.TEXT_DIM)
        screen.blit(fps_text, (10, self.height - 20) if hasattr(self, 'height') else (10, 880))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    run_integrated_hud()
