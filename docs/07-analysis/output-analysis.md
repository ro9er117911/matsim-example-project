# 模擬輸出分析指南

本文件整理 MATSim 主要輸出檔與分析方法，協助快速判斷收斂、運具分擔與路網瓶頸。

## 一、輸出目錄結構

常見輸出檔案：
- `output_events.xml.gz`：完整事件流
- `output_plans.xml.gz`：最終計畫
- `output_network.xml.gz`：輸出路網
- `scorestats.csv`：效用收斂
- `modestats.csv`：運具分擔
- `ph_modestats.csv`：人時統計
- `pkm_modestats.csv`：人公里統計
- `output_trips.csv.gz`、`output_legs.csv.gz`：旅次與 leg 統計

---

## 二、核心 CSV 解讀

### 1) `scorestats.csv`
- 觀察 `avg_executed` 是否逐步趨於穩定
- 若 `avg_best` 與 `avg_executed` 長期差距大，代表尚未收斂

### 2) `modestats.csv`
- 追蹤 `car/pt/walk` 比例變化
- 若迭代 0~5 完全不變，通常代表模式探索不足

### 3) `ph_modestats.csv` / `pkm_modestats.csv`
- `ph` 看時間負擔，`pkm` 看距離負擔
- `pt_wait` 過高代表班次不足或轉乘成本過高

---

## 三、事件流快速檢查

```bash
# 事件摘要
zcat output/output_events.xml.gz | head -50

# PT 上下車事件
gunzip -c output/output_events.xml.gz | \
  grep "VehicleArrivesAtFacility\|VehicleDepartsAtFacility" | head -20
```

---

## 四、瓶頸與速度分析

```bash
python3 5000_disatar/05_scripts/07_analysis/analyze_agent_speeds.py \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --out output/slow_links_analysis.csv
```

---

## 五、視覺化

SimWrapper 請參考 `docs/05-simulation/simwrapper.md`。

---

## 六、參考報告

- `docs/07-analysis/reports/simulation-verification-report.md`
