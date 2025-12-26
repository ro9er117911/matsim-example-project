# MATSim 數據科學研究聚焦策略 (Data Science Research Strategy)

本指南旨在協助資料科學家理解 MATSim 的數據管線 (Data Pipeline)，並為災難撤離模擬中的民眾偏好研究建立科學化的實驗框架。

---

## 1. 數據管線透明化 (Data Pipeline)

### 1.1 OSM 映射至 Network (OSM to Network)
MATSim 使用 `SupersonicOsmNetworkReader` 處理數據。
*   **關鍵屬性**: `highway` 決定了 Link 的層級、速限與容量。
*   **自定義邏輯**: 在 `BuildCarWalkNetworkFromOsm.java` 中，只有在 `driveable` 集合內的道路才允許 `car` 模式，而 `walk` 預設允許於所有道路。

### 1.2 GTFS 整合細節
*   **Stop Times**: **完全讀取**。MATSim 依此決定班次的精確排程。
*   **Shapes.txt**: 
    *   `ptmapper` **不強制依賴** `shapes.txt`。
    *   它是透過站點間的**路網搜索**來重建公車路徑。如果有 `shapes.txt`，映射會更貼合地理曲線。
*   **LinkID 運作**: 公車與捷運路線最終導向一連串的 `linkId`。捷運通常擁有專屬的、僅限 `pt` 模式的 LinkID 集合。

---

## 2. 災難模擬偏好研究 (Disaster Preference Strategy)

對於公車與捷運的偏好實驗，建議採取以下科學步驟：

### 2.1 實驗組設計 (Experimental Design)
*   **Baseline (基準組)**: 使用一般通勤效用參數。
*   **Scenario A (信任組)**: 降低大眾運輸的「移動負效用」，模擬災難中民眾信任集體疏散。
*   **Scenario B (規避組)**: 增加轉乘懲罰 (Transfer Penalty)，模擬災難中的焦慮導致不願多次換乘。

### 2.2 效用參數 (Scoring Parameters) 調整建議
在 `config.xml` 的 `scoring` 模組：
| 參數 | 建議調整方向 |
| :--- | :--- |
| `marginalUtilityOfTraveling` | 提高 PT 的值（使其負效用變小） |
| `additionalTransferTime` | 災難場景下建議顯著增加（民眾厭惡不確定性） |
| `marginalUtilityOfMoney` | 建議設為 0（逃生不考慮財力） |

### 2.3 驗證方法 (Verification)
*   **模式份額位移 (Mode Share Shift)**: 觀察偏好調整後，實際選擇公車的人數比例變化是否符合預期。
*   **疏散效率分析**: 比較不同偏好組合下的「最後一人撤離時間」。
