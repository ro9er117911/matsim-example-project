#!/bin/bash
# ========================================
# v5 淡水撤離情境 - 280K 人口 Server 執行腳本
# ========================================
# 場景: 政府徵召淡水公車 + 市區公車協助撤離
# PT: 7條捷運 + 801條公車
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    v5 淡水撤離情境 - 280K MATSim 模擬                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  🚇 捷運: 7 條線     🚌 公車: 801 條    👥 人口: 280K         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Working directory: $(pwd)"
echo ""

# 檢查必要檔案
echo "📋 檢查必要檔案..."
REQUIRED_FILES=(
    "config_v5_280k.xml"
    "input/network_final_v5_islands.xml.gz"
    "input/transitSchedule_mapped_v5.xml.gz"
    "input/transitVehicles_v5.xml"
    "input/population_280k.xml.gz"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$f" ]; then
        echo "  ✗ Missing: $f"
        exit 1
    fi
    echo "  ✓ $f"
done

# 檢查 MATSim JAR
MATSIM_JAR="../../../matsim-example-project-0.0.1-SNAPSHOT.jar"
if [ ! -f "$MATSIM_JAR" ]; then
    # 嘗試其他位置
    MATSIM_JAR="$(find /home -name 'matsim*.jar' -type f 2>/dev/null | head -1)"
    if [ -z "$MATSIM_JAR" ]; then
        echo "  ✗ MATSim JAR not found"
        echo "  Please set MATSIM_JAR environment variable"
        exit 1
    fi
fi
echo "  ✓ MATSim JAR: $MATSIM_JAR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "開始執行 MATSim 模擬..."
echo "  記憶體: 200GB"
echo "  執行緒: 58"
echo "  迭代: 20"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 執行 MATSim
java -Xmx200G -Xms100G \
    -Djava.io.tmpdir=/tmp \
    -cp "$MATSIM_JAR" \
    org.matsim.core.controler.Controler \
    config_v5_280k.xml

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    模擬完成! ✓                                "
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 輸出目錄: output/"
ls -lh output/ 2>/dev/null | head -10 || echo "(輸出檔案將在成功執行後產生)"
