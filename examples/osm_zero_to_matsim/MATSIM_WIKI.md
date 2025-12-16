# MATSim 百科（OSM 工程師版）

本文件把「你熟悉的 OSM/路網工程」映射到 MATSim 的資料模型、config、debug 方法與本 repo 的工具鏈，目標是讓你能夠：

- 讀懂 MATSim 的核心檔案（network / plans / config / events）
- 知道每個 config module 在控制什麼
- 看到錯誤時能快速定位根因（尤其是 modes/CRS/路由/卡住）
- 把本範例延伸到本 repo 的 PT、災難封路、SimWrapper 分析

參考來源（本 repo 既有文件）：

- `README.md`
- `CLAUDE.md`
- `.agent/workflows/disaster.network.md`
- `.agent/workflows/disaster.simulation.md`
- `.agent/workflows/disaster.simwrapper.md`

---

## 1) 最小心智模型：你在 MATSim 真的在做什麼？

### 1.1 一句話版本

MATSim = **Scenario(供給+需求) + Config(規則) + Controler(迭代迴圈) + Events(真相)**。

### 1.2 Iteration loop（每次迭代的四步）

1. **Routing**：把每個 leg 變成 route（走 network router 或 teleported）
2. **Mobsim/QSim**：在 link 上跑、排隊、互動，產生 events
3. **Scoring**：把這次執行的 plan 打分
4. **Replanning**：按策略產生/選擇下一輪 plan

工程上你最常改的是：

- **Network**：速度/容量/車道/modes/封路
- **Plans**：活動位置、時間、模式、OD/需求假設
- **Config**：routing/qsim/scoring/replanning/controller 的參數

---

## 2) OSM → MATSim：你需要補齊的「模擬語意」

你熟悉的 OSM：幾何拓樸 + 標籤。  
MATSim 要跑 QSim：要能回答「**這條路能跑什麼？多快？多大容量？會不會塞？**」。

### 2.1 有向 link（方向性）

- OSM way：可能雙向/單向（`oneway=*`）
- MATSim link：**有向邊**
  - 雙向道路 → 兩條相反方向 link
  - 單向道路 → 一條 link

### 2.2 三個 QSim 核心欄位（決定塞不塞）

- `freespeed`：自由流速度（m/s）
- `capacity`：容量（veh/h）
- `permlanes`：車道數（可小數）

這三個值決定了：

- 排隊怎麼形成（flow / storage）
- travel time 變化回饋到 routing/replanning 的力度

### 2.3 modes：不是「看起來能不能走」，而是「router/mobsim 會不會用它」

MATSim 的 mode 有三個對齊點：

1. **Network link 的 `modes`**：這條 link 允許哪些 mode
2. **`routing.networkModes`**：哪些 mode 走 network router
3. **`qsim.mainMode`/mainModes**：哪些 mode 進 QSim（會排隊/塞車）

最常見的 bug 就是三者不一致。

### 2.4 CRS：OSM 經緯度不能直接拿來跑（除非你只測 parser）

OSM = WGS84（度）。  
MATSim 建議用投影座標（公尺），否則：

- 距離/速度/容量語意會錯（量綱崩壞）
- routing/scoring 的距離成本會失真

本 repo 預設：`EPSG:3826`（台灣 TWD97 / TM2 121）。

---

## 3) MATSim 資料模型（你需要會看）

### 3.1 Scenario / Config / Controler

- **Config**：模擬規則（module-based XML）
- **Scenario**：把 network/plans/transit 等 input load 到記憶體後的容器
- **Controler**：組裝 mobsim/scoring/replanning/listeners，跑 iteration loop

### 3.2 Person / Plan / Activity / Leg（需求）

最小一個人通常長這樣：

```xml
<person id="p1">
  <plan selected="yes">
    <activity type="home" link="..." x="..." y="..." end_time="08:00:00"/>
    <leg mode="car"/>
    <activity type="work" link="..." x="..." y="..." end_time="17:00:00"/>
    <leg mode="car"/>
    <activity type="home" link="..." x="..." y="..."/>
  </plan>
</person>
```

常見概念：

- **Activity**：人在做什麼（home/work/pt interaction…）
- **Leg**：怎麼移動（car/pt/walk…）
- **Route**：leg 的路由結果（car 通常是 NetworkRoute；pt 是 TransitPassengerRoute）

### 3.3 Network（供給）

你會常看這些欄位：

- node：`id, x, y`
- link：`id, from, to, length, freespeed, capacity, permlanes, modes`

### 3.4 快速詞彙表（Glossary）

- Agent / Person：一個決策單元（會執行 plan、被計分、可重規劃）
- Plan：一天的行程腳本（活動序列 + 交通腿）
- Activity：停留/目的（home/work/shop/pt interaction…）
- Leg：移動段（car/pt/walk…）
- Route：Leg 的具體路徑（car 常是 NetworkRoute；pt 常是 TransitPassengerRoute）
- Scenario：把 network/plans/transit 等載入後的「世界狀態」
- Controler：負責跑 iteration loop 的組裝器（listeners/modules 都掛在這裡）
- QSim：MATSim 的 queue-based microsim（會排隊、會塞車）
- Events：模擬事件流（debug 最可靠來源）

---

## 4) 核心檔案與輸出：你要去哪裡找真相？

### 4.1 核心輸入

- `network.xml(.gz)`：路網
- `population.xml(.gz)`：人口 plans
- `config.xml`：入口配置（modules）

### 4.2 PT（公共運輸）追加輸入

- `transitSchedule*.xml(.gz)`
- `transitVehicles*.xml(.gz|xml)`

並在 config 開啟：

- `transit`（useTransit / schedule / vehicles / usingTransitInMobsim）
- `swissRailRaptor`（PT routing）

### 4.3 最常用輸出（一定會用到）

輸出根目錄通常有：

- `scorestats.csv`：分數收斂
- `modestats.csv`：模式份額
- `ITERS/it.<n>/...`：每次迭代的詳細輸出

你 debug 最常看的兩個檔案：

- `ITERS/it.<n>/<n>.events.xml.gz`
- `ITERS/it.<n>/<n>.plans.xml.gz`

在本 repo 的大型場景，你也會看到：

- `output_events.xml.gz` / `output_plans.xml.gz`（最後 iteration 的 copy）
- `output_trips.csv.gz` 等分析輸出

### 4.4 SimWrapper-ready output

`examples/osm_zero_to_matsim/scenario/output_car_only` 是這個最小範例的結果資料夾，裡面除了 `ITERS` 之外還保留了：

- `output_events.xml.gz` / `output_plans.xml.gz`（方便直接拿來分析或裝到 dashboard）
- `output_network.xml.gz`、`network_wgs84_congestion.geojson`（重新放大的 network + GeoJSON 背景）
- `evac_cumulative.csv` / `evac_bins.csv` / `evac_time_grid.csv`
- `link_congestion_0300_0315.csv` / `link_congestion_0315_0330.csv`
- `bottleneck_curves_vc.csv` / `bottleneck_curves_tt.csv`
- `policy_summary_transposed.csv`

以上 CSV 是 `tools/generate_dashboard_yamls.py` 會讀到的 stub data，它會產生 `dashboard-*.yaml` + `dashboard-*-desc.md` 供 SimWrapper 使用，`NETWORK_GEOJSON` 指向 `network_wgs84_congestion.geojson`。完成之後可以這樣啟動 SimWrapper（若環境允許綁定網路埠）：

```bash
cd examples/osm_zero_to_matsim/scenario/output_car_only
simwrapper run --port 8050   # 或 simwrapper serve 8050
```

然後在瀏覽器打 `http://localhost:8050` 看 dashboard。如果 `run` 報 `Operation not permitted`（或 `serve` 找不到 port），可以換成別的 port 或把資料夾丟到官方的 SimWrapper 網站。

### 4.5 Events 事件速查（你會常 grep 的）

car-only 場景最常見事件（名稱以 MATSim event class 為準）：

- `ActivityEndEvent` / `ActivityStartEvent`：活動結束/開始（對應離開/抵達）
- `PersonDepartureEvent` / `PersonArrivalEvent`：人出發/抵達（mode）
- `LinkEnterEvent` / `LinkLeaveEvent`：進/出 link（可拿來算 travel time、壅塞）
- `VehicleEntersTrafficEvent` / `VehicleLeavesTrafficEvent`：車進/出交通（car mode）
- `PersonStuckEvent` / `VehicleStuckEvent`：卡住（通常代表網路/容量/可達性問題）

PT 場景會額外大量出現：

- `PersonEntersVehicleEvent` / `PersonLeavesVehicleEvent`
- `TransitDriverStartsEvent`
- `VehicleArrivesAtFacilityEvent` / `VehicleDepartsAtFacilityEvent`

實務建議：先用 `rg` 在 `*.events.xml.gz` 裡找一兩個 personId 的事件序列，最快判斷「到底發生了什麼」。

---

## 5) Config 模組速查（用「你什麼時候需要碰它」來學）

### 5.1 `global`

- `coordinateSystem`：CRS（必須與 network/plans 一致）
- `randomSeed`：可重現性

### 5.2 `network`

- `inputNetworkFile`
- 災難/封路：`inputChangeEventsFile` + `timeVariantNetwork=true`（見 `.agent/workflows/disaster.network.md`）

### 5.3 `plans`

- `inputPlansFile`
- `handlingOfPlansWithoutRoutingMode`：建議 early stage 用 `reject`（讓錯誤早爆）

### 5.4 `routing`

你最常改：

- `networkModes`：哪些 mode 走 network router（car/bike/…）
- teleportedModeParameters：walk/access_walk/egress_walk 是否 teleport

典型坑：

- networkModes 含 car，但 network link 沒有 `car` → routing 直接失敗

### 5.5 `qsim`

工程上最常調：

- `mainMode`：car-only 先用 car
- `flowCapacityFactor` / `storageCapacityFactor`：壅塞程度與速度（容量縮放）
- `stuckTime` / `removeStuckVehicles`：卡住處理（debug 期先不移除）
- `startTime` / `endTime`：模擬時間窗

### 5.6 `controller`

- `outputDirectory`
- `lastIteration`
- `writeEventsInterval` / `writePlansInterval`：輸出頻率（大場景不要 1）
- `overwriteFiles=deleteDirectoryIfExists`：工程上最常用

### 5.7 `replanning`

常見策略組合（本 repo 的 config 也大量用這個套路）：

- `ChangeExpBeta`：plan 選擇（logit-like）
- `ReRoute`：重新路由
- `SubtourModeChoice`：改 mode（會增加除錯面積，初期可關）

### 5.8 `scoring`

你要知道的最小集合：

- 每個 mode 有 `modeParams`
- 每個活動 type 有 `activityParams`

工程上常見流程：

1. 先用簡化 scoring 跑通
2. 再校準 car vs pt vs walk 的相對吸引力

### 5.9 CLI 覆寫（config override）與路徑解析（很重要）

MATSim 支援在執行時覆寫 config 值（工程上非常常用）：

- 覆寫語法：`--config:<module>.<param> <value>`
- 例：`--config:controller.lastIteration 5`

本 repo 的 headless runner（本範例用的）是用 `ConfigUtils.loadConfig(args)`，因此可直接把覆寫參數接在 config 後面：

```bash
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.examples.osm.RunOsmFromScratchHeadless \
  examples/osm_zero_to_matsim/scenario/config.xml \
  --config:controller.lastIteration 5 \
  --config:controller.outputDirectory examples/osm_zero_to_matsim/scenario/output
```

路徑解析規則（最常踩坑）：

- `inputNetworkFile` / `inputPlansFile` 等 **相對路徑**，通常會以 `config.xml` 所在資料夾為 base（MATSim 的 config context）
- 若你用自訂 runner 或 shell working directory 亂跳，可能導致路徑被當成「相對於目前目錄」
- 工程上最穩的做法：要嘛用 config context，要嘛直接改成絕對路徑（或在 pipeline 裡統一 cwd）

---

## 6) 本 repo 內你可以直接拿來用的工具（工程化入口）

### 6.1 OSM / Network

Java 工具（可直接用 jar 呼叫）：

- `src/main/java/org/matsim/project/tools/BuildCarWalkNetworkFromOsm.java`（PBF，car+walk，允許客製 highway defaults）
- `src/main/java/org/matsim/project/tools/BuildNetworkFromOsmXml.java`（OSM XML，小範圍快速）
- `src/main/java/org/matsim/project/tools/CleanNetworkForCar.java`（清理連通性）

範例腳本封裝（本資料夾）：

- `examples/osm_zero_to_matsim/scripts/20_build_network.py`

### 6.2 GTFS / PT

入口文件與工具：

- `docs/MATSim_Pipeline_完整指南.md`
- `docs/3-public-transit.md`
- `CLAUDE.md`（SwissRailRaptor/pt2matsim 指令與除錯）

### 6.3 災難封路 / 撤離

三個 workflow（最推薦從這裡讀）：

- `.agent/workflows/disaster.network.md`（time-variant network change events）
- `.agent/workflows/disaster.simulation.md`（headless 長跑）
- `.agent/workflows/disaster.simwrapper.md`（SimWrapper dashboard）

---

## 7) Debug Playbook（從症狀快速回推根因）

### 7.1 Routing 失敗 / 找不到路

檢查順序（幾乎永遠有效）：

1. leg 的 `mode` 拼字是否正確
2. `routing.networkModes` 是否包含該 mode
3. network link 的 `modes` 是否包含該 mode
4. activity 的 `link` 是否存在，或 x/y 是否可映射到 network
5. CRS 是否一致（最常被忽略）

### 7.2 卡住（stuck）

先分辨：

- **真壅塞**：容量/瓶頸設太小（flow/storage 因子）
- **網路不連通**：孤島、斷頭路、單向錯誤、活動點在不可達位置

常用手段：

- 降低人口、先跑通
- `NetworkCleaner` / `CleanNetworkForCar`
- 調 `qsim.stuckTime`，必要時 `removeStuckVehicles=true` 讓模擬不要停死

### 7.3 PT agent 不上車 / route cast 錯誤

這類問題本 repo 已整理在 `CLAUDE.md`，典型根因：

- 缺 ground network（即使你以為 PT-only）
- `TransitPassengerRoute` 與 `NetworkRoute` 型別不同
- SwissRailRaptor 設定（轉乘成本/模式映射/接駁）

---

## 8) 延伸：本 repo 的災難模擬在加什麼？

### 8.1 Time-Variant Network（動態封路/降速）

本質就是讓 network 在模擬時間軸上變動：

- freespeed factor（降速）
- capacity factor（降容量）
- factor=0（封閉）

工作流入口：`.agent/workflows/disaster.network.md`

### 8.2 SimWrapper（把 events 變成 dashboard）

工作流入口：`.agent/workflows/disaster.simwrapper.md`

---

## 9) 建議學習路徑（OSM 工程師版）

1. 跑通本範例：`examples/osm_zero_to_matsim/README.md`
2. 看懂 config：`routing/qsim/controller/replanning/scoring`
3. 再上 PT：`docs/MATSim_Pipeline_完整指南.md` + `CLAUDE.md`
4. 最後上災難封路與可視化：3 份 `.agent/workflows/disaster.*.md`
