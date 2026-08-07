@echo off
setlocal enabledelayedexpansion
REM One-click launcher for Windows. Double-click this file in File Explorer.
REM
REM What it does: creates a virtual environment on first run, installs Flask
REM if needed, starts the app, and opens your browser to the dashboard.
REM Nothing here talks to Skin.Club or any other external service.
REM
REM This window is meant to stay open (it "pauses" at the end) so you can
REM read any error message. If it still closes immediately, open Command
REM Prompt yourself, cd into this folder, and type: run.bat
REM   -- that keeps the window open no matter what and shows the real error.

title Skin.Club Stats Tool
cd /d "%~dp0"

echo Looking for Python...
where python >nul 2>nul
if %errorlevel%==0 (
  set "PY=python"
) else (
  where py >nul 2>nul
  if !errorlevel!==0 (
    set "PY=py"
  ) else (
    echo.
    echo ERROR: Python was not found on your PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    echo and make sure to check "Add python.exe to PATH" during setup.
    echo.
    pause
    exit /b 1
  )
)
echo Using: %PY%

if not exist ".venv" (
  echo Setting up - first run only...
  %PY% -m venv .venv
  if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo ERROR: Failed to create the virtual environment in .venv\
    echo Try running this manually from Command Prompt to see the full error:
    echo   %PY% -m venv .venv
    echo.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
if not %errorlevel%==0 (
  echo.
  echo ERROR: Failed to activate the virtual environment.
  echo.
  pause
  exit /b 1
)

echo Installing dependencies (fast no-op if already installed)...
pip install -q -r requirements.txt
if not %errorlevel%==0 (
  echo.
  echo ERROR: pip install failed. Check your internet connection and try again.
  echo.
  pause
  exit /b 1
)

if not defined FLASK_DEBUG set FLASK_DEBUG=0
if not defined PORT set PORT=5000

echo.
echo Starting Skin.Club Stats Tool at http://127.0.0.1:%PORT%/
echo (Close this window, or press Ctrl+C, to stop the server.)
echo.

REM Open the browser a couple seconds after the server has time to start,
REM without blocking the server itself. Uses explorer.exe to hand the URL
REM to your default browser, which avoids nested-quote parsing problems.
start "" /min cmd /c "timeout /t 2 /nobreak >nul && explorer http://127.0.0.1:%PORT%/"

python app.py

echo.
echo Server stopped.
pause
