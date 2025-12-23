# MATSim Example Project — Single Source of Truth (SSoT)

> Audience: data scientists / engineers with 交通模擬（OTP 等）背景、但沒碰過 MATSim。
> If anything conflicts with other docs, treat **this file** as the canonical source and update it first.

---

## 1) MATSim 的心智模型

| OTP / routing world | MATSim world | Notes |
|---|---|---|
| Routing request | **Plan** (活動 + legs) | MATSim 需要完整的日行程 (population.xml)，不是單次路徑查詢。 |
| Graph / street network | **network.xml(.gz)** | 所有模式都在同一張 network，以 modes 控制可走性。 |
| GTFS feed | **transitSchedule + transitVehicles** | GTFS 需轉換、合併、再 map 到 network。 |
| Deterministic shortest path | **Agent-based simulation** | 會出現壅塞、排隊、stuck 等現象；輸出是 events。 |
| Itinerary output | **events / trips / plans** | 事件流是主要分析來源。 |

**MATSim 必備檔案 (最小集合)**
- `network.xml(.gz)`：路網 + modes
- `transitSchedule.xml(.gz)` + `transitVehicles.xml`：PT
- `population.xml(.gz)`：代理人計畫
- `config.xml`：串起全部輸入 + 模擬參數
- `changeEvents.xml`（選用）：time-variant network（災害封路）

---

## 2) 專案地圖（唯一真相）

```
matsim-example-project/
├── README.md                         # 專案簡介
├── PROJECT_WIKI.md                   # ✅ 單一真相 (this file)
├── docs/                             # 深度文件 (架構/配置/GTFS/PT/分析)
├── src/main/java/                    # Java 進入點與工具
├── src/main/python/                  # 通用 Python 分析/轉換/視覺化
├── scripts/                          # 執行/實驗/運維腳本
├── tools/                            # 分析與 SimWrapper pipeline 工具
├── scenarios/                        # 小型/基準場景 (equil/corridor 等)
├── pt2matsim/                        # GTFS 轉換工具 (JAR)
├── 5000_disatar/                     # 災難撤離專案 (5000 agents) ✅
│   ├── 00_docs/                      # 災難專案文件 (NETWORK_README 等)
│   ├── 01_raw_data/                  # OSM/GTFS/ABM 原始資料
│   ├── 03_phase2_production/         # 生產級 network + schedule
│   ├── 05_scripts/                   # ABM → MATSim pipeline
│   └── 05_combined_evac/             # 災難撤離模擬 configs + tools
└── output_*/                         # 模擬輸出 (本地測試)
```

---

## 2.5) 環境與依賴 (最低需求)

- Java 21 + Maven (`./mvnw`)：建置與執行 MATSim
- Python 3.10+：分析/轉換工具（建議用 `poetry install` 管理依賴）
- Node.js：SimWrapper 視覺化 (`npx simwrapper serve`)
- Optional: `osmium-tool`（OSM 萃取/裁剪，見 `5000_disatar/05_combined_evac/WORKFLOW.md`）

---

## 3) 新城市災難撤離模擬：Golden Path

### Step 0 — 決定座標系統與範圍
- **座標系統 (CRS)** 必須一致（network / population / GTFS / hazard）。
- 台北場景使用 `EPSG:3826 (TWD97)`；新城市請選擇**可用的投影座標**。
- 設定 `config.xml` → `global.coordinateSystem`。

### Step 1 — 準備輸入資料
必備：
- OSM (道路)
- GTFS (bus/metro/rail)
- Population (ABM/OD/合成)
- 災害資料 (淹水深度 / 海岸線 / 封路區域)

### Step 2 — 建路網 (OSM → MATSim)
- **pt2matsim JAR** 是主工具（見 `pt2matsim/`）。
- 參考 `5000_disatar/00_docs/NETWORK_README.md` 的 Phase 1/2 指令。
- 常見修正：
  - `scripts/fix_network_capacity.py`：修正 0 capacity link
  - `tools/merge_short_links.py`：合併超短 links
  - `scripts/clean_car_components.py`：保留最大 car SCC
  - `scripts/make_subway_exclusive.py`：subway-only network

### Step 3 — GTFS 前處理與合併
- 裁剪：
  - `scripts/clip_gtfs_scientific.py`（lat/lon bounds + 去除無效 trips）
  - `tools/clip_gtfs_bbox.py`（EPSG:3826 bbox）
- 驗證：`src/main/python/validate_gtfs.py`
- 合併：`src/main/python/merge_gtfs.py`
- 映射：pt2matsim `PublicTransitMapper`（configs 在 `5000_disatar/03_phase2_production/configs/`）

### Step 4 — 產生人口 (population.xml)
- **從 ABM JSON**：`5000_disatar/05_scripts/json_to_population.py`
- **合成測試**：`5000_disatar/05_scripts/generate_evacuation_population.py`
- **擴量**：`5000_disatar/05_scripts/augment_population.py`
- 核心概念：不要用「每 3 秒一個 activity」(參考 `5000_disatar/00_docs/json_mapping_to_plan.md`)。

### Step 5 — 交通計畫驗證
- 路徑可達性檢查 + car→pt 轉換：
  - `5000_disatar/05_scripts/validation/validate_population_routes.py`
- 快速格式檢查：
  - `tools/validate-agent-journey.sh`
  - `src/main/python/validate_population.py`

### Step 6 — 災害封路 / 時變路網
- 產生 `changeEvents.xml`：
  - `5000_disatar/05_combined_evac/tools/generate_change_events_depth.py`（淹水深度）
  - `5000_disatar/05_combined_evac/tools/generate_change_events.py`（海岸線距離）
- 產生視覺化：
  - `5000_disatar/05_combined_evac/tools/generate_closed_links_geojson.py`
  - `5000_disatar/05_combined_evac/tools/network_to_geojson.py`

### Step 7 — 組好 config
- 在 `config.xml` 內指定：
  - `network.inputNetworkFile`
  - `plans.inputPlansFile`
  - `transitScheduleFile` / `vehiclesFile`
  - `network.inputChangeEventsFile` + `network.timeVariantNetwork=true`
- 災難案例常見設定：
  - PT 可能使用 teleportation：`transit.usingTransitInMobsim=false`

### Step 8 — 執行模擬
- 快速執行（含 SimWrapper 分析）：
  - `scripts/run_simulation_with_via_export.sh <config.xml>`
- 背景長跑：
  - `scripts/run_simulation.sh <config.xml>`
- 災難專案 baseline：
  - `5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh`
  - 詳情：`5000_disatar/05_combined_evac/WORKFLOW.md`

### Step 9 — 產出分析與視覺化
- SimWrapper dashboard：`tools/run_dashboard_pipeline.sh <output_dir>`
- 壅塞瓶頸：`python -m src.main.python.bottleneck_analysis.analyze_bottlenecks --output-dir <output>`
- Via / 軌跡輸出：`src/main/python/build_agent_tracks.py`
- 速度 / stuck：`tools/analyze_agent_speeds.py`, `tools/generate_stuck_agents_csv.py`
- Flowmap：`tools/generate_flowmap_data.py`

---

## 4) 現有場景快速上手

**Build**
```bash
./mvnw clean package
```

**最小測試 (equil)**
```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml
```

**災難撤離 (5000 agents)**
```bash
scripts/run_simulation_with_via_export.sh 5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

---

## 5) 腳本 / 工具總覽（何時用）

### scripts/（執行與實驗）
- `scripts/run_simulation_with_via_export.sh`：推薦主入口，含 SimWrapper 後處理
- `scripts/run_simulation.sh`：背景跑（可搭配 `MATSIM_MEMORY=16g`）
- `scripts/run_analysis.sh`：對 output 進行速度分析 + dashboard YAML
- `scripts/run_experiment_100k.sh`：100k 情境變體實驗
- `scripts/run_100_agents_simulation.sh`：小型 smoke test + Via export
- `scripts/run_pt_test_with_timeout.sh`：PT pipeline 快速檢查
- `scripts/monitor_resources.sh`：記錄 CPU / RAM
- `scripts/EXPORT_VIA_COMMAND.sh`：Via 輸出
- `scripts/clip_gtfs_scientific.py`：災難場景 GTFS 裁剪 + 無效 trips 過濾
- `scripts/merge_populations.py`：產生更豐富的 population（equil）
- `scripts/fix_network_capacity.py`：修正 0 capacity
- `scripts/clean_car_components.py`：保留最大 car SCC
- `scripts/make_subway_exclusive.py`：subway-only network + PCE
- `scripts/generate_travel_time_comparison.py`：補齊 SimWrapper travel time dashboard
- `scripts/setup_remote_server.sh` / `sync_to_server.sh` / `sync_from_server.sh` / `upload_data_once.sh`：遠端同步

### tools/（分析與視覺化管線）
- `tools/run_dashboard_pipeline.sh`：完整 SimWrapper pipeline
- `tools/generate_dashboard_yamls.py`：產生 dashboard YAML
- `tools/generate_flowmap_data.py`：生成 TAZ + OD flows
- `tools/generate_stuck_agents_csv.py`：stuck agents 統計
- `tools/analyze_agent_speeds.py`：慢速 link 診斷
- `tools/population_to_shapefile.py`：population → shapefile (evacuation-gui)
- `tools/create_evacuation_zones.py`：快速產生撤離區域/人口 shapefile
- `tools/create_500m_test_shp.py`：500m 測試 shapefile
- `tools/clip_gtfs_bbox.py`：GTFS 依 EPSG:3826 bbox 裁剪
- `tools/merge_short_links.py`：合併短 link
- `tools/cleanup_iters.sh`：清理 ITERS 節省硬碟
- `tools/find-nearest-stop.sh`：查最近 PT stop
- `tools/validate-agent-journey.sh`：population 與 network/schedule 檢查

### src/main/python/（通用 Python 工具）
- `build_agent_tracks/`：事件/計畫 → 軌跡（含 Activity 匹配）
- `bottleneck_analysis/`：瓶頸分析 + GeoJSON
- `visualization/vehicle_metro_webpage.py`：產生 metro vs car 地圖
- `merge_gtfs.py`：GTFS 合併
- `validate_gtfs.py`：GTFS 檢查
- `validate_population.py`：population 格式檢查
- `generate_test_population_*.py`：測試人口
- `tools/xml_gz_converter.py`：XML ↔ GZ 轉換
- `README_events_converter.md`：events → JSON/Parquet 說明

### 5000_disatar/05_scripts/（災難專案資料管線）
- `json_to_population.py`：ABM JSON → population.xml.gz
- `events_to_json_parquet.py`：events → JSON/Parquet（含路徑重建）
- `events_to_abm_parquet.py`：events → ABM 友善格式
- `json_to_parquet.py` / `read_parquet.py`：格式轉換
- `augment_population.py`：擴量 + jitter
- `generate_evacuation_population.py`：快速合成 evacuation population
- `create_population_shapefile.py`：人口 → shapefile
- `validate_population_routes.py`：路徑驗證 + car→pt
- `validate_agent_outputs.py` / `validate_population_routes.py`：輸出檢查
- `filter_gtfs_subset.py`：GTFS 子集
- `validation/`：完整 route validator 模組

### 5000_disatar/05_combined_evac/tools/（災害事件產生）
- `generate_change_events_depth.py`：淹水深度 → changeEvents
- `generate_change_events.py`：海岸線距離 → changeEvents
- `generate_change_events_moderate.py`：中度封路事件
- `network_to_geojson.py`：network → WGS84 GeoJSON
- `generate_closed_links_geojson.py`：封路視覺化
- `generate_zone_polygons.py` / `generate_hex_zones.py`：區域多邊形/hex

---

## 6) 輸出與分析結果位置

典型輸出目錄 (`output_*`) 內常見檔案：
- `output_events.xml.gz`：事件流（主要分析來源）
- `output_network.xml.gz`：輸出網路
- `output_trips.csv.gz`：trip summary
- `scorestats.csv` / `modestats.csv`
- `analysis/`：SimWrapper 需要的 dashboard / CSV / AVRO

啟動 SimWrapper：
```bash
npx simwrapper serve --port 8000
```

---

## 7) 相關深入文件（需要再看）

- `docs/README.md`：完整文件索引
- `docs/03-public-transit/public-transit-guide.md`：GTFS → MATSim
- `docs/08-configuration/configuration-reference.md`：config 參數
- `docs/05-simulation/simulation-guide.md`：模擬流程
- `docs/07-analysis/output-analysis.md`：分析
- `defaultConfig.xml`：完整 config 參數參考
- `5000_disatar/00_docs/NETWORK_README.md`：災難路網建置
- `5000_disatar/00_docs/PT_BUS_INTEGRATION_GUIDE.md`：PT mapping 參數
- `5000_disatar/05_combined_evac/WORKFLOW.md`：撤離流程
- `.agent/workflows/disaster.*.md`：SOP（建網 / 模擬 / SimWrapper）

---

## 8) 維護規則（讓這份文件永遠正確）

1. 任何新工具 / pipeline，**先更新 `PROJECT_WIKI.md`**。
2. 新城市移植時，務必在此文件新增「城市差異」與「資料來源」說明。
3. 若其他文件與此文件衝突，以此文件為準，並回補其它文件。
