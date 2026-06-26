#!/usr/bin/env python3
"""
Pia4 für Windows – Persönlicher Sprachassistent
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

# Prüfe Windows
if platform.system() != "Windows":
    print("⚠️ Dies ist die Windows-Version von Pia4")
    print("Auf Linux läuft die Original-Version besser")

def check_ollama():
    """Prüft ob Ollama läuft, startet es wenn nötig"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 11434))
        sock.close()
        if result == 0:
            print("✅ Ollama Server läuft")
            return True
    except:
        pass
    
    print("⚠️ Ollama läuft nicht!")
    print("   Bitte starte Ollama separat oder installiere es von:")
    print("   https://ollama.com/download/windows")
    print("\n   Nach der Installation: ollama pull llama3.2:3b")
    return False

def main():
    print("""
╔══════════════════════════════════════════════╗
║         🎤 Pia4 – Windows-Assistent          ║
║         Dein persönlicher Sprachassistent    ║
╚══════════════════════════════════════════════╝
    """)
    
    # Ollama prüfen (optional)
    ollama_ok = check_ollama()
    
    print("\n📋 Modus auswählen:")
    print("   1️⃣  Terminal-Modus (Text-Eingabe)")
    print("   2️⃣  Sprach-Modus (Hey Pia) – experimentell")
    print("   ❓  hilfe – Befehlsübersicht")
    print("   🚪  q – Beenden")
    
    while True:
        try:
            choice = input("\n👉 ").strip().lower()
            
            if choice == "1" or choice == "terminal":
                print("\n--- Terminal-Modus ---")
                print("Tippe deine Befehle ein. ':q' zum Beenden\n")
                
                from assistant_core import befehl_verarbeiten
                
                while True:
                    cmd = input("Pia4> ").strip()
                    if cmd.lower() in (":q", "exit", "quit"):
                        break
                    if cmd:
                        response = befehl_verarbeiten(cmd)
                        print(f"\n{response}\n")
            
            elif choice == "2" or choice == "sprache":
                print("\n--- Sprach-Modus ---")
                print("Aktiviere Mikrofon...")
                try:
                    from voice_tools import sprachmodus
                    sprachmodus()
                except ImportError:
                    print("❌ Sprachmodus nicht verfügbar")
                    print("Installiere: pip install sounddevice faster-whisper")
                except Exception as e:
                    print(f"Fehler: {e}")
            
            elif choice == "hilfe" or choice == "?":
                from assistant_core import zeige_hilfemenue
                zeige_hilfemenue()
            
            elif choice in ("q", "quit", "exit"):
                print("\n👋 Auf Wiedersehen!")
                break
            
            else:
                print("❌ Unbekannte Auswahl. Versuche: 1, 2, hilfe, q")
                
        except KeyboardInterrupt:
            print("\n\n👋 Abbruch – bis bald!")
            break
        except Exception as e:
            print(f"\n❌ Fehler: {e}\n")

if __name__ == "__main__":
    main()