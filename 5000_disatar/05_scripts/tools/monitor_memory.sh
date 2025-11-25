#!/bin/bash
# Memory monitoring script for PT mapping
# Usage: ./monitor_memory.sh

OUTPUT_FILE="logs/memory_usage.txt"

echo "開始監控記憶體使用..." | tee "$OUTPUT_FILE"
echo "時間戳 | 記憶體(MB) | CPU(%)" | tee -a "$OUTPUT_FILE"
echo "================================================" | tee -a "$OUTPUT_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # 取得進程資訊
    PROC_INFO=$(ps aux | grep "PublicTransitMapper.*ptmapper-config-full-final" | grep -v grep | head -1)

    if [ ! -z "$PROC_INFO" ]; then
        MEM_MB=$(echo "$PROC_INFO" | awk '{print $6/1024}')
        CPU=$(echo "$PROC_INFO" | awk '{print $3}')

        echo "$TIMESTAMP | ${MEM_MB} MB | ${CPU}%" | tee -a "$OUTPUT_FILE"

        # 如果記憶體超過 14GB，發出警告
        MEM_INT=$(echo "$MEM_MB" | awk '{print int($1)}')
        if [ $MEM_INT -gt 14000 ]; then
            echo "⚠️  警告：記憶體使用超過 14GB！" | tee -a "$OUTPUT_FILE"
        fi
    else
        echo "$TIMESTAMP | 進程未運行" | tee -a "$OUTPUT_FILE"
        break
    fi

    # 每分鐘檢查一次
    sleep 60
done

echo "================================================" | tee -a "$OUTPUT_FILE"
echo "監控結束於 $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$OUTPUT_FILE"
