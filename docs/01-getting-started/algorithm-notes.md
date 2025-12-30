# MATSim 評分與行為機制筆記

本文件整理 MATSim 的迭代流程與效用函數重點，方便在參數校準時快速對照。

---

## 一、迭代流程摘要

MATSim 以迭代方式讓代理人調整計畫：
1. **Mobsim**：執行路網模擬
2. **Scoring**：依旅行時間、距離與活動效用計分
3. **Replanning**：產生新計畫（改模式、改路徑、改出發）
4. **Selection**：選擇下輪執行計畫

可在 `controller.lastIteration` 控制迭代次數，`fractionOfIterationsToStartScoreMSA` 可用於後期收斂。

---

## 二、旅行效用核心參數

### 1) `marginalUtilityOfTraveling_util_hr`
- **意義**：旅行時間的邊際效用（通常為負）
- **效果**：時間越長，效用越低

### 2) `marginalUtilityOfDistance_util_m`
- **意義**：旅行距離的邊際效用（常用於 walk/bike）
- **效果**：距離越遠，效用越低

---

## 三、旅行效用公式（簡化）

\[
S_{trav,q} = \beta_{trav,mode(q)} \cdot t_{trav,q}
+ \beta_{dist,mode(q)} \cdot d_{trav,q}
+ \gamma_{cost,mode(q)} \cdot \beta_m \cdot C_{trav,q}
\]

常用解讀：
- **時間成本**：旅行時間越長越不利
- **距離成本**：走路或短程模式影響較大
- **金錢成本**：收費道路、票價等

---

## 四、校準常見方向

- **轉乘成本過高**：調整 `utilityOfLineSwitch` 或 SRR 轉乘成本
- **步行比例過高**：加大 walk 的時間或距離不效用
- **PT 不合理偏低**：調整 `marginalUtilityOfTraveling` 與轉乘設定

---

## 五、相關設定位置

- `config.xml` → `scoring` 模組
- `defaultConfig.xml` 為完整參考
