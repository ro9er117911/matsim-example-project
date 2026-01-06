#!/bin/bash
# ============================================================
# 執行 Python 分析腳本
# ============================================================

OUTPUT_DIR=$1

if [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <output_directory>"
    echo "Example: $0 5000_disatar/05_combined_evac/output_optimized_iter10"
    exit 1
fi

echo "=== 執行分析 ==="
echo "目錄: $OUTPUT_DIR"
echo ""

# 速度分析
if [ -f "${OUTPUT_DIR}/output_events.xml.gz" ]; then
    echo "[1/2] 分析 agent 速度..."
    poetry run python 5000_disatar/05_scripts/07_analysis/analyze_agent_speeds.py \
        --events ${OUTPUT_DIR}/output_events.xml.gz \
        --network ${OUTPUT_DIR}/output_network.xml.gz \
        --out ${OUTPUT_DIR}/slow_links_analysis.csv
fi

# Dashboard 生成
echo "[2/2] 生成 Dashboard..."
poetry run python 5000_disatar/05_scripts/07_analysis/generate_dashboard_yamls.py \
    --output_dir ${OUTPUT_DIR}

echo ""
echo "✓ 分析完成"
echo "輸出: ${OUTPUT_DIR}/"
