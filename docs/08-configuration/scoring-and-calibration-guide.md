# MATSim 核心演算法：評分函數 (Scoring) 與參數標定指南

MATSim 的靈魂在於「效用最大化」。每一個代理人 (Agent) 都會根據其計畫的執行結果獲得一個得分 (Score)。本文件解析 **Charypar-Nagel Scoring Function** 的數學組成與在台灣場景下的標定建議。

---

## 1. 評分函數數學組成 (Charypar-Nagel Model)

總得分 $S_{plan}$ 通常表示為：
$$S_{plan} = \sum S_{act, i} + \sum S_{trav, j}$$

### 1.1 活動效用 ($S_{act}$)
活動的得分主要取決於持續時間。
- **邊際效用 (Marginal Utility of Performing)**：一般設為正值。
- **遲到懲罰 (Late Arrival)**：負效用，通常影響極大。
- **早退/超時 (Early Departure/Short Duration)**：負效用。

### 1.2 旅次效用 ($S_{trav, mode}$)
旅次的得分通常為負值（旅行是代價）：
$$S_{trav, mode} = C_{mode} + \beta_{time, mode} \cdot t_{trav} + \beta_{dist, mode} \cdot d_{trav} + \beta_{m} \cdot \text{money}$$
- **$C_{mode}$**: 模式常數 (Mode Constant)，代表對該模式的整體偏好或厭惡。
- **$\beta_{time}$**: 時間邊際效用。這通常與 **時間價值 (Value of Time, VOT)** 掛鉤。

---

## 2. 參數標定建議 (台灣案例)

針對台灣的交通特性與災難情境，我們建議調整以下參數：

| 參數 | 建議值 | 說明 |
| :--- | :--- | :--- |
| **`performing`** | +6.0 | 活動執行的基準正效用。 |
| **`marginalUtilityOfTraveling`** | -6.0 | 每小時旅行的負效用（基準值）。 |
| **`monetaryDistanceCostRate`** (Car) | -0.0002 | 每公尺的油資與磨損。 |
| **`constant`** (PT) | -0.5 ~ -1.0 | 台灣民眾對公車的平均心理屏障。 |
| **`constant`** (Walk) | 0.0 | 基準模式。 |

### 2.1 災難撤離場景下的特殊調整
在災難（如颱風、極端降雨）撤離中，傳統的通勤行為邏輯會發生「偏好倒置」：
- **`performing` (Home/Work)**：效用應降低，因為留在原地是不安全的。
- **`arrival` (Safe Zone)**：應給予極大的正效用或零門檻得分。
- **`marginalUtilityOfTraveling`**：在撤離初期可能較低（急於移動），但在極度擁堵後，負效用會劇增（恐慌心理）。

---

## 3. 均衡機制 (Equilibrium) 的達成

MATSim 透過 **Co-evolution** 達成均衡。

1.  **執行 (Execution)**：在路網上運行計畫。
2.  **評分 (Scoring)**：根據擁擠情況給予分數。
3.  **創新 (Innovation/Strategy)**：
    - **Re-routing**: 0.1 (10% 的人換路)
    - **Time Allocation**: 0.1 (10% 的人改發車時間)
    - **Change Mode**: 0.1 (10% 的人換交通工具)
4.  **選擇 (Selection)**：根據機率選擇歷史最高分的計畫或嘗試新計畫。

> [!TIP]
> **標定技巧**：若模擬結果中大部分代理人都選擇了步行，往往是因為 `marginalUtilityOfTraveling_car` 設定過於嚴苛，或模式常數不平衡。建議先微調 `Constant`，再動參數係數 $\beta$。

---

## 4. 如何驗證評分參數？

- **模式產出分析 (Modal Split)**：比對模擬的模式佔比與政府調查資料（如交通部 OD 調查）。
- **旅行時間分布 (Travel Time Distribution)**：檢查模擬的平均旅行時間是否與現實感測資料匹配。
- **得分趨勢圖 (Score Convergence)**：在 100 次迭代後，總得分應呈現穩定的飽和曲線。若曲線持續劇烈波動，代表策略創新率 (Strategy Rate) 過高。
