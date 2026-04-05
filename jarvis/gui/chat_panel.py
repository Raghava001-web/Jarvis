"""
Chat Panel - Expandable chat history panel for JARVIS
Slides out from the globe to show conversation history
"""

import pygame
import threading
import time
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class MessageRole(Enum):
    USER = "user"
    JARVIS = "jarvis"


@dataclass
class ChatMessage:
    role: MessageRole
    content: str
    timestamp: str


class ChatColors:
    """Color scheme for chat panel"""
    BACKGROUND = (10, 15, 25, 230)     # Dark blue-ish with alpha
    USER_BG = (0, 60, 120, 200)        # Blue bubble
    JARVIS_BG = (0, 100, 80, 200)      # Teal bubble
    TEXT = (220, 240, 255)              # Light cyan
    BORDER = (0, 200, 255)              # Cyan
    TIMESTAMP = (100, 150, 180)         # Subtle blue


class ChatPanel:
    """Expandable chat panel that shows conversation history"""
    
    def __init__(self, screen_width: int, screen_height: int):
        print("[CHAT PANEL] Initializing Chat Panel...")
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Panel dimensions
        self.panel_width = 350
        self.panel_height = screen_height - 40
        self.panel_x = screen_width  # Start off-screen
        self.target_x = screen_width - self.panel_width - 20  # Open position
        
        # Animation
        self.is_open = False
        self.animation_speed = 20
        
        # Messages
        self.messages: List[ChatMessage] = []
        self.scroll_offset = 0
        self.max_visible_messages = 20
        
        # Input
        self.input_text = ""
        self.input_active = False
        
        # Font (will be set during render)
        self.font = None
        self.small_font = None
        
        print("[CHAT PANEL] Chat Panel Ready")
    
    def toggle(self):
        """Toggle panel open/closed"""
        self.is_open = not self.is_open
    
    def open(self):
        """Open the panel"""
        self.is_open = True
    
    def close(self):
        """Close the panel"""
        self.is_open = False
    
    def add_message(self, role: str, content: str):
        """Add a message to the chat"""
        msg_role = MessageRole.JARVIS if role.lower() == "jarvis" else MessageRole.USER
        timestamp = time.strftime("%H:%M")
        
        self.messages.append(ChatMessage(msg_role, content, timestamp))
        
        # Auto-scroll to bottom
        if len(self.messages) > self.max_visible_messages:
            self.scroll_offset = len(self.messages) - self.max_visible_messages
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within a width"""
        if not self.font:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    def _draw_message_bubble(self, screen, message: ChatMessage, y: int) -> int:
        """Draw a message bubble and return its height"""
        is_user = message.role == MessageRole.USER
        
        # Bubble parameters
        bubble_width = self.panel_width - 60
        padding = 10
        max_text_width = bubble_width - padding * 2
        
        # Wrap text
        lines = self._wrap_text(message.content, max_text_width)
        line_height = 20
        bubble_height = len(lines) * line_height + padding * 2 + 15  # Extra for timestamp
        
        # Position (user on right, JARVIS on left)
        if is_user:
            bubble_x = self.panel_x + self.panel_width - bubble_width - 20
            bg_color = ChatColors.USER_BG
        else:
            bubble_x = self.panel_x + 20
            bg_color = ChatColors.JARVIS_BG
        
        # Skip if out of view
        if y + bubble_height < 50 or y > self.panel_height - 60:
            return bubble_height + 10
        
        # Draw bubble with alpha
        bubble_surface = pygame.Surface((bubble_width, bubble_height), pygame.SRCALPHA)
        pygame.draw.rect(bubble_surface, bg_color, 
                        (0, 0, bubble_width, bubble_height), 
                        border_radius=10)
        
        # Border glow
        pygame.draw.rect(bubble_surface, (*ChatColors.BORDER, 100),
                        (0, 0, bubble_width, bubble_height),
                        width=1, border_radius=10)
        
        screen.blit(bubble_surface, (bubble_x, y))
        
        # Draw text
        text_y = y + padding
        for line in lines:
            text_surf = self.font.render(line, True, ChatColors.TEXT)
            screen.blit(text_surf, (bubble_x + padding, text_y))
            text_y += line_height
        
        # Draw timestamp
        timestamp_surf = self.small_font.render(message.timestamp, True, ChatColors.TIMESTAMP)
        screen.blit(timestamp_surf, (bubble_x + padding, text_y))
        
        return bubble_height + 10  # Return height + spacing
    
    def render(self, screen):
        """Render the chat panel"""
        # Initialize fonts if needed
        if not self.font:
            self.font = pygame.font.Font(None, 22)
            self.small_font = pygame.font.Font(None, 16)
        
        # Animate panel position
        if self.is_open:
            if self.panel_x > self.target_x:
                self.panel_x -= self.animation_speed
                self.panel_x = max(self.panel_x, self.target_x)
        else:
            if self.panel_x < self.screen_width:
                self.panel_x += self.animation_speed
                self.panel_x = min(self.panel_x, self.screen_width)
        
        # Don't render if fully closed
        if self.panel_x >= self.screen_width:
            return
        
        # Panel background
        panel_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel_surface.fill(ChatColors.BACKGROUND)
        
        # Border
        pygame.draw.rect(panel_surface, ChatColors.BORDER,
                        (0, 0, self.panel_width, self.panel_height),
                        width=2, border_radius=15)
        
        screen.blit(panel_surface, (self.panel_x, 20))
        
        # Header
        header_text = "CONVERSATION LOG"
        header_surf = self.font.render(header_text, True, ChatColors.BORDER)
        screen.blit(header_surf, (self.panel_x + 20, 35))
        
        # Draw separator line
        pygame.draw.line(screen, ChatColors.BORDER,
                        (self.panel_x + 20, 55),
                        (self.panel_x + self.panel_width - 20, 55), 1)
        
        # Draw messages
        y = 65 - self.scroll_offset * 80
        
        for msg in self.messages:
            height = self._draw_message_bubble(screen, msg, y)
            y += height
    
    def handle_scroll(self, direction: int):
        """Handle scroll (direction: 1 = up, -1 = down)"""
        self.scroll_offset = max(0, self.scroll_offset - direction)
        max_scroll = max(0, len(self.messages) - self.max_visible_messages)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle click event, return True if handled"""
        # Check if click is on panel toggle area
        if x >= self.panel_x - 30 and x <= self.panel_x and y >= self.panel_height // 2 - 50 and y <= self.panel_height // 2 + 50:
            self.toggle()
            return True
        
        # Check if click is on input box
        input_box_y = self.panel_height - 30
        if self.is_open and x >= self.panel_x + 20 and x <= self.panel_x + self.panel_width - 60:
            if y >= input_box_y and y <= input_box_y + 40:
                self.input_active = True
                return True
        
        self.input_active = False
        return False


class ChatPanelWithInput(ChatPanel):
    """Extended chat panel with text input functionality"""
    
    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height)
        
        # Text input
        self.input_text = ""
        self.input_active = False
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        self.max_input_length = 200
        
        # Callbacks
        self.on_submit = None  # Called when user presses Enter
        
        print("[CHAT PANEL] Text input enabled")
    
    def set_submit_callback(self, callback):
        """Set callback for when text is submitted"""
        self.on_submit = callback
    
    def handle_key(self, event) -> bool:
        """Handle keyboard input, return True if handled"""
        if not self.input_active or not self.is_open:
            return False
        
        if event.type != pygame.KEYDOWN:
            return False
        
        if event.key == pygame.K_RETURN:
            # Submit
            if self.input_text.strip():
                if self.on_submit:
                    self.on_submit(self.input_text.strip())
                self.add_message("user", self.input_text.strip())
                self.input_text = ""
            return True
        
        elif event.key == pygame.K_BACKSPACE:
            # Delete character
            self.input_text = self.input_text[:-1]
            return True
        
        elif event.key == pygame.K_ESCAPE:
            # Deactivate input
            self.input_active = False
            return True
        
        elif event.unicode and len(self.input_text) < self.max_input_length:
            # Add character
            self.input_text += event.unicode
            return True
        
        return False
    
    def _draw_input_box(self, screen):
        """Draw the text input box at bottom of panel"""
        if not self.is_open:
            return
        
        # Input box dimensions
        box_x = int(self.panel_x) + 15
        box_y = self.panel_height - 25
        box_width = self.panel_width - 70
        box_height = 35
        
        # Background
        input_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        
        if self.input_active:
            bg_color = (30, 50, 70, 220)
            border_color = ChatColors.BORDER
        else:
            bg_color = (20, 30, 45, 200)
            border_color = ChatColors.TIMESTAMP
        
        pygame.draw.rect(input_surface, bg_color, (0, 0, box_width, box_height), border_radius=8)
        pygame.draw.rect(input_surface, (*border_color, 150), (0, 0, box_width, box_height), width=1, border_radius=8)
        
        screen.blit(input_surface, (box_x, box_y))
        
        # Text
        if self.input_text:
            # Truncate if too long for display
            display_text = self.input_text
            max_text_width = box_width - 15
            
            while self.font and self.font.size(display_text)[0] > max_text_width:
                display_text = display_text[1:]
            
            text_surf = self.font.render(display_text, True, ChatColors.TEXT)
            screen.blit(text_surf, (box_x + 10, box_y + 9))
        else:
            # Placeholder
            placeholder = "Type a message..."
            placeholder_surf = self.font.render(placeholder, True, ChatColors.TIMESTAMP)
            screen.blit(placeholder_surf, (box_x + 10, box_y + 9))
        
        # Cursor
        if self.input_active:
            self.cursor_blink_timer += 1
            if self.cursor_blink_timer % 30 < 15:  # Blink every 0.5 seconds at 60fps
                cursor_x = box_x + 10
                if self.input_text and self.font:
                    cursor_x += self.font.size(self.input_text)[0]
                pygame.draw.line(screen, ChatColors.TEXT, 
                               (cursor_x, box_y + 8), 
                               (cursor_x, box_y + 27), 2)
        
        # Send button
        send_x = int(self.panel_x) + self.panel_width - 50
        send_surface = pygame.Surface((35, 35), pygame.SRCALPHA)
        pygame.draw.rect(send_surface, (*ChatColors.BORDER, 150), (0, 0, 35, 35), border_radius=8)
        screen.blit(send_surface, (send_x, box_y))
        
        # Send arrow
        arrow_color = ChatColors.TEXT if self.input_text else ChatColors.TIMESTAMP
        pygame.draw.polygon(screen, arrow_color, [
            (send_x + 10, box_y + 17),
            (send_x + 25, box_y + 17),
            (send_x + 17, box_y + 8)
        ])
    
    def render(self, screen):
        """Render chat panel with input box"""
        super().render(screen)
        self._draw_input_box(screen)
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle click event"""
        # Check send button click
        if self.is_open:
            send_x = int(self.panel_x) + self.panel_width - 50
            send_y = self.panel_height - 25
            
            if send_x <= x <= send_x + 35 and send_y <= y <= send_y + 35:
                if self.input_text.strip():
                    if self.on_submit:
                        self.on_submit(self.input_text.strip())
                    self.add_message("user", self.input_text.strip())
                    self.input_text = ""
                return True
        
        # Check input box click
        if self.is_open:
            input_x = int(self.panel_x) + 15
            input_y = self.panel_height - 25
            input_width = self.panel_width - 70
            
            if input_x <= x <= input_x + input_width and input_y <= y <= input_y + 35:
                self.input_active = True
                return True
            else:
                self.input_active = False
        
        return super().handle_click(x, y)
