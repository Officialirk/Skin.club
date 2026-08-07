@echo off
REM One-click launcher for Windows. Double-click this file in File Explorer.
REM
REM What it does: creates a virtual environment on first run, installs Flask
REM if needed, starts the app, and opens your browser to the dashboard.
REM Nothing here talks to Skin.Club or any other external service.

cd /d "%~dp0"

if not exist ".venv" (
  echo Setting up (first run only)...
  python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

if not defined FLASK_DEBUG set FLASK_DEBUG=0
if not defined PORT set PORT=5000

echo Starting Skin.Club Stats Tool at http://127.0.0.1:%PORT%/
echo (Close this window to stop the server.)

REM Open the browser a couple seconds after the server has time to start,
REM without blocking the server itself.
start "" cmd /c "timeout /t 2 /nobreak >nul & start "" http://127.0.0.1:%PORT%/"

python app.py
pause
