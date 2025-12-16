---
description: 災難模擬 SimWrapper 可視化 - 生成撤離分析 Dashboard
---

# SimWrapper 可視化技能

## 觸發條件

- 需要撤離結果可視化
- 生成 SimWrapper dashboard
- 查看交通擁塞熱力圖
- 分析撤離時間分佈

---

## Step 1: 生成 Dashboard YAML

### 一鍵生成 (使用 Pipeline)

```bash
# 跳過模擬，只重生視覺化
SKIP_SIM=1 ./5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh

# 調整濾鏡門檻
MIN_VOLUME=10 MIN_TT_RATIO=1.5 SKIP_SIM=1 \
  ./5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh
```

### 手動生成

```bash
# 生成 dashboard YAML
python3 tools/generate_dashboard_yamls.py \
  --output-dir output_staggered_iter100 \
  --network output_staggered_iter100/output_network.xml.gz

# 生成卡住車輛分析
python3 tools/generate_stuck_agents_csv.py \
  --events output_staggered_iter100/output_events.xml.gz \
  --output output_staggered_iter100/stuck_agents.csv
```

---

## Step 2: 生成 GeoJSON 可視化資料

### 路網轉換 (高擁塞路段)

```bash
python3 5000_disatar/05_combined_evac/tools/generate_advanced_dashboard.py \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --output-dir output/ \
  --min-volume 20 \
  --min-tt-ratio 2.0
```

### 撤離區域多邊形

```bash
python3 5000_disatar/05_combined_evac/tools/generate_zone_polygons.py \
  --zones-csv population_zones.csv \
  --output output/evacuation_zones.geojson
```

---

## Step 3: 啟動 SimWrapper 伺服器

```bash
cd output_staggered_iter100
simwrapper serve --port 8050

# 或使用 Docker
docker run -p 8050:8050 -v $(pwd):/data simwrapper/simwrapper
```

瀏覽器開啟: `http://localhost:8050`

---

## Dashboard 內容結構

### Dashboard 1: 總覽
- 撤離累計曲線
- 出發時間分佈
- 路網地圖 (network.avro)

### Dashboard 2: 交通分析  
- 壅塞熱力圖 (traffic_congestion.geojson)
- 模式分佈統計

### Dashboard 3: 卡住分析
- 卡住車輛位置
- 時間序列分析

---

## Step 4: 驗證 Dashboard

```bash
# 檢查 YAML 語法
for f in output/dashboard-*.yaml; do
  echo "Checking $f"
  cat "$f" | head -20
done

# 驗證 GeoJSON
python3 -c "import json; json.load(open('output/network_wgs84.geojson'))"

# 檢查 Avro 檔案
ls -lh output/*.avro
```

---

## 常見問題

### Dashboard 無顯示
**檢查**: YAML 語法、檔案路徑是否正確

### GeoJSON 座標錯誤
**解決**: 確認轉換為 WGS84 (EPSG:4326)

### 熱力圖資料不完整
**解決**: 調低 `--min-volume` 門檻

### 中文路名亂碼
**解決**: 確保使用 UTF-8 編碼輸出

---

## Dashboard YAML 範例

```yaml
header:
  title: "5000 代理人撤離模擬分析"
  description: "淡水海嘯撤離場景"

layout:
  row1:
    - type: map
      network: network.avro
      height: 12
    - type: line
      dataset: evacuation_cumulative.csv
      x: time
      y: evacuated
      title: "撤離累計曲線"
      
  row2:
    - type: geojson
      file: traffic_congestion.geojson
      colorRamp: RdYlGn
      colorScale: volume
      title: "交通壅塞熱力圖"
```

---

## 輸出檔案

| 檔案 | 用途 |
|------|------|
| `dashboard-*.yaml` | SimWrapper 配置 |
| `network.avro` | 路網可視化 |
| `network_wgs84.geojson` | 路網 GeoJSON |
| `traffic_congestion.geojson` | 壅塞分析 |
| `stuck_agents.csv` | 卡住車輛統計 |

## 參考檔案

- Dashboard 生成: `tools/generate_dashboard_yamls.py`
- 進階分析: `5000_disatar/05_combined_evac/tools/generate_advanced_dashboard.py`
- Pipeline: `tools/run_dashboard_pipeline.sh`
