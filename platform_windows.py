"""
platform_windows.py – Windows-spezifische Implementierungen
Reparierte Version – keine Activate-Fehler mehr
"""

import os
import subprocess
import platform
import sys
from datetime import datetime

IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    # Dummy-Funktionen für Nicht-Windows
    def audio_lauter(): pass
    def audio_leiser(): pass
    def audio_mute(): pass
    def audio_get_volume(): return 50
    def fenster_liste(): return ""
    def fenster_schliessen(name): return 0
    def screenshot_machen(path): return path
    def programm_starten(name): pass
    def programm_beenden(name): pass
    def system_ausschalten(): pass
    def system_neustart(): pass
else:
    # Versuche verschiedene Audio-Methoden
    _audio_method = None
    
    # Methode 1: pycaw (falls verfügbar)
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        _volume = cast(interface, POINTER(IAudioEndpointVolume))
        _audio_method = "pycaw"
        print("[Audio] pycaw geladen")
    except Exception as e:
        print(f"[Audio] pycaw nicht verfügbar: {e}")
        _volume = None
    
    # Methode 2: keysend (Fallback via Tastatur)
    try:
        import pyautogui
        _has_pyautogui = True
    except:
        _has_pyautogui = False
    
    def audio_lauter():
        """Lautstärke erhöhen"""
        global _audio_method, _volume
        try:
            if _audio_method == "pycaw" and _volume:
                current = _volume.GetMasterVolumeLevelScalar()
                new_vol = min(1.0, current + 0.05)
                _volume.SetMasterVolumeLevelScalar(new_vol, None)
                return True
        except:
            pass
        
        # Fallback: Tastatur-Shortcut
        if _has_pyautogui:
            pyautogui.press('volumeup', presses=2)
            return True
        return False
    
    def audio_leiser():
        """Lautstärke verringern"""
        global _audio_method, _volume
        try:
            if _audio_method == "pycaw" and _volume:
                current = _volume.GetMasterVolumeLevelScalar()
                new_vol = max(0.0, current - 0.05)
                _volume.SetMasterVolumeLevelScalar(new_vol, None)
                return True
        except:
            pass
        
        if _has_pyautogui:
            pyautogui.press('volumedown', presses=2)
            return True
        return False
    
    def audio_mute():
        """Stummschaltung umschalten"""
        global _audio_method, _volume
        try:
            if _audio_method == "pycaw" and _volume:
                current = _volume.GetMute()
                _volume.SetMute(not current, None)
                return True
        except:
            pass
        return False
    
    def audio_get_volume():
        """Aktuelle Lautstärke in Prozent"""
        try:
            if _audio_method == "pycaw" and _volume:
                return int(_volume.GetMasterVolumeLevelScalar() * 100)
        except:
            pass
        return 50
    
    # Fensterverwaltung (vereinfacht, robust)
    def fenster_liste() -> str:
        """Liste offener Fenster"""
        try:
            import pygetwindow as gw
            windows = gw.getAllWindows()
            fenster = [w.title for w in windows if w.title and w.title.strip()]
            if not fenster:
                return "Keine geöffneten Fenster gefunden."
            # Zeige nur erste 15 Fenster
            result = "\n".join(f"• {title[:50]}" for title in fenster[:15])
            return result
        except Exception as e:
            return f"Fensterliste: {e}"
    
    def fenster_schliessen(name: str) -> int:
        """Fenster schließen"""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(name)
            count = 0
            for w in windows:
                try:
                    w.close()
                    count += 1
                except:
                    pass
            return count
        except:
            return 0
    
    def screenshot_machen(path: str) -> str:
        """Screenshot erstellen"""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            return path
        except Exception as e:
            raise Exception(f"Screenshot fehlgeschlagen: {e}")
    
    def programm_starten(name: str) -> bool:
        """Programm öffnen"""
        try:
            # Bekannte Windows-Programme
            app_map = {
                "notepad": "notepad.exe",
                "calc": "calc.exe",
                "rechner": "calc.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "explorer": "explorer.exe",
                "msedge": "msedge.exe",
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "code": "code.exe",
            }
            
            # Prüfe auf bekannte Namen
            name_lower = name.lower()
            for key, app in app_map.items():
                if key in name_lower:
                    subprocess.Popen([app], shell=True)
                    return True
            
            # Direkt ausführen
            if os.path.exists(name):
                os.startfile(name)
            else:
                subprocess.Popen(name, shell=True)
            return True
        except Exception as e:
            print(f"Fehler beim Starten: {e}")
            return False
    
    def programm_beenden(name: str) -> bool:
        """Programm beenden"""
        try:
            # Entferne .exe für bessere Suche
            proc_name = name.replace('.exe', '').lower()
            os.system(f'taskkill /f /im "{proc_name}.exe" 2>nul')
            return True
        except:
            return False
    
    def system_ausschalten():
        """Herunterfahren"""
        os.system("shutdown /s /t 60")
    
    def system_neustart():
        """Neustart"""
        os.system("shutdown /r /t 60")
    
    def system_abbrechen():
        """Abbruch"""
        os.system("shutdown /a")
    
    def get_active_window() -> str:
        """Aktives Fenster"""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            return active.title if active else "Unbekannt"
        except:
            return "Unbekannt"