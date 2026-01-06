#!/bin/bash
set -e

# 設定路徑 (根據目前目錄 v5_tamsui_evac 的相對位置)
PROJECT_ROOT="../../../" # 指向 matsim-example-project
DISASTER_ROOT="../../"    # 指向 5000_disatar
TOOLS_ROOT="${PROJECT_ROOT}/tools"

# 主要工具腳本 (使用本機 Patch 過的版本)
MAKE_EVAC_SCRIPT="scripts/make_evac_v5.py"
DASHBOARD_YAML_SCRIPT="${TOOLS_ROOT}/generate_dashboard_yamls.py"

# 定義輸入與輸出
INPUT_DIR="output"
OUTPUT_DIR="output_vis"

echo "======================================================"
echo "準備 SimWrapper 可視化資料"
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "======================================================"

# 建立輸出資料夾
mkdir -p "$OUTPUT_DIR"

# 檢查輸入檔案
EVENTS="$INPUT_DIR/output_events.xml.gz"
NETWORK="input/network_final_v5_islands.xml.gz"

if [ ! -f "$EVENTS" ]; then
    echo "❌ 錯誤: 找不到 $EVENTS"
    exit 1
fi

echo "1. 執行基礎撤離分析 (make_evac_simwrapper.py)..."
if [ -f "$MAKE_EVAC_SCRIPT" ]; then
    python3 "$MAKE_EVAC_SCRIPT" \
        "$EVENTS" \
        --outdir "$OUTPUT_DIR" \
        --cells 20 \
        --base_time 10800 # 03:00:00 = 10800s
else
    echo "❌ 錯誤: 找不到工具腳本 $MAKE_EVAC_SCRIPT"
    exit 1
fi

echo "2. 生成進階 Dashboard 配置 (generate_dashboard_yamls.py)..."
if [ -f "$DASHBOARD_YAML_SCRIPT" ]; then
    # 注意: 這個腳本通常依賴 generate_advanced_dashboard.py 產生的 CSV
    # 如果那些 CSV 不存在，它會嘗試生成基礎的 YAML
    python3 "$DASHBOARD_YAML_SCRIPT" \
        --output_dir "$OUTPUT_DIR"
else
    echo "⚠️ 警告: 找不到 $DASHBOARD_YAML_SCRIPT，跳過 YAML 生成"
fi

echo "======================================================"
echo "✅ 可視化資料準備完成！"
echo "📂 結果位置: $OUTPUT_DIR"
echo ""
echo "🔥 啟動 SimWrapper (預覽):"
echo "   simwrapper serve -d $OUTPUT_DIR"
echo "======================================================"
