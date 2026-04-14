#!/bin/bash

PROJECT_DIR="/home/verdi/MOEX_Trading_bot"
PID_STRAZH_FILE="$PROJECT_DIR/pid_strazh.bot"
LOG_STRAZH_FILE="$PROJECT_DIR/log_strazh.txt"
PID_FILE="$PROJECT_DIR/pid.bot"
LOG_FILE="$PROJECT_DIR/log.txt"

cd "$PROJECT_DIR" || exit 1

# Check, run?
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Bot running (PID: $PID)"
        exit 1
    fi
fi

# Running
nohup python3 bot_moex.py > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "Bot running! PID: $(cat $PID_FILE)"
echo "Logs: tail -f $LOG_FILE"

sleep 3

# Check, run?
if [ -f "$PID_STRAZH_FILE" ]; then
    PID=$(cat "$PID_STRAZH_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Strazh running (PID: $PID)"
        exit 1
    fi
fi

# Running
nohup python3 strazh_bot.py > "$LOG_STRAZH_FILE" 2>&1 &
echo $! > "$PID_STRAZH_FILE"
echo "Strazh running! PID: $(cat $PID_STRAZH_FILE)"
