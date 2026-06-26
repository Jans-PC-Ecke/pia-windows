@echo off
title Pia4 Windows Assistant
color 0A

echo ========================================
echo    Starting Pia4 Windows Assistant
echo ========================================
echo.

cd /d "%~dp0"

REM Prüfe venv
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Aktiviere venv
call venv\Scripts\activate.bat

REM Prüfe Abhängigkeiten
pip show ollama > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements_windows.txt
)

REM Starte Pia4
python pia4.py

pause