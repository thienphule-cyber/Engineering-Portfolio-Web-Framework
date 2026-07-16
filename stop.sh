#!/bin/bash
# ============================================================
# stop.sh - Stop the Engineering Portfolio Flask server
# ============================================================

cd "$(dirname "$0")"

PID_FILE=".server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No running server found (no PID file)."
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    kill "$PID"
    sleep 1

    # Force kill if it's still alive after 1 second
    if ps -p "$PID" > /dev/null 2>&1; then
        kill -9 "$PID"
    fi

    echo "Server stopped (PID: $PID)."
else
    echo "Server was not running (stale PID file removed)."
fi

rm -f "$PID_FILE"