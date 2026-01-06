# 動態海嘯撤離模擬 Workflow

## 概述

本 workflow 用於建立淡水沿海海嘯撤離模擬，包含分階段道路封閉和 5000 代理人多模態交通。

## 資料來源與人口規模（觀測紀錄）

- 28 萬人口代表淡水 + 八里的可能居民規模（災害情境與封路參數另有假設文件，待補連結）。
- GTFS（台北 + 新北公車）：`5000_disatar/01_raw_data/bus_disaster_gtfs`
- 底圖/路網來源（國土測繪圖資）：`5000_disatar/01_raw_data/taipei_shp_map`
- 人口放大腳本：`5000_disatar/05_scripts/04_population/augment_population.py`（clone + jitter；不改變原模式比例）

## 最新快速流程（staggered iter10 baseline）

調整內容：分散出發時間（02:50–03:20）、延後/降速封路（`input/tsunami_changeEvents_staggered.xml`）、10 iter 學習（`config_combined_5000_staggered_iter10.xml`，stuck=0），視覺濾鏡只保留 `volume>=20` 且 `tt_ratio>=2` 的 link。

一鍵執行（含 SimWrapper 資料產出）：
```bash
./5000_disatar/05_scripts/06_disaster_evacuation/run_staggered_iter10_pipeline.sh
# 不重跑模擬，只重生視覺與 YAML
SKIP_SIM=1 ./5000_disatar/05_scripts/06_disaster_evacuation/run_staggered_iter10_pipeline.sh
# 調整濾鏡門檻（預設 MIN_VOLUME=20, MIN_TT_RATIO=2）
MIN_VOLUME=10 MIN_TT_RATIO=1.5 SKIP_SIM=1 ./5000_disatar/05_scripts/06_disaster_evacuation/run_staggered_iter10_pipeline.sh
# 跑 100 iter 版本（輸出：output_staggered_iter100）
CONFIG_FILE=5000_disatar/05_combined_evac/config_combined_5000_staggered_iter100.xml \
  ./5000_disatar/05_scripts/06_disaster_evacuation/run_staggered_iter10_pipeline.sh
```

輸出：`output_staggered_iter10/`（包含濾過後的 `network_wgs84.geojson` 與 dashboard YAML）。

## 前置需求

- Java 21 + Maven
- Python 3 + pyproj
- osmium-tool
- MATSim 2025.0

---

## Step 1: 提取 OSM 海岸線

```bash
# 1.1 建立 10km ROI (中心: 淡水 25.18, 121.44)
cd 5000_disatar/05_combined_evac/input
python3 - <<'PY'
import json, math
from pyproj import Transformer
lat, lon = 25.18, 121.44
r = 10000
n = 128
to3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
to4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
x0,y0 = to3857.transform(lon,lat)
coords=[[to4326.transform(x0+r*math.cos(2*math.pi*i/n), y0+r*math.sin(2*math.pi*i/n)) for i in range(n+1)]]
gj={"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[list(c) for c in coords[0]]]}}]}
open("tamsui_10km.geojson","w").write(json.dumps(gj))
PY

# 1.2 從 OSM 提取範圍
osmium extract -p tamsui_10km.geojson ../01_raw_data/osm/source.osm.pbf -o tamsui_10km.osm.pbf

# 1.3 提取海岸線
osmium tags-filter tamsui_10km.osm.pbf nwr/natural=coastline -o coastline.osm.pbf
osmium export coastline.osm.pbf -o coastline_10km.geojson -u type_id

# 1.4 提取河岸 (選用)
osmium tags-filter tamsui_10km.osm.pbf nwr/waterway=riverbank -o riverbank.osm.pbf
osmium export riverbank.osm.pbf -o riverbank_10km.geojson -u type_id
```

---

## Step 2: 生成分階段封閉事件

### 方法 A: 基於海嘯溢淹深度 (2025 年潛勢圖) - 推薦

使用 2025 年海嘯溢淹潛勢圖的 `Max_depth` 欄位來分類道路：

```bash
python3 5000_disatar/05_scripts/06_disaster_evacuation/generate_change_events_depth.py \
  --network ../../scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz \
  --inundation ../evacuation_shp/2025年海嘯溢淹潛勢圖資/2025年海嘯溢淹潛勢更新模擬.shp \
  --output input/tsunami_changeEvents_2025.xml \
  --geojson-output output/inundation_closure_2025.geojson \
  --roi "121.35,25.10,121.52,25.22"
```

#### 深度分階段配置

| 階段 | 深度 (公尺) | 降速時間 | 封閉時間 | 速度係數 |
|-----|------------|---------|---------|---------|
| depth_gt3 | >3m | 03:00:00 | 03:05:00 | 0% (立即封閉) |
| depth_2_3 | 2-3m | 03:01:00 | 03:06:00 | 30% |
| depth_1_2 | 1-2m | 03:02:00 | 03:07:00 | 40% |
| depth_05_1 | 0.5-1m | 03:03:00 | 03:08:00 | 50% |
| depth_03_05 | 0.3-0.5m | 03:04:00 | 03:09:00 | 60% |
| depth_0_03 | <0.3m | 03:05:00 | (不封閉) | 70% |

### 方法 B: 基於海岸線距離 (舊方法)

```bash
python3 5000_disatar/05_scripts/06_disaster_evacuation/generate_change_events.py \
  --network ../../scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz \
  --shoreline input/tamsui_shoreline.geojson \
  --output input/tsunami_changeEvents.xml \
  --geojson-output output/coastal_closure.geojson
```

#### 距離分階段配置

| 階段 | 距離 | 降速時間 | 封閉時間 |
|-----|------|---------|---------|
| 1 | 0-500m | 03:00 | 03:10 |
| 2 | 500-1500m | 03:05 | 03:15 |
| 3 | 1500-3000m | 03:10 | 03:20 |
| 4 | 3000-10000m | 03:15 | (不封閉) |

---

## Step 3: 配置模擬

關鍵配置 (`config_combined_5000.xml`):

```xml
<!-- 啟用 time-variant network -->
<module name="network">
    <param name="inputChangeEventsFile" value="input/tsunami_changeEvents.xml" />
    <param name="timeVariantNetwork" value="true" />
</module>

<!-- PT 使用 teleportation (避免 subway 速度問題) -->
<module name="transit">
    <param name="usingTransitInMobsim" value="false" />
</module>
```

---

## Step 4: 執行模擬

```bash
./mvnw exec:java -Dexec.mainClass="org.matsim.core.controler.Controler" \
  -Dexec.args="5000_disatar/05_combined_evac/config_combined_5000.xml"

# 複製輸出
cp -r output/* 5000_disatar/05_combined_evac/output/
```

---

## Step 5: 查看結果

```bash
cd 5000_disatar/05_combined_evac/output
simwrapper run --port 8050
```

---

## 常見問題

### PT 車輛卡住
**解決**: 設定 `usingTransitInMobsim="false"` 使用 teleportation

### 封閉區域呈矩形
**解決**: 使用真實 OSM 海岸線，不要用固定座標

### 模擬太慢
**解決**: 減少 iterations，或禁用 within-day replanning

---

## 輸出檔案說明

| 檔案 | 用途 |
|-----|-----|
| `output_events.xml.gz` | 所有模擬事件 |
| `scorestats.csv` | 分數統計 |
| `modestats.csv` | 模式分佈 |
| `coastal_closure.geojson` | 封閉區域可視化 |
