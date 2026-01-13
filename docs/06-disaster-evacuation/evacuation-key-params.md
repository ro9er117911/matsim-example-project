# 災難撤離關鍵參數（5000_disatar）

基準來源：`5000_disatar/05_combined_evac/config_optimized_iter10.xml`  
目的：列出撤離情境的可調參數與意義，供交接與驗收使用。

---

## A. 網路與封路事件

- `network.inputNetworkFile`  
用於撤離的基礎路網，需與 PT schedule 對應。
- `network.inputChangeEventsFile`  
封路/淹水事件檔案（撤離核心）。
- `network.timeVariantNetwork=true`  
必須啟用，否則封路不會生效。

---

## B. 需求與人口

- `plans.inputPlansFile`  
撤離人口與活動鏈輸入。

---

## C. 供給與動力學（QSim）

- `qsim.flowCapacityFactor=0.06`  
樣本化比例，影響流量與擁擠程度。
- `qsim.storageCapacityFactor=0.06`  
與流量對應的儲存容量倍率。
- `qsim.startTime=00:00:00`  
- `qsim.endTime=24:00:00`  
撤離時窗，必要時可延長。
- `qsim.stuckTime=300.0`  
卡住判定秒數。
- `qsim.removeStuckVehicles=false`  
避免直接移除卡住車輛。
- `qsim.linkDynamics=PassingQ`  
排隊動力學模式。
- `qsim.trafficDynamics=queue`  
對短 link 穩定，避免 storage 問題。

---

## D. 模式與路徑（Routing / PT）

- `routing.networkModes=car`  
路網模式設定（本場景以車為主）。
- `routing.teleportedModeParameters`  
walk 的速度與直線放大係數。
- `transit.useTransit=true`  
PT 開啟（但 `usingTransitInMobsim=false` 為 teleport）。
- `transit.transitScheduleFile` / `transit.vehiclesFile`  
PT 時刻表與車輛檔案。

---

## E. 行為與效用（Scoring）

- `scoring.lateArrival=-18`  
遲到懲罰。
- `scoring.performing=+6`  
活動效用。
- `scoring.fractionOfIterationsToStartScoreMSA=0.9`  
後期才啟用 MSA 評分。

活動時長：
- `activityParams: home typicalDuration=03:00:00`  
- `activityParams: evacuation typicalDuration=06:00:00`

模式旅行效用：
- `modeParams: car marginalUtilityOfTraveling_util_hr=-6.0`
- `modeParams: pt marginalUtilityOfTraveling_util_hr=-6.0`
- `modeParams: walk marginalUtilityOfTraveling_util_hr=-12.0`

---

## F. 重規劃（Replanning）

- `replanning.maxAgentPlanMemorySize=5`
- `replanning.fractionOfIterationsToDisableInnovation=0.8`
- `strategy: ChangeExpBeta weight=0.5`
- `strategy: ReRoute weight=0.3`
- `strategy: SubtourModeChoice weight=0.0`

---

## G. 輸出與迭代

- `controller.lastIteration=10`  
基準迭代次數（可用 100 / 1000 版本作比較）。
- `controller.writeEventsInterval=1`  
每次迭代輸出事件（方便分析）。

---

## 交接提醒

- 若切換至 `config_optimized_iter100.xml` 或 `config_optimized_iter1000.xml`，請同步更新交接文件中的 baseline 說明。  
- 重要調整請記錄「調整原因」與「影響指標」，避免黑盒化。
