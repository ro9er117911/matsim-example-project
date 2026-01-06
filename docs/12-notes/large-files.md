# 未推送的大型檔案說明

本專案包含大量原始資料與中間產物，為避免 Git 儲存庫膨脹，以下檔案與目錄被忽略、未推送到 GitHub。這些檔案會保留在本機，但不會出現在遠端。

## 主要被忽略的資料類型

- 原始 GTFS 與裁切後 GTFS（包含 `stop_times`、`shapes` 等大型檔案）
- 原始 SHP / GPKG 與相關 GIS 輔助檔案
- ABM 原始輸出與大型中間資料
- 模擬輸出與分析產物
- Taipei 測試場景產物（`06_taipei_test` 內的 `output/`、`ITERS/`、`*.xml.gz`、`*.log`）
- pt2matsim 測試資料（`pt2matsim/pt2matsim_code/test/*.zip`）

## 此次未推送的大型檔案（範例）

以下為實際被忽略的路徑與檔案（如需取得請向資料持有者索取或由流程重新生成）：

- `5000_disatar/01_raw_data/GTFS/BUS_shape_TPE_newTPE/merged/merged_bus_shapes.gpkg` (~10 MiB)
- `5000_disatar/01_raw_data/GTFS/gtfs_clipped/bus_clipped/stop_times.original` (~31 MiB)
- `5000_disatar/01_raw_data/GTFS/gtfs_clipped/bus_clipped/stop_times.original2` (~39 MiB)
- `5000_disatar/01_raw_data/GTFS/` (其他 GTFS 相關大型檔案)
- `5000_disatar/01_raw_data/MAP_SHP/` (SHP/GIS 原始資料)
- `5000_disatar/01_raw_data/templete_agent_abm/` (ABM 原始資料)
- `5000_disatar/06_taipei_test/**/output/`、`5000_disatar/06_taipei_test/**/ITERS/`、`5000_disatar/06_taipei_test/**/*.xml.gz`
- `pt2matsim/pt2matsim_code/test/*.zip`

## 追蹤規則

忽略規則已寫入 `.gitignore`。若需要將特定檔案納入版本控管，請先縮小檔案或改為提供產生流程。
