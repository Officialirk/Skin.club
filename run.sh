#!/usr/bin/env bash
# One-click launcher for macOS / Linux.
#
# Double-click behavior:
#   - macOS: rename/copy this to run.command (already provided as run.command)
#            and double-click it in Finder — it opens Terminal and runs this.
#   - Linux: double-click support depends on your file manager's settings for
#            .sh files ("Run in Terminal" / "Execute" vs "Open with text editor").
#            If double-click just opens a text editor, right-click the file and
#            choose "Run in Terminal", or open a terminal and run: ./run.sh
#
# What it does: creates a virtual environment on first run, installs Flask
# if needed, starts the app, and opens your browser to the dashboard.
# Nothing here talks to Skin.Club or any other external service.
#
# This window stays open (waits for a keypress) when the script exits, on
# both success and failure, so you can always read what happened. If it
# still closes immediately for you, open Terminal yourself, cd into this
# folder, and run: ./run.sh  -- that guarantees the window stays open.

pause_on_exit() {
  status=$?
  echo
  if [ $status -ne 0 ]; then
    echo "Exited with an error (see above)."
  else
    echo "Server stopped."
  fi
  read -n 1 -s -r -p "Press any key to close this window..." || true
  echo
}
trap pause_on_exit EXIT

set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found on your PATH."
  echo "Install Python 3.10+ from https://www.python.org/downloads/ (macOS)"
  echo "or your system package manager (Linux), then try again."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Setting up (first run only)..."
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "Installing dependencies (fast no-op if already installed)..."
pip install -q -r requirements.txt

export FLASK_DEBUG="${FLASK_DEBUG:-0}"
export PORT="${PORT:-5000}"
URL="http://127.0.0.1:${PORT}/"

echo "Starting Skin.Club Stats Tool at ${URL}"
echo "(Press Ctrl+C in this window to stop the server.)"

# Open the browser shortly after the server starts, in the background.
(
  sleep 1.5
  if command -v open >/dev/null 2>&1; then
    open "$URL"                    # macOS
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"                # Linux
  fi
) &

python app.py
