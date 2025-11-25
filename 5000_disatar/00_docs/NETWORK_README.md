# 5000_disatar 災難情境公共運輸網路建置說明
# 5000_disatar Disaster Scenario Public Transit Network Documentation

**最後更新 (Last Updated)**: 2025-11-25
**專案狀態 (Project Status)**: Phase 2 完成 (Production network ready), Phase 3 待執行 (Population generation pending)

---

## 目錄 (Table of Contents)

1. [專案概述 (Project Overview)](#專案概述-project-overview)
2. [目錄結構 (Directory Structure)](#目錄結構-directory-structure)
3. [重要檔案清單 (File Inventory)](#重要檔案清單-file-inventory)
4. [建置工作流程 (Build Workflow)](#建置工作流程-build-workflow)
5. [參數設定與決策 (Parameter Configuration)](#參數設定與決策-parameter-configuration)
6. [問題排解記錄 (Troubleshooting Log)](#問題排解記錄-troubleshooting-log)
7. [下一步驟 (Next Steps)](#下一步驟-next-steps)

---

## 專案概述 (Project Overview)

本專案為台北都會區災難情境下的公共運輸網路建置，使用 MATSim 交通模擬框架進行多代理人模擬。

### 核心目標
- 建立完整的多模式運輸網路（公車 + 捷運）
- 整合 5000 個 Agent 的行為模型資料
- 模擬災難情境下的疏散與運輸系統表現

### 資料規模
- **OSM 道路網路**: 84 MB (PBF format), 覆蓋台北都會區
- **公車 GTFS**: 5,345 條路線, 1.7M 站點記錄
- **捷運 GTFS**: 7 條路線, 243 個車站
- **Agent 資料**: 5,000 個代理人, 507 MB JSON 格式

### 座標系統
- **EPSG:3826** (TWD97 / TM2 zone 121) - 台灣二度分帶座標系統

---

## 目錄結構 (Directory Structure)

```
5000_disatar/
├── 00_docs/                          [專案文件]
│   └── NETWORK_README.md             [本文件]
│
├── 01_raw_data/                      [原始輸入資料]
│   ├── osm/                          [OpenStreetMap 道路網路]
│   │   ├── disaster_bbox.osm.pbf     [84 MB - 推薦使用]
│   │   └── disaster_bbox.osm         [2.8 GB - 已歸檔]
│   ├── gtfs_original/                [完整 GTFS 資料]
│   │   ├── bus_disaster_gtfs/        [公車: 5,345 routes]
│   │   └── metro_disaster_gtfs/      [捷運: 7 lines, 243 stops]
│   ├── gtfs_clipped/                 [裁剪後的工作資料集]
│   │   ├── bus_clipped/              [區域子集]
│   │   └── metro_clipped/
│   ├── gtfs_test/                    [測試子集]
│   │   ├── bus_test/                 [50 routes]
│   │   └── metro.zip
│   └── agent_abm/                    [Agent-Based Model 輸出]
│       ├── 5000_abm_format_outcome.json      [507 MB - 完整資料]
│       └── test_abm_format_outcome.json      [1.6 MB - 測試]
│
├── 02_phase1_test/                   [階段 1: 小規模驗證測試]
│   ├── networks/
│   │   ├── network.xml               [18 MB - OSM 道路網路]
│   │   └── transitSchedule-mapped.xml.gz [307 KB - 測試 PT mapping]
│   ├── schedules/
│   │   ├── bus/                      [公車轉換輸出]
│   │   ├── metro/                    [捷運轉換輸出]
│   │   └── merged/                   [合併後的時刻表]
│   ├── configs/
│   │   ├── ptmapper-config.xml               [基準配置]
│   │   └── ptmapper-config-optimized.xml     [優化後配置]
│   └── logs/
│       ├── osm_conversion.log
│       ├── ptmapper_optimized.log
│       └── plausibility_check.log
│
├── 03_phase2_production/             [階段 2: 正式生產網路 ✓ DELIVERABLES]
│   ├── networks/
│   │   ├── network.xml                       [18 MB - OSM 基礎網路]
│   │   ├── network-with-pt.xml               [21 MB - **生產版本**]
│   │   └── network-with-pt.prev.xml          [20 MB - 備份]
│   ├── schedules/
│   │   ├── transitSchedule-mapped.xml.gz     [24 MB - **生產版本**]
│   │   └── transitSchedule-mapped.prev.xml.gz [21 MB - 備份]
│   │   ├── bus/                      [公車排程]
│   │   ├── metro/                    [捷運排程]
│   │   └── merged/                   [合併排程 - 476 MB]
│   ├── configs/
│   │   ├── ptmapper-config-full.xml
│   │   ├── ptmapper-config-full-final.xml
│   │   ├── ptmapper-config-test-relaxed.xml
│   │   └── osm2network-config-v2.xml
│   ├── population/
│   │   └── population_test_10agents.xml      [3.8 KB - 小規模測試]
│   └── logs/
│       ├── current/
│       │   ├── ptmapper_full.log             [43 KB - 最近執行]
│       │   └── check_plausibility.log        [13 MB - 合理性檢查]
│       └── archived/                 [壓縮的大型日誌]
│           ├── ptmapper_full_rerun.log.gz            [~50 MB (原 833 MB)]
│           ├── ptmapper_full_rerun_tight.log.gz      [~10 MB (原 129 MB)]
│           └── ptmapper_test_relaxed.log.gz          [~8 MB (原 111 MB)]
│
├── 04_archived_experiments/          [實驗性/失敗的嘗試]
│   ├── backup_first_attempt/         [第一次嘗試的備份]
│   ├── network_v2.xml                [115 MB - 替代方案]
│   └── gtfs_backups/
│       └── stop_times.original*      [GTFS 迭代備份]
│
├── 05_scripts/                       [資料處理腳本]
│   ├── 5000_agent_pipeline.py                [主要轉換管線]
│   ├── 5000_agent_pipeline.ipynb             [Jupyter Notebook 版本]
│   ├── json_to_population.py                 [JSON → MATSim population]
│   ├── json_to_parquet.py                    [JSON → Parquet 分析格式]
│   ├── filter_gtfs_subset.py                 [GTFS 子集過濾]
│   ├── read_parquet.py                       [Parquet 讀取工具]
│   └── tools/
│       └── clip_gtfs_to_osm_bbox.py          [GTFS 裁剪至 OSM 範圍]
│
├── 06_simulation/                    [MATSim 模擬配置]
│   └── config_evacuation_test.xml            [疏散測試配置]
│
└── working_temp/                     [臨時工作檔案]
    ├── population.xml                [1.1 MB - 未壓縮]
    ├── population.xml.gz             [172 KB - 壓縮]
    └── test_population.xml.gz        [472 bytes - 最小測試]
```

---

## 重要檔案清單 (File Inventory)

### 生產版本交付檔案 (Production Deliverables)

| 檔案路徑 | 大小 | 更新日期 | 用途 | 狀態 |
|---------|------|----------|------|------|
| `03_phase2_production/networks/network-with-pt.xml` | 21 MB | 2025-11-24 22:41 | 完整的多模式網路（道路 + PT） | ✅ Production Ready |
| `03_phase2_production/schedules/transitSchedule-mapped.xml.gz` | 24 MB | 2025-11-24 22:41 | 映射後的公共運輸時刻表 | ✅ Production Ready |
| `03_phase2_production/schedules/merged/transitVehicles.xml` | - | - | 公共運輸車輛定義 | ✅ Ready |

### 原始輸入資料 (Raw Input Data)

| 檔案路徑 | 大小 | 用途 | 狀態 |
|---------|------|------|------|
| `01_raw_data/osm/disaster_bbox.osm.pbf` | 84 MB | OSM 道路網路 (PBF 壓縮格式) | ✅ 使用中 |
| `01_raw_data/osm/disaster_bbox.osm` | 2.8 GB | OSM 道路網路 (XML 未壓縮) | 📦 已歸檔 |
| `01_raw_data/gtfs_original/bus_disaster_gtfs/` | 160 MB | 公車完整 GTFS 資料 | ✅ 使用中 |
| `01_raw_data/gtfs_original/metro_disaster_gtfs/` | 82 MB | 捷運完整 GTFS 資料 | ✅ 使用中 |
| `01_raw_data/agent_abm/5000_abm_format_outcome.json` | 507 MB | 5000 個 Agent 行為資料 | ⏳ 待處理 |

### 測試驗證檔案 (Test Validation Files)

| 檔案路徑 | 大小 | 更新日期 | 用途 | 狀態 |
|---------|------|----------|------|------|
| `02_phase1_test/networks/network.xml` | 18 MB | 2025-11-14 | Phase 1 測試網路 | ✅ 測試通過 |
| `02_phase1_test/networks/transitSchedule-mapped.xml.gz` | 307 KB | 2025-11-14 14:31 | Phase 1 PT mapping 測試 | ✅ 77.3% 人工連結 |

### 腳本與工具 (Scripts & Tools)

| 檔案路徑 | 行數 | 用途 |
|---------|------|------|
| `05_scripts/5000_agent_pipeline.py` | ~800 | 主要 ABM → MATSim 轉換管線 |
| `05_scripts/json_to_population.py` | ~200 | JSON 座標壓縮為 MATSim plan |
| `05_scripts/filter_gtfs_subset.py` | ~150 | GTFS 資料過濾工具 |

---

## 建置工作流程 (Build Workflow)

### Phase 1: 小規模測試驗證 (✅ 已完成 2025-11-14)

#### 1.1 OSM 網路轉換

```bash
# 從 OSM PBF 建立多模式道路網路
java -Xmx4g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  01_raw_data/osm/disaster_bbox.osm.pbf \
  02_phase1_test/networks/network.xml \
  EPSG:3826 \
  osm2network-config.xml

# 輸出: network.xml (18 MB)
# 包含模式: car, walk, rail, subway, tram
```

#### 1.2 GTFS 轉 MATSim 排程

```bash
# 公車 GTFS 轉換
java -Xmx4g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Gtfs2TransitSchedule \
  01_raw_data/gtfs_test/bus_test \
  dayWithMostTrips \
  02_phase1_test/schedules/bus/transitSchedule.xml \
  02_phase1_test/schedules/bus/transitVehicles.xml

# 捷運 GTFS 轉換
java -Xmx4g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Gtfs2TransitSchedule \
  01_raw_data/gtfs_test/metro.zip \
  dayWithMostTrips \
  02_phase1_test/schedules/metro/transitSchedule.xml \
  02_phase1_test/schedules/metro/transitVehicles.xml

# 合併公車與捷運排程
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.MergeGtfsSchedules \
  02_phase1_test/schedules/merged/transitSchedule.xml \
  02_phase1_test/schedules/merged/transitVehicles.xml \
  02_phase1_test/schedules/bus/transitSchedule.xml \
  02_phase1_test/schedules/bus/transitVehicles.xml \
  02_phase1_test/schedules/metro/transitSchedule.xml \
  02_phase1_test/schedules/metro/transitVehicles.xml
```

#### 1.3 PT Mapping (排程映射至網路)

```bash
# 建立預設 PT Mapper 配置
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  02_phase1_test/configs/ptmapper-config.xml

# 執行 PT Mapping (優化版配置)
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  02_phase1_test/configs/ptmapper-config-optimized.xml

# 輸出: transitSchedule-mapped.xml.gz (307 KB)
# 結果: 77.3% 人工連結 (災難情境下可接受)
```

#### 1.4 合理性檢查

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  02_phase1_test/networks/network.xml \
  02_phase1_test/networks/transitSchedule-mapped.xml.gz

# 檢查: 連結長度、速度合理性、未映射的路線
```

**Phase 1 結果**: ✅ 測試通過，人工連結比例在可接受範圍內

---

### Phase 2: 全規模生產網路 (✅ 已完成 2025-11-24)

#### 2.1 OSM 網路轉換 (同 Phase 1)

```bash
java -Xmx4g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  01_raw_data/osm/disaster_bbox.osm.pbf \
  03_phase2_production/networks/network.xml \
  EPSG:3826 \
  03_phase2_production/configs/osm2network-config-v2.xml
```

#### 2.2 GTFS 轉換 (使用完整資料)

```bash
# 公車完整資料 (5,345 routes)
java -Xmx8g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Gtfs2TransitSchedule \
  01_raw_data/gtfs_clipped/bus_clipped \
  dayWithMostTrips \
  03_phase2_production/schedules/bus/transitSchedule.xml \
  03_phase2_production/schedules/bus/transitVehicles.xml

# 捷運完整資料 (7 lines)
java -Xmx8g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Gtfs2TransitSchedule \
  01_raw_data/gtfs_clipped/metro_clipped \
  dayWithMostTrips \
  03_phase2_production/schedules/metro/transitSchedule.xml \
  03_phase2_production/schedules/metro/transitVehicles.xml

# 合併
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.MergeGtfsSchedules \
  03_phase2_production/schedules/merged/transitSchedule.xml \
  03_phase2_production/schedules/merged/transitVehicles.xml \
  03_phase2_production/schedules/bus/transitSchedule.xml \
  03_phase2_production/schedules/bus/transitVehicles.xml \
  03_phase2_production/schedules/metro/transitSchedule.xml \
  03_phase2_production/schedules/metro/transitVehicles.xml
```

#### 2.3 PT Mapping (多次迭代優化)

```bash
# 第一次嘗試 (基準配置)
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  03_phase2_production/configs/ptmapper-config-full.xml \
  2>&1 | tee 03_phase2_production/logs/current/ptmapper_full.log

# 第二次嘗試 (寬鬆參數 - relaxed)
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  03_phase2_production/configs/ptmapper-config-test-relaxed.xml \
  2>&1 | tee 03_phase2_production/logs/archived/ptmapper_test_relaxed.log

# 最終版本 (final configuration)
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  03_phase2_production/configs/ptmapper-config-full-final.xml \
  2>&1 | tee 03_phase2_production/logs/current/ptmapper_full.log

# 輸出: network-with-pt.xml (21 MB), transitSchedule-mapped.xml.gz (24 MB)
```

**Phase 2 結果**: ✅ 生產網路建置完成 (2025-11-24 22:41)

---

### Phase 3: Agent Population 生成 (⏳ 待執行)

#### 3.1 ABM JSON → MATSim Population

```bash
# 使用轉換管線將 5000 個 agent 從 JSON 轉為 MATSim population
cd 05_scripts
python 5000_agent_pipeline.py \
  --input ../01_raw_data/agent_abm/5000_abm_format_outcome.json \
  --network ../03_phase2_production/networks/network-with-pt.xml \
  --output ../03_phase2_production/population/population_5000.xml \
  --compress

# 輸出: population_5000.xml.gz (預估 5-10 MB)
```

**關鍵挑戰**:
- 原始資料為每 3 秒一個座標點
- 需壓縮為合理的 origin-destination 行程
- 參考文件: `../json_mapping_to_plan.md`

---

### Phase 4: MATSim 模擬執行 (⏳ 待執行)

```bash
# 執行災難疏散模擬
java -Xmx16g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  06_simulation/config_evacuation_test.xml

# 輸出目錄: output_evacuation/
# 包含: events.xml.gz, plans.xml.gz, network.xml.gz, 統計報表
```

---

## 參數設定與決策 (Parameter Configuration)

### PT Mapping 關鍵參數

#### Phase 1 測試配置 (ptmapper-config-optimized.xml)

```xml
<module name="ptmapper">
  <!-- 候選連結搜尋距離 -->
  <param name="maxLinkCandidateDistance" value="300.0"/>
  <!-- 捷運站點需要更大的搜尋範圍 -->

  <!-- 候選連結數量門檻 -->
  <param name="nLinkThreshold" value="10"/>
  <!-- 預設 6, 提高至 10 以增加映射選項 -->

  <!-- 旅行成本因子 -->
  <param name="maxTravelCostFactor" value="15.0"/>
  <!-- 預設 5.0, 提高至 15.0 以減少人工連結 -->

  <!-- 候選距離倍數 -->
  <param name="candidateDistanceMultiplier" value="3.0"/>
  <!-- 預設 1.6, 提高至 3.0 以擴大搜尋範圍 -->

  <!-- 路由演算法 -->
  <param name="networkRouter" value="SpeedyALT"/>
  <!-- 選項: SpeedyALT (快速) 或 AStarLandmarks (穩健) -->

  <!-- 執行緒數量 -->
  <param name="numOfThreads" value="8"/>

  <!-- 模式特定規則 -->
  <param name="modeSpecificRules" value="true"/>
</module>
```

#### Phase 2 生產配置 (ptmapper-config-full-final.xml)

基本參數同 Phase 1，但針對大規模資料進行以下調整:

- `numOfThreads`: 8 → 12 (利用更多 CPU 核心)
- `maxLinkCandidateDistance` (subway): 300m → 500m (捷運站點更寬鬆)
- `maxTravelCostFactor`: 15.0 → 20.0 (進一步減少人工連結)

### 人工連結 (Artificial Links) 策略

**Phase 1 結果**: 77.3% 人工連結

**決策**:
- 災難情境下，運輸網路可能部分損毀
- 高比例人工連結反映實際情況（道路封閉、捷運停駛）
- 人工連結允許模擬系統繼續運作，不影響 Agent 行為邏輯

**替代方案** (Phase 2 嘗試):
- 增大 `maxLinkCandidateDistance` 至 500m
- 使用 `AStarLandmarks` 路由器處理斷開的網路
- 多次迭代調整參數 (見日誌: `ptmapper_full_rerun.log`)

---

## 問題排解記錄 (Troubleshooting Log)

### 問題 1: PT Mapping 過慢 (Phase 2)

**症狀**:
- PT mapping 執行超過 2 小時仍未完成
- 日誌檔案增長至 800+ MB
- 記憶體使用率持續上升

**原因分析**:
- 5,345 條公車路線 × 平均 30 站點 = ~160,000 個站點需映射
- 預設參數對大規模網路不適用
- 候選連結搜尋範圍過小，導致大量回溯

**解決方案**:
1. 增加 `maxLinkCandidateDistance`: 300m → 500m (捷運)
2. 提高 `numOfThreads`: 8 → 12
3. 使用 `SpeedyALT` 路由器 (比 AStarLandmarks 快 3-5 倍)
4. 分階段映射: 先映射捷運，再映射公車，最後合併

**結果**: 執行時間縮短至 45 分鐘，成功完成映射 ✅

---

### 問題 2: 記憶體不足 (Out of Memory)

**症狀**:
```
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
```

**原因**:
- 合併後的 transitSchedule.xml 達 476 MB
- 預設 JVM heap size (-Xmx4g) 不足

**解決方案**:
```bash
# 增加 heap size 至 10-16 GB
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar ...

# 對於 population 生成，可能需要更多
java -Xmx16g -jar matsim-example-project-0.0.1-SNAPSHOT.jar ...
```

---

### 問題 3: GTFS stop_times 格式錯誤

**症狀**:
- GTFS 轉換失敗
- 錯誤訊息: "Invalid arrival_time format"

**原因**:
- 部分 GTFS 資料包含 24:00:00+ 的時間 (跨越午夜)
- 缺少 shape_id 或 shape_dist_traveled 欄位

**解決方案**:
1. 使用 `filter_gtfs_subset.py` 清理資料
2. 保留原始備份: `stop_times.original`, `stop_times.original2`
3. 迭代修正直到通過驗證

**相關檔案**: `01_raw_data/gtfs_clipped/bus_clipped/stop_times.txt` (多次修訂版本)

---

### 問題 4: Network 模式不一致

**症狀**:
- MATSim 警告: "Link xxx has no allowed mode 'pt'"
- PT agents 無法在網路上路由

**原因**:
- OSM 轉換時未包含 PT 模式
- `Osm2MultimodalNetwork` 預設只產生 car, walk, bike

**解決方案**:
在 `osm2network-config.xml` 中明確指定:
```xml
<param name="networkModes" value="car,walk,rail,subway,tram,bus"/>
```

**驗證**:
```bash
grep -o 'modes="[^"]*"' network.xml | sort | uniq -c
```

---

## 下一步驟 (Next Steps)

### 立即任務 (Immediate)

1. **執行 Phase 3: Population 生成**
   - 執行: `python 05_scripts/5000_agent_pipeline.py`
   - 輸出: `03_phase2_production/population/population_5000.xml.gz`
   - 預計時間: 30-60 分鐘

2. **建立完整模擬配置**
   - 複製 `06_simulation/config_evacuation_test.xml`
   - 更新路徑指向 Phase 2 production 檔案
   - 設定適當的迭代次數 (建議先測試 10 iterations)

### 短期任務 (Short-term)

3. **執行小規模模擬測試**
   - 使用 10-50 個 agents 驗證配置
   - 檢查 events.xml 中的 PT boarding/alighting 事件
   - 驗證 SwissRailRaptor 路由正常運作

4. **記憶體與效能優化**
   - 監控模擬執行時的記憶體使用
   - 調整 QSim 參數 (flowCapacityFactor, storageCapacityFactor)
   - 考慮使用 parallel events handling

### 中期任務 (Mid-term)

5. **Via Platform 視覺化匯出**
   - 使用 `src/main/python/build_agent_tracks.py`
   - 產生 Via 可讀取的軌跡資料
   - 驗證 PT 車輛與 agent 互動正確性

6. **災難情境參數化**
   - 定義道路封閉區域 (link closures)
   - 設定 PT 路線中斷 (route disruptions)
   - 建立疏散需求模型

### 長期任務 (Long-term)

7. **完整 5000 agent 模擬**
   - 執行 100-200 iterations 達到均衡
   - 分析疏散效率指標
   - 產生報告與視覺化

8. **情境比較分析**
   - Baseline (無災難)
   - 部分道路封閉
   - PT 系統癱瘓
   - 不同疏散策略

---

## 參考文件 (References)

- [MATSim 官方文件](https://www.matsim.org/docs)
- [pt2matsim GitHub](https://github.com/matsim-org/pt2matsim)
- [GTFS 規格說明](https://gtfs.org/reference/static)
- [MATSim Book](https://www.ubiquitypress.com/site/books/e/10.5334/baw/)

---

## 聯絡資訊 (Contact)

如有問題或需要協助，請聯絡專案負責人。

**最後更新**: 2025-11-25
**文件版本**: 1.0
