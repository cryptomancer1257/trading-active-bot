#!/bin/bash

# Plan Expiry Cron Job
# Run this script daily to check for expiring/expired plans
# Add to crontab: 0 9 * * * /path/to/plan_expiry_cron.sh

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Log file
LOG_FILE="$PROJECT_ROOT/logs/plan_expiry_$(date +\%Y\%m\%d).log"
mkdir -p "$PROJECT_ROOT/logs"

echo "========================================" >> "$LOG_FILE"
echo "Plan Expiry Cron Job - $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Send 7-day expiry reminders
echo "[$(date)] Sending expiry reminders..." >> "$LOG_FILE"
python3 "$PROJECT_ROOT/services/plan_expiry_notifier.py" >> "$LOG_FILE" 2>&1

# Downgrade expired plans
echo "[$(date)] Downgrading expired plans..." >> "$LOG_FILE"
python3 "$PROJECT_ROOT/services/plan_expiry_notifier.py" downgrade >> "$LOG_FILE" 2>&1

echo "[$(date)] Plan expiry cron job completed" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

