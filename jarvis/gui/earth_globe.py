"""
JARVIS Holographic Globe Interface
A futuristic HUD-style 3D Earth globe that represents JARVIS
"""

import pygame
import math
import time
import threading
from enum import Enum
from typing import Optional, Tuple, Callable
from dataclasses import dataclass


class JARVISState(Enum):
    """Visual states for the JARVIS interface"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    NEWS = "news"
    ERROR = "error"


@dataclass
class GlobeColors:
    """Color scheme for the holographic interface"""
    PRIMARY = (0, 255, 255)      # Cyan
    SECONDARY = (0, 128, 255)    # Blue
    ACCENT = (255, 255, 255)     # White
    ALERT = (255, 51, 51)        # Red
    BACKGROUND = (0, 0, 0)        # Black
    
    # State-specific colors
    IDLE_GLOW = (0, 150, 200)
    LISTENING_GLOW = (0, 255, 150)
    PROCESSING_GLOW = (255, 200, 0)
    SPEAKING_GLOW = (0, 200, 255)
    ERROR_GLOW = (255, 50, 50)


@dataclass
class CountryCoord:
    """Geographic coordinates for countries"""
    lat: float
    lon: float
    name: str


# Country coordinates for news pointers
COUNTRIES = {
    "india": CountryCoord(20.5937, 78.9629, "India"),
    "usa": CountryCoord(37.0902, -95.7129, "USA"),
    "uk": CountryCoord(55.3781, -3.4360, "UK"),
    "china": CountryCoord(35.8617, 104.1954, "China"),
    "russia": CountryCoord(61.5240, 105.3188, "Russia"),
    "japan": CountryCoord(36.2048, 138.2529, "Japan"),
    "germany": CountryCoord(51.1657, 10.4515, "Germany"),
    "france": CountryCoord(46.2276, 2.2137, "France"),
    "australia": CountryCoord(-25.2744, 133.7751, "Australia"),
    "brazil": CountryCoord(-14.2350, -51.9253, "Brazil"),
    "canada": CountryCoord(56.1304, -106.3468, "Canada"),
    "pakistan": CountryCoord(30.3753, 69.3451, "Pakistan"),
    "sri lanka": CountryCoord(7.8731, 80.7718, "Sri Lanka"),
    "bangladesh": CountryCoord(23.6850, 90.3563, "Bangladesh"),
    "uae": CountryCoord(23.4241, 53.8478, "UAE"),
    "south korea": CountryCoord(35.9078, 127.7669, "South Korea"),
}


class HolographicGlobe:
    """The main holographic JARVIS globe interface"""
    
    def __init__(self, width: int = 600, height: int = 600):
        print("[GLOBE] Initializing Holographic Globe Interface...")
        
        # Window settings
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Globe parameters
        self.globe_radius = min(width, height) // 4
        self.rotation_angle = 0
        self.rotation_speed = 0.5  # degrees per frame
        
        # State
        self.state = JARVISState.IDLE
        self.running = False
        self.screen = None
        self.clock = None
        
        # Animation parameters
        self.pulse_phase = 0
        self.particle_phase = 0
        self.ring_angles = [0, 120, 240]  # Three orbital rings
        
        # News pointer
        self.news_country = None
        self.pointer_visible = False
        
        # Mouse interaction
        self.mouse_glow = 0
        
        # Data panels
        self.cpu_percent = 0
        self.memory_percent = 0
        self.battery_percent = 100
        self.current_time = ""
        
        # Callbacks
        self.on_click_callback: Optional[Callable] = None
        
        print("[GLOBE] Globe Interface Initialized")
    
    def _init_pygame(self):
        """Initialize pygame with transparent window"""
        pygame.init()
        pygame.display.set_caption("JARVIS Interface")
        
        # Create window
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.NOFRAME  # Borderless
        )
        self.clock = pygame.time.Clock()
        
        # Try to make window always on top (Windows-specific)
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info()["window"]
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)
        except:
            pass
    
    def set_state(self, state: JARVISState):
        """Set the current visual state"""
        self.state = state
        
        # Adjust animation speeds based on state
        if state == JARVISState.IDLE:
            self.rotation_speed = 0.3
        elif state == JARVISState.LISTENING:
            self.rotation_speed = 0.8
        elif state == JARVISState.PROCESSING:
            self.rotation_speed = 2.0
        elif state == JARVISState.SPEAKING:
            self.rotation_speed = 0.5
    
    def point_to_country(self, country_name: str):
        """Point to a country on the globe (for news)"""
        country_lower = country_name.lower()
        if country_lower in COUNTRIES:
            self.news_country = COUNTRIES[country_lower]
            self.pointer_visible = True
        else:
            self.pointer_visible = False
    
    def clear_pointer(self):
        """Clear the country pointer"""
        self.pointer_visible = False
        self.news_country = None
    
    def update_system_stats(self, cpu: float = None, memory: float = None, battery: float = None):
        """Update system statistics display"""
        if cpu is not None:
            self.cpu_percent = cpu
        if memory is not None:
            self.memory_percent = memory
        if battery is not None:
            self.battery_percent = battery
    
    def _get_state_color(self) -> Tuple[int, int, int]:
        """Get color based on current state"""
        colors = {
            JARVISState.IDLE: GlobeColors.IDLE_GLOW,
            JARVISState.LISTENING: GlobeColors.LISTENING_GLOW,
            JARVISState.PROCESSING: GlobeColors.PROCESSING_GLOW,
            JARVISState.SPEAKING: GlobeColors.SPEAKING_GLOW,
            JARVISState.NEWS: GlobeColors.PRIMARY,
            JARVISState.ERROR: GlobeColors.ERROR_GLOW,
        }
        return colors.get(self.state, GlobeColors.PRIMARY)
    
    def _draw_wireframe_globe(self):
        """Draw the wireframe Earth globe"""
        color = self._get_state_color()
        
        # Pulsing effect
        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase * 0.1)
        glow_color = tuple(int(c * pulse) for c in color)
        
        # Draw latitude lines
        for lat in range(-60, 90, 30):
            lat_rad = math.radians(lat)
            y_offset = int(self.globe_radius * math.sin(lat_rad))
            radius_at_lat = int(self.globe_radius * math.cos(lat_rad))
            
            if radius_at_lat > 0:
                pygame.draw.ellipse(
                    self.screen, glow_color,
                    (self.center_x - radius_at_lat, 
                     self.center_y - y_offset - 5,
                     radius_at_lat * 2, 10),
                    1
                )
        
        # Draw longitude lines (affected by rotation)
        for lon in range(0, 360, 30):
            lon_rad = math.radians(lon + self.rotation_angle)
            
            points = []
            for lat in range(-90, 91, 10):
                lat_rad = math.radians(lat)
                
                x = int(self.globe_radius * math.cos(lat_rad) * math.sin(lon_rad))
                y = int(self.globe_radius * math.sin(lat_rad))
                z = self.globe_radius * math.cos(lat_rad) * math.cos(lon_rad)
                
                # Only draw if on visible side
                if z > 0:
                    points.append((self.center_x + x, self.center_y - y))
            
            if len(points) > 1:
                pygame.draw.lines(self.screen, glow_color, False, points, 1)
        
        # Draw main globe outline with glow
        for i in range(3):
            glow_radius = self.globe_radius + i * 2
            alpha = 255 - i * 60
            glow_surf = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf, (*glow_color, alpha),
                (glow_radius + 5, glow_radius + 5), glow_radius, 2
            )
            self.screen.blit(
                glow_surf,
                (self.center_x - glow_radius - 5, self.center_y - glow_radius - 5)
            )
    
    def _draw_orbital_rings(self):
        """Draw rotating orbital rings around the globe"""
        color = GlobeColors.PRIMARY
        
        for i, base_angle in enumerate(self.ring_angles):
            angle = base_angle + self.rotation_angle * (0.5 + i * 0.3)
            angle_rad = math.radians(angle)
            
            # Ring tilt based on index
            tilt = 15 + i * 20
            
            # Draw elliptical ring
            ring_width = self.globe_radius + 30 + i * 20
            ring_height = int(ring_width * math.cos(math.radians(tilt)))
            
            ring_rect = pygame.Rect(
                self.center_x - ring_width,
                self.center_y - ring_height,
                ring_width * 2,
                ring_height * 2
            )
            
            # Rotate ring (simulated with multiple ellipses)
            pulse = 0.5 + 0.5 * math.sin(self.pulse_phase * 0.05 + i)
            ring_color = tuple(int(c * pulse) for c in color)
            
            pygame.draw.ellipse(self.screen, ring_color, ring_rect, 1)
            
            # Add data points on rings
            for j in range(8):
                data_angle = angle + j * 45
                data_rad = math.radians(data_angle)
                
                dx = int(ring_width * math.cos(data_rad))
                dy = int(ring_height * math.sin(data_rad))
                
                # Small dot on ring
                point_size = 2 if j % 2 == 0 else 1
                pygame.draw.circle(
                    self.screen, GlobeColors.ACCENT,
                    (self.center_x + dx, self.center_y + dy),
                    point_size
                )
    
    def _draw_particles(self):
        """Draw floating particles around the globe"""
        particle_color = GlobeColors.PRIMARY
        
        for i in range(20):
            # Calculate particle position
            angle = (self.particle_phase * 2 + i * 18) % 360
            radius = self.globe_radius + 50 + math.sin(self.particle_phase * 0.1 + i) * 20
            
            angle_rad = math.radians(angle)
            x = int(self.center_x + radius * math.cos(angle_rad))
            y = int(self.center_y + radius * math.sin(angle_rad) * 0.5)
            
            # Particle size varies
            size = 1 + int(math.sin(self.particle_phase * 0.1 + i * 0.5) * 2)
            size = max(1, size)
            
            pygame.draw.circle(self.screen, particle_color, (x, y), size)
    
    def _draw_scan_lines(self):
        """Draw holographic scan lines effect"""
        scan_y = int((self.pulse_phase * 3) % self.height)
        
        for i in range(0, self.height, 4):
            alpha = 30 if i == scan_y else 10
            line_color = (*GlobeColors.PRIMARY, alpha)
            
            line_surf = pygame.Surface((self.width, 1), pygame.SRCALPHA)
            line_surf.fill(line_color)
            self.screen.blit(line_surf, (0, i))
    
    def _draw_country_pointer(self):
        """Draw pointer to a specific country"""
        if not self.pointer_visible or not self.news_country:
            return
        
        country = self.news_country
        
        # Convert lat/lon to screen position (simplified)
        lon_rad = math.radians(country.lon + self.rotation_angle)
        lat_rad = math.radians(country.lat)
        
        x = int(self.globe_radius * math.cos(lat_rad) * math.sin(lon_rad))
        y = int(self.globe_radius * math.sin(lat_rad))
        z = self.globe_radius * math.cos(lat_rad) * math.cos(lon_rad)
        
        # Only show if on visible side
        if z > 0:
            screen_x = self.center_x + x
            screen_y = self.center_y - y
            
            # Draw pointer with pulsing effect
            pulse = 0.5 + 0.5 * math.sin(self.pulse_phase * 0.2)
            pointer_size = int(5 + pulse * 5)
            
            # Red glowing dot
            for i in range(3):
                glow_size = pointer_size + i * 3
                alpha = 255 - i * 80
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf, (*GlobeColors.ALERT, alpha),
                    (glow_size, glow_size), glow_size
                )
                self.screen.blit(
                    glow_surf,
                    (screen_x - glow_size, screen_y - glow_size)
                )
            
            # Label
            font = pygame.font.Font(None, 24)
            label = font.render(country.name, True, GlobeColors.ACCENT)
            self.screen.blit(label, (screen_x + 10, screen_y - 10))
    
    def _draw_data_panels(self):
        """Draw floating HUD data panels"""
        font = pygame.font.Font(None, 20)
        
        # Left panel - System stats
        panel_x = 20
        panel_y = self.height // 2 - 60
        
        self._draw_panel_item(panel_x, panel_y, f"CPU: {self.cpu_percent:.0f}%", font)
        self._draw_panel_item(panel_x, panel_y + 25, f"MEM: {self.memory_percent:.0f}%", font)
        self._draw_panel_item(panel_x, panel_y + 50, f"BAT: {self.battery_percent:.0f}%", font)
        
        # Right panel - Status
        panel_x = self.width - 100
        
        status_text = self.state.value.upper()
        self._draw_panel_item(panel_x, panel_y, f"STATUS:", font)
        self._draw_panel_item(panel_x, panel_y + 25, status_text, font, self._get_state_color())
        
        # Bottom status bar
        self.current_time = time.strftime("%H:%M:%S")
        time_text = font.render(self.current_time, True, GlobeColors.ACCENT)
        self.screen.blit(time_text, (self.center_x - 30, self.height - 40))
    
    def _draw_panel_item(self, x: int, y: int, text: str, font, color=None):
        """Draw a single panel item with glow"""
        if color is None:
            color = GlobeColors.PRIMARY
        
        # Background glow
        text_surf = font.render(text, True, color)
        glow_surf = pygame.Surface((text_surf.get_width() + 10, text_surf.get_height() + 6), pygame.SRCALPHA)
        glow_surf.fill((*color, 30))
        self.screen.blit(glow_surf, (x - 5, y - 3))
        
        # Text
        self.screen.blit(text_surf, (x, y))
    
    def _draw_frame(self):
        """Draw a complete frame"""
        # Clear screen with dark background
        self.screen.fill(GlobeColors.BACKGROUND)
        
        # Draw scan lines (subtle)
        self._draw_scan_lines()
        
        # Draw orbital rings
        self._draw_orbital_rings()
        
        # Draw particles
        self._draw_particles()
        
        # Draw wireframe globe
        self._draw_wireframe_globe()
        
        # Draw country pointer if active
        self._draw_country_pointer()
        
        # Draw data panels
        self._draw_data_panels()
        
        # Update animation phases
        self.rotation_angle = (self.rotation_angle + self.rotation_speed) % 360
        self.pulse_phase += 1
        self.particle_phase += 1
        
        pygame.display.flip()
    
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if click is on globe
                mx, my = event.pos
                dist = math.sqrt((mx - self.center_x)**2 + (my - self.center_y)**2)
                
                if dist < self.globe_radius + 30:
                    if self.on_click_callback:
                        self.on_click_callback()
            
            elif event.type == pygame.MOUSEMOTION:
                # Mouse proximity effect
                mx, my = event.pos
                dist = math.sqrt((mx - self.center_x)**2 + (my - self.center_y)**2)
                self.mouse_glow = max(0, 1 - dist / 200)
    
    def run_loop(self):
        """Main render loop"""
        self._init_pygame()
        self.running = True
        
        while self.running:
            self._handle_events()
            self._draw_frame()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
    
    def start(self):
        """Start the globe interface in a background thread"""
        self.render_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.render_thread.start()
        print("[GLOBE] Interface started in background")
    
    def stop(self):
        """Stop the globe interface"""
        self.running = False
        print("[GLOBE] Interface stopped")
    
    def set_click_callback(self, callback: Callable):
        """Set callback for when globe is clicked"""
        self.on_click_callback = callback


# Demo function
def demo():
    """Demo the holographic globe"""
    globe = HolographicGlobe(600, 600)
    
    # Demo state changes
    def cycle_states():
        import time as t
        states = [
            JARVISState.IDLE,
            JARVISState.LISTENING,
            JARVISState.PROCESSING,
            JARVISState.SPEAKING,
        ]
        
        while globe.running:
            for state in states:
                globe.set_state(state)
                t.sleep(3)
            
            # Demo country pointer
            globe.point_to_country("india")
            t.sleep(3)
            globe.point_to_country("usa")
            t.sleep(3)
            globe.clear_pointer()
    
    # Start state cycling thread
    state_thread = threading.Thread(target=cycle_states, daemon=True)
    state_thread.start()
    
    # Run main loop (blocking)
    globe.run_loop()


if __name__ == "__main__":
    demo()
