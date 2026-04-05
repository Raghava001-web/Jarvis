"""
Globe Controller - Connects JARVIS to the Holographic Globe Interface
Bridges the globe visuals with JARVIS state
"""

import threading
import time
from typing import Optional

try:
    from .earth_globe import HolographicGlobe, JARVISState
    GLOBE_AVAILABLE = True
except ImportError:
    try:
        from earth_globe import HolographicGlobe, JARVISState
        GLOBE_AVAILABLE = True
    except ImportError:
        GLOBE_AVAILABLE = False
        print("[GLOBE CTRL] Globe interface not available")


class GlobeController:
    """Controls the holographic globe interface from JARVIS"""
    
    def __init__(self, perception=None, system_status=None):
        print("[GLOBE CTRL] Initializing Globe Controller...")
        self.perception = perception
        self.system_status = system_status
        
        self.globe: Optional[HolographicGlobe] = None
        self.is_running = False
        self.stats_thread = None
        
        if GLOBE_AVAILABLE:
            print("[GLOBE CTRL] Globe interface available")
        else:
            print("[GLOBE CTRL] Globe interface not available")
    
    def start(self):
        """Start the globe interface"""
        if not GLOBE_AVAILABLE:
            print("[GLOBE CTRL] Cannot start - globe not available")
            return False
        
        if self.is_running:
            return True
        
        try:
            self.globe = HolographicGlobe(600, 600)
            self.globe.set_click_callback(self._on_globe_click)
            self.globe.start()
            self.is_running = True
            
            # Start stats updater
            self.stats_thread = threading.Thread(target=self._update_stats_loop, daemon=True)
            self.stats_thread.start()
            
            print("[GLOBE CTRL] Globe interface started")
            return True
        except Exception as e:
            print(f"[GLOBE CTRL] Failed to start: {e}")
            return False
    
    def stop(self):
        """Stop the globe interface"""
        self.is_running = False
        if self.globe:
            self.globe.stop()
            self.globe = None
        print("[GLOBE CTRL] Globe interface stopped")
    
    def _on_globe_click(self):
        """Handle click on the globe"""
        print("[GLOBE CTRL] Globe clicked - activating listening mode")
        
        if self.perception:
            # Toggle listening
            self.set_state("listening")
    
    def _update_stats_loop(self):
        """Background thread to update system stats on globe"""
        while self.is_running and self.globe:
            try:
                if self.system_status:
                    cpu = self.system_status.get_cpu_usage()
                    mem = self.system_status.get_memory_usage()
                    bat = self.system_status.get_battery_status()
                    
                    self.globe.update_system_stats(
                        cpu=cpu if cpu else 0,
                        memory=mem.get("percent", 0) if mem else 0,
                        battery=bat.get("percent", 100) if bat else 100
                    )
            except Exception as e:
                pass
            
            time.sleep(2)  # Update every 2 seconds
    
    def set_state(self, state: str):
        """Set the globe visual state"""
        if not self.globe:
            return
        
        state_map = {
            "idle": JARVISState.IDLE,
            "listening": JARVISState.LISTENING,
            "processing": JARVISState.PROCESSING,
            "speaking": JARVISState.SPEAKING,
            "news": JARVISState.NEWS,
            "error": JARVISState.ERROR,
        }
        
        jarvis_state = state_map.get(state.lower(), JARVISState.IDLE)
        self.globe.set_state(jarvis_state)
    
    def point_to_country(self, country: str):
        """Point the globe to a specific country (for news)"""
        if self.globe:
            self.globe.point_to_country(country)
    
    def clear_pointer(self):
        """Clear the country pointer"""
        if self.globe:
            self.globe.clear_pointer()
    
    def is_available(self) -> bool:
        """Check if globe interface is available"""
        return GLOBE_AVAILABLE
