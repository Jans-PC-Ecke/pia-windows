import requests
import logging
import subprocess
import os
import platform
from datetime import datetime
from utils import sprich, lade_json, speichere_json, telegram_senden, IS_WINDOWS

# Windows-spezifische Funktionen laden
if IS_WINDOWS:
    from platform_windows import (
        audio_lauter, audio_leiser, audio_mute, audio_get_volume,
        fenster_liste, fenster_schliessen, screenshot_machen,
        programm_starten, programm_beenden, get_active_window
    )

def kontext_laden():
    return lade_json("kontext.json", {"historie": []})

def kontext_speichern(d):
    speichere_json("kontext.json", d)

def zeige_hilfemenue() -> str:
    hilfe_text = """
╔══════════════════════════════════════════════════════════════╗
║                    🎤 Pia4 – Windows-Assistent                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ⏰ Zeit & Wetter                                            ║
║     • wie spät ist es? / uhrzeit / datum                    ║
║     • wetter in Berlin                                      ║
║                                                              ║
║  📝 Notizen & Kalender                                       ║
║     • notiz Milch kaufen                                    ║
║     • termin arzt morgen 14 uhr                             ║
║     • termine heute                                         ║
║                                                              ║
║  🎵 Musik & Lautstärke (Windows Media)                       ║
║     • play / pause / next / previous                        ║
║     • lauter / leiser / stumm                               ║
║                                                              ║
║  🪟 Fenster & Programme                                      ║
║     • öffne notepad / starte rechner                         ║
║     • schließe notepad / beende chrome                       ║
║     • welche fenster sind offen?                            ║
║     • mach screenshot                                       ║
║                                                              ║
║  💻 System                                                   ║
║     • ausschalten / neustart                                ║
║                                                              ║
║  🔍 Suche & Internet                                         ║
║     • suche nach Python Tutorial                            ║
║                                                              ║
║  🤖 KI (Ollama)                                             ║
║     • Alles andere fragst du einfach mich!                  ║
║                                                              ║
║  ❓ hilfe / was kannst du / ?                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(hilfe_text)
    sprich("Hier ist das Hilfemenü")
    return hilfe_text

def befehl_verarbeiten(befehl: str) -> str:
    if not befehl:
        return ""
    
    clean = befehl.strip().lower()
    orig = befehl.strip()
    
    # ──────────────────────────────
    # Hilfemenü
    # ──────────────────────────────
    if clean in ("hilfe", "help", "was kannst du", "befehle", "?"):
        return zeige_hilfemenue()
    
    # ──────────────────────────────
    # Zeit & Datum
    # ──────────────────────────────
    if any(w in clean for w in ["wie spät", "uhrzeit", "zeit"]):
        jetzt = datetime.now().strftime("%H:%M Uhr")
        sprich(f"Es ist {jetzt}")
        return f"Es ist {jetzt}"
    
    if any(w in clean for w in ["datum", "welches datum", "heute"]):
        heute = datetime.now().strftime("%d. %B %Y")
        sprich(f"Heute ist der {heute}")
        return f"Heute ist der {heute}"
    
    # ──────────────────────────────
    # Wetter
    # ──────────────────────────────
    if "wetter" in clean:
        try:
            from weather_tools import wetter_holen
            stadt = clean.split("wetter", 1)[-1].strip() or "Berlin"
            return wetter_holen(stadt)
        except Exception as e:
            return f"Wetter nicht verfügbar: {e}"
    
    # ──────────────────────────────
    # Lautstärke (Windows)
    # ──────────────────────────────
    if IS_WINDOWS:
        if "lauter" in clean or "lautstärke hoch" in clean:
            audio_lauter()
            vol = audio_get_volume()
            sprich(f"Lautstärke auf {vol} Prozent")
            return f"🔊 Lauter → {vol}%"
        
        if "leiser" in clean or "lautstärke runter" in clean:
            audio_leiser()
            vol = audio_get_volume()
            sprich(f"Lautstärke auf {vol} Prozent")
            return f"🔉 Leiser → {vol}%"
        
        if "stumm" in clean or "mute" in clean:
            audio_mute()
            sprich("Stummschaltung umgeschaltet")
            return "🔇 Stumm umgeschaltet"
    
    # ──────────────────────────────
    # Musik (Windows Media Keys)
    # ──────────────────────────────
    if any(w in clean for w in ["play", "pause", "next", "weiter", "vorheriger", "previous"]):
        try:
            import pyautogui
            if "play" in clean or "pause" in clean:
                pyautogui.press("playpause")
                sprich("Play/Pause")
                return "⏯️ Play/Pause"
            elif "next" in clean or "weiter" in clean:
                pyautogui.press("nexttrack")
                sprich("Nächster Titel")
                return "⏭️ Next"
            elif "vorheriger" in clean or "previous" in clean:
                pyautogui.press("prevtrack")
                sprich("Vorheriger Titel")
                return "⏮️ Previous"
        except:
            pass
    
    # ──────────────────────────────
    # Programme öffnen (Windows)
    # ──────────────────────────────
    open_keywords = ["öffne", "starte", "mach auf", "start"]
    if any(kw in clean for kw in open_keywords):
        used_kw = next((kw for kw in open_keywords if kw in clean), None)
        app_part = clean.split(used_kw, 1)[-1].strip() if used_kw else clean
        
        if not app_part:
            return "Was soll ich öffnen?"
        
        # Bekannte Windows-Apps
        app_map = {
            "notepad": "notepad.exe",
            "editor": "notepad.exe",
            "rechner": "calc.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "datei explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "kommandozeile": "cmd.exe",
            "powershell": "powershell.exe",
            "edge": "msedge.exe",
            "browser": "msedge.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "thunderbird": "thunderbird.exe",
            "mail": "thunderbird.exe",
            "email": "thunderbird.exe",
            "vscode": "code.exe",
            "visual studio code": "code.exe",
        }
        
        for key, app in app_map.items():
            if key in app_part:
                programm_starten(app)
                sprich(f"Öffne {key}")
                return f"✅ {key} wird geöffnet"
        
        programm_starten(app_part)
        sprich(f"Versuche {app_part} zu öffnen")
        return f"Öffne {app_part}"
    
    # ──────────────────────────────
    # Programme schließen (Windows)
    # ──────────────────────────────
    close_keywords = ["schließe", "beende", "mach zu", "kill"]
    if any(kw in clean for kw in close_keywords):
        used_kw = next((kw for kw in close_keywords if kw in clean), None)
        app_part = clean.split(used_kw, 1)[-1].strip() if used_kw else ""
        
        if not app_part:
            return "Welches Programm soll ich schließen?"
        
        if programm_beenden(app_part):
            sprich(f"{app_part} wird beendet")
            return f"❌ {app_part} beendet"
        else:
            return f"Konnte {app_part} nicht finden"
    
    # ──────────────────────────────
    # Fensterliste (Windows)
    # ──────────────────────────────
    if any(kw in clean for kw in ["welche fenster", "fenster offen", "fensterliste"]):
        if IS_WINDOWS:
            result = fenster_liste()
            sprich("Hier sind die offenen Fenster")
            print(result)
            return result
    
    # ──────────────────────────────
    # Screenshot (Windows)
    # ──────────────────────────────
    if any(kw in clean for kw in ["screenshot", "mach screenshot", "bildschirmfoto"]):
        try:
            pictures = os.path.expanduser("~/Pictures")
            os.makedirs(pictures, exist_ok=True)
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(pictures, filename)
            
            if IS_WINDOWS:
                screenshot_machen(path)
            else:
                import pyautogui
                pyautogui.screenshot(path)
            
            sprich(f"Screenshot gespeichert unter Bilder/{filename}")
            return f"📸 Screenshot: {path}"
        except Exception as e:
            return f"Screenshot fehlgeschlagen: {e}"
    
    # ──────────────────────────────
    # Notizen
    # ──────────────────────────────
    if "notiz" in clean:
        text = clean.split("notiz", 1)[-1].strip()
        try:
            from quicknotes_tools import schnellnotiz
            return schnellnotiz(text)
        except:
            return "Notiz konnte nicht gespeichert werden"
    
    # ──────────────────────────────
    # Kalender/Termine
    # ──────────────────────────────
    if any(w in clean for w in ["termin", "termine", "kalender"]):
        try:
            from calendar_tools import termin_hinzufügen, termine_heute
            if "heute" in clean or "termine" in clean:
                return termine_heute()
            titel = clean.split("termin", 1)[-1].strip()
            return termin_hinzufügen(titel)
        except:
            return "Kalender nicht verfügbar"
    
    # ──────────────────────────────
    # Web-Suche
    # ──────────────────────────────
    if "suche" in clean:
        suchbegriff = clean.split("suche", 1)[-1].strip()
        try:
            from web_search_tools import web_suche
            return web_suche(suchbegriff)
        except:
            return "Suche nicht verfügbar"
    
    # ──────────────────────────────
    # System (Herunterfahren)
    # ──────────────────────────────
    if "ausschalten" in clean or "herunterfahren" in clean or "shutdown" in clean:
        if IS_WINDOWS:
            from platform_windows import system_ausschalten
            sprich("Fahre in einer Minute herunter")
            system_ausschalten()
            return "🖥️ Herunterfahren in 60 Sekunden"
    
    if "neustart" in clean or "reboot" in clean:
        if IS_WINDOWS:
            from platform_windows import system_neustart
            sprich("Starte neu")
            system_neustart()
            return "🔄 Neustart in 60 Sekunden"
    
    if "abbrechen" in clean and ("herunterfahren" in clean or "neustart" in clean):
        if IS_WINDOWS:
            from platform_windows import system_abbrechen
            os.system("shutdown /a")
            sprich("Herunterfahren abgebrochen")
            return "✅ Abgebrochen"
    
    # ──────────────────────────────
    # Ollama / KI (Fallback für alles andere)
    # ──────────────────────────────
    ctx = kontext_laden()
    historie = "\n".join(ctx["historie"][-8:])
    
    system_prompt = f"""Du bist Pia – frech, direkt, hilfsbereit.
Du sprichst den Benutzer mit Vornamen an (falls bekannt, sonst einfach 'du').
Antworte auf Deutsch, kurz und praktisch. Maximal 2-3 Sätze.

Letzte Unterhaltung:
{historie}

Frage/Anweisung des Benutzers:"""
    
    try:
        from ollama_tools import ollama_antwort
        antwort = ollama_antwort(befehl, system_prompt=system_prompt)
        
        ctx["historie"].append(f"User: {befehl}")
        ctx["historie"].append(f"Pia: {antwort[:200]}")
        if len(ctx["historie"]) > 30:
            ctx["historie"] = ctx["historie"][-20:]
        kontext_speichern(ctx)
        
        return antwort
    except Exception as e:
        logging.error(f"Ollama Fehler: {e}")
        return "Entschuldige, Ollama ist gerade nicht erreichbar. Starte 'ollama serve' im Hintergrund."

def tools_holen():
    return [("befehl_verarbeiten", befehl_verarbeiten, "Kern / KI")]