import os
import json
import logging
import subprocess
import threading
import platform
from datetime import datetime
from pathlib import Path

# Basisverzeichnis
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).resolve()
os.makedirs(BASE_DIR, exist_ok=True)

# Logging
logging.basicConfig(
    filename=BASE_DIR / "pia4.log",
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    encoding='utf-8',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s'))
logging.getLogger('').addHandler(console_handler)

IS_WINDOWS = platform.system() == "Windows"

# JSON Handling
json_lock = threading.RLock()
_json_cache = {}

def lade_json(name: str, default=None, use_cache: bool = True):
    if default is None:
        default = {}
    path = BASE_DIR / name
    with json_lock:
        if use_cache:
            cached = _json_cache.get(name)
            if cached and path.exists() and cached[0] == path.stat().st_mtime:
                return cached[1]
        if not path.exists():
            speichere_json(name, default)
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if use_cache:
                _json_cache[name] = (path.stat().st_mtime, data)
            return data
        except Exception as e:
            logging.error(f"lade_json Fehler bei {name}: {e}")
            return default

def speichere_json(name: str, daten, indent=2):
    path = BASE_DIR / name
    with json_lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(daten, f, indent=indent, ensure_ascii=False)
            _json_cache.pop(name, None)
        except Exception as e:
            logging.error(f"speichere_json Fehler bei {name}: {e}")

# Konfiguration
KONFIG = lade_json("pia4_konfig.json", {
    "openweather_api_key": "",
    "telegram_bot_token": "",
    "telegram_chat_id": ""
})

# Sprachausgabe (Windows optimiert)
def sprich(text: str):
    """Text-to-Speech für Windows"""
    text = str(text).strip()
    if not text:
        return
    
    # 1. Versuch: gTTS (beste Qualität)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="de", slow=False)
        tmp_mp3 = BASE_DIR / "tmp_sprache.mp3"
        tts.save(tmp_mp3)
        
        if IS_WINDOWS:
            # Windows: Verwende winsound
            import winsound
            winsound.PlaySound(str(tmp_mp3), winsound.SND_FILENAME)
        else:
            subprocess.run(["mpg123", "-q", str(tmp_mp3)], check=False, timeout=15)
        
        tmp_mp3.unlink(missing_ok=True)
        return
    except Exception as e:
        logging.warning(f"gTTS-Fehler: {e}")
    
    # 2. Versuch: Windows SAPI (offline, keine Internetverbindung nötig)
    if IS_WINDOWS:
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
            return
        except ImportError:
            # pywin32 nicht installiert
            pass
        except Exception as e:
            logging.warning(f"SAPI-Fehler: {e}")
    
    # 3. Fallback: Nur ausgeben
    print(f"\n🔊 Pia: {text}\n")

def system_befehl(befehl: str, shell=True, timeout=None, capture_output=False):
    """Führt Systembefehle aus (plattformunabhängig)"""
    kwargs = {"shell": shell, "timeout": timeout}
    if capture_output:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    else:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    
    try:
        result = subprocess.run(befehl, **kwargs)
        if capture_output:
            return result.stdout.strip() if result.returncode == 0 else ""
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Systembefehl fehlgeschlagen: {befehl} → {e}")
        return False

def telegram_senden(nachricht: str, anhang=None, parse_mode: str = "MarkdownV2"):
    """Telegram deaktiviert (Backup via Server)"""
    logging.warning("Telegram ist deaktiviert")
    return False