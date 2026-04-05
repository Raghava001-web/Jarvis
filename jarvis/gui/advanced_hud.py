"""
JARVIS ULTIMATE HUD v10
- JARVIS orb moves based on work context
- Iron Man style ultra-realistic globe
- Full widget suite (Music, News, Weather, To-Do, Reminders)
- Reactive display (reads from StateManager)
"""

import pygame
import math
import random
import webbrowser
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from collections import deque
import psutil
from datetime import datetime

# Import StateManager
try:
    from core.state_manager import StateManager, JARVISState, StateContext, get_state_manager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False

# Import Iron Man Globe
try:
    from gui.iron_man_globe import IronManGlobe, GlobeTheme
    IRON_MAN_GLOBE_AVAILABLE = True
except ImportError:
    IRON_MAN_GLOBE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════

class Theme:
    BG = (4, 10, 18)
    OCEAN = (5, 20, 35)
    GRID = (15, 38, 58)
    CYAN = (0, 220, 255)
    CYAN_DIM = (0, 90, 130)
    CYAN_GLOW = (0, 255, 255)
    LAND = (0, 80, 110)
    LAND_HOVER = (0, 150, 195)
    ORANGE = (255, 160, 0)
    ORANGE_DIM = (180, 100, 0)
    GREEN = (0, 255, 120)
    RED = (255, 60, 60)
    PURPLE = (180, 100, 255)
    TEXT = (0, 200, 240)
    TEXT_DIM = (0, 65, 95)
    PANEL = (6, 18, 30)
    PANEL_HOVER = (10, 28, 45)
    BORDER = (0, 160, 200)
    # Aliases for integrated HUD compatibility
    PRIMARY = CYAN
    SECONDARY = CYAN_DIM
    ACCENT = ORANGE
    INDICATOR_ACTIVE = GREEN


# ═══════════════════════════════════════════════════════════════
# REALISTIC CONTINENT DATA (Much more detailed)
# ═══════════════════════════════════════════════════════════════

CONTINENTS = {
    "north_america": [
        # Alaska and Canada Arctic
        (71, -156), (70, -141), (69, -135), (68, -136), (67, -139), (65, -141),
        (64, -139), (63, -136), (61, -140), (60, -145), (59, -151), (58, -154),
        (57, -157), (55, -161), (54, -166), (52, -172), (55, -163), (56, -158),
        (57, -153), (59, -150), (60, -147), (61, -142), (62, -138), (63, -132),
        (64, -126), (66, -126), (67, -133), (69, -130), (70, -125), (68, -116),
        (67, -112), (65, -111), (62, -110), (60, -108), (58, -102), (57, -95),
        (59, -94), (63, -92), (65, -88), (66, -82), (64, -77), (62, -75),
        (60, -78), (58, -76), (56, -77), (54, -78), (52, -79), (49, -77),
        (47, -79), (45, -75), (44, -77), (43, -79), (42, -82), (44, -82),
        (46, -84), (47, -88), (48, -89), (49, -95), (48, -97), (49, -101),
        (49, -109), (49, -117), (49, -123),
        # West Coast
        (48, -124), (46, -124), (43, -124), (40, -124), (38, -123), (36, -122),
        (34, -120), (32, -117), (31, -115), (29, -114), (27, -112), (25, -110),
        (23, -106), (21, -105), (19, -105), (18, -103), (17, -100), (16, -96),
        (17, -92), (18, -88), (20, -87), (21, -90), (22, -97), (25, -97),
        (27, -97), (29, -96), (30, -94), (29, -91), (28, -88), (29, -85),
        (30, -84), (29, -82), (27, -80), (25, -80), (24, -81), (25, -82),
        (26, -80), (27, -79), (30, -81), (31, -81), (33, -79), (35, -76),
        (37, -76), (39, -74), (41, -72), (43, -70), (45, -67), (46, -64),
        (47, -62), (48, -59), (50, -57), (52, -56), (54, -57), (56, -61),
        (58, -66), (60, -65), (62, -66), (65, -68), (67, -74), (69, -82),
        (70, -90), (71, -100), (72, -115), (73, -130), (72, -145), (71, -156)
    ],
    "south_america": [
        (12, -71), (11, -73), (10, -75), (8, -77), (6, -78), (4, -78), (2, -79),
        (0, -80), (-2, -80), (-4, -79), (-5, -77), (-6, -75), (-8, -74), (-10, -76),
        (-12, -77), (-13, -76), (-14, -74), (-15, -70), (-14, -66), (-15, -60),
        (-17, -54), (-19, -48), (-21, -45), (-23, -42), (-25, -44), (-27, -47),
        (-29, -49), (-31, -51), (-33, -53), (-34, -55), (-36, -57), (-38, -58),
        (-40, -62), (-42, -64), (-44, -65), (-46, -66), (-48, -68), (-50, -70),
        (-52, -71), (-54, -69), (-55, -67), (-54, -64), (-53, -70), (-51, -73),
        (-49, -75), (-46, -74), (-43, -73), (-40, -72), (-38, -70), (-36, -70),
        (-34, -72), (-32, -71), (-30, -70), (-28, -69), (-26, -69), (-24, -70),
        (-22, -70), (-20, -71), (-18, -73), (-16, -75), (-14, -77), (-12, -78),
        (-10, -78), (-8, -76), (-6, -74), (-4, -73), (-2, -71), (0, -72), (2, -74),
        (4, -72), (6, -71), (8, -72), (10, -72), (12, -71)
    ],
    "africa": [
        (37, -1), (36, 4), (35, 10), (33, 12), (32, 15), (31, 18), (31, 22),
        (30, 26), (31, 30), (29, 33), (27, 35), (24, 36), (21, 36), (18, 38),
        (15, 40), (12, 43), (10, 45), (7, 48), (4, 50), (1, 51), (-2, 50),
        (-5, 47), (-8, 44), (-11, 42), (-14, 39), (-16, 37), (-18, 36),
        (-20, 35), (-22, 33), (-25, 31), (-28, 28), (-31, 25), (-33, 22),
        (-34, 18), (-34, 14), (-33, 16), (-31, 19), (-29, 23), (-27, 26),
        (-25, 29), (-23, 32), (-21, 35), (-19, 37), (-17, 39), (-15, 40),
        (-13, 38), (-11, 34), (-9, 29), (-7, 24), (-5, 19), (-3, 14),
        (0, 10), (3, 5), (6, 1), (9, -3), (12, -7), (15, -12), (18, -16),
        (21, -17), (24, -15), (27, -13), (30, -10), (33, -6), (35, -3), (37, -1)
    ],
    "europe": [
        (36, -9), (37, -7), (39, -9), (42, -8), (43, -5), (44, -2), (43, 1),
        (45, 3), (47, 4), (49, 5), (51, 7), (53, 9), (55, 10), (57, 12),
        (59, 15), (61, 19), (63, 23), (65, 26), (67, 28), (70, 30), (71, 28),
        (69, 24), (67, 20), (65, 16), (63, 13), (60, 10), (58, 7), (56, 5),
        (54, 4), (52, 3), (50, 2), (48, 3), (46, 5), (44, 8), (42, 12),
        (40, 15), (38, 18), (36, 22), (37, 25), (39, 27), (41, 28), (43, 26),
        (45, 23), (47, 19), (49, 16), (47, 12), (45, 9), (43, 6), (41, 4),
        (39, 1), (37, -2), (36, -9)
    ],
    "asia": [
        # From Middle East eastward
        (42, 28), (44, 35), (46, 42), (48, 50), (50, 58), (52, 65), (54, 72),
        (56, 78), (58, 85), (60, 92), (62, 100), (64, 110), (66, 120), (68, 130),
        (70, 145), (72, 160), (71, 175), (68, 180), (65, -175), (62, -170),
        (60, -168), (58, -173), (55, -168), (52, -172), (50, -178),
        # Back to Pacific coast
        (45, 145), (40, 140), (35, 135), (32, 130), (28, 122), (25, 118),
        (22, 114), (18, 108), (15, 105), (12, 104), (8, 100), (5, 103),
        (2, 105), (-2, 106), (-5, 108), (-8, 114), (-10, 120), (-8, 125),
        (-5, 130), (-3, 135), (0, 140), (3, 145),
        # South Asia and back
        (8, 95), (12, 93), (16, 96), (20, 93), (24, 88), (26, 84), (28, 77),
        (32, 75), (35, 72), (38, 68), (40, 62), (42, 55), (44, 48), (42, 28)
    ],
    "australia": [
        (-12, 131), (-14, 127), (-17, 123), (-20, 118), (-24, 114), (-28, 114),
        (-32, 116), (-34, 119), (-35, 123), (-35, 128), (-34, 133), (-35, 137),
        (-37, 140), (-38, 145), (-38, 148), (-36, 150), (-33, 152), (-30, 153),
        (-27, 153), (-24, 152), (-21, 149), (-18, 146), (-16, 145), (-14, 147),
        (-12, 143), (-11, 139), (-12, 136), (-12, 131)
    ],
    "india": [
        (35, 74), (33, 78), (30, 80), (28, 84), (26, 88), (24, 90), (22, 92),
        (20, 93), (17, 95), (15, 94), (12, 92), (9, 78), (8, 77), (10, 76),
        (12, 77), (14, 79), (16, 80), (18, 82), (20, 85), (22, 86), (24, 83),
        (22, 80), (20, 77), (18, 73), (20, 72), (22, 70), (24, 69), (26, 70),
        (28, 72), (30, 73), (33, 72), (35, 74)
    ],
    "greenland": [
        (83, -35), (82, -25), (81, -19), (79, -17), (77, -18), (74, -20),
        (72, -22), (70, -25), (68, -28), (65, -38), (63, -42), (60, -45),
        (60, -50), (62, -52), (65, -55), (68, -56), (71, -56), (74, -58),
        (77, -60), (80, -65), (82, -55), (83, -45), (83, -35)
    ]
}

COUNTRIES = {
    "United States": {"lat": 38, "lon": -97},
    "Canada": {"lat": 56, "lon": -106},
    "Brazil": {"lat": -10, "lon": -55},
    "Argentina": {"lat": -34, "lon": -64},
    "United Kingdom": {"lat": 52, "lon": -1},
    "France": {"lat": 46, "lon": 2},
    "Germany": {"lat": 51, "lon": 10},
    "Russia": {"lat": 60, "lon": 100},
    "China": {"lat": 35, "lon": 105},
    "Japan": {"lat": 36, "lon": 138},
    "India": {"lat": 20, "lon": 78},
    "Australia": {"lat": -25, "lon": 134},
    "South Africa": {"lat": -29, "lon": 24},
    "Egypt": {"lat": 27, "lon": 30},
    "Nigeria": {"lat": 9, "lon": 8},
    "Mexico": {"lat": 23, "lon": -102},
    "Italy": {"lat": 42, "lon": 12},
    "Spain": {"lat": 40, "lon": -4},
    "South Korea": {"lat": 36, "lon": 128},
    "Indonesia": {"lat": -5, "lon": 120},
}


# ═══════════════════════════════════════════════════════════════
# STATE & MODE
# ═══════════════════════════════════════════════════════════════

if STATE_MANAGER_AVAILABLE:
    State = JARVISState
else:
    class State(Enum):
        STARTUP = "STARTUP"
        IDLE = "IDLE"
        LISTENING = "LISTENING"
        PROCESSING = "PROCESSING"
        SPEAKING = "SPEAKING"
        INTERRUPTED = "INTERRUPTED"
        ERROR = "ERROR"
        SHUTDOWN = "SHUTDOWN"

class Mode(Enum):
    JARVIS = "J.A.R.V.I.S."
    FRIDAY = "F.R.I.D.A.Y."


# ═══════════════════════════════════════════════════════════════
# JARVIS ORB - WORK-REACTIVE (MOVES BASED ON CONTEXT)
# ═══════════════════════════════════════════════════════════════

class OrbTarget(Enum):
    """Where JARVIS orb should be positioned based on work"""
    HOME = "home"           # Default position (top center)
    GLOBE = "globe"         # Near globe for location/weather queries
    SYSTEM = "system"       # Near system panel for system info
    MUSIC = "music"         # Near music panel for music commands
    CHAT = "chat"           # Near chat panel for conversation
    NEWS = "news"           # Near news panel for news queries
    CENTER = "center"       # Center of screen for general


class JARVISOrb:
    """JARVIS orb that moves based on work context (not randomly)"""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # Home position (top center)
        self.home_x = screen_w // 2
        self.home_y = 80
        
        # Current position
        self.x = float(self.home_x)
        self.y = float(self.home_y)
        
        # Target (where to move)
        self.target_x = self.home_x
        self.target_y = self.home_y
        self.current_target = OrbTarget.HOME
        
        # Panel positions (will be set from HUD)
        self.panel_positions = {
            OrbTarget.HOME: (screen_w // 2, 80),
            OrbTarget.GLOBE: (screen_w // 2, screen_h // 2 - 80),
            OrbTarget.SYSTEM: (100, 60),
            OrbTarget.MUSIC: (100, 340),
            OrbTarget.CHAT: (screen_w - 100, 400),
            OrbTarget.NEWS: (screen_w - 100, 60),
            OrbTarget.CENTER: (screen_w // 2, screen_h // 2),
        }
        
        # Animation
        self.pulse = 0.0
        self.rings = [0.0, 45.0, 90.0]
        self.state = State.IDLE
        self.particles = []
        
        # Movement
        self.move_speed = 0.04  # Smooth movement
        self.idle_timer = 0
    
    def set_target(self, target: OrbTarget):
        """Set where the orb should move to"""
        if target in self.panel_positions:
            self.current_target = target
            self.target_x, self.target_y = self.panel_positions[target]
    
    def set_target_from_intent(self, intent: str):
        """Set target based on current intent/work"""
        intent_lower = intent.lower() if intent else ""
        
        # Map intents to positions
        if any(w in intent_lower for w in ["weather", "location", "country", "map", "globe", "world"]):
            self.set_target(OrbTarget.GLOBE)
        elif any(w in intent_lower for w in ["music", "song", "play", "spotify", "pause"]):
            self.set_target(OrbTarget.MUSIC)
        elif any(w in intent_lower for w in ["system", "cpu", "memory", "battery", "status"]):
            self.set_target(OrbTarget.SYSTEM)
        elif any(w in intent_lower for w in ["news", "headlines", "article"]):
            self.set_target(OrbTarget.NEWS)
        elif any(w in intent_lower for w in ["chat", "talk", "conversation", "message"]):
            self.set_target(OrbTarget.CHAT)
        elif intent_lower:
            self.set_target(OrbTarget.CENTER)
        else:
            self.set_target(OrbTarget.HOME)
    
    def update_panel_positions(self, w, h, globe_cx, globe_cy):
        """Update panel positions when screen resizes"""
        self.screen_w = w
        self.screen_h = h
        self.panel_positions = {
            OrbTarget.HOME: (w // 2, 80),
            OrbTarget.GLOBE: (globe_cx, globe_cy - 80),
            OrbTarget.SYSTEM: (100, 60),
            OrbTarget.MUSIC: (100, 340),
            OrbTarget.CHAT: (w - 100, 400),
            OrbTarget.NEWS: (w - 100, 60),
            OrbTarget.CENTER: (w // 2, h // 2),
        }
    
    def update(self, state, mouse_pos=None, context=None):
        """Update orb position and animation"""
        self.state = state
        self.pulse += 0.08
        
        # Rotate rings based on state
        ring_speed_mult = 1.0
        if state == State.PROCESSING:
            ring_speed_mult = 2.5  # Spin faster when processing
        elif state == State.SPEAKING:
            ring_speed_mult = 1.5
        elif state == State.LISTENING:
            ring_speed_mult = 0.7
        
        for i in range(len(self.rings)):
            speed = (1.2 + i * 0.6) * ring_speed_mult
            self.rings[i] = (self.rings[i] + speed) % 360
        
        # Update target based on context (if provided)
        if context and hasattr(context, 'last_intent'):
            self.set_target_from_intent(context.last_intent)
        
        # Return to home when idle for a while
        if state == State.IDLE:
            self.idle_timer += 1
            if self.idle_timer > 180:  # After 3 seconds of idle
                self.set_target(OrbTarget.HOME)
        else:
            self.idle_timer = 0
        
        # Smooth movement toward target
        self.x += (self.target_x - self.x) * self.move_speed
        self.y += (self.target_y - self.y) * self.move_speed
        
        # React to mouse - pull toward cursor when clicked nearby
        if mouse_pos:
            dx = mouse_pos[0] - self.x
            dy = mouse_pos[1] - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 100 and dist > 0:
                # Gently attract to cursor when close
                self.x += dx * 0.01
                self.y += dy * 0.01
        
        # Generate particles when active
        if state in [State.LISTENING, State.SPEAKING, State.PROCESSING]:
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                self.particles.append({
                    "x": self.x + math.cos(angle) * 25,
                    "y": self.y + math.sin(angle) * 25,
                    "vx": math.cos(angle) * random.uniform(0.5, 2),
                    "vy": math.sin(angle) * random.uniform(0.5, 2),
                    "life": 40,
                    "max_life": 40
                })
        
        # Update particles
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)
    
    def draw(self, screen):
        """Draw the JARVIS orb"""
        cx, cy = int(self.x), int(self.y)
        
        # Color based on state
        colors = {
            State.IDLE: Theme.CYAN,
            State.LISTENING: Theme.GREEN,
            State.PROCESSING: Theme.ORANGE,
            State.SPEAKING: Theme.PURPLE,
        }
        col = colors.get(self.state, Theme.CYAN)
        
        pulse = math.sin(self.pulse) * 0.15 + 1.0
        radius = int(22 * pulse)
        
        # Draw particles
        for p in self.particles:
            alpha = int(255 * p["life"] / p["max_life"])
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (3, 3), 3)
            screen.blit(s, (int(p["x"]) - 3, int(p["y"]) - 3))
        
        # Outer glow
        for i in range(4, 0, -1):
            s = pygame.Surface((radius*4 + i*12, radius*4 + i*12), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, 12), (radius*2 + i*6, radius*2 + i*6), radius + i*6)
            screen.blit(s, (cx - radius*2 - i*6, cy - radius*2 - i*6))
        
        # Rotating rings
        for i, rot in enumerate(self.rings):
            rr = radius + 5 + i * 8
            rect = pygame.Rect(cx - rr, cy - rr, rr*2, rr*2)
            pygame.draw.arc(screen, col, rect, math.radians(rot), math.radians(rot + 80), 2)
            pygame.draw.arc(screen, col, rect, math.radians(rot + 180), math.radians(rot + 260), 2)
        
        # Inner core
        pygame.draw.circle(screen, Theme.BG, (cx, cy), radius - 6)
        pygame.draw.circle(screen, col, (cx, cy), 5)
        
        # State label below orb
        font = pygame.font.Font(None, 14)
        label = self.state.value if hasattr(self.state, 'value') else str(self.state)
        ts = font.render(label, True, col)
        screen.blit(ts, (cx - ts.get_width() // 2, cy + radius + 15))


# ═══════════════════════════════════════════════════════════════
# GLOBE
# ═══════════════════════════════════════════════════════════════

class Globe:
    def __init__(self, cx, cy, radius):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        
        self.rot = 78
        self.tilt = 12
        self.auto_rotate = True
        self.dragging = False
        self.last_mouse = (0, 0)
        self.interaction_timer = 0  # Pause auto-rotate during interaction
        
        self.hover_coords = None
        self.hovered_country = None
        self.glow_cache = {}
    
    def latlon_screen(self, lat, lon):
        lat_r = math.radians(lat)
        lon_r = math.radians(lon + self.rot)
        tilt_r = math.radians(self.tilt)
        
        x = math.cos(lat_r) * math.sin(lon_r)
        y = math.sin(lat_r) * math.cos(tilt_r) - math.cos(lat_r) * math.cos(lon_r) * math.sin(tilt_r)
        z = math.sin(lat_r) * math.sin(tilt_r) + math.cos(lat_r) * math.cos(lon_r) * math.cos(tilt_r)
        
        sx = int(self.cx + x * self.radius)
        sy = int(self.cy - y * self.radius)
        return sx, sy, z
    
    def screen_to_latlon(self, sx, sy):
        dx = (sx - self.cx) / self.radius
        dy = -(sy - self.cy) / self.radius
        d2 = dx*dx + dy*dy
        if d2 > 1:
            return None
        dz = math.sqrt(max(0, 1 - d2))
        
        tilt_r = math.radians(self.tilt)
        y_rot = dy * math.cos(tilt_r) + dz * math.sin(tilt_r)
        z_rot = -dy * math.sin(tilt_r) + dz * math.cos(tilt_r)
        
        lat = math.degrees(math.asin(y_rot))
        lon = math.degrees(math.atan2(dx, z_rot)) - self.rot
        lon = ((lon + 180) % 360) - 180
        return lat, lon
    
    def glow(self, r, color, spread):
        key = (r, color, spread)
        if key not in self.glow_cache:
            size = r * 2 + spread * 2
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            for i in range(spread, 0, -1):
                alpha = int(30 * (1 - i / spread))
                pygame.draw.circle(s, (*color[:3], alpha), (size // 2, size // 2), r + i)
            self.glow_cache[key] = s
        return self.glow_cache[key]
    
    def find_country(self, lat, lon):
        for name, data in COUNTRIES.items():
            dlat = abs(lat - data["lat"])
            dlon = abs(lon - data["lon"])
            if dlat < 8 and dlon < 10:
                return name
        return None
    
    def update(self):
        # Auto-rotate only when not interacting
        if self.interaction_timer > 0:
            self.interaction_timer -= 1
        elif self.auto_rotate and not self.dragging:
            self.rot = (self.rot + 0.15) % 360
    
    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            dx = e.pos[0] - self.cx
            dy = e.pos[1] - self.cy
            if dx*dx + dy*dy < self.radius * self.radius:
                self.dragging = True
                self.last_mouse = e.pos
                self.interaction_timer = 180  # Pause auto-rotate for 3 seconds
        
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        
        elif e.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = e.pos[0] - self.last_mouse[0]
                dy = e.pos[1] - self.last_mouse[1]
                self.rot = (self.rot + dx * 0.4) % 360
                self.tilt = max(-60, min(60, self.tilt - dy * 0.25))
                self.last_mouse = e.pos
                self.interaction_timer = 180
            
            # Hover detection
            self.hover_coords = self.screen_to_latlon(*e.pos)
            if self.hover_coords:
                lat, lon = self.hover_coords
                self.hovered_country = self.find_country(lat, lon)
            else:
                self.hovered_country = None
        
        elif e.type == pygame.MOUSEWHEEL:
            self.radius = max(80, min(280, self.radius + e.y * 12))
            self.glow_cache.clear()
    
    def draw(self, screen):
        # Glow
        g = self.glow(self.radius + 15, Theme.CYAN, 18)
        screen.blit(g, (self.cx - g.get_width()//2, self.cy - g.get_height()//2))
        
        # Ocean
        pygame.draw.circle(screen, Theme.OCEAN, (self.cx, self.cy), self.radius)
        
        # Grid
        for lat in range(-75, 90, 15):
            pts = []
            for lon in range(0, 361, 5):
                x, y, z = self.latlon_screen(lat, lon)
                if z > -0.02:
                    pts.append((x, y))
                elif pts and len(pts) > 1:
                    c = Theme.CYAN_DIM if lat == 0 else Theme.GRID
                    pygame.draw.lines(screen, c, False, pts, 1)
                    pts = []
            if len(pts) > 1:
                pygame.draw.lines(screen, Theme.CYAN_DIM if lat == 0 else Theme.GRID, False, pts, 1)
        
        for lon in range(0, 360, 15):
            pts = []
            for lat in range(-75, 76, 4):
                x, y, z = self.latlon_screen(lat, lon)
                if z > -0.02:
                    pts.append((x, y))
                elif pts and len(pts) > 1:
                    pygame.draw.lines(screen, Theme.GRID, False, pts, 1)
                    pts = []
            if len(pts) > 1:
                pygame.draw.lines(screen, Theme.GRID, False, pts, 1)
        
        # Continents
        for name, poly in CONTINENTS.items():
            pts = []
            visible = True
            for lat, lon in poly:
                x, y, z = self.latlon_screen(lat, lon)
                if z > 0.05:
                    pts.append((x, y))
                else:
                    visible = False
            
            if len(pts) > 2 and visible:
                is_hover = (name == "india" and self.hovered_country == "India")
                col = Theme.LAND_HOVER if is_hover else Theme.LAND
                pygame.draw.polygon(screen, col, pts)
                bc = Theme.CYAN_GLOW if name == "india" else Theme.BORDER
                pygame.draw.polygon(screen, bc, pts, 2)
        
        # Country markers
        for name, data in COUNTRIES.items():
            x, y, z = self.latlon_screen(data["lat"], data["lon"])
            if z > 0.15:
                is_hov = (name == self.hovered_country)
                col = Theme.ORANGE if is_hov else Theme.CYAN
                pygame.draw.circle(screen, col, (x, y), 4 if is_hov else 2)
        
        # Outline
        pygame.draw.circle(screen, Theme.CYAN, (self.cx, self.cy), self.radius, 2)


# ═══════════════════════════════════════════════════════════════
# ORBITAL RINGS (around globe)
# ═══════════════════════════════════════════════════════════════

class Orbits:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.rings = [
            {"off": 18, "spd": 0.38, "seg": 52, "gap": 4, "col": Theme.CYAN_DIM},
            {"off": 40, "spd": -0.25, "seg": 64, "gap": 5, "col": Theme.CYAN_DIM},
            {"off": 62, "spd": 0.32, "seg": 76, "gap": 3, "col": Theme.CYAN_DIM},
            {"off": 88, "spd": -0.16, "seg": 58, "gap": 6, "col": Theme.ORANGE_DIM},
        ]
        for r in self.rings:
            r["rot"] = 0
    
    def update(self):
        for r in self.rings:
            r["rot"] += r["spd"]
    
    def draw(self, screen, radius):
        for r in self.rings:
            rad = radius + r["off"]
            for i in range(r["seg"]):
                if (i + int(r["rot"] / 8)) % r["gap"] == 0:
                    continue
                ang = 2 * math.pi * i / r["seg"] + math.radians(r["rot"])
                arc = 2 * math.pi / r["seg"] * 0.7
                rect = pygame.Rect(self.cx - rad, self.cy - rad, rad*2, rad*2)
                pygame.draw.arc(screen, r["col"], rect, ang, ang + arc, 1)


# ═══════════════════════════════════════════════════════════════
# MAIN HUD (Reactive Display)
# ═══════════════════════════════════════════════════════════════

class HUD:
    """JARVIS HUD - Reactive Display Interface"""
    
    def __init__(self, state_manager: 'StateManager' = None):
        pygame.init()
        print("=" * 55)
        print("   J.A.R.V.I.S. ULTIMATE INTERFACE v9.0")
        print("=" * 55)
        
        self._state_manager = state_manager
        if self._state_manager is None and STATE_MANAGER_AVAILABLE:
            try:
                self._state_manager = get_state_manager()
            except:
                pass
        
        info = pygame.display.Info()
        self.W = min(1750, int(info.current_w * 0.95))
        self.H = min(980, int(info.current_h * 0.92))
        
        gcx, gcy = self.W // 2, self.H // 2 + 20
        gradius = min(self.W, self.H) // 4  # Slightly larger globe
        
        # Use Iron Man globe if available
        if IRON_MAN_GLOBE_AVAILABLE:
            self.globe = IronManGlobe(gcx, gcy, gradius)
            self.use_iron_man_globe = True
            print("[HUD] Using Iron Man Globe")
        else:
            self.globe = Globe(gcx, gcy, gradius)
            self.use_iron_man_globe = False
            print("[HUD] Using standard Globe")
        
        self.orb = JARVISOrb(self.W, self.H)  # Work-reactive JARVIS orb
        self.orbits = Orbits(gcx, gcy)
        
        self._fallback_state = State.IDLE
        self.mode = Mode.JARVIS
        self.frame = 0
        
        self.mouse = (0, 0)
        self.mouse_smooth = [float(self.W // 2), float(self.H // 2)]
        
        # Particles
        self.particles = [(random.uniform(0, self.W), random.uniform(0, self.H),
                          random.uniform(0.2, 1.0), random.uniform(1, 2.5),
                          random.uniform(0.3, 1.0)) for _ in range(100)]
        
        # Audio visualization
        self.audio = deque([0] * 60, maxlen=60)
        
        # System info
        self.sys = {"cpu": 0, "mem": 0, "bat": 100}
        self._update_sys()
        
        # Chat
        self.chat = [
            ("jarvis", "Good evening sir. All systems ready."),
            ("user", "Show me the world"),
            ("jarvis", "Interactive globe displayed."),
        ]
        self.chat_input = ""
        self.chat_focused = False
        
        # Widgets data
        self.weather = {"temp": "24°C", "cond": "Partly Cloudy", "city": "Loading..."}
        self.news = ["AI breakthrough announced...", "Tech stocks rise 5%...", "New energy solution..."]
        self.todo = ["Review project", "Call team", "Update docs"]
        self.reminders = ["Meeting at 3 PM", "Gym at 6 PM"]
        self.music = {"track": "No Track", "artist": "—", "playing": False}
        
        self.show_help = False
        
        # Fonts
        self.f_sm = pygame.font.Font(None, 14)
        self.f_md = pygame.font.Font(None, 18)
        self.f_lg = pygame.font.Font(None, 28)
        
        print(f"[HUD] {self.W}x{self.H} | StateManager: {'Connected' if self._state_manager else 'Standalone'}")
    
    @property
    def state(self) -> State:
        if self._state_manager:
            return self._state_manager.state
        return self._fallback_state
    
    def _update_sys(self):
        try:
            self.sys["cpu"] = psutil.cpu_percent()
            self.sys["mem"] = psutil.virtual_memory().percent
            bat = psutil.sensors_battery()
            if bat:
                self.sys["bat"] = bat.percent
        except:
            pass
    
    def _parallax(self, screen):
        ox = (self.mouse_smooth[0] - self.W / 2) / 25
        oy = (self.mouse_smooth[1] - self.H / 2) / 25
        
        for px, py, pz, sz, br in self.particles:
            x = (px + ox * pz) % self.W
            y = (py + oy * pz) % self.H
            tw = 0.7 + 0.3 * math.sin(self.frame * 0.04 + px)
            a = int(br * tw * 160)
            if a > 0:
                s = pygame.Surface((int(sz) + 1, int(sz) + 1), pygame.SRCALPHA)
                pygame.draw.circle(s, (200, 230, 255, a), (int(sz)//2, int(sz)//2), max(1, int(sz)//2))
                screen.blit(s, (int(x), int(y)))
    
    def _panel(self, screen, x, y, w, h, title, hov=False):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        bc = Theme.CYAN if hov else Theme.CYAN_DIM
        pygame.draw.rect(s, (Theme.PANEL[0], Theme.PANEL[1], Theme.PANEL[2], 220), (0, 0, w, h))
        pygame.draw.rect(s, bc, (0, 0, w, h), 2 if hov else 1)
        screen.blit(s, (x, y))
        screen.blit(self.f_sm.render(title, True, Theme.ORANGE), (x + 7, y + 4))
        pygame.draw.line(screen, Theme.CYAN_DIM, (x + 5, y + 18), (x + w - 5, y + 18), 1)
        return y + 22
    
    # ─────── LEFT PANELS ───────
    
    def _sys_panel(self, screen):
        x, y, w, h = 16, 16, 180, 100
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "SYSTEM", hov)
        
        for i, (lbl, val, col) in enumerate([
            ("CPU", self.sys["cpu"], Theme.CYAN),
            ("MEM", self.sys["mem"], Theme.ORANGE),
            ("BAT", self.sys["bat"], Theme.GREEN if self.sys["bat"] > 20 else Theme.RED),
        ]):
            iy = ty + i * 24
            screen.blit(self.f_sm.render(f"{lbl}: {val:.0f}%", True, Theme.TEXT), (x + 7, iy))
            bx, bw = x + 58, 112
            pygame.draw.rect(screen, Theme.GRID, (bx, iy, bw, 10))
            pygame.draw.rect(screen, col, (bx, iy, int(bw * val / 100), 10))
    
    def _audio_panel(self, screen):
        x, y, w, h = 16, 126, 180, 70
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "AUDIO", hov)
        
        if self.state == State.LISTENING:
            self.audio.append(random.uniform(0.4, 1.0))
        else:
            self.audio.append(random.uniform(0, 0.08))
        
        for i, v in enumerate(self.audio):
            bh = int(v * 32)
            col = Theme.GREEN if self.state == State.LISTENING else Theme.CYAN_DIM
            pygame.draw.rect(screen, col, (x + 6 + i * 2, ty + 28 - bh, 1, bh))
    
    def _weather_panel(self, screen):
        x, y, w, h = 16, 206, 180, 80
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "WEATHER", hov)
        
        screen.blit(self.f_lg.render(self.weather["temp"], True, Theme.CYAN), (x + 10, ty + 2))
        screen.blit(self.f_sm.render(self.weather["cond"], True, Theme.TEXT), (x + 10, ty + 28))
        screen.blit(self.f_sm.render(self.weather["city"], True, Theme.TEXT_DIM), (x + 10, ty + 42))
    
    def _music_panel(self, screen):
        x, y, w, h = 16, 296, 180, 90
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "MUSIC", hov)
        
        screen.blit(self.f_md.render(self.music["track"][:20], True, Theme.TEXT), (x + 10, ty + 2))
        screen.blit(self.f_sm.render(self.music["artist"][:20], True, Theme.TEXT_DIM), (x + 10, ty + 18))
        
        # Play/Pause button
        btn_rect = pygame.Rect(x + 10, ty + 38, 60, 22)
        btn_hov = btn_rect.collidepoint(self.mouse)
        pygame.draw.rect(screen, Theme.PANEL_HOVER if btn_hov else Theme.PANEL, btn_rect)
        pygame.draw.rect(screen, Theme.CYAN if btn_hov else Theme.CYAN_DIM, btn_rect, 1)
        lbl = "PAUSE" if self.music["playing"] else "PLAY"
        ts = self.f_sm.render(lbl, True, Theme.CYAN)
        screen.blit(ts, (btn_rect.centerx - ts.get_width()//2, btn_rect.centery - ts.get_height()//2))
        
        # Open Spotify button
        sp_rect = pygame.Rect(x + 80, ty + 38, 80, 22)
        sp_hov = sp_rect.collidepoint(self.mouse)
        pygame.draw.rect(screen, Theme.PANEL_HOVER if sp_hov else Theme.PANEL, sp_rect)
        pygame.draw.rect(screen, Theme.GREEN if sp_hov else Theme.CYAN_DIM, sp_rect, 1)
        ts = self.f_sm.render("SPOTIFY", True, Theme.GREEN)
        screen.blit(ts, (sp_rect.centerx - ts.get_width()//2, sp_rect.centery - ts.get_height()//2))
    
    # ─────── RIGHT PANELS ───────
    
    def _news_panel(self, screen):
        x, y, w, h = self.W - 196, 16, 180, 100
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "NEWS", hov)
        
        for i, item in enumerate(self.news[:3]):
            screen.blit(self.f_sm.render("• " + item[:22], True, Theme.TEXT), (x + 7, ty + i * 22))
    
    def _todo_panel(self, screen):
        x, y, w, h = self.W - 196, 126, 180, 90
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "TO-DO", hov)
        
        for i, item in enumerate(self.todo[:3]):
            screen.blit(self.f_sm.render(f"□ {item[:20]}", True, Theme.TEXT), (x + 7, ty + i * 20))
    
    def _reminders_panel(self, screen):
        x, y, w, h = self.W - 196, 226, 180, 70
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "REMINDERS", hov)
        
        for i, item in enumerate(self.reminders[:2]):
            screen.blit(self.f_sm.render(f"⏰ {item[:20]}", True, Theme.ORANGE), (x + 7, ty + i * 20))
    
    def _chat_panel(self, screen):
        x, y, w, h = self.W - 196, 306, 180, 200
        hov = pygame.Rect(x, y, w, h).collidepoint(self.mouse)
        ty = self._panel(screen, x, y, w, h, "CHAT", hov)
        
        # Messages
        my = ty
        for role, msg in self.chat[-5:]:
            if my > y + h - 48:
                break
            is_u = role == "user"
            c = Theme.ORANGE if is_u else Theme.CYAN
            screen.blit(self.f_sm.render(f"[{'YOU' if is_u else 'J'}] {msg[:22]}", True, c), (x + 5, my))
            my += 16
        
        # Input box
        iy = y + h - 26
        ir = pygame.Rect(x + 5, iy, w - 10, 20)
        pygame.draw.rect(screen, Theme.GRID, ir)
        pygame.draw.rect(screen, Theme.CYAN if self.chat_focused else Theme.CYAN_DIM, ir, 1)
        
        txt = self.chat_input if self.chat_input else "Type here..."
        tc = Theme.TEXT if self.chat_input else Theme.TEXT_DIM
        screen.blit(self.f_sm.render(txt[:20], True, tc), (x + 8, iy + 4))
    
    # ─────── BOTTOM ───────
    
    def _time_display(self, screen):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %B %d, %Y")
        
        ts = self.f_lg.render(time_str, True, Theme.CYAN)
        screen.blit(ts, (self.W // 2 - ts.get_width() // 2, self.H - 70))
        
        ds = self.f_sm.render(date_str, True, Theme.TEXT_DIM)
        screen.blit(ds, (self.W // 2 - ds.get_width() // 2, self.H - 48))
    
    def _buttons(self, screen):
        btns = [
            ("[H] Help", False),
            ("[C] Chat", True),
            ("[S] Spotify", False),
        ]
        
        bw, bh, gap = 85, 25, 10
        total = len(btns) * bw + (len(btns) - 1) * gap
        sx = self.W // 2 - total // 2
        by = self.H - 30
        
        for i, (txt, active) in enumerate(btns):
            bx = sx + i * (bw + gap)
            rect = pygame.Rect(bx, by, bw, bh)
            hov = rect.collidepoint(self.mouse)
            col = Theme.ORANGE if active else (Theme.CYAN if hov else Theme.CYAN_DIM)
            
            pygame.draw.rect(screen, Theme.PANEL, rect)
            pygame.draw.rect(screen, col, rect, 2 if hov or active else 1)
            ts = self.f_sm.render(txt, True, col)
            screen.blit(ts, (rect.centerx - ts.get_width() // 2, rect.centery - ts.get_height() // 2))
    
    def _mode_indicator(self, screen):
        mode_str = self.mode.value
        state_str = self.state.value if hasattr(self.state, 'value') else str(self.state)
        
        screen.blit(self.f_md.render(mode_str, True, Theme.CYAN), (self.W // 2 - 40, 12))
        screen.blit(self.f_sm.render(f"STATE: {state_str}", True, Theme.TEXT_DIM), (self.W // 2 - 35, 30))
    
    def _tooltip(self, screen):
        # Handle both IronManGlobe (hover_latlon/hover_country) and Globe (hover_coords/hovered_country)
        hover_coords = getattr(self.globe, 'hover_coords', None) or getattr(self.globe, 'hover_latlon', None)
        hovered_country = getattr(self.globe, 'hovered_country', None) or getattr(self.globe, 'hover_country', None)
        
        if hover_coords and hovered_country:
            lat, lon = hover_coords
            country = hovered_country
            
            lines = [country, f"{lat:.1f}°, {lon:.1f}°"]
            
            mx, my = self.mouse
            tw = max(self.f_md.size(l)[0] for l in lines) + 20
            th = len(lines) * 18 + 10
            
            tx = min(mx + 15, self.W - tw - 10)
            ty = max(10, my - th - 10)
            
            s = pygame.Surface((tw, th), pygame.SRCALPHA)
            pygame.draw.rect(s, (10, 20, 35, 230), (0, 0, tw, th))
            pygame.draw.rect(s, Theme.CYAN, (0, 0, tw, th), 1)
            screen.blit(s, (tx, ty))
            
            screen.blit(self.f_md.render(lines[0], True, Theme.CYAN), (tx + 8, ty + 5))
            screen.blit(self.f_sm.render(lines[1], True, Theme.TEXT_DIM), (tx + 8, ty + 22))
    
    def _help(self, screen):
        if not self.show_help:
            return
        
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        
        w, h = 340, 260
        x, y = self.W // 2 - w // 2, self.H // 2 - h // 2
        pygame.draw.rect(screen, Theme.PANEL, (x, y, w, h))
        pygame.draw.rect(screen, Theme.ORANGE, (x, y, w, h), 2)
        
        screen.blit(self.f_md.render("JARVIS CONTROLS", True, Theme.ORANGE), (self.W // 2 - 60, y + 12))
        
        cmds = [
            ("Drag Globe", "Rotate view"), ("Scroll", "Zoom in/out"),
            ("Hover", "Country info"), ("H", "Toggle help"),
            ("C", "Toggle chat focus"), ("S", "Open Spotify"),
            ("ESC", "Exit")
        ]
        
        for i, (k, d) in enumerate(cmds):
            screen.blit(self.f_sm.render(k, True, Theme.CYAN), (x + 25, y + 42 + i * 28))
            screen.blit(self.f_sm.render(d, True, Theme.TEXT), (x + 120, y + 42 + i * 28))
    
    def event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.mouse = e.pos
        
        self.globe.event(e)
        
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_h:
                self.show_help = not self.show_help
            elif e.key == pygame.K_c:
                self.chat_focused = not self.chat_focused
            elif e.key == pygame.K_s:
                webbrowser.open("spotify:///")
            elif e.key == pygame.K_f:
                self.mode = Mode.FRIDAY if self.mode == Mode.JARVIS else Mode.JARVIS
            elif self.chat_focused:
                if e.key == pygame.K_RETURN and self.chat_input:
                    self.chat.append(("user", self.chat_input))
                    self.chat_input = ""
                elif e.key == pygame.K_BACKSPACE:
                    self.chat_input = self.chat_input[:-1]
                elif e.unicode and len(self.chat_input) < 50:
                    self.chat_input += e.unicode
        
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            # Check Spotify button click
            sp_rect = pygame.Rect(96, 334, 80, 22)
            if sp_rect.collidepoint(e.pos):
                webbrowser.open("spotify:///")
    
    def update(self):
        self.frame += 1
        self.mouse_smooth[0] += (self.mouse[0] - self.mouse_smooth[0]) * 0.08
        self.mouse_smooth[1] += (self.mouse[1] - self.mouse_smooth[1]) * 0.08
        
        self.globe.update()
        self.orbits.update()
        self.orb.update(self.state, self.mouse)  # JARVIS orb moves freely
        
        if self.frame % 60 == 0:
            self._update_sys()
    
    def render(self, screen):
        screen.fill(Theme.BG)
        self._parallax(screen)
        
        # Globe with orbits
        self.orbits.draw(screen, self.globe.radius)
        self.globe.draw(screen)
        
        # JARVIS orb (moves freely across screen)
        self.orb.draw(screen)
        
        # Left panels
        self._sys_panel(screen)
        self._audio_panel(screen)
        self._weather_panel(screen)
        self._music_panel(screen)
        
        # Right panels
        self._news_panel(screen)
        self._todo_panel(screen)
        self._reminders_panel(screen)
        self._chat_panel(screen)
        
        # Bottom
        self._mode_indicator(screen)
        self._time_display(screen)
        self._buttons(screen)
        
        # Overlays
        self._tooltip(screen)
        self._help(screen)


def main():
    hud = HUD()
    screen = pygame.display.set_mode((hud.W, hud.H), pygame.RESIZABLE)
    pygame.display.set_caption("J.A.R.V.I.S. Ultimate v9")
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            elif e.type == pygame.VIDEORESIZE:
                hud.W, hud.H = e.w, e.h
                hud.globe.cx = hud.orbits.cx = e.w // 2
                hud.globe.cy = hud.orbits.cy = e.h // 2 + 20
                hud.orb.screen_w = e.w
                hud.orb.screen_h = e.h
                hud.globe.glow_cache.clear()
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            else:
                hud.event(e)
        
        hud.update()
        hud.render(screen)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()
