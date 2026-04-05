"""
Settings Panel GUI - Visual settings interface for JARVIS
Provides a user-friendly interface for configuring JARVIS
"""

import pygame
import threading
from typing import Dict, Callable, Optional
from dataclasses import dataclass


class SettingsColors:
    """Color scheme for settings panel"""
    BACKGROUND = (15, 20, 35, 240)
    PANEL_BG = (25, 35, 55, 220)
    PRIMARY = (0, 200, 255)       # Cyan
    SECONDARY = (0, 150, 200)     # Darker cyan
    TEXT = (220, 240, 255)        # Light
    TEXT_DIM = (100, 140, 170)    # Dimmed
    ACCENT = (0, 255, 150)        # Green
    WARNING = (255, 200, 50)      # Yellow
    TOGGLE_ON = (0, 255, 150)     # Green
    TOGGLE_OFF = (100, 100, 120)  # Gray
    SLIDER_BG = (40, 50, 70)
    SLIDER_FILL = (0, 200, 255)


@dataclass
class SettingsItem:
    """A single settings item"""
    key: str
    label: str
    type: str  # "toggle", "slider", "choice"
    value: any
    min_val: float = 0
    max_val: float = 100
    choices: list = None


class SettingsPanel:
    """Visual settings panel for JARVIS configuration"""
    
    def __init__(self, width: int = 400, height: int = 600):
        print("[SETTINGS GUI] Initializing Settings Panel...")
        
        self.width = width
        self.height = height
        
        # Animation
        self.is_open = False
        self.panel_x = -width  # Start off-screen (left)
        self.target_x = 20     # Open position
        self.animation_speed = 25
        
        # Settings items
        self.categories = {
            "Voice": [
                SettingsItem("speech_rate", "Speech Speed", "slider", 175, 100, 250),
                SettingsItem("speech_volume", "Volume", "slider", 90, 0, 100),
                SettingsItem("voice_assistant", "Voice", "choice", "jarvis", choices=["JARVIS", "FRIDAY"]),
            ],
            "Wellness": [
                SettingsItem("wellness_enabled", "Wellness Reminders", "toggle", True),
                SettingsItem("water_reminder", "Water Reminders", "slider", 30, 10, 120),
                SettingsItem("break_reminder", "Break Reminders", "slider", 45, 15, 120),
                SettingsItem("eye_care", "Eye Care (20-20-20)", "toggle", True),
            ],
            "Features": [
                SettingsItem("emotion_detection", "Emotion Detection", "toggle", True),
                SettingsItem("proactive", "Proactive Suggestions", "toggle", True),
                SettingsItem("sound_effects", "Sound Effects", "toggle", True),
                SettingsItem("save_history", "Save Chat History", "toggle", True),
            ],
            "Interface": [
                SettingsItem("globe_enabled", "Holographic Globe", "toggle", True),
                SettingsItem("always_on_top", "Always on Top", "toggle", True),
                SettingsItem("startup_greeting", "Startup Greeting", "toggle", True),
            ],
        }
        
        # Current category
        self.current_category = "Voice"
        self.category_list = list(self.categories.keys())
        
        # Fonts (initialized on first render)
        self.font = None
        self.small_font = None
        self.title_font = None
        
        # Callbacks
        self.on_setting_changed: Optional[Callable] = None
        
        # Scroll
        self.scroll_offset = 0
        
        # Hover tracking
        self.hovered_item = None
        
        print("[SETTINGS GUI] Settings Panel Ready")
    
    def toggle(self):
        """Toggle panel open/closed"""
        self.is_open = not self.is_open
    
    def open(self):
        self.is_open = True
    
    def close(self):
        self.is_open = False
    
    def _init_fonts(self):
        """Initialize fonts if not already done"""
        if not self.font:
            self.font = pygame.font.Font(None, 22)
            self.small_font = pygame.font.Font(None, 18)
            self.title_font = pygame.font.Font(None, 28)
    
    def _draw_toggle(self, screen, x: int, y: int, value: bool, hovered: bool) -> pygame.Rect:
        """Draw a toggle switch"""
        width = 50
        height = 24
        radius = height // 2
        
        # Background
        bg_color = SettingsColors.TOGGLE_ON if value else SettingsColors.TOGGLE_OFF
        if hovered:
            bg_color = tuple(min(c + 30, 255) for c in bg_color)
        
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, bg_color, rect, border_radius=radius)
        
        # Toggle circle
        circle_x = x + width - radius - 2 if value else x + radius + 2
        pygame.draw.circle(screen, SettingsColors.TEXT, (circle_x, y + radius), radius - 4)
        
        return rect
    
    def _draw_slider(self, screen, x: int, y: int, value: float, 
                     min_val: float, max_val: float, width: int = 180) -> pygame.Rect:
        """Draw a slider control"""
        height = 8
        
        # Background track
        track_rect = pygame.Rect(x, y + 8, width, height)
        pygame.draw.rect(screen, SettingsColors.SLIDER_BG, track_rect, border_radius=4)
        
        # Fill based on value
        fill_pct = (value - min_val) / (max_val - min_val)
        fill_width = int(width * fill_pct)
        fill_rect = pygame.Rect(x, y + 8, fill_width, height)
        pygame.draw.rect(screen, SettingsColors.SLIDER_FILL, fill_rect, border_radius=4)
        
        # Handle
        handle_x = x + fill_width
        pygame.draw.circle(screen, SettingsColors.TEXT, (handle_x, y + 12), 8)
        
        # Value text
        value_text = self.small_font.render(str(int(value)), True, SettingsColors.TEXT)
        screen.blit(value_text, (x + width + 10, y + 5))
        
        return track_rect
    
    def _draw_choice(self, screen, x: int, y: int, value: str, choices: list) -> pygame.Rect:
        """Draw a choice selector"""
        total_width = 0
        rects = []
        
        for choice in choices:
            is_selected = choice.lower() == value.lower()
            
            # Button background
            text_surf = self.font.render(choice, True, SettingsColors.TEXT)
            btn_width = text_surf.get_width() + 20
            btn_height = 28
            
            btn_rect = pygame.Rect(x + total_width, y, btn_width, btn_height)
            
            if is_selected:
                pygame.draw.rect(screen, SettingsColors.PRIMARY, btn_rect, border_radius=5)
            else:
                pygame.draw.rect(screen, SettingsColors.SLIDER_BG, btn_rect, border_radius=5)
                pygame.draw.rect(screen, SettingsColors.SECONDARY, btn_rect, width=1, border_radius=5)
            
            screen.blit(text_surf, (x + total_width + 10, y + 5))
            
            rects.append((btn_rect, choice))
            total_width += btn_width + 10
        
        return rects
    
    def _draw_category_tabs(self, screen, x: int, y: int):
        """Draw category tabs at top"""
        tab_x = x + 10
        
        for category in self.category_list:
            is_selected = category == self.current_category
            
            text_surf = self.font.render(category, True, 
                                         SettingsColors.PRIMARY if is_selected else SettingsColors.TEXT_DIM)
            
            # Underline if selected
            if is_selected:
                underline_rect = pygame.Rect(tab_x, y + 22, text_surf.get_width(), 2)
                pygame.draw.rect(screen, SettingsColors.PRIMARY, underline_rect)
            
            screen.blit(text_surf, (tab_x, y))
            tab_x += text_surf.get_width() + 20
    
    def render(self, screen):
        """Render the settings panel"""
        self._init_fonts()
        
        # Animate panel position
        if self.is_open:
            if self.panel_x < self.target_x:
                self.panel_x += self.animation_speed
                self.panel_x = min(self.panel_x, self.target_x)
        else:
            if self.panel_x > -self.width:
                self.panel_x -= self.animation_speed
                self.panel_x = max(self.panel_x, -self.width)
        
        # Don't render if fully closed
        if self.panel_x <= -self.width:
            return
        
        # Panel background
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        panel_surface.fill(SettingsColors.BACKGROUND)
        pygame.draw.rect(panel_surface, SettingsColors.PRIMARY, 
                        (0, 0, self.width, self.height), width=2, border_radius=10)
        
        screen.blit(panel_surface, (self.panel_x, 20))
        
        # Title
        title_surf = self.title_font.render("SETTINGS", True, SettingsColors.PRIMARY)
        screen.blit(title_surf, (self.panel_x + 20, 35))
        
        # Close button
        close_surf = self.font.render("✕", True, SettingsColors.TEXT_DIM)
        screen.blit(close_surf, (self.panel_x + self.width - 35, 35))
        
        # Category tabs
        self._draw_category_tabs(screen, int(self.panel_x), 70)
        
        # Separator
        pygame.draw.line(screen, SettingsColors.SECONDARY,
                        (self.panel_x + 20, 100),
                        (self.panel_x + self.width - 20, 100), 1)
        
        # Settings items
        items = self.categories.get(self.current_category, [])
        y = 120
        
        for item in items:
            # Label
            label_surf = self.font.render(item.label, True, SettingsColors.TEXT)
            screen.blit(label_surf, (self.panel_x + 20, y))
            
            # Control based on type
            control_x = self.panel_x + 20
            control_y = y + 25
            
            if item.type == "toggle":
                self._draw_toggle(screen, int(control_x), control_y, item.value, False)
            elif item.type == "slider":
                self._draw_slider(screen, int(control_x), control_y, 
                                 item.value, item.min_val, item.max_val)
            elif item.type == "choice":
                self._draw_choice(screen, int(control_x), control_y, 
                                 item.value, item.choices or [])
            
            y += 70
        
        # Reset button at bottom
        reset_text = self.font.render("Reset to Defaults", True, SettingsColors.WARNING)
        reset_rect = pygame.Rect(self.panel_x + 20, self.height - 30, 
                                reset_text.get_width() + 20, 30)
        pygame.draw.rect(screen, SettingsColors.SLIDER_BG, reset_rect, border_radius=5)
        screen.blit(reset_text, (self.panel_x + 30, self.height - 25))
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle click event"""
        if not self.is_open:
            return False
        
        # Check if click is inside panel
        if x < self.panel_x or x > self.panel_x + self.width:
            return False
        
        # Close button
        if x > self.panel_x + self.width - 45 and y < 60:
            self.close()
            return True
        
        # Category tabs
        if 65 < y < 95:
            tab_x = self.panel_x + 10
            for category in self.category_list:
                text_width = self.font.size(category)[0]
                if tab_x < x < tab_x + text_width + 20:
                    self.current_category = category
                    return True
                tab_x += text_width + 20
        
        return True
    
    def update_setting(self, key: str, value: any):
        """Update a setting value"""
        for category, items in self.categories.items():
            for item in items:
                if item.key == key:
                    item.value = value
                    if self.on_setting_changed:
                        self.on_setting_changed(key, value)
                    return
