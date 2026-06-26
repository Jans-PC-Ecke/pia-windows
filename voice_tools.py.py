# voice_tools.py – Sprachmodus für Windows mit Wake-Word "hey pia"
import os
import time
import threading
import queue
import numpy as np
import sys

# Versuche Mikrofon-Bibliotheken zu laden
try:
    import sounddevice as sd
    SOUNDDEVICE_OK = True
except ImportError:
    SOUNDDEVICE_OK = False
    print("❌ sounddevice nicht installiert. Führe aus: pip install sounddevice")

try:
    from faster_whisper import WhisperModel
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False
    print("❌ faster-whisper nicht installiert. Führe aus: pip install faster-whisper")

from utils import sprich, logging

WAKE_WORD = "hey pia"
MODEL_SIZE = "base"  # "base" ist kleiner und schneller für Windows, alternativ "tiny" oder "small"
DEVICE = "cpu"  # Windows: meiste keine CUDA → CPU
COMPUTE_TYPE = "int8"  # Schneller auf CPU

# Globaler Audio-Queue
audio_queue = queue.Queue(maxsize=30)

def audio_callback(indata, frames, time_info, status):
    """Callback für Mikrofon-Eingabe"""
    if status:
        print(f"Audio-Status: {status}")
    audio_queue.put(indata.copy())

def sprachmodus():
    """Startet den kontinuierlichen Sprachmodus mit Wake-Word"""
    
    # Prüfe Abhängigkeiten
    if not SOUNDDEVICE_OK:
        sprich("Sounddevice ist nicht installiert.")
        print("\n🔧 Installation: pip install sounddevice")
        return
    
    if not WHISPER_OK:
        sprich("Faster-Whisper ist nicht installiert.")
        print("\n🔧 Installation: pip install faster-whisper")
        return
    
    sprich("Hey Pia Modus ist aktiv. Sag einfach 'Hey Pia' gefolgt von deinem Befehl.")
    print("\n" + "="*50)
    print("🎤 Sprachmodus aktiv – Mikrofon wird verwendet")
    print("   Sage: 'Hey Pia' + dein Befehl")
    print("   Drücke Ctrl+C zum Beenden")
    print("="*50 + "\n")
    
    # Lade Whisper-Modell
    print(f"📦 Lade Whisper-Modell ({MODEL_SIZE}) ...")
    try:
        model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            cpu_threads=4,
            num_workers=2
        )
        print("✅ Whisper-Modell geladen")
    except Exception as e:
        print(f"❌ Fehler beim Laden des Modells: {e}")
        sprich("Konnte das Sprachmodell nicht laden.")
        return
    
    # Buffer für Audio
    buffer = np.array([], dtype=np.float32)
    samplerate = 16000
    
    # Mikrofon-Stream starten
    try:
        with sd.InputStream(
            samplerate=samplerate,
            channels=1,
            dtype='float32',
            blocksize=8000,
            callback=audio_callback
        ):
            print("🎙️ Mikrofon aktiv – höre auf 'Hey Pia'...")
            
            while True:
                try:
                    # Audio-Chunk holen (Timeout 1 Sekunde)
                    chunk = audio_queue.get(timeout=1.0)
                    buffer = np.concatenate((buffer, chunk.flatten()))
                    
                    # Buffer nicht zu groß werden lassen (~10 Sekunden)
                    max_samples = samplerate * 10
                    if len(buffer) > max_samples:
                        buffer = buffer[-max_samples:]
                    
                    # Nur alle 2 Sekunden transkribieren (Performance)
                    if len(buffer) > samplerate * 2:  # Mindestens 2 Sekunden
                        
                        # Transkribiere
                        segments, info = model.transcribe(
                            buffer,
                            language="de",
                            vad_filter=True,  # Voice Activity Detection
                            vad_parameters={
                                "min_silence_duration_ms": 500,
                                "speech_threshold": 0.5
                            }
                        )
                        
                        # Text aus Segmenten sammeln
                        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip()).lower()
                        
                        if text:
                            print(f"\n📝 Erkannt: {text}")
                            
                            # Prüfe auf Wake-Word
                            if WAKE_WORD in text:
                                # Extrahiere Befehl nach dem Wake-Word
                                parts = text.split(WAKE_WORD, 1)
                                if len(parts) > 1:
                                    kommando = parts[1].strip()
                                    if kommando:
                                        print(f"\n🎯 Befehl: {kommando}")
                                        sprich("Einen Moment...")
                                        
                                        # Führe Befehl aus
                                        try:
                                            from assistant_core import befehl_verarbeiten
                                            antwort = befehl_verarbeiten(kommando)
                                            sprich(antwort)
                                            print(f"\n✅ {antwort}\n")
                                        except Exception as e:
                                            print(f"❌ Fehler: {e}")
                                            sprich("Entschuldigung, das habe ich nicht verstanden.")
                                        
                                        # Buffer zurücksetzen
                                        buffer = np.array([], dtype=np.float32)
                                    else:
                                        # Nur Wake-Word ohne Befehl
                                        sprich("Ja? Wie kann ich helfen?")
                                        buffer = np.array([], dtype=np.float32())
                            else:
                                # Kein Wake-Word – nur Feedback für Debug (optional)
                                pass
                        
                        # Buffer nach Verarbeitung etwas zurücksetzen (gleitendes Fenster)
                        if len(buffer) > samplerate * 4:
                            buffer = buffer[-samplerate*2:]
                            
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    print("\n\n👋 Sprachmodus beendet")
                    break
                except Exception as e:
                    print(f"Fehler im Hauptloop: {e}")
                    logging.error(f"Sprachmodus Fehler: {e}")
                    time.sleep(0.5)
                    
    except Exception as e:
        print(f"❌ Mikrofon-Fehler: {e}")
        sprich("Konnte das Mikrofon nicht öffnen.")
        return

def tools_holen():
    return [
        ("sprachmodus", sprachmodus, "Sprache / Wake-Word"),
        ("voice_mode", sprachmodus, "Sprache / Wake-Word"),
        ("hey_pia", sprachmodus, "Sprache / Wake-Word"),
    ]

if __name__ == "__main__":
    # Test-Modus
    sprachmodus()