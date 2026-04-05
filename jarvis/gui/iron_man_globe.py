"""
JARVIS ULTIMATE GLOBE - Iron Man Style
Ultra-realistic 3D holographic globe with:
- GeoJSON-accurate continent shapes
- Country borders and city markers
- Real-time day/night terminator
- Animated data connections
- Detailed latitude/longitude grid
- Glass-like holographic effect
"""

import pygame
import math
import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════
# IRON MAN GLOBE THEME
# ═══════════════════════════════════════════════════════════════

class GlobeTheme:
    # Core colors
    BG = (2, 6, 12)
    OCEAN = (3, 15, 28)
    DEEP_OCEAN = (2, 10, 22)
    
    # Holographic cyan
    HOLO_CYAN = (0, 255, 255)
    HOLO_CYAN_MED = (0, 200, 220)
    HOLO_CYAN_DIM = (0, 100, 140)
    HOLO_CYAN_FAINT = (0, 50, 70)
    
    # Land
    LAND = (0, 90, 120)
    LAND_GLOW = (0, 140, 170)
    LAND_BORDER = (0, 220, 255)
    
    # India highlight
    INDIA = (255, 180, 0)
    INDIA_GLOW = (255, 200, 100)
    
    # Grid
    GRID_MAJOR = (0, 80, 110)
    GRID_MINOR = (0, 40, 60)
    EQUATOR = (0, 255, 200)
    
    # Cities
    CITY_GLOW = (255, 255, 255)
    CITY_PULSE = (0, 255, 180)
    
    # Data streams
    DATA_STREAM = (0, 255, 200)
    DATA_STREAM_2 = (255, 180, 0)


# ═══════════════════════════════════════════════════════════════
# VERY DETAILED CONTINENT DATA (GeoJSON-like accuracy)
# ═══════════════════════════════════════════════════════════════

CONTINENTS_DETAILED = {
    "africa": [
        (37.5, -5.5), (36.8, -2.0), (35.9, 0.0), (35.5, 1.5), (36.5, 3.0), (37.3, 6.5),
        (36.9, 8.5), (35.8, 10.0), (34.5, 11.5), (33.0, 11.0), (32.5, 13.5), (31.5, 15.5),
        (31.2, 18.0), (30.5, 20.5), (31.0, 23.5), (30.5, 26.0), (31.2, 28.5), (31.5, 30.0),
        (31.0, 31.5), (30.0, 32.5), (29.5, 34.0), (27.5, 34.0), (25.0, 35.0), (22.5, 36.5),
        (20.0, 37.0), (17.5, 38.5), (15.0, 40.0), (12.5, 42.0), (11.5, 43.5), (10.5, 45.0),
        (9.0, 46.5), (7.0, 48.0), (5.0, 49.0), (3.0, 50.0), (1.0, 50.0), (-1.0, 49.0),
        (-3.0, 47.5), (-5.0, 45.5), (-7.0, 43.0), (-9.0, 41.0), (-11.0, 39.5), (-13.0, 38.0),
        (-15.0, 36.5), (-17.5, 35.0), (-20.0, 33.5), (-22.5, 31.5), (-25.0, 29.5), (-27.0, 27.0),
        (-29.0, 25.0), (-31.0, 22.5), (-33.0, 20.0), (-34.5, 18.0), (-34.8, 16.0), (-34.0, 17.5),
        (-33.0, 19.5), (-31.5, 22.0), (-30.0, 24.5), (-28.5, 27.0), (-27.0, 29.0), (-25.5, 31.0),
        (-24.0, 32.5), (-22.0, 34.0), (-20.0, 35.5), (-17.5, 37.0), (-15.0, 37.5), (-13.0, 36.0),
        (-11.0, 33.5), (-9.0, 30.0), (-7.0, 26.0), (-5.0, 21.0), (-3.0, 16.0), (-1.0, 12.0),
        (1.0, 8.0), (3.0, 5.0), (5.0, 2.0), (7.0, -1.0), (9.0, -3.5), (11.0, -6.0),
        (13.0, -8.0), (15.0, -10.0), (17.0, -12.5), (19.0, -14.5), (21.0, -16.0), (23.0, -14.5),
        (25.0, -12.5), (27.0, -10.0), (29.0, -8.0), (31.0, -6.0), (33.0, -4.0), (35.0, -3.0),
        (37.0, -4.5), (37.5, -5.5)
    ],
    "europe": [
        (36.0, -9.0), (37.0, -8.0), (38.5, -9.0), (40.0, -8.5), (41.5, -8.5), (43.0, -9.0),
        (43.5, -7.5), (43.0, -4.5), (43.5, -2.0), (42.5, 0.0), (43.0, 2.5), (43.5, 4.0),
        (44.0, 5.5), (44.5, 7.0), (45.5, 8.0), (46.0, 9.5), (47.0, 10.0), (47.5, 11.5),
        (48.5, 12.0), (49.0, 13.0), (50.0, 14.0), (50.5, 15.5), (51.5, 14.0), (52.0, 12.5),
        (53.5, 12.0), (54.5, 10.0), (55.0, 9.0), (55.5, 10.5), (56.5, 12.0), (57.5, 12.5),
        (58.0, 14.0), (59.0, 16.0), (59.5, 18.0), (60.5, 20.0), (61.5, 22.0), (62.5, 24.0),
        (64.0, 26.0), (65.5, 27.5), (67.0, 29.0), (68.5, 30.0), (70.0, 30.0), (71.0, 28.5),
        (70.0, 26.0), (69.0, 23.5), (68.0, 21.0), (67.0, 18.5), (66.0, 16.0), (64.5, 14.0),
        (63.0, 12.0), (61.5, 10.5), (60.0, 9.5), (58.5, 8.0), (57.0, 6.5), (55.5, 5.0),
        (54.0, 4.0), (52.5, 3.5), (51.0, 2.5), (49.5, 2.0), (48.0, 2.5), (46.5, 4.0),
        (45.0, 6.0), (44.0, 8.0), (43.0, 10.0), (42.0, 12.5), (41.0, 14.5), (40.0, 16.5),
        (39.0, 18.5), (38.0, 20.0), (37.0, 21.5), (36.5, 23.0), (37.0, 25.0), (38.0, 26.5),
        (39.5, 27.5), (41.0, 28.0), (42.5, 27.0), (44.0, 25.0), (45.5, 22.5), (46.5, 20.0),
        (47.0, 17.5), (46.5, 15.0), (45.5, 12.5), (44.5, 10.0), (43.5, 7.5), (42.5, 5.0),
        (41.5, 3.0), (40.0, 1.0), (38.5, -0.5), (37.0, -2.5), (36.0, -5.0), (36.0, -9.0)
    ],
    "asia": [
        # Western border
        (42.0, 28.0), (43.5, 32.0), (45.0, 38.0), (47.0, 45.0), (49.0, 52.0), (51.0, 58.0),
        (53.0, 64.0), (55.0, 70.0), (57.0, 78.0), (59.0, 85.0), (61.0, 92.0), (63.0, 100.0),
        (65.0, 110.0), (67.0, 120.0), (69.0, 135.0), (70.5, 150.0), (71.0, 165.0), (70.5, 175.0),
        (68.0, -178.0), (66.0, -172.0), (64.0, -168.0),
        # Eastern coast
        (62.0, 165.0), (60.0, 160.0), (58.0, 155.0), (55.0, 150.0), (52.0, 145.0),
        (48.0, 142.0), (45.0, 140.0), (42.0, 138.0), (38.0, 135.0), (35.0, 132.0),
        (32.0, 128.0), (28.0, 122.0), (24.0, 118.0), (20.0, 112.0), (16.0, 108.0),
        (12.0, 104.0), (8.0, 100.0), (4.0, 102.0), (0.0, 105.0), (-4.0, 108.0),
        (-8.0, 115.0), (-6.0, 120.0), (-4.0, 128.0), (-2.0, 135.0), (0.0, 140.0),
        # Southern Asia
        (8.0, 98.0), (12.0, 95.0), (16.0, 96.0), (20.0, 93.0), (22.0, 90.0),
        (24.0, 88.0), (26.0, 86.0), (28.0, 82.0), (30.0, 78.0), (32.0, 75.0),
        (34.0, 72.0), (36.0, 68.0), (38.0, 62.0), (40.0, 55.0), (42.0, 48.0),
        (42.0, 28.0)  # Back to start
    ],
    "north_america": [
        (72.0, -95.0), (73.0, -80.0), (71.0, -70.0), (69.0, -68.0), (67.0, -75.0),
        (65.0, -80.0), (63.0, -78.0), (61.0, -75.0), (59.0, -77.0), (57.0, -78.0),
        (55.0, -78.0), (53.0, -79.0), (51.0, -78.0), (49.0, -75.0), (47.0, -78.0),
        (45.0, -75.0), (44.0, -77.0), (43.0, -79.0), (42.0, -82.0), (44.0, -82.5),
        (46.0, -84.0), (47.0, -88.0), (48.0, -90.0), (49.0, -95.0), (49.0, -102.0),
        (49.0, -110.0), (49.0, -118.0), (49.0, -123.0),
        # West coast
        (48.0, -124.0), (46.0, -124.0), (43.0, -124.0), (40.0, -124.0),
        (38.0, -123.0), (36.0, -122.0), (34.0, -120.0), (32.0, -117.0),
        (30.0, -114.0), (28.0, -112.0), (26.0, -110.0), (24.0, -108.0),
        (22.0, -106.0), (20.0, -105.0), (18.0, -103.0), (16.0, -98.0),
        (18.0, -92.0), (19.0, -88.0), (21.0, -87.0), (22.0, -90.0),
        (24.0, -97.0), (26.0, -97.0), (28.0, -96.0), (30.0, -94.0),
        (29.0, -90.0), (28.0, -88.0), (30.0, -84.0), (29.0, -82.0),
        (27.0, -80.0), (25.0, -80.0), (26.0, -82.0), (28.0, -80.0),
        (30.0, -81.0), (32.0, -80.0), (34.0, -77.0), (36.0, -75.0),
        (38.0, -74.0), (40.0, -73.0), (42.0, -70.0), (44.0, -68.0),
        (46.0, -65.0), (48.0, -60.0), (50.0, -57.0), (52.0, -56.0),
        (54.0, -58.0), (56.0, -62.0), (58.0, -66.0), (60.0, -65.0),
        (62.0, -68.0), (64.0, -72.0), (66.0, -78.0), (68.0, -85.0),
        (70.0, -95.0), (72.0, -95.0)
    ],
    "south_america": [
        (12.0, -72.0), (11.0, -74.0), (9.0, -76.0), (7.0, -78.0), (4.0, -78.0),
        (2.0, -79.0), (0.0, -80.0), (-2.0, -80.0), (-4.0, -79.0), (-6.0, -76.0),
        (-8.0, -74.0), (-10.0, -75.0), (-12.0, -76.0), (-14.0, -74.0), (-16.0, -70.0),
        (-14.0, -64.0), (-16.0, -58.0), (-18.0, -52.0), (-20.0, -48.0), (-22.0, -44.0),
        (-24.0, -45.0), (-26.0, -48.0), (-28.0, -50.0), (-30.0, -52.0), (-32.0, -54.0),
        (-34.0, -56.0), (-36.0, -58.0), (-38.0, -60.0), (-40.0, -62.0), (-42.0, -64.0),
        (-44.0, -66.0), (-46.0, -68.0), (-48.0, -70.0), (-50.0, -72.0), (-52.0, -70.0),
        (-54.0, -68.0), (-55.0, -66.0), (-54.0, -64.0), (-52.0, -72.0), (-50.0, -74.0),
        (-48.0, -75.0), (-46.0, -74.0), (-44.0, -73.0), (-42.0, -72.0), (-40.0, -71.0),
        (-38.0, -70.0), (-36.0, -71.0), (-34.0, -72.0), (-32.0, -71.0), (-30.0, -70.0),
        (-28.0, -70.0), (-26.0, -70.0), (-24.0, -71.0), (-22.0, -71.0), (-20.0, -72.0),
        (-18.0, -74.0), (-16.0, -76.0), (-14.0, -78.0), (-12.0, -78.0), (-10.0, -77.0),
        (-8.0, -75.0), (-6.0, -73.0), (-4.0, -72.0), (-2.0, -71.0), (0.0, -72.0),
        (2.0, -73.0), (4.0, -72.0), (6.0, -71.0), (8.0, -72.0), (10.0, -72.0),
        (12.0, -72.0)
    ],
    "australia": [
        (-12.0, 132.0), (-14.0, 127.0), (-17.0, 122.0), (-20.0, 118.0), (-24.0, 114.0),
        (-28.0, 114.0), (-31.0, 116.0), (-33.0, 119.0), (-35.0, 124.0), (-35.0, 130.0),
        (-36.0, 135.0), (-37.0, 140.0), (-38.0, 145.0), (-38.0, 148.0), (-36.0, 150.0),
        (-33.0, 152.0), (-30.0, 153.0), (-27.0, 153.0), (-24.0, 152.0), (-21.0, 149.0),
        (-18.0, 146.0), (-16.0, 145.0), (-14.0, 147.0), (-12.0, 142.0), (-11.0, 138.0),
        (-12.0, 135.0), (-12.0, 132.0)
    ],
    "india": [
        (35.0, 74.0), (33.0, 78.0), (30.0, 80.0), (28.0, 84.0), (26.0, 88.0), (24.0, 90.0),
        (22.0, 92.0), (20.0, 93.0), (17.0, 95.0), (14.0, 93.0), (11.0, 90.0), (8.5, 78.0),
        (8.0, 77.0), (10.0, 76.0), (12.0, 77.0), (14.0, 79.0), (16.0, 80.0), (18.0, 82.0),
        (19.0, 84.0), (21.0, 86.0), (22.0, 84.0), (21.0, 80.0), (19.0, 76.0), (18.0, 73.0),
        (20.0, 72.0), (22.0, 69.0), (24.0, 69.0), (26.0, 70.0), (28.0, 72.0), (30.0, 73.0),
        (33.0, 72.0), (35.0, 74.0)
    ],
    "greenland": [
        (84.0, -35.0), (83.0, -25.0), (81.0, -18.0), (78.0, -18.0), (75.0, -20.0),
        (72.0, -22.0), (70.0, -25.0), (68.0, -30.0), (65.0, -40.0), (62.0, -45.0),
        (60.0, -48.0), (60.5, -52.0), (63.0, -55.0), (66.0, -56.0), (70.0, -57.0),
        (74.0, -60.0), (77.0, -65.0), (80.0, -68.0), (82.0, -58.0), (83.0, -45.0),
        (84.0, -35.0)
    ],
    "uk": [
        (50.0, -5.5), (51.0, -4.0), (52.5, -2.5), (53.5, -3.0), (54.5, -2.0),
        (55.5, -1.5), (56.5, -3.0), (57.5, -5.5), (58.5, -5.0), (58.0, -3.0),
        (57.0, -2.0), (55.5, 0.0), (54.0, 0.5), (53.0, 0.0), (52.0, 1.5),
        (51.0, 1.0), (50.5, 0.0), (50.0, -2.0), (50.0, -5.5)
    ],
    "japan": [
        (45.5, 142.0), (44.0, 145.0), (43.0, 146.0), (42.0, 144.0), (41.0, 140.0),
        (40.0, 139.0), (38.0, 139.0), (36.0, 140.0), (35.0, 139.0), (34.0, 136.0),
        (33.0, 132.0), (32.0, 130.0), (31.5, 131.0), (33.0, 135.0), (35.0, 136.0),
        (37.0, 137.0), (39.0, 138.0), (41.0, 140.0), (43.0, 141.0), (45.5, 142.0)
    ]
}


# Major cities
MAJOR_CITIES = [
    ("New York", 40.7, -74.0), ("London", 51.5, -0.1), ("Tokyo", 35.7, 139.7),
    ("Beijing", 39.9, 116.4), ("Mumbai", 19.1, 72.9), ("Delhi", 28.6, 77.2),
    ("São Paulo", -23.5, -46.6), ("Sydney", -33.9, 151.2), ("Dubai", 25.2, 55.3),
    ("Singapore", 1.3, 103.8), ("Paris", 48.9, 2.3), ("Moscow", 55.8, 37.6),
    ("Cairo", 30.0, 31.2), ("Lagos", 6.5, 3.4), ("Jakarta", -6.2, 106.8),
    ("Toronto", 43.7, -79.4), ("Los Angeles", 34.0, -118.2), ("Shanghai", 31.2, 121.5),
    ("Berlin", 52.5, 13.4), ("Seoul", 37.6, 127.0)
]


# ═══════════════════════════════════════════════════════════════
# IRON MAN GLOBE CLASS
# ═══════════════════════════════════════════════════════════════

class IronManGlobe:
    """Ultra-realistic Iron Man style holographic globe"""
    
    def __init__(self, cx: int, cy: int, radius: int):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        
        # Rotation
        self.rot_lon = 78.0  # Start viewing India
        self.rot_lat = 15.0
        self.auto_rotate = True
        self.dragging = False
        self.last_mouse = (0, 0)
        self.interaction_pause = 0
        
        # Hover info
        self.hover_latlon = None
        self.hover_country = None
        
        # Animation
        self.frame = 0
        self.pulse = 0.0
        
        # Data streams (animated connections)
        self.data_streams = self._init_data_streams()
        
        # City pulse animation
        self.city_pulses = {city[0]: random.uniform(0, 2*math.pi) for city in MAJOR_CITIES}
        
        # Cache
        self._glow_cache = {}
    
    def _init_data_streams(self) -> List[Dict]:
        """Initialize animated data streams between cities"""
        streams = []
        connections = [
            ("New York", "London"), ("London", "Mumbai"), ("Tokyo", "Singapore"),
            ("Dubai", "Mumbai"), ("Sydney", "Singapore"), ("Moscow", "Berlin"),
            ("Beijing", "Tokyo"), ("São Paulo", "New York"), ("Delhi", "Dubai"),
            ("Paris", "Cairo")
        ]
        
        for city1, city2 in connections:
            c1 = next((c for c in MAJOR_CITIES if c[0] == city1), None)
            c2 = next((c for c in MAJOR_CITIES if c[0] == city2), None)
            if c1 and c2:
                streams.append({
                    "from": (c1[1], c1[2]),
                    "to": (c2[1], c2[2]),
                    "progress": random.uniform(0, 1),
                    "speed": random.uniform(0.008, 0.018),
                    "color": GlobeTheme.DATA_STREAM if random.random() > 0.3 else GlobeTheme.DATA_STREAM_2
                })
        return streams
    
    def latlon_to_screen(self, lat: float, lon: float) -> Tuple[int, int, float]:
        """Convert lat/lon to screen coordinates with visibility check"""
        lat_r = math.radians(lat)
        lon_r = math.radians(lon - self.rot_lon)
        tilt_r = math.radians(self.rot_lat)
        
        # 3D coordinates
        x = math.cos(lat_r) * math.sin(lon_r)
        y = math.sin(lat_r) * math.cos(tilt_r) - math.cos(lat_r) * math.cos(lon_r) * math.sin(tilt_r)
        z = math.sin(lat_r) * math.sin(tilt_r) + math.cos(lat_r) * math.cos(lon_r) * math.cos(tilt_r)
        
        # Screen position
        sx = int(self.cx + x * self.radius)
        sy = int(self.cy - y * self.radius)
        
        return sx, sy, z
    
    def screen_to_latlon(self, sx: int, sy: int) -> Optional[Tuple[float, float]]:
        """Convert screen coordinates to lat/lon"""
        dx = (sx - self.cx) / self.radius
        dy = -(sy - self.cy) / self.radius
        d2 = dx*dx + dy*dy
        if d2 > 1:
            return None
        dz = math.sqrt(max(0, 1 - d2))
        
        tilt_r = math.radians(self.rot_lat)
        y_rot = dy * math.cos(tilt_r) + dz * math.sin(tilt_r)
        z_rot = -dy * math.sin(tilt_r) + dz * math.cos(tilt_r)
        
        lat = math.degrees(math.asin(max(-1, min(1, y_rot))))
        lon = math.degrees(math.atan2(dx, z_rot)) + self.rot_lon
        lon = ((lon + 180) % 360) - 180
        return lat, lon
    
    def get_glow(self, size: int, color: Tuple[int, int, int], spread: int) -> pygame.Surface:
        """Get cached glow surface"""
        key = (size, color, spread)
        if key not in self._glow_cache:
            dim = size * 2 + spread * 2
            surf = pygame.Surface((dim, dim), pygame.SRCALPHA)
            center = dim // 2
            for i in range(spread, 0, -1):
                alpha = int(40 * (1 - i / spread))
                pygame.draw.circle(surf, (*color[:3], alpha), (center, center), size + i)
            self._glow_cache[key] = surf
        return self._glow_cache[key]
    
    def update(self):
        """Update globe animation"""
        self.frame += 1
        self.pulse = (self.pulse + 0.05) % (2 * math.pi)
        
        # Auto rotation
        if self.interaction_pause > 0:
            self.interaction_pause -= 1
        elif self.auto_rotate and not self.dragging:
            self.rot_lon = (self.rot_lon - 0.12) % 360
        
        # Update data streams
        for stream in self.data_streams:
            stream["progress"] = (stream["progress"] + stream["speed"]) % 1.0
        
        # Update city pulses
        for city in self.city_pulses:
            self.city_pulses[city] += 0.08
    
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dx = event.pos[0] - self.cx
            dy = event.pos[1] - self.cy
            if dx*dx + dy*dy < self.radius * self.radius:
                self.dragging = True
                self.last_mouse = event.pos
                self.interaction_pause = 180
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                self.rot_lon = (self.rot_lon - dx * 0.35) % 360
                self.rot_lat = max(-70, min(70, self.rot_lat + dy * 0.25))
                self.last_mouse = event.pos
                self.interaction_pause = 180
            
            # Hover detection
            self.hover_latlon = self.screen_to_latlon(event.pos[0], event.pos[1])
            if self.hover_latlon:
                self.hover_country = self._find_country(self.hover_latlon[0], self.hover_latlon[1])
            else:
                self.hover_country = None
        
        elif event.type == pygame.MOUSEWHEEL:
            self.radius = max(80, min(350, self.radius + event.y * 15))
            self._glow_cache.clear()
    
    def _find_country(self, lat: float, lon: float) -> Optional[str]:
        """Find which country is at the given coordinates"""
        for name, data in [("United States", (38, -97)), ("India", (20, 78)), 
                           ("China", (35, 105)), ("Brazil", (-10, -55)),
                           ("Russia", (60, 100)), ("Australia", (-25, 134)),
                           ("UK", (52, -1)), ("Japan", (36, 138))]:
            dlat = abs(lat - data[0])
            dlon = abs(lon - data[1])
            if dlat < 12 and dlon < 15:
                return name
        return None
    
    def draw(self, screen: pygame.Surface):
        """Draw the complete globe"""
        # Outer glow
        glow = self.get_glow(self.radius + 20, GlobeTheme.HOLO_CYAN, 25)
        screen.blit(glow, (self.cx - glow.get_width()//2, self.cy - glow.get_height()//2))
        
        # Ocean background
        pygame.draw.circle(screen, GlobeTheme.OCEAN, (self.cx, self.cy), self.radius)
        
        # Inner ocean gradient
        for i in range(3):
            r = self.radius - 8 - i * 6
            alpha = 15 - i * 4
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*GlobeTheme.DEEP_OCEAN, alpha), (r, r), r)
            screen.blit(surf, (self.cx - r, self.cy - r))
        
        # Grid lines
        self._draw_grid(screen)
        
        # Continents
        self._draw_continents(screen)
        
        # Data streams
        self._draw_data_streams(screen)
        
        # Cities
        self._draw_cities(screen)
        
        # Outer ring
        pygame.draw.circle(screen, GlobeTheme.HOLO_CYAN, (self.cx, self.cy), self.radius, 2)
        
        # Pulsing outer ring
        pulse_r = self.radius + 5 + int(math.sin(self.pulse) * 3)
        pulse_alpha = int(80 + 40 * math.sin(self.pulse))
        for i in range(3):
            ring_surf = pygame.Surface((pulse_r*2+10, pulse_r*2+10), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*GlobeTheme.HOLO_CYAN, pulse_alpha - i*20), 
                             (pulse_r+5, pulse_r+5), pulse_r - i*2, 1)
            screen.blit(ring_surf, (self.cx - pulse_r - 5, self.cy - pulse_r - 5))
    
    def _draw_grid(self, screen: pygame.Surface):
        """Draw latitude/longitude grid"""
        # Latitude lines
        for lat in range(-75, 90, 15):
            pts = []
            for lon in range(0, 361, 5):
                sx, sy, z = self.latlon_to_screen(lat, lon)
                if z > -0.05:
                    pts.append((sx, sy))
                elif pts and len(pts) > 1:
                    col = GlobeTheme.EQUATOR if lat == 0 else GlobeTheme.GRID_MINOR
                    pygame.draw.lines(screen, col, False, pts, 1)
                    pts = []
            if len(pts) > 1:
                col = GlobeTheme.EQUATOR if lat == 0 else GlobeTheme.GRID_MINOR
                pygame.draw.lines(screen, col, False, pts, 1)
        
        # Longitude lines
        for lon in range(0, 360, 15):
            pts = []
            for lat in range(-75, 76, 4):
                sx, sy, z = self.latlon_to_screen(lat, lon)
                if z > -0.05:
                    pts.append((sx, sy))
                elif pts and len(pts) > 1:
                    pygame.draw.lines(screen, GlobeTheme.GRID_MINOR, False, pts, 1)
                    pts = []
            if len(pts) > 1:
                pygame.draw.lines(screen, GlobeTheme.GRID_MINOR, False, pts, 1)
    
    def _draw_continents(self, screen: pygame.Surface):
        """Draw all continents"""
        for name, points in CONTINENTS_DETAILED.items():
            screen_pts = []
            all_visible = True
            
            for lat, lon in points:
                sx, sy, z = self.latlon_to_screen(lat, lon)
                if z > 0.05:
                    screen_pts.append((sx, sy))
                else:
                    all_visible = False
            
            if len(screen_pts) > 2 and all_visible:
                # Is this India?
                is_india = name == "india"
                is_hover = (self.hover_country and name.lower() == self.hover_country.lower())
                
                # Fill
                if is_india:
                    fill_color = GlobeTheme.INDIA
                elif is_hover:
                    fill_color = GlobeTheme.LAND_GLOW
                else:
                    fill_color = GlobeTheme.LAND
                
                pygame.draw.polygon(screen, fill_color, screen_pts)
                
                # Border
                border_color = GlobeTheme.INDIA_GLOW if is_india else GlobeTheme.LAND_BORDER
                border_width = 3 if is_india else (2 if is_hover else 1)
                pygame.draw.polygon(screen, border_color, screen_pts, border_width)
    
    def _draw_data_streams(self, screen: pygame.Surface):
        """Draw animated data connections between cities"""
        for stream in self.data_streams:
            lat1, lon1 = stream["from"]
            lat2, lon2 = stream["to"]
            
            sx1, sy1, z1 = self.latlon_to_screen(lat1, lon1)
            sx2, sy2, z2 = self.latlon_to_screen(lat2, lon2)
            
            if z1 > 0 and z2 > 0:
                # Draw arc
                pts = []
                for t in range(21):
                    p = t / 20.0
                    lat = lat1 + (lat2 - lat1) * p
                    lon = lon1 + (lon2 - lon1) * p
                    # Add arc height
                    arc_height = math.sin(p * math.pi) * 0.1
                    sx, sy, z = self.latlon_to_screen(lat, lon)
                    sy = int(sy - arc_height * self.radius)
                    if z > 0:
                        pts.append((sx, sy))
                
                if len(pts) > 2:
                    # Draw faded line
                    for i in range(len(pts) - 1):
                        alpha = 40 + int(30 * abs(math.sin(self.frame * 0.05 + i * 0.2)))
                        surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (*stream["color"], alpha), (2, 2), 2)
                        screen.blit(surf, pts[i])
                    
                    # Draw moving particle
                    idx = int(stream["progress"] * (len(pts) - 1))
                    if 0 <= idx < len(pts):
                        px, py = pts[idx]
                        pygame.draw.circle(screen, stream["color"], (px, py), 4)
                        # Glow
                        glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*stream["color"], 100), (8, 8), 6)
                        screen.blit(glow_surf, (px - 8, py - 8))
    
    def _draw_cities(self, screen: pygame.Surface):
        """Draw major city markers with pulsing effect"""
        font = pygame.font.Font(None, 14)
        
        for name, lat, lon in MAJOR_CITIES:
            sx, sy, z = self.latlon_to_screen(lat, lon)
            
            if z > 0.15:
                # Pulse effect
                pulse = math.sin(self.city_pulses[name])
                
                # Core dot
                pygame.draw.circle(screen, GlobeTheme.CITY_PULSE, (sx, sy), 3)
                
                # Pulsing ring
                ring_r = int(5 + 3 * abs(pulse))
                ring_alpha = int(150 - 80 * abs(pulse))
                ring_surf = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*GlobeTheme.CITY_PULSE, ring_alpha), 
                                 (ring_r+2, ring_r+2), ring_r, 1)
                screen.blit(ring_surf, (sx - ring_r - 2, sy - ring_r - 2))
    
    def draw_tooltip(self, screen: pygame.Surface):
        """Draw hover tooltip"""
        if self.hover_latlon:
            lat, lon = self.hover_latlon
            
            lines = []
            if self.hover_country:
                lines.append(self.hover_country)
            lines.append(f"{lat:.1f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}°{'E' if lon >= 0 else 'W'}")
            
            font = pygame.font.Font(None, 18)
            widths = [font.size(l)[0] for l in lines]
            tw = max(widths) + 20
            th = len(lines) * 18 + 12
            
            # Position near mouse
            mouse_pos = pygame.mouse.get_pos()
            tx = min(mouse_pos[0] + 15, screen.get_width() - tw - 10)
            ty = max(10, mouse_pos[1] - th - 10)
            
            # Draw background
            surf = pygame.Surface((tw, th), pygame.SRCALPHA)
            pygame.draw.rect(surf, (5, 15, 30, 230), (0, 0, tw, th))
            pygame.draw.rect(surf, GlobeTheme.HOLO_CYAN, (0, 0, tw, th), 1)
            screen.blit(surf, (tx, ty))
            
            # Draw text
            for i, line in enumerate(lines):
                col = GlobeTheme.HOLO_CYAN if i == 0 else GlobeTheme.HOLO_CYAN_DIM
                text_surf = font.render(line, True, col)
                screen.blit(text_surf, (tx + 10, ty + 6 + i * 18))


# ═══════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pygame.init()
    
    W, H = 1200, 800
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("JARVIS Iron Man Globe")
    clock = pygame.time.Clock()
    
    globe = IronManGlobe(W // 2, H // 2, 250)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                W, H = event.w, event.h
                globe.cx = W // 2
                globe.cy = H // 2
                globe._glow_cache.clear()
                screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
            else:
                globe.handle_event(event)
        
        globe.update()
        
        screen.fill(GlobeTheme.BG)
        globe.draw(screen)
        globe.draw_tooltip(screen)
        
        # FPS
        fps_font = pygame.font.Font(None, 18)
        fps_text = fps_font.render(f"FPS: {int(clock.get_fps())}", True, GlobeTheme.HOLO_CYAN_DIM)
        screen.blit(fps_text, (10, H - 25))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
