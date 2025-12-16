# SimWrapper 儀表板工作流說明

本文件說明如何在專案中建立與維護 SimWrapper 儀表板，從資料生成到視覺化呈現的完整流程。

## 1. 整體架構

SimWrapper 儀表板的运作流程如下：

1.  **MATSim Output**: 模擬產生的原始檔案 (Events, Network, Plans)。
2.  **Post-Processing (Python)**: 使用 script 處理原始檔案，產生輕量化的 CSV 或 GeoJSON。
3.  **Visualization Config (YAML)**: 定義儀表板的 layout、圖表類型與資料來源。
4.  **Browser Display**: SimWrapper 讀取 YAML 與資料檔進行渲染。

## 2. 資料生成 (Data Generation)

我們使用 Python script 統一處理資料，避免在前端進行繁重的運算。

*   **Script 位置**: `output/generate_advanced_dashboard.py` (或是 `tools/` 下的相關工具)
*   **輸入**: `output_network.xml.gz`, `output_events.xml.gz`, `output_trips.csv.gz`
*   **輸出**:
    *   `evac_cumulative.csv`: 撤離曲線資料
    *   `evac_time_grid.csv`: 空間網格資料 (需轉為 WGS84 經緯度)
    *   `link_congestion_*.csv`: 路段擁塞資料
    *   `policy_summary.csv`: KPI 摘要
    *   `network_wgs84.geojson`: 視覺化底圖 (篩選後的輕量路網)

**執行指令**:
```bash
python3 output/generate_advanced_dashboard.py output
```

## 3. 設定檔 (Configuration)

儀表板在 `output/` 目錄下以 YAML 格式定義。為避免單一檔案過大，建議拆分為多個 dashboard 檔案。

### 檔案結構
*   `dashboard-1.yaml`: 撤離成效 (Evacuation Performance)
*   `dashboard-2.yaml`: 交通瓶頸 (Traffic Bottlenecks)
*   `dashboard-3.yaml`: 關鍵斷面 (Key Sections)
*   `dashboard-4.yaml`: 政策摘要 (Policy Summary)
*   `dashboard-*-desc.md`: 對應的文字說明 (Markdown 格式)

### 常用元件範例

**Line Chart (曲線圖)**
```yaml
- type: line
  dataset: "data.csv"
  x: "time_min"
  columns: ["col1", "col2"] # 明確指定欄位
  xAxisName: "Time"
  yAxisName: "Value"
```

**Map (地圖)**
```yaml
- type: map
  center: [121.43, 25.18]
  zoom: 12
  layers:
    - type: csv
      file: "grid.csv"
      colorRamp: { column: "value", ramp: "Spectral" }
    - type: geojson
      file: "zones.geojson"
      color: "#ff0000"
      opacity: 0.3
```

**Advanced Map (Datasets + Display)** - 適用於複雜的路段著色
```yaml
  datasets:
    data: congestion.csv
  display:
    lineColor:
      dataset: data
      columnName: "v_c"
      join: "linkId" # CSV 欄位
      colorRamp: { ramp: "Magma", steps: 5 }
    fill: {}         # 避免 TypeError
    fillHeight: {}   # 避免 TypeError
    radius: {}       # 避免 TypeError
  shapes:
    file: network.geojson
    join: "id"       # GeoJSON 屬性
```

## 4. 常見問題排解 (Troubleshooting)

| 錯誤訊息 | 可能原因 | 解決方法 |
|---------|---------|---------|
| `TypeError: Cannot read properties of undefined (reading 'fill')` | Map 圖層缺少樣式屬性或設定不完整 | 在 `display` 中加入 `fill: {}`，或簡化 `style` 設定 |
| `TypeError: Cannot read properties of undefined (reading '0')` | 座標系統不合 (非 WGS84) 或幾何錯誤 | 確保 GeoJSON/CSV 使用 WGS84 (Lon, Lat)，且幾何有效 |
| `undefined: BAD REQUEST` (Text Panel) | 舊版語法不支援內嵌文字 | 使用 `file: desc.md` 引用外部 Markdown 檔案 |
| `undefined: BAD REQUEST` (Chart/Table) | 找不到欄位或 Config 錯誤 | 明確指定 `columns`，檢查 CSV 檔頭是否正確 |
| `Error in configuration` (Table) | 同上 | 同上 |

## 5. 最佳實踐

1.  **座標系統**: 網頁地圖一律使用 **WGS84 (EPSG:4326)**。Script 輸出前務必轉換 (如 `pyproj`)。
2.  **檔案大小**: GeoJSON 若過大會導致瀏覽器崩潰。請篩選只保留需要的 Features (如僅保留有流量的路段)。
3.  **結構簡潔**: 避免 YAML 嵌套過深 (如 `layout` 下直接接 Row 名稱)。
4.  **明確定義**: 盡量明確寫出 `columns`、`x` 等屬性，依賴自動偵測雖方便但易出錯。
