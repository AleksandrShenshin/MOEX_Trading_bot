#!/bin/bash
PROJECT_DIR="/home/verdi/MOEX_Trading_bot"
PID_STRAZH_FILE="$PROJECT_DIR/pid_strazh.bot"
PID_FILE="$PROJECT_DIR/pid.bot"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill $PID
        rm "$PID_FILE"
        echo "Bot stopped (PID: $PID)"
    else
        echo "PID $PID not found"
        rm "$PID_FILE"
    fi
else
    echo "pid.bot not found"
fi

if [ -f "$PID_STRAZH_FILE" ]; then
    PID=$(cat "$PID_STRAZH_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill $PID
        rm "$PID_STRAZH_FILE"
        echo "Strazh stopped (PID: $PID)"
    else
        echo "PID $PID not found"
        rm "$PID_STRAZH_FILE"
    fi
else
    echo "pid_strazh.bot not found"
fi
