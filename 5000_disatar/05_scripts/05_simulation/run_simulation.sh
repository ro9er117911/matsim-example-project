#!/bin/bash
# ============================================================
# 在伺服器背景執行 MATSim 模擬
# ============================================================

CONFIG=$1

if [ -z "$CONFIG" ]; then
    echo "Usage: $0 <config.xml>"
    echo "Example: $0 5000_disatar/05_combined_evac/config_optimized_iter10.xml"
    exit 1
fi

LOG_FILE="${CONFIG%.xml}.log"
MEMORY="${MATSIM_MEMORY:-16g}"

echo "=== MATSim 模擬 (背景執行) ==="
echo "配置: $CONFIG"
echo "日誌: $LOG_FILE"
echo "記憶體: $MEMORY"
echo ""

nohup java -Xmx${MEMORY} -Xms8g \
    -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    "$CONFIG" \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo "✓ 模擬已啟動"
echo "  PID: $PID"
echo ""
echo "監控指令:"
echo "  tail -f $LOG_FILE"
echo "  ps aux | grep $PID"
