# Simwrapper Evacuation Demo

此目錄包含 Simwrapper 撤離視覺化的演示檔案。

## 目錄結構

- `dashboard-evacuation.yml`: Simwrapper 儀表板配置
- `evacuation_zones.geojson`: 危險區與安全點 (含樣式)
- `evacuation_progress.csv`: 撤離進度數據
- `departure_profile.csv`: 出發時間數據
- `summary.md`: 關鍵指標摘要

## 如何使用

1. 將此目錄拖曳至 [Simwrapper 網站](https://simwrapper.github.io/site/)
2. 或在本地開啟 Simwrapper 並瀏覽至此目錄

## 數據來源

- 模擬: `phase3_withinday` (Within-Day Replanning)
- 路網: `network_large.xml.gz` (參考)
- 事件: `output_events.xml.gz` (參考)
