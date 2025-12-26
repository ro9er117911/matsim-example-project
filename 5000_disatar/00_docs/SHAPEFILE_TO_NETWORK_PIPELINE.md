# Shapefile 轉 MATSim Network 完整流程

本文檔說明如何將**台灣國土測繪圖資 shapefile** 轉換為 MATSim 路網，並整合捷運和公車 GTFS 資料。

## 前置需求

### 軟體環境
```bash
# Python 環境
pip3 install geopandas shapely pyproj

# Java 環境 (pt2matsim)
java -version  # 需要 Java 21+
```

### 資料準備
1. **Shapefile 圖資** - `Q_ROAD.shp`, `Q_RDNODE.shp`
2. **GTFS 捷運資料** - `metro.zip`  
3. **GTFS 公車資料** - `bus.zip`

---

## Phase 1: Shapefile → raw_network.xml.gz

### Step 1.1: 檢查 Shapefile 結構（Optional）

```bash
python3 5000_disatar/05_scripts/inspect_shapefile_schema.py \
  5000_disatar/01_raw_data/chayi_map
```

**輸出**: JSON 檔案包含欄位結構和樣本資料 (`*_schema.json`)

### Step 1.2: 轉換 Shapefile → Network

```bash
python3 5000_disatar/05_scripts/convert_shapefile_to_network.py \
  --input 5000_disatar/01_raw_data/chayi_map \
  --output 5000_disatar/03_phase2_production/networks/raw_network.xml.gz \
  --modes "car,walk"
```

**參數說明**:
- `--input`: shapefile 資料夾路徑
- `--output`: 輸出 MATSim network 檔案
- `--modes`: 路網模式 (預設: `car,walk`)
- `--road-file`: 道路 shapefile 名稱 (預設: `Q_ROAD.shp`)
- `--node-file`: 節點 shapefile 名稱 (預設: `Q_RDNODE.shp`)

**輸出**:
- `raw_network.xml.gz` - 基礎路網 (僅 car/walk modes)
- 節點數：~77,000
- 連結數：~91,000 × 2 (含雙向)

### Step 1.3: 驗證路網

```bash
# 檢查節點和連結數量
zcat raw_network.xml.gz | grep -c '<node '
zcat raw_network.xml.gz | grep -c '<link '

# 檢查 XML 結構
zcat raw_network.xml.gz | head -50
```

---

## Phase 2: 整合捷運 GTFS

### Step 2.1: GTFS → MATSim Transit Schedule

使用專案內建工具 `GtfsToMatsim.java` 或 pt2matsim:

```bash
# 方法 1: 使用專案工具 (推薦)
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.GtfsToMatsim" \
  -Dexec.args="metro.zip raw_network.xml.gz EPSG:3826 transitSchedule-metro.xml"

# 方法 2: 使用 pt2matsim
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Gtfs2TransitSchedule \
  metro.zip raw_network.xml.gz transitSchedule-metro.xml
```

### Step 2.2: 建立 PT Mapper 配置檔

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  ptmapper-metro-config.xml
```

**編輯 `ptmapper-metro-config.xml`**:
```xml
<module name="PublicTransitMapping">
  <param name="inputNetworkFile" value="raw_network.xml.gz"/>
  <param name="inputScheduleFile" value="transitSchedule-metro.xml"/>
  <param name="outputNetworkFile" value="network-with-pt-metro.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-metro-mapped.xml.gz"/>
  
  <!-- 捷運參數 -->
  <param name="maxLinkCandidateDistance" value="300.0"/>
  <param name="nLinkThreshold" value="12"/>
  <param name="maxTravelCostFactor" value="15.0"/>
</module>
```

### Step 2.3: 執行捷運 Mapping

```bash
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-metro-config.xml
```

**輸出**:
- `network-with-pt-metro.xml.gz` - 整合捷運後路網
- `transitSchedule-metro-mapped.xml.gz` - 捷運時刻表

**驗證**:
```bash
# 檢查 pt mode links
zcat network-with-pt-metro.xml.gz | grep -c 'modes="pt"'

# 檢查 transit routes
zcat transitSchedule-metro-mapped.xml.gz | grep -c '<transitRoute'
```

---

## Phase 3: 整合公車 GTFS

### Step 3.1: GTFS → Transit Schedule

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.GtfsToMatsim" \
  -Dexec.args="bus.zip network-with-pt-metro.xml.gz EPSG:3826 transitSchedule-bus.xml"
```

### Step 3.2: 建立公車 Mapper 配置

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  ptmapper-bus-config.xml
```

**編輯 `ptmapper-bus-config.xml`**:
```xml
<module name="PublicTransitMapping">
  <param name="inputNetworkFile" value="network-with-pt-metro.xml.gz"/>
  <param name="inputScheduleFile" value="transitSchedule-bus.xml"/>
  <param name="outputNetworkFile" value="network-with-pt-final.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-bus-mapped.xml.gz"/>
  
  <!-- 公車參數 -->
  <param name="maxLinkCandidateDistance" value="90.0"/>
  <param name="nLinkThreshold" value="6"/>
  <param name="maxTravelCostFactor" value="5.0"/>
</module>
```

### Step 3.3: 執行公車 Mapping

```bash
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-bus-config.xml
```

### Step 3.4: 合併 Transit Schedules

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.MergeGtfsSchedules" \
  -Dexec.args="transitSchedule-metro-mapped.xml.gz transitSchedule-bus-mapped.xml.gz transitSchedule-final.xml.gz"
```

**最終輸出**:
- `network-with-pt-final.xml.gz` - 完整路網 (car, walk, pt)
- `transitSchedule-final.xml.gz` - 合併的捷運+公車時刻表

---

## 驗證與視覺化

### 統計資訊

```bash
# 路網統計
zcat network-with-pt-final.xml.gz | grep -c '<node '
zcat network-with-pt-final.xml.gz | grep -c '<link '
zcat network-with-pt-final.xml.gz | grep 'modes="pt"' | wc -l

# PT 統計
zcat transitSchedule-final.xml.gz | grep -c '<transitLine'
zcat transitSchedule-final.xml.gz | grep -c '<transitRoute'
zcat transitSchedule-final.xml.gz | grep -c '<departure'
```

### SimWrapper 預覽

將路網轉換為 GeoJSON 預覽：

```bash
python3 -c "
import geopandas as gpd
from matsim import Network

network = Network('network-with-pt-final.xml.gz')
gdf = network.to_gdf()
gdf.to_file('network_preview.geojson', driver='GeoJSON')
"
```

---

## 常見問題 (Troubleshooting)

### 1. PT Mapping 產生過多 artificial links

**原因**: `maxLinkCandidateDistance` 太小

**解決**:
```xml
<param name="maxLinkCandidateDistance" value="300.0"/>  <!-- 捷運加大 -->
<param name="maxTravelCostFactor" value="15.0"/>
```

### 2. Nodes 找不到對應座標

**原因**: Q_RDNODE 欄位名稱不標準

**解決**: 腳本會自動嘗試 `NODEID`, `NODE_ID`, `ID`, `FID`，仍失敗則回報

### 3. Python 環境問題

**檢查依賴**:
```bash
python3 -c "import geopandas; print(geopandas.__version__)"
python3 -c "import shapely; print(shapely.__version__)"
```

---

## OSM 替代方案

如果沒有 shapefile，可使用 OSM 資料：

```bash
# 使用 pt2matsim 從 OSM 生成路網
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  disaster_bbox_complete.pbf \
  network_osm.xml \
  osm_config.xml
```

---

## 參考資料

- **MATSim 文檔**: [matsim.org](https://matsim.org)
- **pt2matsim**: [github.com/matsim-org/pt2matsim](https://github.com/matsim-org/pt2matsim)
- **GTFS 規範**: [gtfs.org](https://gtfs.org)
- **Taiwan GIS**: 國土測繪圖資服務雲
