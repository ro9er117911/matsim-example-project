# MATSim Example Project 專案導覽（單一真相）

若與其他文件衝突，以本文件為準，並同步更新 `docs/README.md`。

---

## 1) MATSim 心智模型

| 概念 | MATSim 對應 | 說明 |
|---|---|---|
| 路網 | `network.xml(.gz)` | 所有模式共用，靠 modes 控制可走性 |
| 公共運輸 | `transitSchedule` + `transitVehicles` | 需先 GTFS 轉換並映射到路網 |
| 代理人 | `population.xml(.gz)` | 一日活動與腿部行程（plan） |
| 模擬設定 | `config.xml` | 串接所有輸入與參數 |
| 事件輸出 | `output_events.xml.gz` | 主要分析來源 |

---

## 2) 專案結構

```
matsim-example-project/
├── README.md
├── PROJECT_WIKI.md
├── docs/                          # 主要文件
├── src/main/java/                 # Java 入口與工具
├── src/main/python/               # Python 工具
├── tools/                         # 輔助資源與模板
├── scenarios/                     # 範例場景
├── pt2matsim/                     # GTFS 轉換工具
└── 5000_disatar/                  # 災難撤離專案
    ├── 01_raw_data/
    ├── 03_phase2_production/
    ├── 05_scripts/
    └── 05_combined_evac/
```

---

## 3) 新城市／新場景建置流程

### Step 0 — 決定 CRS
- network / population / GTFS / hazard 必須一致
- 台北案例使用 `EPSG:3826`

### Step 1 — 建路網
- OSM 或 SHP 轉換
- 文件：`docs/02-osm-network/network-guide.md`

### Step 2 — GTFS 處理與 PT 映射
- GTFS 驗證、合併、映射
- 文件：`docs/03-gtfs-public-transit/public-transit-guide.md`

### Step 3 — 生成人口
- 測試人口或 ABM 轉換
- 文件：`docs/04-population/population-guide.md`

### Step 4 — 產生災害封路（選用）
- `5000_disatar/05_scripts/06_disaster_evacuation/generate_change_events_*.py`

### Step 5 — 組好 config
- 模擬設定請見 `docs/08-configuration/configuration-reference.md`

### Step 6 — 執行模擬
- 文件：`docs/05-simulation/simulation-guide.md`

### Step 7 — 分析與視覺化
- SimWrapper：`docs/05-simulation/simwrapper.md`
- 分析：`docs/07-analysis/output-analysis.md`

---

## 4) 常用腳本索引

### 5000_disatar/05_scripts/
- `5000_disatar/05_scripts/05_simulation/run_simulation.sh`：主執行入口
- `5000_disatar/05_scripts/07_analysis/run_analysis.sh`：產生分析與 YAML
- `5000_disatar/05_scripts/03_gtfs_public_transit/clip_gtfs_scientific.py`：GTFS 裁切
- `5000_disatar/05_scripts/07_analysis/run_dashboard_pipeline.sh`：SimWrapper pipeline
- `5000_disatar/05_scripts/04_population/validation/validate-agent-journey.sh`：人口/路網驗證
- `5000_disatar/05_scripts/07_analysis/analyze_agent_speeds.py`：速度診斷
- `5000_disatar/05_scripts/07_analysis/generate_stuck_agents_csv.py`：卡住代理人統計

---

## 5) 既有場景快速執行

```bash
# 台北測試場景
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/corridor/taipei_test/config.xml

# 災難撤離
5000_disatar/05_scripts/05_simulation/run_simulation.sh 5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

---

## 6) 文件總覽

- `docs/README.md`：完整索引
- `docs/06-disaster-evacuation/evacuation-guide.md`：撤離情境
