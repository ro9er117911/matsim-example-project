# PT Toolchain 功能規格

## 概述

PT (Public Transit) 工具鏈提供從原始 GTFS 資料到可模擬的 MATSim 運輸網路的完整轉換管線。

## 工具清單

### 1. GtfsToMatsim

**用途**: GTFS ZIP 檔案轉換為 MATSim 運輸時刻表和車輛

**輸入**:
- GTFS ZIP 檔案
- MATSim 網路檔案
- 目標座標系統 (預設: EPSG:3826)

**輸出**:
- `transitSchedule.xml` - 運輸時刻表
- `transitVehicles.xml` - 車輛定義
- `population.xml` - 樣本人口 (可選，100 個代理人)
- `network.xml.gz` - 網路副本

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  --gtfsZip <path> \
  --network <path> \
  --outDir <path> \
  --targetCRS <crs> \
  --sample <selector>
```

**參數**:
- `--gtfsZip` (必要): GTFS ZIP 檔案路徑
- `--network` (必要): MATSim 網路檔案
- `--outDir` (必要): 輸出目錄
- `--targetCRS` (選用): 目標座標系統，預設 EPSG:3826
- `--sample` (選用): 取樣策略，預設 dayWithMostTrips

**功能特點**:
- 自動解壓 GTFS 到臨時目錄 (UUID-based)
- 呼叫 pt2matsim 的 Gtfs2TransitSchedule
- 驗證輸入存在性
- 自動生成簡單人口 (home-work-home trips)

**限制**:
- GTFS 必須是有效的 ZIP 格式
- 網路必須預先存在
- 生成的人口為簡化版本 (前兩個站點)

---

### 2. ConvertGtfsCoordinates

**用途**: 轉換 GTFS CSV 檔案中的座標到投影座標系統

**支援檔案類型**:
- `stops` - stops.txt (stop_lat, stop_lon)
- `shapes` - shapes.txt (shape_pt_lat, shape_pt_lon)

**輸入**:
- 檔案類型 (stops 或 shapes)
- 輸入 CSV 檔案
- 輸出 CSV 檔案
- 目標 CRS

**輸出**:
- 新 CSV 檔案，包含原始欄位 + 投影座標欄位
- 新欄位命名: `{base}_x_{CRS}`, `{base}_y_{CRS}`
- 例如: `stop_x_EPSG3826`, `stop_y_EPSG3826`

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.ConvertGtfsCoordinates \
  <type> <input> <output> <targetCRS>

# 範例
ConvertGtfsCoordinates stops \
  gtfs/stops.txt \
  gtfs/stops_projected.txt \
  EPSG:3826
```

**使用時機**:
- GTFS 使用 WGS84 (lat/lon)，但網路使用投影座標
- pt2matsim 轉換前需要預處理座標
- 需要在 GIS 工具中查看 GTFS 資料

---

### 3. MergeGtfsSchedules

**用途**: 合併多個 MATSim 運輸時刻表和車輛檔案

**輸入**:
- 多組時刻表和車輛檔案 (成對)
- 輸出時刻表路徑
- 輸出車輛路徑

**輸出**:
- 合併的 `transitSchedule.xml`
- 合併的 `transitVehicles.xml`

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.MergeGtfsSchedules \
  <outputSchedule> <outputVehicles> \
  <schedule1> <vehicles1> \
  <schedule2> <vehicles2> \
  ...
```

**ID 前綴策略**:
- 從檔案父目錄名稱衍生前綴
- 例如: `tp_metro_gtfs_small/transitSchedule.xml` → 前綴 `tp_metro_gtfs_small_`
- 防止 ID 衝突

**合併元素**:
- ✅ 運輸站點設施 (座標、連結、屬性)
- ✅ 運輸線和路線 (網路路線)
- ✅ 路線站點 (偏移量、上下車設定)
- ✅ 發車班次 (車輛分配)
- ✅ 車輛類型 (容量、尺寸)
- ✅ 車輛實例 (類型對應)

**使用情境**:
- 合併不同運營商的 GTFS (例如: 捷運 + 公車)
- 合併不同路線的時刻表 (例如: 藍線 + 綠線)
- 建立多模式運輸場景

---

### 4. PrepareNetworkForPTMapping

**用途**: 清理和準備網路以進行 PT 對應

**輸入**:
- 輸入網路檔案
- 輸出網路檔案

**處理步驟**:
1. 確保所有 subway 連結有 'pt' mode
2. 執行 `NetworkUtils.cleanNetwork()` 移除未連接元件
3. 回報統計數據

**輸出**:
- 清理後的網路
- 主控台統計報告:
  - 原始 vs 清理後連結/節點數
  - pt 和 subway mode 的連結數
  - 所有發現的運輸模式

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.PrepareNetworkForPTMapping \
  <inputNetwork> <outputNetwork>
```

**為何需要**:
- pt2matsim PublicTransitMapper 需要強連通網路
- subway 連結缺少 'pt' mode 會導致 "Network is not connected" 錯誤
- 未連接的元件會導致建立人工連結

**重要性**: ⚠️ 必須在 PT mapping 前執行

---

### 5. CleanSubwayNetwork

**用途**: 從多模式網路中提取僅地鐵的網路

**輸入**:
- 多模式網路 (包含 car, pt, subway, 等)
- 輸出網路路徑

**處理邏輯**:
1. 識別所有具有 'subway' 或 'pt' mode 的連結
2. 提取這些連結使用的節點
3. 建立僅包含篩選節點/連結的新網路
4. 標準化所有連結為 `{pt, subway}` modes
5. 執行連通性清理

**輸出**:
- 僅地鐵網路
- 所有連結具有 `modes="pt,subway"`

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.CleanSubwayNetwork \
  <inputNetwork> <outputNetwork>
```

**使用案例**:
- 減少網路大小以加快 PT mapping
- 隔離地鐵系統以單獨處理
- 在簡化網路上除錯 PT mapping 問題

**效能提升**:
- 完整網路: ~1.5 小時 mapping
- 僅地鐵: ~30 分鐘 mapping

---

### 6. PreRoutePt

**用途**: 在模擬開始前預路徑人口中的 PT 腿段

**輸入**:
- 配置檔案 (包含網路、時刻表、人口引用)
- 輸出人口路徑

**處理邏輯**:
1. 啟用 transit 配置
2. 載入場景 (網路 + 時刻表 + 人口)
3. 使用 TripRouter 路徑所有 PT 腿段
4. 將活動分配到網路連結 (XY2Links)
5. 輸出路徑後的人口

**輸出**:
- 人口檔案，PT 腿段已路徑
- PT routes 使用 `experimentalPt1` 格式

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.PreRoutePt \
  <configFile> <outputPopulation>
```

**使用時機**:
- 在完整模擬前測試運輸時刻表
- 除錯 PT 路徑問題
- 建立 warm start 的初始路徑計劃

---

### 7. OsmPbfToXml

**用途**: 轉換 OSM PBF (binary) 格式到 XML 格式

**輸入**:
- OSM PBF 檔案 (.osm.pbf)
- 輸出 XML 路徑 (.osm)

**處理**:
- 使用 Osmosis library
- 自動建立輸出目錄
- 處理大型 PBF 提取

**輸出**:
- OSM XML 檔案 (未壓縮，可能很大 ~1 GB)

**命令列介面**:
```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.OsmPbfToXml \
  <inputPbf> <outputXml>
```

**為何需要**:
- pt2matsim 的 `Osm2MultimodalNetwork` 需要 XML 格式
- PBF 檔案下載較小但必須轉換
- Osmosis (v0.49.2) 已包含在專案依賴中

---

## 完整工作流程

### A. GTFS 到 MATSim 管線

```
GTFS ZIP + OSM 資料
       ↓
[步驟 1: GTFS 轉換]
  → GtfsToMatsim
       ↓
transitSchedule.xml + transitVehicles.xml + population.xml
       ↓
[步驟 2: 座標轉換] (選用)
  → ConvertGtfsCoordinates
       ↓
[步驟 3: 網路準備]
  → OSM PBF → XML (OsmPbfToXml)
  → OSM XML → MATSim 網路 (pt2matsim Osm2MultimodalNetwork)
  → 網路清理 (PrepareNetworkForPTMapping)
       ↓
清理後的網路 + 運輸時刻表
       ↓
[步驟 4: PT Mapping]
  → pt2matsim PublicTransitMapper
       ↓
對應的運輸時刻表 + 包含 PT 的網路
       ↓
[步驟 5: 人口預路徑] (選用)
  → PreRoutePt
       ↓
準備好進行模擬
```

## pt2matsim 整合

### Vendored JAR 資訊

**位置**: `pt2matsim/work/pt2matsim-25.8-shaded.jar`
**大小**: 85 MB (shaded with all dependencies)
**版本**: 25.8
**範圍**: system (in Maven)

### 可用的 pt2matsim 工具

透過 vendored JAR 提供:

1. **Gtfs2TransitSchedule** - 由 GtfsToMatsim 包裝
2. **PublicTransitMapper** - PT mapping 主工具
3. **CreateDefaultPTMapperConfig** - 生成範本配置
4. **CheckMappedSchedulePlausibility** - 驗證對應
5. **Osm2MultimodalNetwork** - OSM → MATSim 網路
6. **CreateDefaultOsmConfig** - 生成 OSM 配置範本

## 配置檔案

### OSM 轉換配置

**位置**: `pt2matsim/work/osm-config-metro.xml`

**關鍵設定**:
```xml
<param name="keepPaths" value="true" />
<param name="keepWaysWithPublicTransit" value="true" />
<param name="outputCoordinateSystem" value="EPSG:3826" />
<param name="maxLinkLength" value="500.0" />
```

**可路徑子網路**:
- car (allowedTransportModes: "car")
- pt (allowedTransportModes: "pt,subway")

**鐵路定義**:
- subway: 80 km/h, modes="pt,subway"
- rail: 160 km/h, modes="rail"
- tram: 40 km/h, modes="pt"

### PT Mapper 配置

**位置**: `pt2matsim/work/ptmapper-config-metro-v4.xml` (最新)

**關鍵參數**:
- `maxLinkCandidateDistance`: 300m (地鐵)
- `nLinkThreshold`: 10-12 (候選連結數)
- `maxTravelCostFactor`: 15.0 (容差)
- `networkRouter`: SpeedyALT (快速演算法)
- `numOfThreads`: 6 (平行處理)

**模式特定設定**:
| 模式 | 距離 | 候選數 | 嚴格度 |
|------|------|--------|--------|
| Subway | 300m | 12 | 最寬鬆 |
| Rail | 250m | 10 | 寬鬆 |
| Tram | 150m | 8 | 中等 |
| Bus | 100m | 6 | 嚴格 |

## 效能指標

| 操作 | 輸入規模 | 時間 | 記憶體 |
|------|----------|------|--------|
| GTFS 轉換 | 小型 feed | <1 分鐘 | 2 GB |
| OSM 轉換 | 台北 (35 MB PBF) | ~5 分鐘 | 8 GB |
| PT Mapping (完整) | 1300 站點 | ~1.5 小時 | 10 GB |
| PT Mapping (僅地鐵) | 1300 站點 | ~30 分鐘 | 10 GB |
| 網路清理 | 63K 連結 | <1 分鐘 | 2 GB |

## 常見問題

### Q: 為何 PT mapping 這麼慢?

**A**:
- 使用 `SpeedyALT` router 而非 `AStarLandmarks`
- 使用 `CleanSubwayNetwork` 減少網路大小
- 增加 `numOfThreads` 到 6-8

### Q: 太多人工連結怎麼辦?

**A**:
- 增加 `maxLinkCandidateDistance` (90→300m)
- 增加 `maxTravelCostFactor` (5.0→15.0)
- 增加 `candidateDistanceMultiplier` (1.6→3.0)

### Q: "Network is not connected" 警告?

**A**:
- 執行 `PrepareNetworkForPTMapping` 確保 PT 連結有 'pt' mode
- 檢查 OSM config 的 routableSubnetworks

## 相關文檔

- 開發指南: `../dev-master/development-guide.md`
- 配置調優: `../research-mve-designer/configuration-tuning-guide.md`
- 場景文檔: `scenario-documentation.md`
