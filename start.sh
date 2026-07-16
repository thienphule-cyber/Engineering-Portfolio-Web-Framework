#!/bin/bash
# ============================================================
# start.sh - Start the Engineering Portfolio Flask server
# ============================================================

# Move to the directory this script is located in,
# so it works regardless of where you run it from.
cd "$(dirname "$0")"

PID_FILE=".server.pid"
LOG_FILE="server.log"
PORT=5000

# Check if the server is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Server is already running (PID: $OLD_PID)."
        echo "Open: http://127.0.0.1:$PORT"
        exit 0
    else
        # Stale PID file from a previous crash/close — clean it up
        rm "$PID_FILE"
    fi
fi

# Create virtual environment if it doesn't exist yet
if [ ! -d "venv" ]; then
    echo "No virtual environment found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies quietly
pip install -r requirements.txt --quiet

# Start Flask in the background, redirect output to log file
nohup python app.py > "$LOG_FILE" 2>&1 &
NEW_PID=$!

echo $NEW_PID > "$PID_FILE"

# Give it a moment to boot up
sleep 1

if ps -p "$NEW_PID" > /dev/null 2>&1; then
    echo "Server started successfully (PID: $NEW_PID)."
    echo "Open: http://127.0.0.1:$PORT"
    echo "Logs: tail -f $LOG_FILE"
else
    echo "Server failed to start. Check $LOG_FILE for details."
    rm -f "$PID_FILE"
    exit 1
fi