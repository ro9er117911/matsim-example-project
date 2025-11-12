以下是你提供內容的結構化 Markdown 版本，保持學術邏輯清晰、層級明確、適合技術文件引用：

---

# MATSim 模擬中的代理人行為決策與效用函數解析

MATSim 模擬中的代理人行為決策，尤其是**模式選擇（Mode Choice）**，是基於**共同演化演算法（Co-Evolutionary Algorithm, CEA）**中，計畫的**效用分數（Score / Utility）**計算。
以下兩個參數是 **Charypar–Nagel 效用函數**中計算旅行不效用（Travel Disutility, $S_{trav,q}$）的核心組成部分。

---

## 核心交通模擬參數詳解

### 1. `marginalUtilityOfTraveling_util_hr` ($\beta_{trav,mode(q)}$)

此參數代表在特定運輸模式下，花費旅行時間的**直接邊際效用（Direct Marginal Utility of Time Spent Traveling）**。

| 參數名稱                                 | 效用函數符號                 | 單位              | 功能與細節                                                                                  | 文獻出處                     |
| :----------------------------------- | :--------------------- | :-------------- | :------------------------------------------------------------------------------------- | :----------------------- |
| `marginalUtilityOfTraveling_util_hr` | $\beta_{trav,mode(q)}$ | 效用/小時 (util/hr) | 為旅行時間 $t_{trav,q}$ 的係數，衡量代理人對該模式旅行本身的偏好或厭惡。                                            | MATSim Book, Ch. 3.2–3.4 |
| **技術含義**                             |                        |                 | 總旅行時間效用包括兩部分：<br>(1) 直接邊際效用 ($\beta_{trav}$)，<br>(2) 時間機會成本（Opportunity Cost of Time）。 |                          |
|                                      |                        |                 | MATSim 的效用函數以 24 小時循環計分，若代理人花費 $t_{trav}$ 時間旅行，則損失等長活動的邊際效用 $\beta_{perf}$。            |                          |
| **實際應用**                             |                        |                 | 研究顯示私家車旅行的 $\beta_{trav,car}$ 常接近 0 或為正，因為旅行時間的不效用多由活動機會成本（$\beta_{perf}$）反映。          |                          |
| **預設值**                              |                        |                 | 約為 $-6$ utils/h。                                                                       |                          |

---

### 2. `marginalUtilityOfDistance_util_m` ($\beta_{dist,mode(q)}$)

此參數代表特定運輸模式下，旅行距離的**邊際效用（Marginal Utility of Distance）**。

| 參數名稱                               | 效用函數符號                                       | 單位            | 功能與細節                                                                                                        | 文獻出處                 |
| :--------------------------------- | :------------------------------------------- | :------------ | :----------------------------------------------------------------------------------------------------------- | :------------------- |
| `marginalUtilityOfDistance_util_m` | $\beta_{dist,mode(q)}$ 或 $\beta_{d,mode(q)}$ | 效用/米 (util/m) | 為距離 $d_{trav,q}$ 的係數，用於計算非貨幣性不效用。                                                                            | MATSim Book, Ch. 3.4 |
| **技術含義**                           |                                              |               | 反映體力消耗或距離疲勞，常用於步行、騎乘等模式。                                                                                     |                      |
| **與貨幣距離的關係**                       |                                              |               | 距離不效用可經由兩路徑貢獻：<br>(1) $\beta_{dist,mode(q)}$（非貨幣性距離不效用）<br>(2) $\gamma_{dist,mode(q)} \times \beta_m$（貨幣成本項） |                      |
| **預設值**                            |                                              |               | 多數模式（如汽車）預設為 0。                                                                                              |                      |

---

## 效用函數整體關聯式

在 Charypar–Nagel 效用模型中，旅行段 $q$ 的效用為：

$$
S_{trav,q} = \beta_{trav,mode(q)} \cdot t_{trav,q} + \beta_{dist,mode(q)} \cdot d_{trav,q} + \gamma_{cost,mode(q)} \cdot \beta_m \cdot C_{trav,q}
$$

其中：

* $\beta_{trav,mode(q)}$：時間效用權重
* $\beta_{dist,mode(q)}$：距離效用權重
* $\gamma_{cost,mode(q)}$：金錢成本係數
* $\beta_m$：金錢邊際效用
* $C_{trav,q}$：金錢花費

---

## 結論與實作建議

在 MATSim 中，若代理人偏好步行而非公共運輸轉乘，代表公共運輸的總不效用高於步行路徑，其關鍵原因可能包括：

1. **轉乘懲罰過高**

   * 參數：`utilityOfLineSwitch`（$\beta_{transfer}$）
   * 轉乘次數越多，效用下降越顯著。

2. **步行模式成本過低**

   * 若 $\beta_{trav,walk}$ 或 $\beta_{dist,walk}$ 不夠負面，步行效用會偏高。
   * 調整應確保步行時間與距離成本合理反映實際不便。

3. **調校策略建議**

   * 調整公共運輸轉乘懲罰，避免過度懲罰多次換乘。
   * 校準步行參數以反映現實行為（例如長距離步行應具顯著不效用）。
   * 結合觀測資料（如旅行時間分布或實際模式分配）進行 CaDyTS 校準。

---

**參考文獻**

* Horni, A., Nagel, K., & Axhausen, K. W. (Eds.). *The Multi-Agent Transport Simulation MATSim*. Ubiquity Press, 2016.
* Charypar, D. & Nagel, K. (2005). *Generating complete all-day activity plans with genetic algorithms*. Transportation, 32(4), 369–397.
* Kickhöfer, B., et al. (2011). *Calibration of MATSim using Cadyts*. *Transportation Research Record*, 2263, 29–36.

---

自我檢查：缺口→{待補：文獻頁碼對應（Ch. 3.2–3.4 細節）與臺灣在地化效用校準範例}
