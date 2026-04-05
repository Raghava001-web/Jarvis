"""
Audio Waveform Visualizer - Real-time voice waveform display
Shows audio input levels and animated waveforms during speech
"""

import pygame
import math
import random
import threading
import queue
from typing import List, Optional
from collections import deque


class WaveformColors:
    """Waveform color scheme"""
    IDLE = (0, 150, 200)
    LISTENING = (0, 255, 150)
    SPEAKING = (0, 200, 255)
    PROCESSING = (255, 180, 0)
    BACKGROUND = (0, 0, 0, 0)


class AudioWaveformVisualizer:
    """Real-time audio waveform visualization"""
    
    def __init__(self, width: int = 400, height: int = 100):
        print("[WAVEFORM] Initializing Waveform Visualizer...")
        
        self.width = width
        self.height = height
        self.center_y = height // 2
        
        # Waveform data
        self.samples = deque(maxlen=100)
        self.target_samples = deque(maxlen=100)
        
        # Fill with zeros
        for _ in range(100):
            self.samples.append(0)
            self.target_samples.append(0)
        
        # Animation
        self.frame = 0
        self.smoothing = 0.3
        
        # State
        self.is_listening = False
        self.is_speaking = False
        self.is_processing = False
        
        # Audio level
        self.current_level = 0
        self.target_level = 0
        
        print("[WAVEFORM] Visualizer Ready")
    
    def set_audio_level(self, level: float):
        """Set current audio input level (0.0 to 1.0)"""
        self.target_level = max(0, min(1, level))
    
    def set_listening(self, listening: bool):
        """Set listening state"""
        self.is_listening = listening
        if listening:
            self.is_speaking = False
            self.is_processing = False
    
    def set_speaking(self, speaking: bool):
        """Set speaking state"""
        self.is_speaking = speaking
        if speaking:
            self.is_listening = False
            self.is_processing = False
    
    def set_processing(self, processing: bool):
        """Set processing state"""
        self.is_processing = processing
        if processing:
            self.is_listening = False
            self.is_speaking = False
    
    def _generate_waveform(self):
        """Generate animated waveform based on state"""
        if self.is_listening:
            # Responsive waveform based on audio level
            for i in range(len(self.target_samples)):
                freq = 0.15 + self.current_level * 0.3
                amplitude = 20 + self.current_level * 30
                noise = random.uniform(-5, 5) * self.current_level
                
                value = math.sin((i + self.frame) * freq) * amplitude + noise
                self.target_samples[i] = value
        
        elif self.is_speaking:
            # Smooth speaking waveform
            for i in range(len(self.target_samples)):
                freq = 0.1 + (i % 3) * 0.05
                amplitude = 15 + math.sin(self.frame * 0.05) * 10
                
                value = math.sin((i + self.frame * 0.5) * freq) * amplitude
                value += math.sin((i + self.frame * 0.3) * 0.2) * 8
                self.target_samples[i] = value
        
        elif self.is_processing:
            # Pulsing processing effect
            for i in range(len(self.target_samples)):
                pulse = math.sin(self.frame * 0.1) * 0.5 + 0.5
                amplitude = 10 + pulse * 20
                
                value = math.sin((i + self.frame * 0.2) * 0.3) * amplitude
                self.target_samples[i] = value
        
        else:
            # Idle - gentle sine wave
            for i in range(len(self.target_samples)):
                value = math.sin((i + self.frame * 0.3) * 0.1) * 8
                self.target_samples[i] = value
    
    def update(self):
        """Update waveform animation"""
        self.frame += 1
        
        # Smooth audio level
        self.current_level += (self.target_level - self.current_level) * 0.2
        
        # Generate new waveform
        self._generate_waveform()
        
        # Smooth toward target
        for i in range(len(self.samples)):
            diff = self.target_samples[i] - self.samples[i]
            self.samples[i] += diff * self.smoothing
    
    def render(self, screen, x: int, y: int):
        """Render the waveform at position"""
        # Determine color based on state
        if self.is_listening:
            color = WaveformColors.LISTENING
        elif self.is_speaking:
            color = WaveformColors.SPEAKING
        elif self.is_processing:
            color = WaveformColors.PROCESSING
        else:
            color = WaveformColors.IDLE
        
        # Draw center line
        pygame.draw.line(screen, (30, 50, 70), 
                        (x, y + self.center_y), 
                        (x + self.width, y + self.center_y), 1)
        
        # Draw waveform
        points_top = []
        points_bottom = []
        
        sample_width = self.width / len(self.samples)
        
        for i, sample in enumerate(self.samples):
            px = x + i * sample_width
            
            # Mirror effect
            points_top.append((px, y + self.center_y - sample))
            points_bottom.append((px, y + self.center_y + sample))
        
        # Draw filled polygon for glow effect
        if len(points_top) > 2:
            all_points = points_top + list(reversed(points_bottom))
            
            # Glow surface
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            
            # Offset points for glow surface
            glow_points = [(p[0] - x + 10, p[1] - y + 10) for p in all_points]
            
            if len(glow_points) > 2:
                pygame.draw.polygon(glow_surf, (*color, 30), glow_points)
                screen.blit(glow_surf, (x - 10, y - 10))
            
            # Draw the lines
            pygame.draw.lines(screen, color, False, points_top, 2)
            pygame.draw.lines(screen, color, False, points_bottom, 2)
        
        # Draw audio level bars on sides
        level_height = int(self.height * 0.8 * self.current_level)
        bar_width = 6
        
        # Left bar
        pygame.draw.rect(screen, (30, 50, 70), 
                        (x - 15, y + self.height // 2 - self.height * 0.4, 
                         bar_width, self.height * 0.8))
        pygame.draw.rect(screen, color,
                        (x - 15, y + self.height // 2 + self.height * 0.4 - level_height,
                         bar_width, level_height))
        
        # Right bar
        pygame.draw.rect(screen, (30, 50, 70),
                        (x + self.width + 9, y + self.height // 2 - self.height * 0.4,
                         bar_width, self.height * 0.8))
        pygame.draw.rect(screen, color,
                        (x + self.width + 9, y + self.height // 2 + self.height * 0.4 - level_height,
                         bar_width, level_height))


class CircularWaveform:
    """Circular waveform that pulses around the globe"""
    
    def __init__(self, center_x: int, center_y: int, radius: int):
        print("[WAVEFORM] Initializing Circular Waveform...")
        
        self.cx = center_x
        self.cy = center_y
        self.radius = radius
        
        # Samples around the circle
        self.num_samples = 72
        self.samples = [0] * self.num_samples
        self.target_samples = [0] * self.num_samples
        
        self.frame = 0
        self.audio_level = 0
        
        self.is_active = False
    
    def set_audio_level(self, level: float):
        self.audio_level = max(0, min(1, level))
    
    def set_active(self, active: bool):
        self.is_active = active
    
    def update(self):
        self.frame += 1
        
        if self.is_active:
            # Generate wave pattern
            for i in range(self.num_samples):
                angle = i / self.num_samples * 2 * math.pi
                
                # Multiple sine waves
                wave1 = math.sin(angle * 3 + self.frame * 0.1) * 10
                wave2 = math.sin(angle * 5 - self.frame * 0.15) * 5
                wave3 = math.sin(angle * 8 + self.frame * 0.2) * 3
                
                # Audio reactivity
                audio_boost = self.audio_level * 20 * math.sin(angle * 2 + self.frame * 0.05)
                
                self.target_samples[i] = wave1 + wave2 + wave3 + audio_boost
        else:
            # Gentle idle wave
            for i in range(self.num_samples):
                angle = i / self.num_samples * 2 * math.pi
                self.target_samples[i] = math.sin(angle * 2 + self.frame * 0.05) * 5
        
        # Smooth
        for i in range(self.num_samples):
            self.samples[i] += (self.target_samples[i] - self.samples[i]) * 0.3
    
    def render(self, screen):
        """Render circular waveform around globe"""
        color = (0, 255, 150) if self.is_active else (0, 150, 200)
        
        points = []
        for i in range(self.num_samples):
            angle = i / self.num_samples * 2 * math.pi - math.pi / 2
            r = self.radius + self.samples[i]
            
            px = self.cx + r * math.cos(angle)
            py = self.cy + r * math.sin(angle)
            points.append((px, py))
        
        # Draw filled area with transparency
        if len(points) > 2:
            glow_surf = pygame.Surface((self.radius * 3, self.radius * 3), pygame.SRCALPHA)
            
            # Offset points for surface
            offset_points = [(p[0] - self.cx + self.radius * 1.5, 
                             p[1] - self.cy + self.radius * 1.5) for p in points]
            
            pygame.draw.polygon(glow_surf, (*color, 20), offset_points)
            screen.blit(glow_surf, (self.cx - self.radius * 1.5, self.cy - self.radius * 1.5))
            
            # Draw line
            pygame.draw.polygon(screen, color, points, 2)


class VoiceActivityIndicator:
    """Shows current voice activity with visual feedback"""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        
        # Bars
        self.num_bars = 5
        self.bar_heights = [0] * self.num_bars
        self.target_heights = [0] * self.num_bars
        
        self.is_active = False
        self.frame = 0
    
    def set_active(self, active: bool):
        self.is_active = active
    
    def update(self):
        self.frame += 1
        
        if self.is_active:
            # Random heights for activity
            for i in range(self.num_bars):
                self.target_heights[i] = random.uniform(10, 40)
        else:
            # Minimal heights
            for i in range(self.num_bars):
                self.target_heights[i] = 3 + math.sin(self.frame * 0.1 + i) * 2
        
        # Smooth
        for i in range(self.num_bars):
            self.bar_heights[i] += (self.target_heights[i] - self.bar_heights[i]) * 0.3
    
    def render(self, screen):
        bar_width = 6
        gap = 4
        
        color = (0, 255, 150) if self.is_active else (0, 150, 200)
        
        for i in range(self.num_bars):
            bx = self.x + i * (bar_width + gap)
            h = int(self.bar_heights[i])
            
            pygame.draw.rect(screen, color, (bx, self.y - h, bar_width, h * 2), border_radius=2)
