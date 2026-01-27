# GTFS PT Mapping 錯誤歷程與排除指南

本文件系統性地整理了專案執行以來遭遇的**所有重大錯誤**。除了標準的錯誤訊息外，也包含了當時的**發生情境**、**診斷過程**與**引用日誌**，供後續維護參考。

參考來源目錄：
- `archive/old_docs/PT_ERROR_HANDLING.md`
- `archive/working_journal/` (2025-11-03, 2025-11-06, 2025-11-17)

---

## 1. 嚴重架構錯誤 (Simulation Critical)

這些錯誤會導致模擬可以執行，但結果完全錯誤（如飛天公車）。

### 1.1 "Straight-Line Teleportation" (直線傳輸)
> **引用日誌**: [2025-11-03-PT-SwissRailRaptor-Fix.md](file:///Users/ro9air/matsim-example-project/archive/working_journal/2025-11-03-PT-SwissRailRaptor-Fix.md)

| 屬性 | 內容 |
|:---|:---|
| **現象** | 代理人從上車站「瞬間移動」到下車站，未經過任何中間站點。事件紀錄 (Events) 只有 `PersonEntersVehicle` 和 `PersonLeavesVehicle`，中間缺少 `VehicleArrivesAtFacility` 序列。 |
| **錯誤配置** | `config.xml` 中錯誤地為 `pt` 模式設定了 `teleportedModeParameters`。這導致 MATSim 繞過 SwissRailRaptor，改用 Teleportation 邏輯。 |
| **解決方案** | 1. **移除** `pt` 的 teleported 參數。<br> 2. **啟用** `swissRailRaptor` 模組，並設定 `transferPenaltyBaseCost=0.0` (以符合最短路徑邏輯)。 |
| **驗證指令** | `gunzip -c output_events.xml.gz | grep "VehicleArrivesAtFacility" | grep "pt_BL"` (確認中間站點有被訪問) |

---

## 2. 進程卡死與效能檢測 (Performance & Stalls)

### 2.1 "Infinite Loop / 38-Hour Stall" (進程卡死)
> **引用日誌**: [2025-11-06-PT-Mapper-Fix.md](file:///Users/ro9air/matsim-example-project/archive/working_journal/2025-11-06-PT-Mapper-Fix.md)

| 屬性 | 內容 |
|:---|:---|
| **現象** | `PublicTransitMapper` 運行超過 38 小時未完成，Log 停滯。CPU 滿載但無進度。 |
| **根因** | 路網不連通 (Network Gaps)。OSM 資料範圍 (Lat 25.02+) 比 GTFS 範圍 (Lat 24.95+) 小，導致板南線西段 32 個站點落在**路網邊界之外**。SpeedyALT 路由算法在嘗試尋找路徑時陷入無限迴圈或極長搜尋。 |
| **解決方案** | **策略 A (快速修復)**: 設定 `maxLinkCandidateDistance = 0.0`，強制生成 **Artificial Links** (虛擬路段)。映射時間從 >96 小時縮短至 **1 分鐘**。<br> **策略 B (正規解法)**: 使用 `filter_gtfs_to_osm_bounds.py` 裁切 GTFS，或擴大 OSM 下載範圍。 |

---

## 3. 資料整合與驗證錯誤 (Data Integrity)

### 3.1 "Missing stop_times.txt" (資料集不可用)
> **引用日誌**: [2025-11-17-GTFS-Merge-Analysis.md](file:///Users/ro9air/matsim-example-project/archive/working_journal/2025-11-17-GTFS-Merge-Analysis.md)

| 屬性 | 內容 |
|:---|:---|
| **現象** | 下載的 `gtfs_tw_v5` 資料集無法生成時刻表。 |
| **根因** | 該官方資料集**缺少 `stop_times.txt`** 檔案。這是 GTFS 標準中定義時刻表的必要檔案，沒有它 MATSim 無法運作。 |
| **解決方案** | 放棄該資料集，改用 `tp_metro_gtfs` (包含 100,015 筆 stop_times) 或直接從 PTX API 抓取。開發 `validate_gtfs.py` 以在流程早期偵測此類缺失。 |

### 3.2 "Vehicle not found"
> **引用來源**: `archive/old_docs/PT_ERROR_HANDLING.md`

| 屬性 | 內容 |
|:---|:---|
| **現象** | `ERROR: Vehicle tr_1 not found in VehicleContainer` |
| **根因** | `transitVehicles.xml` 未正確載入，或 Config 中的 `vehicles` 模組未指向該檔案。 |
| **解決方案** | 確認 Config：<br> `<module name="vehicles"><param name="vehiclesFile" value="transitVehicles.xml" /></module>` |

---

## 4. 路網映射常見錯誤 (Mapping Errors)

### 4.1 "No route found"
| 屬性 | 內容 |
|:---|:---|
| **現象** | `ERROR: No route found from stopFacility BL12_UP to BL14_UP` |
| **根因** | 路網連通性不足 (如單行道限制)，或站點投影位置過遠。 |
| **特殊解法** | 若無法修復路網，可啟用 `strictLinkRule=false` (允許公車行駛一般道路) 或增加 `maxTravelCostFactor` (允許繞路)。 |

### 4.2 "Artificial Links Warning"
| 屬性 | 內容 |
|:---|:---|
| **訊息** | `WARN: Route requires artificial links (stops not connected)` |
| **嚴重性** | **低 (Low)**。本專案早期因為路網破碎，有 87.6% 的路線依賴 artificial links。這不影響模擬執行，只是路徑會變成直線。 |

---

## 5. JVM 與資源錯誤

### 5.1 "OutOfMemoryError: Java heap space"
| 屬性 | 內容 |
|:---|:---|
| **現象** | 程式啟動後直接崩潰。 |
| **解決方案** | 調整 JAVA_OPTS。對於台北全路網 (270k links + 400 routes)，建議至少分配 **12GB**，理想 **24GB**。使用 `-Xmx24g` 參數。 |

---

## 6. 工具與腳本對照表

| 錯誤類型 | 推薦使用的診斷工具/腳本 | 位置 |
|:---|:---|:---|
| **進程卡死** | `monitor_pt_mapping.sh` | `5000_disatar/.../monitor_pt_mapping.sh` |
| **資料缺失** | `validate_gtfs.py` | `src/main/python/validate_gtfs.py` |
| **路網斷點** | `diagnose_network_gaps.py` | `5000_disatar/.../diagnose_network_gaps.py` |
| **合併衝突** | `merge_gtfs.py` | `src/main/python/merge_gtfs.py` |

---
*最後更新: 2026-01-14*
