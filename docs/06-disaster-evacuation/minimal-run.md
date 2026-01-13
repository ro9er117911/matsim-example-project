# 災難撤離最小可跑流程（5000_disatar）

本流程目標是快速重現撤離情境的 baseline 結果，作為交接驗收與後續擴充基準。

---

## 1) 產生人口

```bash
python3 5000_disatar/05_scripts/04_population/json_to_population.py
```

輸出位置：  
`5000_disatar/05_combined_evac/input/population_*.xml`

---

## 2) 產生封路事件

```bash
python3 5000_disatar/05_scripts/06_disaster_evacuation/generate_change_events_depth.py
```

輸出位置：  
`5000_disatar/05_combined_evac/input/tsunami_changeEvents_*.xml`

---

## 3) 執行模擬

```bash
5000_disatar/05_scripts/05_simulation/run_simulation.sh 5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

輸出位置：  
`output_*`

---

## 4) 分析與視覺化

```bash
5000_disatar/05_scripts/07_analysis/run_dashboard_pipeline.sh output_staggered_iter10
```

重點輸出：  
`output_*/output_events.xml.gz`  
`5000_disatar/05_scripts/07_analysis/analyze_agent_speeds.py`

---

## 驗收重點

- baseline 可完整重跑  
- 撤離曲線與瓶頸路段可被輸出  
- 參數設定可追溯到 config 與文件說明
