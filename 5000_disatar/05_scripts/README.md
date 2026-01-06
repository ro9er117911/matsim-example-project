# 5000_disatar/05_scripts - 腳本地圖

本目錄依照流程階段整理專案腳本，並與文件說明對齊。

## 目錄對照

- `02_osm_network/` - OSM/SHP 路網匯入與清理
  - 主要工具：`convert_shapefile_to_network.py`, `build_combined_network.py`, `clean_network_connectivity.py`, `merge_short_links.py`
- `03_gtfs_public_transit/` - GTFS 與公共運輸前處理
  - 主要工具：`clip_gtfs_bbox.py`, `clip_gtfs_scientific.py`, `filter_gtfs_subset.py`, `convert_bus_shapes_to_gtfs.py`
- `04_population/` - 人口生成與轉換
  - 主要工具：`json_to_population.py`, `augment_population.py`, `generate_evacuation_population.py`
  - 驗證工具：`04_population/validation/validate_population_routes.py`, `validate-agent-journey.sh`
- `05_simulation/` - 模擬執行腳本
  - 主要工具：`run_simulation.sh`, `run_100_agents_simulation.sh`, `run_experiment_100k.sh`
- `06_disaster_evacuation/` - 撤離情境工具
  - 主要工具：`generate_change_events_depth.py`, `generate_change_events.py`, `run_staggered_iter10_pipeline.sh`
- `07_analysis/` - 模擬後分析與儀表板
  - 主要工具：`run_dashboard_pipeline.sh`, `analyze_agent_speeds.py`, `generate_dashboard_yamls.py`, `generate_stuck_agents_csv.py`
- `09_operations/` - 維運、監控與同步
  - 主要工具：`setup_remote_server.sh`, `sync_to_server.sh`, `monitor_resources.sh`
- `90_experiments/` - 一次性或探索性腳本

## 備註

- 情境專用腳本（例如 `5000_disatar/06_taipei_test`、`5000_disatar/evacuation_test`）維持放在各自情境資料夾內。
- 共用資源仍保留在 `tools/`（例如 `dashboard-5-stuck.yaml`）。
- 文件會直接引用這些路徑；流程順序請見 `docs/README.md`。
