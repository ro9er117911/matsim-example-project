#!/bin/bash
# monitor_pt_mapping.sh

LOG_FILE=$1
if [ -z "$LOG_FILE" ]; then
    echo "Usage: ./monitor_pt_mapping.sh <log_file>"
    exit 1
fi

echo "Monitoring $LOG_FILE..."
echo "--------------------------------"

while true; do
    # Extract progress line
    PROGRESS=$(grep "Calculating pseudoTransitRoutes ... " "$LOG_FILE" | tail -n 1)
    
    if [ -z "$PROGRESS" ]; then
        echo "Waiting for progress indicator in log..."
    else
        # Extract numbers 
        # Example: Calculating pseudoTransitRoutes ... 15/400 (3.75%)
        NUMS=$(echo "$PROGRESS" | grep -o "[0-9]*/[0-9]*")
        CURRENT=$(echo "$NUMS" | cut -d'/' -f1)
        TOTAL=$(echo "$NUMS" | cut -d'/' -f2)
        PERCENT=$(echo "$PROGRESS" | grep -o "([0-9.]*%)")
        
        # Get start time of routing
        # 2026-01-06T16:32:35,301  INFO PTMapper:171 Calculating pseudoTransitRoutes...
        START_TIME_STR=$(grep "Calculating pseudoTransitRoutes... (" "$LOG_FILE" | head -n 1 | awk '{print $1}')
        
        if [ ! -z "$START_TIME_STR" ] && [ "$CURRENT" -gt 0 ]; then
            ETA_INFO=$(python3 -c "
import datetime
import sys
try:
    start_str = '$START_TIME_STR'.replace(',', '.')
    start = datetime.datetime.fromisoformat(start_str)
    now = datetime.datetime.now()
    elapsed = (now - start).total_seconds()
    current = int($CURRENT)
    total = int($TOTAL)
    if current > 0:
        per_route = elapsed / current
        remaining = (total - current) * per_route
        eta_time = now + datetime.timedelta(seconds=remaining)
        print(f'Elapsed: {int(elapsed)}s | Avg: {per_route:.1f}s/route | Remaining: {int(remaining)}s | ETA: {eta_time.strftime(\"%H:%M:%S\")}')
    else:
        print('Calculating average...')
except Exception as e:
    print(f'Error calculating ETA: {e}')
")
            echo "Progress: $CURRENT/$TOTAL $PERCENT | $ETA_INFO"
        else
            echo "Progress: $CURRENT/$TOTAL $PERCENT | Calculating baseline..."
        fi
    fi
    
    # Check if process finished
    if grep -q "Mapping finished" "$LOG_FILE"; then
        echo "--------------------------------"
        echo "Mapping finished!"
        exit 0
    fi
    
    sleep 10
done
