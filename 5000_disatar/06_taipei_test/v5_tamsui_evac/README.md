# v5 淡水撤離情境 - 280K Server 測試

## 場景說明

模擬政府在災難時徵召淡水區公車與市區公車，協助淡水居民撤離至台北市區。

### 大眾運輸設定

| 類型 | 數量 | 說明 |
|------|------|------|
| 🚇 捷運 | 7 線 | 板南、淡水信義、中和新蘆、松山新店、文湖 + 2支線 |
| 🚌 公車 | 801 線 | 淡水客運、指南客運、大都會、首都、三重客運 |
| 👥 人口 | 280K | 撤離人口 |

## 資料夾結構

```
v5_tamsui_evac/
├── config_v5_280k.xml              # MATSim 設定檔
├── run_simulation.sh               # 執行腳本
├── README.md                       # 本說明
└── input/
    ├── network_with_pt_v5.xml.gz   # 含 PT 的路網 (16 MB)
    ├── transitSchedule_mapped_v5.xml.gz  # 時刻表 (8.6 MB)
    ├── transitVehicles_v5.xml      # 車輛定義 (40 MB)
    └── population_280k.xml.gz      # 280K 人口 (7.6 MB)
```

## 在 Server 上執行

```bash
# 1. 複製到 Server
scp -r v5_tamsui_evac user@server:~/matsim/

# 2. SSH 到 Server
ssh user@server

# 3. 執行模擬
cd ~/matsim/v5_tamsui_evac
chmod +x run_simulation.sh
./run_simulation.sh
```

## 預估執行時間

- **迭代數**: 20
- **人口**: 280,000
- **預估時間**: 6-12 小時（視 Server 規格）

## 輸出

模擬完成後，`output/` 目錄將包含：
- `output_events.xml.gz` - 事件記錄
- `output_plans.xml.gz` - 最終計畫
- SimWrapper dashboards
