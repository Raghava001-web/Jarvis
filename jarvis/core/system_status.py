"""
System Status - CPU, Memory, Battery, and Disk information
Provides system health reports
"""

import platform
from typing import Dict, Optional


class SystemStatus:
    """Provides system status information"""
    
    def __init__(self, perception=None):
        print("[STATUS] Initializing System Status...")
        self.perception = perception
        
        # Check for psutil
        self.psutil_available = False
        try:
            import psutil
            self.psutil_available = True
            print("[STATUS] psutil available")
        except ImportError:
            print("[STATUS] psutil not available - limited system info")
        
        print("[STATUS] System Status Ready")
    
    def _get_title(self) -> str:
        """Get user title from perception layer"""
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        """Speak text via perception layer"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[STATUS] {text}")
    
    def get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage"""
        if not self.psutil_available:
            return None
        
        import psutil
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self) -> Optional[Dict]:
        """Get memory usage information"""
        if not self.psutil_available:
            return None
        
        import psutil
        mem = psutil.virtual_memory()
        
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        }
    
    def get_battery_status(self) -> Optional[Dict]:
        """Get battery status (for laptops)"""
        if not self.psutil_available:
            return None
        
        import psutil
        
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": round(battery.percent),
                    "plugged_in": battery.power_plugged,
                    "time_left": self._format_time(battery.secsleft) if battery.secsleft > 0 else None
                }
        except Exception:
            pass
        
        return None
    
    def get_disk_usage(self, path: str = None) -> Optional[Dict]:
        """Get disk usage for a drive"""
        import os
        if path is None:
            path = os.path.abspath(os.sep)
        if not self.psutil_available:
            return None
        
        import psutil
        
        try:
            disk = psutil.disk_usage(path)
            return {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            }
        except Exception:
            return None
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds into human readable time"""
        if seconds < 0:
            return "calculating"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours} hours {minutes} minutes"
        return f"{minutes} minutes"
    
    def report_cpu(self) -> bool:
        """Report CPU usage"""
        title = self._get_title()
        
        cpu = self.get_cpu_usage()
        if cpu is not None:
            if cpu < 30:
                status = "running smoothly"
            elif cpu < 70:
                status = "moderately busy"
            else:
                status = "quite busy"
            
            self._speak(f"CPU usage is at {cpu} percent, {title}. The system is {status}.")
            return True
        
        self._speak(f"I couldn't get CPU information, {title}.")
        return False
    
    def report_memory(self) -> bool:
        """Report memory usage"""
        title = self._get_title()
        
        mem = self.get_memory_usage()
        if mem:
            percent = mem["percent"]
            available = mem["available_gb"]
            
            if percent < 50:
                status = "plenty of memory available"
            elif percent < 80:
                status = "memory usage is moderate"
            else:
                status = "memory is running low"
            
            self._speak(f"Memory usage is at {percent} percent with {available} gigabytes available, {title}. {status.capitalize()}.")
            return True
        
        self._speak(f"I couldn't get memory information, {title}.")
        return False
    
    def report_battery(self) -> bool:
        """Report battery status"""
        title = self._get_title()
        
        battery = self.get_battery_status()
        if battery:
            percent = battery["percent"]
            plugged = battery["plugged_in"]
            time_left = battery.get("time_left")
            
            if plugged:
                self._speak(f"Battery is at {percent} percent and charging, {title}.")
            else:
                time_msg = f" with approximately {time_left} remaining" if time_left else ""
                
                if percent > 50:
                    self._speak(f"Battery is at {percent} percent{time_msg}, {title}. You're good for a while.")
                elif percent > 20:
                    self._speak(f"Battery is at {percent} percent{time_msg}, {title}. You might want to plug in soon.")
                else:
                    self._speak(f"Battery is at {percent} percent{time_msg}, {title}. I recommend plugging in now.")
            
            return True
        
        self._speak(f"I couldn't get battery information, {title}. This might be a desktop system.")
        return False
    
    def report_disk(self, drive: str = None) -> bool:
        """Report disk usage"""
        import os
        if drive is None:
            drive = os.path.abspath(os.sep)
        title = self._get_title()
        
        disk = self.get_disk_usage(drive)
        if disk:
            percent = disk["percent"]
            free = disk["free_gb"]
            
            if percent < 70:
                status = "plenty of space available"
            elif percent < 90:
                status = "space is getting limited"
            else:
                status = "running low on space"
            
            self._speak(f"Drive {drive} is {percent} percent full with {free} gigabytes free, {title}. {status.capitalize()}.")
            return True
        
        self._speak(f"I couldn't get disk information for {drive}, {title}.")
        return False
    
    def full_system_report(self) -> bool:
        """Give a complete system status report"""
        title = self._get_title()
        
        self._speak(f"Here's your system status report, {title}.")
        
        # CPU
        cpu = self.get_cpu_usage()
        if cpu is not None:
            self._speak(f"CPU is at {cpu} percent.")
        
        # Memory
        mem = self.get_memory_usage()
        if mem:
            self._speak(f"Memory usage is {mem['percent']} percent.")
        
        # Battery
        battery = self.get_battery_status()
        if battery:
            status = "charging" if battery["plugged_in"] else "on battery"
            self._speak(f"Battery is at {battery['percent']} percent, {status}.")
        
        # Disk
        disk = self.get_disk_usage()
        if disk:
            self._speak(f"Main drive has {disk['free_gb']} gigabytes free.")
        
        self._speak("That's the current system status.")
        return True
    
    def get_system_info(self) -> Dict:
        """Get general system information"""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
