#!/bin/bash
set -e

# 設定路徑
PROJECT_ROOT="../../../" # 指向 matsim-example-project
BASE_DIR=$(pwd)
SCRIPTS_DIR="scripts"
OUTPUT_DIR="output_csl"
INPUT_DIR="output"

# 建立輸出資料夾
mkdir -p "$OUTPUT_DIR"

# 定義輸入檔案
EVENTS="$INPUT_DIR/output_events.xml.gz"
NETWORK="input/network_final_v5_islands.xml.gz"

# 檢查輸入
if [ ! -f "$EVENTS" ] || [ ! -f "$NETWORK" ]; then
    echo "❌ 錯誤: 找不到 $EVENTS 或 $NETWORK"
    exit 1
fi

echo "========================================================="
echo "開始處理 CSL 輸出 (Parquet & GeoJSON)"
echo "Output: $OUTPUT_DIR"
echo "========================================================="

# 1. 執行 matsim_to_parquet.py
echo "1. 生成 Trajectory Parquet..."
PARQUET_SCRIPT="$SCRIPTS_DIR/matsim_to_parquet.py"
if [ -f "$PARQUET_SCRIPT" ]; then
    python3 "$PARQUET_SCRIPT" \
        --events "$EVENTS" \
        --network "$NETWORK" \
        --output "$OUTPUT_DIR/trajectories.parquet"
else
    echo "⚠️ 找不到 $PARQUET_SCRIPT"
fi

# 2. 準備 Congestion CSV (為 matsim_to_road_service.py 準備)
CONGESTION_CSV="$OUTPUT_DIR/congestion.csv"
echo "2. 計算 Link Volume 以生成 Congestion CSV..."

python3 -c "
import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import sys

events_file = '$EVENTS'
output_file = '$CONGESTION_CSV'
counts = {}

print(f'  Reading events from {events_file}...')
try:
    with gzip.open(events_file, 'rt', encoding='utf-8') as f:
        # 使用 iterparse 節省記憶體
        context = ET.iterparse(f, events=('end',))
        for event, elem in context:
            if elem.tag == 'event' and elem.get('type') == 'entered link':
                lid = elem.get('link')
                counts[lid] = counts.get(lid, 0) + 1
            elem.clear()
            
    df = pd.DataFrame(list(counts.items()), columns=['link_id', 'volume'])
    df.to_csv(output_file, index=False)
    print(f'  Saved congestion data ({len(df)} links) to {output_file}')
except Exception as e:
    print(f'  Error generating congestion csv: {e}')
    sys.exit(1)
"

# 3. 執行 matsim_to_road_service.py
echo "3. 生成 Road Service LOS GeoJSON..."
ROAD_SCRIPT="$SCRIPTS_DIR/matsim_to_road_service.py"
if [ -f "$ROAD_SCRIPT" ] && [ -f "$CONGESTION_CSV" ]; then
    python3 "$ROAD_SCRIPT" \
        --congestion "$CONGESTION_CSV" \
        --network "$NETWORK" \
        --output "$OUTPUT_DIR/road_service_level.geojson"
else
    echo "⚠️ 無法執行 matsim_to_road_service.py (腳本或輸入檔遺失)"
fi

echo "========================================================="
echo "✅ 處理完成！"
echo "📂 Trajectory: $OUTPUT_DIR/trajectories.parquet"
echo "📂 Road LOS:   $OUTPUT_DIR/road_service_level.geojson"
echo "========================================================="
