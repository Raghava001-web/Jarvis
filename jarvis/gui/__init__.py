"""
GUI Package for JARVIS
Contains holographic interface components
"""

from .earth_globe import HolographicGlobe, JARVISState
from .globe_controller import GlobeController
from .chat_panel import ChatPanel, ChatPanelWithInput
from .advanced_hud import HUD
from .waveform_visualizer import AudioWaveformVisualizer, CircularWaveform
from .integrated_hud import IntegratedJARVISHUD

# Backwards compatibility alias
InteractiveGlobeHUD = HUD

__all__ = [
    'HolographicGlobe',
    'JARVISState',
    'GlobeController', 
    'ChatPanel',
    'ChatPanelWithInput',
    'HUD',
    'InteractiveGlobeHUD',  # Alias for backwards compatibility
    'AudioWaveformVisualizer',
    'CircularWaveform',
    'IntegratedJARVISHUD'
]

