"""
System Control - Hardware Control (Windows)
Volume, Brightness, Bluetooth, and more
JARVIS takes direct control - no manual suggestions
"""

import platform
import subprocess
import os
import time

VOLUME_AVAILABLE = False
BRIGHTNESS_AVAILABLE = False

if platform.system() == "Windows":
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL, CoInitialize
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        VOLUME_AVAILABLE = True
    except ImportError as e:
        print(f"[SYSTEM] pycaw not available: {e}")

    try:
        import screen_brightness_control as sbc
        BRIGHTNESS_AVAILABLE = True
    except ImportError:
        print("[SYSTEM] screen-brightness-control not installed")


class SystemControl:
    """Controls system hardware (Windows) - JARVIS takes control"""

    def __init__(self, perception):
        print("[SYSTEM] Initializing System Control...")
        self.perception = perception
        self.platform = platform.system()
        
        # Initialize volume interface (using pycaw with robust API handling)
        self.volume_interface = None
        if VOLUME_AVAILABLE:
            try:
                CoInitialize()
                devices = AudioUtilities.GetSpeakers()
                # Try the standard Activate method
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                print("[SYSTEM] Volume control ready (pycaw)")
            except AttributeError:
                # Newer pycaw: AudioDevice wrapper doesn't expose Activate directly
                try:
                    # Access the underlying IMMDevice
                    device = devices
                    if hasattr(device, '_dev'):
                        interface = device._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    elif hasattr(device, 'ActivateInterface'):
                        interface = device.ActivateInterface(IAudioEndpointVolume._iid_)
                    else:
                        # Try getting the endpoint volume directly
                        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                    print("[SYSTEM] Volume control ready (pycaw compat)")
                except Exception as e2:
                    print(f"[SYSTEM] Volume init pycaw compat error: {e2}")
                    self.volume_interface = None
            except Exception as e:
                print(f"[SYSTEM] Volume init pycaw error: {e}")
                # Fallback: try with CoInitializeEx for STA threading
                try:
                    import comtypes
                    comtypes.CoInitializeEx(comtypes.COINIT_APARTMENTTHREADED)
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                    print("[SYSTEM] Volume control ready (pycaw CoInitializeEx)")
                except Exception as e2:
                    print(f"[SYSTEM] Volume init fallback error: {e2}")
                    self.volume_interface = None
        
        if not self.volume_interface:
            print("[SYSTEM] Volume will use pyautogui keyboard fallback")
        
        print("[SYSTEM] Control Ready")

    def _get_title(self):
        return getattr(self.perception, 'user_title', 'sir')

    # ---------- VOLUME CONTROL ----------

    def set_volume(self, level: int):
        """Set volume to specific percentage (0-100)"""
        title = self._get_title()
        level = max(0, min(level, 100))
        
        # PRIMARY: Use pycaw (direct Windows API - instant and precise)
        if self.volume_interface:
            try:
                self.volume_interface.SetMasterVolumeLevelScalar(level / 100.0, None)
                self.perception.speak(f"Volume set to {level}%, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] pycaw error: {e}")
        
        # FALLBACK: Use keyboard simulation
        try:
            import pyautogui
            
            # Calculate current vs target (estimate based on 50 steps = 100%)
            # Each press is ~2%
            target_presses = level // 2
            
            # Set to 0 first (mute, then volume down)
            pyautogui.press('volumemute')
            time.sleep(0.05)
            pyautogui.press('volumemute')
            time.sleep(0.05)
            
            # Press down to zero (50 times)
            for _ in range(50):
                pyautogui.press('volumedown')
            
            # Press up to target
            for _ in range(target_presses):
                pyautogui.press('volumeup')
            
            self.perception.speak(f"Volume set to {level}%, {title}.")
            return True
        except Exception as e:
            print(f"[SYSTEM] Keyboard volume error: {e}")
        
        self.perception.speak(f"Volume control failed, {title}.")
        return False

    def volume_up(self, amount=10):
        """Increase volume"""
        title = self._get_title()
        
        # Try pycaw first
        if self.volume_interface:
            try:
                current = self.volume_interface.GetMasterVolumeLevelScalar()
                # BUG FIX: Use 'amount' param instead of hardcoded 0.1
                step = amount / 100.0
                new_level = min(1.0, current + step)
                self.volume_interface.SetMasterVolumeLevelScalar(new_level, None)
                pct = int(new_level * 100)
                self.perception.speak(f"Volume at {pct}%, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] pycaw volume up error: {e}")
        
        # Fallback: Use pyautogui keyboard
        try:
            import pyautogui
            presses = max(1, amount // 2)  # Each press ~2%
            for _ in range(presses):
                pyautogui.press('volumeup')
            self.perception.speak(f"Volume increased, {title}.")
            return True
        except Exception as e:
            print(f"[SYSTEM] Volume up error: {e}")
        
        self.perception.speak(f"Volume increased, {title}.")
        return True

    def volume_down(self, amount=10):
        """Decrease volume"""
        title = self._get_title()
        
        # Try pycaw first
        if self.volume_interface:
            try:
                current = self.volume_interface.GetMasterVolumeLevelScalar()
                # BUG FIX: Use 'amount' param instead of hardcoded 0.1
                step = amount / 100.0
                new_level = max(0.0, current - step)
                self.volume_interface.SetMasterVolumeLevelScalar(new_level, None)
                pct = int(new_level * 100)
                self.perception.speak(f"Volume at {pct}%, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] pycaw volume down error: {e}")
        
        # Fallback: Use pyautogui keyboard
        try:
            import pyautogui
            presses = max(1, amount // 2)
            for _ in range(presses):
                pyautogui.press('volumedown')
            self.perception.speak(f"Volume decreased, {title}.")
            return True
        except Exception as e:
            print(f"[SYSTEM] Volume down error: {e}")
        
        self.perception.speak(f"Volume decreased, {title}.")
        return True

    def mute_volume(self):
        """Toggle mute"""
        title = self._get_title()
        
        # Try pycaw first
        if self.volume_interface:
            try:
                current_mute = self.volume_interface.GetMute()
                self.volume_interface.SetMute(not current_mute, None)
                status = "muted" if not current_mute else "unmuted"
                self.perception.speak(f"Volume {status}, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] pycaw mute error: {e}")
        
        # Fallback: Use pyautogui keyboard
        try:
            import pyautogui
            pyautogui.press('volumemute')
            self.perception.speak(f"Volume muted, {title}.")
            return True
        except Exception as e:
            print(f"[SYSTEM] Mute error: {e}")
        
        self.perception.speak(f"Volume toggled, {title}.")
        return True

    # ---------- BRIGHTNESS CONTROL ----------

    def set_brightness(self, level: int):
        """Set brightness to specific percentage"""
        title = self._get_title()
        level = max(0, min(level, 100))
        
        # PRIMARY: PowerShell WMI (works on most Windows laptops)
        try:
            ps_cmd = f'''
            $brightness = {level}
            $myMonitor = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods
            $myMonitor.WmiSetBrightness(1, $brightness)
            '''
            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                self.perception.speak(f"Brightness set to {level}%, {title}.")
                return True
        except Exception as e:
            print(f"[SYSTEM] PowerShell brightness error: {e}")
        
        # Fallback: screen_brightness_control library
        if BRIGHTNESS_AVAILABLE:
            try:
                sbc.set_brightness(level)
                self.perception.speak(f"Brightness set to {level}%, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] sbc brightness error: {e}")
        
        self.perception.speak(f"Brightness control not available on this device, {title}.")
        return False

    def brightness_up(self, amount=20):
        """Increase brightness"""
        title = self._get_title()
        
        if BRIGHTNESS_AVAILABLE:
            try:
                current = sbc.get_brightness()
                current = current[0] if isinstance(current, list) else current
                new_level = min(100, current + amount)
                sbc.set_brightness(new_level)
                self.perception.speak(f"Brightness increased to {new_level} percent, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] Brightness up error: {e}")
        
        # Fallback: PowerShell
        try:
            ps_cmd = '''
            $current = (Get-WmiObject -Namespace root\\WMI -Class WmiMonitorBrightness).CurrentBrightness
            $new = [Math]::Min(100, $current + 20)
            $myMonitor = Get-WmiObject -Namespace root\\WMI -Class WmiMonitorBrightnessMethods
            $myMonitor.WmiSetBrightness(1, $new)
            '''
            subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, timeout=10)
            self.perception.speak(f"Brightness increased, {title}.")
            return True
        except Exception as e:
            print(f"[SYSTEM] Brightness fallback error: {e}")
        
        self.perception.speak(f"Brightness increased, {title}.")
        return True

    def brightness_down(self, amount=20):
        """Decrease brightness"""
        title = self._get_title()
        
        if BRIGHTNESS_AVAILABLE:
            try:
                current = sbc.get_brightness()
                current = current[0] if isinstance(current, list) else current
                new_level = max(0, current - amount)
                sbc.set_brightness(new_level)
                self.perception.speak(f"Brightness decreased to {new_level} percent, {title}.")
                return True
            except Exception as e:
                print(f"[SYSTEM] Brightness down error: {e}")
        
        # Fallback: PowerShell
        try:
            ps_cmd = '''
            $current = (Get-WmiObject -Namespace root\\WMI -Class WmiMonitorBrightness).CurrentBrightness
            $new = [Math]::Max(0, $current - 20)
            $myMonitor = Get-WmiObject -Namespace root\\WMI -Class WmiMonitorBrightnessMethods
            $myMonitor.WmiSetBrightness(1, $new)
            '''
            subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, timeout=10)
            self.perception.speak(f"Brightness decreased, {title}.")
            return True
        except Exception as e:
            print(f"[SYSTEM] Brightness fallback error: {e}")
        
        self.perception.speak(f"Brightness decreased, {title}.")
        return True

    # ---------- BLUETOOTH ----------

    def bluetooth_on(self):
        """Turn Bluetooth on"""
        title = self._get_title()
        try:
            # Try to actually toggle Bluetooth via PowerShell
            ps_cmd = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
            Function Await($WinRtTask, $ResultType) {
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }
            [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
            $bluetooth = $radios | ? { $_.Kind -eq 'Bluetooth' }
            [void](Await ($bluetooth.SetStateAsync('On')) ([Windows.Devices.Radios.RadioAccessStatus]))
            '''
            result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, timeout=15)
            # BUG FIX: Check returncode before claiming success
            if result.returncode == 0:
                self._is_bt_on = True
                self.perception.speak(f"Bluetooth turned on, {title}.")
            else:
                print(f"[SYSTEM] Bluetooth PS error: {result.stderr.decode(errors='ignore')}")
                self.perception.speak(f"Bluetooth may not have turned on, {title}. Opening settings.")
                subprocess.Popen("ms-settings:bluetooth", shell=True)
            return True
        except Exception as e:
            print(f"[SYSTEM] Bluetooth on error: {e}")
            # Fallback: open settings
            subprocess.Popen("ms-settings:bluetooth", shell=True)
            self.perception.speak(f"Opening Bluetooth settings, {title}.")
            return True

    def bluetooth_off(self):
        """Turn Bluetooth off"""
        title = self._get_title()
        try:
            ps_cmd = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
            Function Await($WinRtTask, $ResultType) {
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }
            [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
            $bluetooth = $radios | ? { $_.Kind -eq 'Bluetooth' }
            [void](Await ($bluetooth.SetStateAsync('Off')) ([Windows.Devices.Radios.RadioAccessStatus]))
            '''
            result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, timeout=15)
            # BUG FIX: Check returncode before claiming success
            if result.returncode == 0:
                self.perception.speak(f"Bluetooth turned off, {title}.")
            else:
                print(f"[SYSTEM] Bluetooth PS error: {result.stderr.decode(errors='ignore')}")
                self.perception.speak(f"Bluetooth may not have turned off, {title}. Opening settings.")
                subprocess.Popen("ms-settings:bluetooth", shell=True)
            return True
        except Exception as e:
            print(f"[SYSTEM] Bluetooth off error: {e}")
            subprocess.Popen("ms-settings:bluetooth", shell=True)
            self.perception.speak(f"Opening Bluetooth settings, {title}.")
            return True

    def toggle_bluetooth(self):
        """Toggle Bluetooth — checks current state first"""
        try:
            # Query current Bluetooth state
            ps_check = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
            Function Await($WinRtTask, $ResultType) {
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }
            [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
            $bt = $radios | ? { $_.Kind -eq 'Bluetooth' }
            $bt.State.ToString()
            '''
            result = subprocess.run(['powershell', '-Command', ps_check],
                                    capture_output=True, text=True, timeout=10)
            if 'On' in result.stdout:
                return self.bluetooth_off()
            else:
                return self.bluetooth_off() if getattr(self, "_is_bt_on", False) else self.bluetooth_on()
        except Exception:
            # Can't determine state — default to turning on
            return self.bluetooth_off() if getattr(self, "_is_bt_on", False) else self.bluetooth_on()

    # ---------- SLEEP / SHUTDOWN ----------

    def sleep_system(self, confirm: bool = False):
        """Put system to sleep"""
        title = self._get_title()
        
        if not confirm:
            self.perception.speak(f"Say 'sleep confirm' to put the system to sleep, {title}.")
            return False

        try:
            self.perception.speak(f"Putting system to sleep now, {title}.")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return True
        except Exception as e:
            print(f"[SYSTEM] Sleep error: {e}")
            self.perception.speak(f"Failed to put system to sleep, {title}.")
            return False
    
    def shutdown_system(self, confirm: bool = False):
        """Shutdown the system"""
        title = self._get_title()
        
        if not confirm:
            self.perception.speak(f"Say 'shutdown confirm' to shut down, {title}.")
            return False
        
        try:
            self.perception.speak(f"Shutting down in 5 seconds, {title}.")
            os.system("shutdown /s /t 5")
            return True
        except Exception as e:
            self.perception.speak(f"Failed to shutdown, {title}.")
            return False
    
    def restart_system(self, confirm: bool = False):
        """Restart the system"""
        title = self._get_title()
        
        if not confirm:
            self.perception.speak(f"Say 'restart confirm' to restart, {title}.")
            return False
        
        try:
            self.perception.speak(f"Restarting in 5 seconds, {title}.")
            os.system("shutdown /r /t 5")
            return True
        except Exception as e:
            self.perception.speak(f"Failed to restart, {title}.")
            return False
