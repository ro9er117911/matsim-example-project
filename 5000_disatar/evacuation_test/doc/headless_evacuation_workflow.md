# 淡水海嘯撤離模擬 Headless Workflow

這份文件記錄如何不使用 GUI，直接透過終端機執行 MATSim Evacuation 模組的完整流程。

---

## 快速開始 - 淡水→萬隆多區域撤離

### 執行概要

| 項目 | 值 |
|-----|---|
| 起點 | 淡水危險區 (25.18, 121.44) |
| 終點 | 萬隆捷運站 (25.001602, 121.539202) |
| 距離 | ~22 km |
| 路網 | 23,070 節點, 52,000 連結 |
| 代理人 | 500 |

### 執行步驟

```bash
# 1. 裁切 OSM (涵蓋淡水到萬隆)
osmium extract -b 121.41,24.97,121.57,25.21 \
  input/tamsui_to_wenshan.osm -o input/tamsui_wanlong_large.osm

# 2. 建立 MATSim 路網
./mvnw exec:java -Dexec.mainClass="org.matsim.project.tools.BuildNetworkFromOsmXml" \
  -Dexec.args="input/tamsui_wanlong_large.osm input/network_large.xml.gz"

# 3. 產生撤離人口 (起點在淡水, 終點萬隆)
python3 tools/generate_evacuation_population.py

# 4. 執行模擬
./mvnw exec:java -Dexec.mainClass="org.matsim.core.controler.Controler" \
  -Dexec.args="config_tamsui_wanlong.xml"
```

### Simwrapper 輸出

```
output/tamsui_wanlong/
├── output_events.xml.gz      (592 KB)
├── output_network.xml.gz     (1.9 MB)
├── output_plans.xml.gz       (67 KB)
└── evacuation_zones.geojson  (危險區 + 安全點)
```

---

## 詳細流程

### 必要工具
- Java JDK 21+
- Maven
- Python 3 (用於資料前處理與 GeoJSON 轉換)
- `osmium-tool` (用於裁切 OSM)

### 目錄結構
```
5000_disatar/evacuation_test/
├── config_evacuation.xml    # 初始設定檔 (指引 scenario generator)
├── input/
│   ├── tamsui_small.osm     # 裁切後的小範圍路網
│   ├── hazard_circle.shp    # 危險區 (WGS84)
│   └── population_wgs84.shp # 人口分布 (WGS84, 含 persons 欄位)
├── output/                  # 輸出目錄
└── tools/                   # Python 工具腳本
```

---

## 2. 資料前處理

### 2.1 準備路網 (OSM)
由於完整路網過大，建議先裁切出模擬範圍 (例如以淡水為中心)。

```bash
# 裁切淡水周邊 (WGS84 bounding box)
osmium extract -b 121.41,25.15,121.47,25.21 \
  input/tamsui_to_wenshan.osm \
  -o input/tamsui_small.osm \
  --overwrite
```

### 2.2 準備 Shapefiles (Python)
使用 Python (`geopandas`) 產生危險區與人口分布。

**關鍵要求：**
1. **座標系統 (CRS)**：必須一致，建議統一使用 **EPSG:4326 (WGS84)**，與 OSM 相同。
2. **人口屬性**：人口 Shapefile 必須包含整數類型的 `persons` 欄位 (舊版文件可能寫 `pop`，但程式碼需要 `persons`)。

```python
# 範例：產生人口 shapefile
import geopandas as gpd
# ... (建立幾何 geometries) ...
gdf = gpd.GeoDataFrame({
    'persons': pd.Series(populations, dtype='int64') # 必須是 int64 且名稱為 persons
}, geometry=geometries, crs='EPSG:4326')
gdf.to_file('input/population_wgs84.shp')
```

---

## 3. 產生場景 (Scenario Generation)

使用 `evacuation-gui` 模組中的 `ScenarioGenerator` 來讀取 OSM 和 Shapefiles，並轉換為 MATSim 格式 (`network.xml.gz`, `population.xml.gz`, `config.xml`)。

**設定檔 (`config_evacuation.xml`) 範例：**
```xml
<grips_config ...>
    <networkFile><inputFile>.../tamsui_small.osm</inputFile></networkFile>
    <evacuationAreaFile><inputFile>.../hazard_circle.shp</inputFile></evacuationAreaFile>
    <populationFile><inputFile>.../population_wgs84.shp</inputFile></populationFile>
    <outputDir><inputFile>.../output/</inputFile></outputDir>
    <!-- 其他參數 -->
</grips_config>
```

**執行指令：**
```bash
cd evacuation-gui
../mvnw exec:java \
  -Dexec.mainClass="org.matsim.evacuationgui.run.ScenarioGenerator" \
  -Dexec.args="../5000_disatar/evacuation_test/config_evacuation.xml"
```

**產出檔案：**
- `output/config.xml`
- `output/network.xml.gz`
- `output/population.xml.gz`

---

## 4. 執行模擬 (Run Simulation)

直接呼叫 MATSim 核心 `Controler` 執行模擬。

**修正 `output/config.xml`：**
由於裁切的路網可能包含無法到達的節點，導致路由檢查失敗，需在設定檔中停用檢查。

1. 修改 `output/config.xml`：
   - 設定 `networkRouteConsistencyCheck` 為 `disable`
   - 設定 `overwriteFiles` 為 `overwriteExistingFiles`

```xml
<module name="routing">
    <param name="networkRouteConsistencyCheck" value="disable" />
</module>
<module name="controler">
    <param name="overwriteFiles" value="overwriteExistingFiles" />
</module>
```

**執行指令：**
```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.core.controler.Controler" \
  -Dexec.args="5000_disatar/evacuation_test/output/config.xml"
```

---

## 5. 結果視覺化 (Simwrapper)

### 5.1 產生 GeoJSON
為了在 Simwrapper 顯示危險區，需將 Shapefile 轉換為 GeoJSON。

```bash
python tools/compute_hazard_metrics.py \
  --hazard input/hazard_circle.shp \
  --output output/output/hazard_zone.geojson
```

### 5.2 啟動 Simwrapper
```bash
simwrapper run --port 8050
```
瀏覽器開啟 `http://localhost:8050` 並導航至輸出目錄即可查看動畫與統計。

---

## 常見問題 (Troubleshooting)

1. **`NullPointerException` at `createPersons`**:
   - 原因：人口 Shapefile 缺少必要欄位。
   - 解法：確保 Shapefile 有 `persons` 欄位 (不是 `pop` 或 `POPULATION`)。

2. **Network empty / No nodes generated**:
   - 原因：危險區 Shapefile 與 OSM 範圍不重疊，或座標系統不一致。
   - 解法：統一使用 WGS84，並確認 shapefile 範圍涵蓋 OSM 路網。

3. **`RuntimeException: Network ... has unreachable links`**:
   - 原因：撤離路網修剪後產生孤島。
   - 解法：在 `config.xml` 中設定 `<param name="networkRouteConsistencyCheck" value="disable" />`。
