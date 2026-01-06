# 設定檔參考（Network 與 Simulation 分離）

本文件區分 **路網建置設定** 與 **模擬設定**，避免把 network 轉換參數混進 simulation config。完整參考可見專案根目錄的 `defaultConfig.xml`。

---

## 一、設定檔類型總覽

| 類型 | 用途 | 典型檔案 | 執行時機 |
|---|---|---|---|
| 路網建置設定 | OSM/SHP → network | `osm2network-config*.xml` | 一次性建置 |
| PT 映射設定 | schedule → network | `ptmapper-config*.xml` | 每次映射時 |
| 模擬設定 | MATSim 執行 | `config.xml` / `defaultConfig.xml` | 每次模擬 |

---

## 二、路網建置設定（Network Build Config）

### 1) OSM → Network

由 `Osm2MultimodalNetwork` 使用的設定檔控制：
- **道路分類與模式**（car / walk / rail 等）
- **自由流速、容量、車道數**
- **允許的 highway 標籤與過濾條件**

範例執行：

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  input.osm.pbf output/network.xml.gz EPSG:3826 osm2network-config.xml
```

### 2) SHP → Network

`5000_disatar/05_scripts/02_osm_network/convert_shapefile_to_network.py` 內的 `ROAD_CLASS_PARAMS` 決定：
- `freespeed`
- `capacity`
- `lanes`

若道路分類不一致，可在腳本內調整對應表。

---

## 三、PT 映射設定（PublicTransitMapper Config）

PT 映射的核心參數放在 `ptmapper-config.xml`：
- `maxLinkCandidateDistance`
- `nLinkThreshold`
- `maxTravelCostFactor`
- `networkRouter`

詳細參數請見 `docs/03-gtfs-public-transit/public-transit-guide.md`。

---

## 四、模擬設定（config.xml）

`config.xml` 用於 MATSim 執行，核心模組如下：

### 1) Controller
```xml
<module name="controller">
  <param name="lastIteration" value="100"/>
  <param name="outputDirectory" value="./output"/>
  <param name="overwriteFiles" value="deleteDirectoryIfExists"/>
</module>
```

### 2) Global
```xml
<module name="global">
  <param name="coordinateSystem" value="EPSG:3826"/>
  <param name="numberOfThreads" value="4"/>
</module>
```

### 3) Network / Plans
```xml
<module name="network">
  <param name="inputNetworkFile" value="network.xml.gz"/>
</module>

<module name="plans">
  <param name="inputPlansFile" value="population.xml.gz"/>
</module>
```

### 4) Routing
```xml
<module name="routing">
  <param name="networkModes" value="car"/>
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
  </parameterset>
</module>
```

### 5) QSim
```xml
<module name="qsim">
  <param name="mainMode" value="car,pt"/>
  <param name="usingTransitInMobsim" value="true"/>
  <param name="stuckTime" value="10.0"/>
</module>
```

### 6) Transit + SwissRailRaptor
```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="transitScheduleFile" value="transitSchedule.xml.gz"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>
  <param name="transferPenaltyBaseCost" value="0.0"/>
</module>
```

### 7) Scoring（效用函數）
- 調整 `modeParams` 與 `activityParams`
- 若需細部效用解釋，請見 `docs/01-getting-started/algorithm-notes.md`

---

## 五、命令列覆寫範例

```bash
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  config.xml \
  --config:controller.lastIteration 10 \
  --config:controller.outputDirectory output_test
```

---

## 六、常見配置問題

- **CRS 不一致**：確保 network / population / GTFS 都是 EPSG:3826
- **PT 被 teleported**：`routing` 不要加入 `pt` 的 teleportedMode
- **PT 不應出現在 networkModes**：PT 路由由 SwissRailRaptor 處理
