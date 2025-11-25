#!/bin/bash
# Error monitoring script for PT mapping
# Usage: ./monitor_errors.sh

LOG_FILE="logs/ptmapper_full_final.log"
ERROR_FILE="logs/errors_realtime.txt"

echo "開始監控錯誤和警告..." | tee "$ERROR_FILE"
echo "時間戳: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$ERROR_FILE"
echo "================================================" | tee -a "$ERROR_FILE"

# 即時追蹤日誌並過濾錯誤
tail -f "$LOG_FILE" 2>/dev/null | grep --line-buffered -i "error\|exception\|warn.*dead\|FATAL" | while read line; do
    echo "$(date '+%H:%M:%S') | $line" | tee -a "$ERROR_FILE"
done
