> [!IMPORTANT]
> **本文件內容已於 2026-01-14 整合至 [PT_Mapping_Workflow_Guide.md](PT_Mapping_Workflow_Guide.md)**
> 請優先參考該文件以獲得最新、最完整的流程說明。

# MATSim 大眾運輸深究：動態調度與轉乘懲罰的科學分析

在 MATSim 中，大眾運輸並非簡單的背景流，而是與車流、路網強耦合的動態系統。本文件探討「動態車輛調度」與「轉乘懲罰 (Transfer Penalty)」對模擬穩定性的數值影響。

---

## 1. 動態車輛調度 (Dynamic Dispatch) 的影響

MATSim 預設是根據 `transitSchedule.xml` 的靜態時刻表運行，但當引入動態特性（如依據即時路況調整發車，或使用 `DRT` 模組）時，系統會變得極其複雜。

### 1.1 數值穩定性挑戰
- **震盪效應 (Oscillation)**：如果車輛調度過於靈敏（例如：一旦前方堵塞立即縮短後方班距），可能會導致「公車成串 (Bus Bunching)」現象，進而引發局部路網的瞬間崩潰。
- **正回饋循環**：延誤 -> 車次重組 -> 更多人湧向特定車次 -> 停站時間 (Dwell Time) 增加 -> 進一步延誤。

### 1.2 科學化監控建議
- **班距偏差率 (Headway Deviation)**：監控實際到達時間與預計時間的標準差。若標準差在迭代中持續發散，代表目前的 `flowCapacityFactor` 或 `storageCapacityFactor` 設定無法支撐該強度的調度策略。

---

## 2. 轉乘懲罰 (Transfer Penalty) 與穩定性

轉乘懲罰是 SwissRailRaptor (或其它 Router) 在計算最優計畫時的核心權重。

### 2.1 數值設定的影響
在 `config.xml` 的 `swissRailRaptor` 模組中，轉乘懲罰通常包含兩部分：
- **`transferPenaltyBaseCost` (基本懲罰)**：每次轉乘的固定扣分。
- **`transferPenaltyCostPerTravelTimeHour` (時間權重)**：等待轉乘時間的負效用。

| 設定方案 | 對模擬行為的影響 | 穩定性表現 |
| :--- | :--- | :--- |
| **高懲罰 (10+ min)** | Agents 傾向於擠向直達車，導致直達路線極度擁擠。 | **不穩定**（局部過載） |
| **低懲罰 (0-2 min)** | Agents 對轉乘極度容忍，可能出現反直覺的多次轉乘行為。 | **穩定**（流量分散） |
| **中度懲罰 (5 min)** | 行為最接近現實，能平衡直達與轉乘路網。 | **最佳平衡** |

### 2.2 數值敏感度分析
- **邊際效用劇變**：若轉乘懲罰設定過高，Scorer 中的 `Score` 會出現斷崖式下降。這會導致代理人在 `Strategy` 階段大規模「逃離」公車模式，轉向私家車，進而引發車道路網的二次擁擠。

---

## 3. 架構層級的優化建議

1.  **分階段穩定 (Phased Stabilization)**：
    建議在模擬的前 20% 迭代中禁用高度動態的調度邏輯，先讓路網拓撲與基準流量達到平衡，再逐步引入動態偏差。
2.  **空間過濾**：
    針對特定擁擠節點，手動調整 `stopAreaCapacity`，避免大量公車在轉運站同時進站導致的模擬死結。
3.  **校準流程**：
    利用 `CheckMappedSchedulePlausibility` 工具先期排除「物理上不可能完成」的調度計畫。

> [!CAUTION]
> **警告**：過高的 `maxTravelCostFactor`（映射倍數）會讓公車在路網上繞行過長，這會放大大眾運輸與私有車流的競爭，導致模擬在深夜時段仍無法結束。
