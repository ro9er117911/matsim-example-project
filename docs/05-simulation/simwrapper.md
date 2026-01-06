# SimWrapper 視覺化與儀表板流程

本文件整理 SimWrapper 的資料生成、儀表板設定與常見錯誤處理。

## 一、基本流程

1. 完成 MATSim 模擬，取得 `output/` 目錄
2. 產生 dashboard 資料與 YAML 設定
3. 啟動 SimWrapper 伺服器並瀏覽儀表板

---

## 二、資料生成與 pipeline

### 1) 一鍵產生（推薦）

```bash
./5000_disatar/05_scripts/07_analysis/run_dashboard_pipeline.sh <output_dir>
```

常用環境變數：
- `MIN_VOLUME`：篩掉極小流量的 link
- `MIN_TT_RATIO`：篩掉低於門檻的壅塞比
- `NETWORK_GEOJSON`：輸出 GeoJSON 檔名

### 2) 產物說明

輸出目錄中常見檔案：
- `dashboard-*.yaml`：儀表板設定
- `*.csv`：統計與圖表資料
- `network_wgs84_congestion.geojson`：路網視覺化
- `hazard_zone.geojson` / `moderate_closure.geojson`：災害區域（若有）

---

## 三、啟動 SimWrapper

```bash
npx simwrapper serve --port 8000
```

瀏覽：`http://localhost:8000`，並選擇對應輸出資料夾。

---

## 四、YAML 設定要點

### 1) 圖表欄位明確指定

```yaml
- type: line
  dataset: "data.csv"
  x: "time_min"
  columns: ["col1", "col2"]
```

### 2) Map 與資料 join

```yaml
datasets:
  data: congestion.csv
shapes:
  file: network.geojson
  join: "id"

display:
  lineColor:
    dataset: data
    columnName: "v_c"
    join: "linkId"
    colorRamp: { ramp: "Magma", steps: 5 }
  fill: {}
  fillHeight: {}
  radius: {}
```

---

## 五、常見錯誤與解法

| 錯誤訊息 | 可能原因 | 解法 |
|---|---|---|
| `TypeError: Cannot read properties of undefined (reading 'fill')` | Map display 欄位不完整 | 在 `display` 中加入 `fill: {}` |
| `TypeError: Cannot read properties of undefined (reading '0')` | 座標系非 WGS84 | 先轉為 EPSG:4326 |
| `undefined: BAD REQUEST` (Text) | 直接寫文字不支援 | 改用 `file: desc.md` |
| `Error in configuration` | 欄位不存在或拼錯 | 明確指定 `columns` 並檢查 CSV header |

---

## 六、最佳實務

- Map/GeoJSON 一律使用 **WGS84 (EPSG:4326)**
- 大型 GeoJSON 請先篩選，避免瀏覽器崩潰
- YAML 結構保持扁平，避免多層嵌套
