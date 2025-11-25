#!/bin/bash
# Progress monitoring script for PT mapping
# Usage: ./monitor_progress.sh

LOG_FILE="logs/ptmapper_full_final.log"
OUTPUT_FILE="logs/progress_monitor.txt"

echo "開始監控 PT 映射進度..." | tee -a "$OUTPUT_FILE"
echo "時間戳 | 已完成路線 | 百分比 | 記憶體使用" | tee -a "$OUTPUT_FILE"
echo "================================================" | tee -a "$OUTPUT_FILE"

while true; do
    # 取得當前時間
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # 計算已完成路線數
    if [ -f "$LOG_FILE" ]; then
        COMPLETED=$(grep -c "Progress.*100\.00%" "$LOG_FILE" 2>/dev/null || echo "0")
        PERCENT=$(echo "scale=2; $COMPLETED / 2362 * 100" | bc 2>/dev/null || echo "0")

        # 取得記憶體使用
        MEM_MB=$(ps aux | grep "PublicTransitMapper.*ptmapper-config-full-final" | grep -v grep | awk '{print $6/1024}' | head -1)

        if [ ! -z "$MEM_MB" ]; then
            echo "$TIMESTAMP | $COMPLETED/2362 | ${PERCENT}% | ${MEM_MB} MB" | tee -a "$OUTPUT_FILE"
        else
            echo "$TIMESTAMP | 進程未運行或已完成" | tee -a "$OUTPUT_FILE"
            break
        fi
    else
        echo "$TIMESTAMP | 日誌檔案尚未建立" | tee -a "$OUTPUT_FILE"
    fi

    # 每 5 分鐘檢查一次
    sleep 300
done

echo "================================================" | tee -a "$OUTPUT_FILE"
echo "監控結束於 $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$OUTPUT_FILE"
