# 災難撤離資料分析策略

本文件整理 MATSim 資料管線重點與偏好研究的實驗設計方向。

---

## 一、資料管線重點

### 1) OSM → Network
- `SupersonicOsmNetworkReader` 依 `highway` 決定屬性
- `BuildCarWalkNetworkFromOsm.java` 控制模式可用性

### 2) GTFS → PT
- `stop_times.txt` 為關鍵來源
- `shapes.txt` 非必要，但可提升路徑貼合度
- 最終輸出為 `transitSchedule` 與 `transitVehicles`

---

## 二、災難偏好實驗設計

### 1) 實驗組設計
- **基準組**：一般通勤參數
- **信任組**：降低 PT 移動負效用
- **規避組**：提高轉乘成本

### 2) 參數調整建議

| 參數 | 調整方向 |
|---|---|
| `marginalUtilityOfTraveling` | 提高 PT 效用 |
| `additionalTransferTime` | 增加轉乘成本 |
| `marginalUtilityOfMoney` | 災害情境可設為 0 |

### 3) 驗證方法
- 模式分擔是否符合預期
- 撤離完成時間是否縮短
