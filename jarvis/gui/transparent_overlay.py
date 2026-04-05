"""
Transparent Overlay Window - Always-on-top transparent JARVIS interface
Uses pygame with Windows-specific transparency
"""

import pygame
import ctypes
from ctypes import wintypes
import win32api
import win32con
import win32gui
import threading
import time
from typing import Optional, Callable, Tuple


class TransparentOverlay:
    """Transparent always-on-top overlay window for JARVIS"""
    
    def __init__(self, width: int = 600, height: int = 600, position: Tuple[int, int] = None):
        print("[OVERLAY] Initializing Transparent Overlay...")
        
        self.width = width
        self.height = height
        
        # Default position: bottom right
        if position is None:
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            self.x = screen_width - width - 50
            self.y = screen_height - height - 100
        else:
            self.x, self.y = position
        
        # Transparency settings
        self.transparency_key = (0, 0, 0)  # Black is transparent
        self.alpha = 255  # Overall opacity (0-255)
        
        # State
        self.running = False
        self.screen = None
        self.clock = None
        self.hwnd = None
        
        # Callbacks
        self.on_render: Optional[Callable] = None
        self.on_click: Optional[Callable] = None
        self.on_hover: Optional[Callable] = None
        
        print("[OVERLAY] Overlay Ready")
    
    def _init_window(self):
        """Initialize pygame with transparency"""
        pygame.init()
        
        # Create window
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.NOFRAME
        )
        pygame.display.set_caption("JARVIS Overlay")
        self.clock = pygame.time.Clock()
        
        # Get window handle
        self.hwnd = pygame.display.get_wm_info()["window"]
        
        # Make window transparent and always on top
        self._set_window_properties()
        
        # Position window
        win32gui.SetWindowPos(
            self.hwnd, win32con.HWND_TOPMOST,
            self.x, self.y,
            self.width, self.height,
            win32con.SWP_SHOWWINDOW
        )
    
    def _set_window_properties(self):
        """Set Windows-specific transparency properties"""
        # Get current style
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        
        # Add layered and transparent styles
        style |= win32con.WS_EX_LAYERED
        style |= win32con.WS_EX_TRANSPARENT  # Click-through for transparent areas
        style |= win32con.WS_EX_TOOLWINDOW   # No taskbar button
        
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
        
        # Set transparency color key (black = transparent)
        win32gui.SetLayeredWindowAttributes(
            self.hwnd,
            win32api.RGB(*self.transparency_key),
            self.alpha,
            win32con.LWA_COLORKEY | win32con.LWA_ALPHA
        )
    
    def set_click_through(self, click_through: bool):
        """Toggle click-through mode"""
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        
        if click_through:
            style |= win32con.WS_EX_TRANSPARENT
        else:
            style &= ~win32con.WS_EX_TRANSPARENT
        
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
    
    def set_position(self, x: int, y: int):
        """Set window position"""
        self.x = x
        self.y = y
        
        if self.hwnd:
            win32gui.SetWindowPos(
                self.hwnd, win32con.HWND_TOPMOST,
                x, y, 0, 0,
                win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
    
    def set_opacity(self, alpha: int):
        """Set overall window opacity (0-255)"""
        self.alpha = max(0, min(255, alpha))
        
        if self.hwnd:
            win32gui.SetLayeredWindowAttributes(
                self.hwnd,
                win32api.RGB(*self.transparency_key),
                self.alpha,
                win32con.LWA_COLORKEY | win32con.LWA_ALPHA
            )
    
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.on_click:
                    self.on_click(event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
                if self.on_hover:
                    self.on_hover(event.pos)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def render_loop(self):
        """Main render loop"""
        self._init_window()
        self.running = True
        
        while self.running:
            self._handle_events()
            
            # Clear with transparency key color
            self.screen.fill(self.transparency_key)
            
            # Call custom render function
            if self.on_render:
                self.on_render(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
    
    def start(self):
        """Start overlay in background thread"""
        self.render_thread = threading.Thread(target=self.render_loop, daemon=True)
        self.render_thread.start()
        print("[OVERLAY] Overlay started")
    
    def stop(self):
        """Stop the overlay"""
        self.running = False
        print("[OVERLAY] Overlay stopped")
    
    def is_running(self) -> bool:
        return self.running


class JARVISOverlay:
    """Combined JARVIS overlay with globe and controls"""
    
    def __init__(self):
        print("[JARVIS OVERLAY] Creating JARVIS Overlay...")
        
        # Import globe components
        try:
            from gui.earth_globe import HolographicGlobe, JARVISState
            self.globe = HolographicGlobe(400, 400)
            self.HAS_GLOBE = True
        except ImportError:
            self.globe = None
            self.HAS_GLOBE = False
        
        # Create overlay
        self.overlay = TransparentOverlay(450, 500)
        self.overlay.on_render = self._render
        self.overlay.on_click = self._on_click
        
        # State
        self.state = "idle"
        self.status_text = "JARVIS Online"
        
        # Animation
        self.pulse_phase = 0
        
        print("[JARVIS OVERLAY] Ready")
    
    def _render(self, screen):
        """Render JARVIS interface on transparent surface"""
        import math
        
        self.pulse_phase += 1
        center_x, center_y = 225, 200
        
        # Draw glow background (non-black so visible)
        pulse = 0.5 + 0.5 * math.sin(self.pulse_phase * 0.05)
        glow_color = (0, int(100 + 50 * pulse), int(150 + 50 * pulse))
        
        # Outer glow rings
        for i in range(3):
            radius = 150 + i * 20
            alpha = int(50 - i * 15)
            glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*glow_color, alpha), (radius, radius), radius, 2)
            screen.blit(glow_surface, (center_x - radius, center_y - radius))
        
        # Main orb
        orb_radius = 80
        orb_color = (0, 200, 255)
        
        # Orb glow
        for i in range(5):
            r = orb_radius + i * 5
            alpha = 100 - i * 20
            glow_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*orb_color, alpha), (r + 5, r + 5), r, 3)
            screen.blit(glow_surf, (center_x - r - 5, center_y - r - 5))
        
        # Core orb
        pygame.draw.circle(screen, (0, 150, 200), (center_x, center_y), orb_radius)
        pygame.draw.circle(screen, orb_color, (center_x, center_y), orb_radius, 2)
        
        # Status text
        font = pygame.font.Font(None, 28)
        status_surface = font.render(self.status_text, True, (0, 255, 255))
        text_x = center_x - status_surface.get_width() // 2
        screen.blit(status_surface, (text_x, center_y + orb_radius + 30))
        
        # State indicator
        state_colors = {
            "idle": (0, 150, 200),
            "listening": (0, 255, 150),
            "processing": (255, 200, 0),
            "speaking": (0, 200, 255),
        }
        state_color = state_colors.get(self.state, (0, 150, 200))
        
        # Pulsing state dot
        dot_size = int(10 + 5 * pulse)
        pygame.draw.circle(screen, state_color, (center_x, center_y + orb_radius + 70), dot_size)
        
        # State label
        small_font = pygame.font.Font(None, 20)
        state_text = small_font.render(self.state.upper(), True, (150, 200, 220))
        screen.blit(state_text, (center_x - state_text.get_width() // 2, center_y + orb_radius + 90))
    
    def _on_click(self, pos):
        """Handle click on overlay"""
        center_x, center_y = 225, 200
        dx = pos[0] - center_x
        dy = pos[1] - center_y
        dist = (dx**2 + dy**2) ** 0.5
        
        if dist < 100:
            # Clicked on orb - toggle listening
            print("[JARVIS OVERLAY] Orb clicked - toggling listening")
    
    def set_state(self, state: str):
        """Set current state"""
        self.state = state.lower()
    
    def set_status(self, text: str):
        """Set status text"""
        self.status_text = text
    
    def start(self):
        """Start the overlay"""
        self.overlay.start()
    
    def stop(self):
        """Stop the overlay"""
        self.overlay.stop()


# Demo
if __name__ == "__main__":
    print("Starting JARVIS Transparent Overlay...")
    
    overlay = JARVISOverlay()
    overlay.start()
    
    # Demo state changes
    states = ["idle", "listening", "processing", "speaking"]
    state_idx = 0
    
    try:
        while overlay.overlay.is_running():
            time.sleep(3)
            state_idx = (state_idx + 1) % len(states)
            overlay.set_state(states[state_idx])
            overlay.set_status(f"JARVIS - {states[state_idx].title()}")
    except KeyboardInterrupt:
        overlay.stop()
