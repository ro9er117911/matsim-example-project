# v5 淡水撤離情境 - 91K 模擬設定

本文件說明如何執行 91,000 名 Agent 的淡水撤離情境模擬。

## 場景說明
模擬政府在災難時徵召淡水區公車與市區公車，協助淡水居民撤離至台北市區。此版本為 **91K 動態路網測試版**，人口檔案由 280K 版本抽樣生成。

### 大眾運輸與人口分佈
| 類型 | 數量 | 說明 |
|------|------|------|
| 🚇 捷運 | 7 線 | 板南、淡水信義、中和新蘆、松山新店、文湖 + 2支線 |
| 🚌 公車 | 365 線 | 包含淡水客運、指南客運、大都會、首都、三重客運 (整合 GTFS shape.txt) |
| 👥 總 Agent | 91,000 | 28,000 pt + 63,000 car |

## 設定細節
- **設定檔**: `config_v5_91k.xml`
- **人口檔**: `input/population_91k.xml.gz`
- **路網檔**: `input/network_final_v5_islands.xml.gz` (標準 v5 路網)

## 資料夾結構
```
v5_tamsui_evac_v2/
├── config_v5_91k.xml               # 91K MATSim 設定檔 (主要)
├── config_v5_280k.xml              # 280K MATSim 設定檔 (備份)
├── README_91K.md                   # 本說明 (已整合)
└── input/
    ├── network_final_v5_islands.xml.gz   # 含 PT 的路網
    ├── transitSchedule_mapped_v5.xml.gz  # 時刻表 (含 shapes)
    ├── transitVehicles_v5.xml            # 車輛定義
    └── population_91k.xml.gz             # 91K 人口檔
```

## 在伺服器上執行

### 1. 上傳檔案
確保 `v5_tamsui_evac_v2` 目錄（包含 `input/` 與 `config_v5_91k.xml`）已完整上傳至伺服器。
```bash
scp -r v5_tamsui_evac_v2 user@server:~/matsim/
```

### 2. 執行模擬
切換到專案根目錄並執行以下指令：
```bash
cd ~/matsim/v5_tamsui_evac_v2
java -Xmx30g -jar matsim-example-project-1.0-SNAPSHOT.jar config_v5_91k.xml
```

## 預估執行時間 (91K scale)
- **迭代數**: 20 (預設)
- **人口規模**: 91,000 Agents
- **預估時間**: 1-3 小時（視伺服器規格與核心數而定）

## 輸出結果
模擬完成後，結果將儲存於 `output/` 目錄：
- `output_events.xml.gz`: 完整事件記錄
- `output_plans.xml.gz`: 代理人最終計畫
- `SimWrapper dashboards`: 用於可視化分析的儀表板資料

## 注意事項
- 此環境已預先配置完成，可直接執行。
- 人口資料是透過從 280K 原始完整人口中進行「模式抽樣」產生的。
