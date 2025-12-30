# 災難撤離情境（5000_disatar）指南

本文件整理 5000_disatar 災難撤離場景的資料結構、執行流程與設定重點。

---

## 一、場景摘要

- **地點**：淡水沿海 → 台北都會區安全區
- **災害**：海嘯／洪水導致分階段道路封閉
- **規模**：5000 agents（可擴量）
- **出發策略**：staggered 出發（例：02:50–03:20）
- **運具**：car + pt + walk（部分 config 為 car-only）

---

## 二、核心檔案與目錄

- **Config**：`5000_disatar/05_combined_evac/config_*.xml`
- **人口**：`5000_disatar/05_combined_evac/input/population_*.xml`
- **封路事件**：`5000_disatar/05_combined_evac/input/tsunami_changeEvents_*.xml`
- **災害資料**：`5000_disatar/evacuation_shp/`
- **工作流**：`5000_disatar/05_combined_evac/WORKFLOW.md`
- **路網建置**：`docs/02-osm-network/network-guide.md`
- **PT 映射**：`docs/03-gtfs-public-transit/public-transit-guide.md`

---

## 三、執行流程（摘要）

1) 產生人口
```bash
python3 5000_disatar/05_scripts/json_to_population.py
```

2) 產生封路事件
```bash
python3 5000_disatar/05_combined_evac/tools/generate_change_events_depth.py
```

3) 執行模擬
```bash
scripts/run_simulation.sh 5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

4) SimWrapper 分析
```bash
tools/run_dashboard_pipeline.sh output_staggered_iter10
```

---

## 四、大規模疏散設定重點（節錄）

以下為大規模疏散常見調校方向：

- **時窗加長**：`endTime=36:00:00` 避免長時窗被截斷
- **收斂策略**：`lastIteration=50`、`fractionOfIterationsToStartScoreMSA=0.9`
- **交通動力學**：`trafficDynamics=kinematicWaves`、`linkDynamics=PassingQ`
- **卡住偵測**：`stuckTime=600`、`removeStuckVehicles=false`
- **模式選擇**：`SubtourModeChoice` 提供 car/pt/walk 轉換
- **步行成本**：提高 walk 不效用避免過度偏好步行

---

## 五、公車徵調 GTFS 篩選邏輯（災害特化）

### 目標
挑選最可能被徵調的公車路線，聚焦災區接駁與疏散。

### 篩選維度
- **營運商**：區公所接駁／在地客運優先
- **空間**：淡水區範圍內有停靠站
- **時間**：撤離時段（03:00–09:00）有班次

### 指令範例
```bash
python3 scripts/filter_bus_routes.py \
  --input <GTFS> \
  --output <filtered_gtfs> \
  --priority 2 \
  --time "03:00:00,09:00:00"
```

---

## 六、輸出與分析

- 事件流：`output_*/output_events.xml.gz`
- 瓶頸與速度：`tools/analyze_agent_speeds.py`
- 儀表板：`tools/run_dashboard_pipeline.sh`

---

## 七、常見錯誤

- **封路事件未生效**：確認 `network.timeVariantNetwork=true`
- **PT 停用**：確認 `transit.useTransit=true` 與 schedule/vehicles 路徑
- **卡住過多**：回到路網連通性與人口活動點檢查
