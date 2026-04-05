"""
JARVIS GUI Launcher
Launches JARVIS with the holographic globe interface
"""

import sys
import threading
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.earth_globe import HolographicGlobe, JARVISState
from gui.chat_panel import ChatPanel


def create_combined_interface():
    """Create the combined globe + chat interface"""
    import pygame
    
    # Window size
    WIDTH = 900
    HEIGHT = 650
    
    pygame.init()
    pygame.display.set_caption("JARVIS Interface")
    
    # Create window (borderless)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    clock = pygame.time.Clock()
    
    # Initialize components
    globe = HolographicGlobe(600, HEIGHT)
    chat_panel = ChatPanel(WIDTH, HEIGHT)
    
    # Add some demo messages
    chat_panel.add_message("jarvis", "Good morning, sir. All systems online.")
    chat_panel.add_message("user", "What's the weather today?")
    chat_panel.add_message("jarvis", "It's currently 28°C with clear skies in your location.")
    chat_panel.add_message("user", "Give me the news")
    chat_panel.add_message("jarvis", "Here are today's top headlines...")
    
    # State for demo
    current_state = 0
    states = [JARVISState.IDLE, JARVISState.LISTENING, JARVISState.PROCESSING, JARVISState.SPEAKING]
    state_timer = 0
    
    # Make window always on top (Windows)
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info()["window"]
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 100, 100, 0, 0, 1)
    except:
        pass
    
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    chat_panel.toggle()
                elif event.key == pygame.K_SPACE:
                    # Cycle state
                    current_state = (current_state + 1) % len(states)
                    globe.set_state(states[current_state])
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                
                # Check chat panel click
                if not chat_panel.handle_click(x, y):
                    # Check globe click
                    pass
            
            elif event.type == pygame.MOUSEWHEEL:
                if chat_panel.is_open:
                    chat_panel.handle_scroll(event.y)
        
        # Auto-cycle states for demo
        state_timer += 1
        if state_timer > 180:  # Every 3 seconds at 60fps
            state_timer = 0
            current_state = (current_state + 1) % len(states)
            globe.set_state(states[current_state])
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw globe (calls _draw_frame components manually for integration)
        globe.screen = screen
        globe._draw_scan_lines()
        globe._draw_orbital_rings()
        globe._draw_particles()
        globe._draw_wireframe_globe()
        globe._draw_country_pointer()
        globe._draw_data_panels()
        
        # Update globe animation
        globe.rotation_angle = (globe.rotation_angle + globe.rotation_speed) % 360
        globe.pulse_phase += 1
        globe.particle_phase += 1
        
        # Draw chat panel on top
        chat_panel.render(screen)
        
        # Draw instructions
        font = pygame.font.Font(None, 18)
        instructions = ["ESC: Exit", "C: Toggle Chat", "SPACE: Cycle State"]
        y = HEIGHT - 60
        for text in instructions:
            surf = font.render(text, True, (100, 150, 200))
            screen.blit(surf, (20, y))
            y += 18
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    print("=" * 50)
    print("    JARVIS Holographic Globe Interface")
    print("=" * 50)
    print("Controls:")
    print("  ESC: Exit")
    print("  C: Toggle chat panel")
    print("  SPACE: Cycle through states")
    print("=" * 50)
    
    create_combined_interface()
