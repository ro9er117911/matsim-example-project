# OSM 工程師的 MATSim 從零開始（Zero-to-One）

本資料夾是一個「**你會 OSM / 會做路網工程，但第一次上手 MATSim**」的最小可跑範例：  
用同一套心智模型，把 **OSM → MATSim Network → Population(Plans) → Run → Output(Events)** 跑通，再逐步延伸到本 repo 的 PT/災難/可視化工作流。

參考來源（本 repo 既有文件）：`README.md`、`CLAUDE.md`、`.agent/workflows/disaster.network.md`、`.agent/workflows/disaster.simulation.md`、`.agent/workflows/disaster.simwrapper.md`

---

## 你會得到什麼（最重要的四件事）

- 一個可直接跑的最小場景：`examples/osm_zero_to_matsim/scenario/`
- 一套把 pipeline 串起來的腳本（只用標準庫）：`examples/osm_zero_to_matsim/scripts/`
- 一份可複製到正式專案的核心 Java runner：`examples/osm_zero_to_matsim/java/`（教學用）+ `src/main/java/org/matsim/project/examples/osm/RunOsmFromScratchHeadless.java`（可直接執行）
- 一份「OSM 工程師視角」的 MATSim 百科：`examples/osm_zero_to_matsim/MATSIM_WIKI.md`

---

## 0) 先建立你的心智模型：OSM vs MATSim

你熟悉的 OSM 主要是「地理拓樸 + 標籤」；MATSim 需要的是「**可模擬的交通供給 + 代理人需求**」。

最直覺的對照表：

| OSM | MATSim |
|---|---|
| node (lat/lon) | node (x/y，通常投影座標、單位 m) |
| way (雙向/單向) | link（**有向**，每個方向一條） |
| tag: highway/maxspeed/lanes | link 的 `freespeed/capacity/permlanes/modes`（要能跑 QSim） |
| 只要幾何合理即可 | 需要「交通語意」：容量、速度、模式可行性 |

這份範例先做最小集合：**car-only demand** + **OSM 轉成 network** + **跑一個 iteration**。

---

## 1) 前置條件（與本 repo 一致）

### 1.1 必要軟體

- Java 21
- Maven（或直接用本 repo 的 `./mvnw`）
- Python 3（本範例腳本只用標準庫，不需要 pip 安裝套件）

快速檢查：

```bash
java -version
./mvnw -version
python3 --version
```

### 1.2 先把本 repo build 出 shaded jar

本範例的 Java 工具（OSM→network）會透過 root 的 `matsim-example-project-0.0.1-SNAPSHOT.jar` 執行：

```bash
./mvnw clean package -DskipTests
ls -la matsim-example-project-0.0.1-SNAPSHOT.jar
```

---

## 2) 一鍵跑通範例（建議照順序）

> 你第一次跑只需要 4 個指令：建網 → 生人口 → 跑模擬 → 快速驗證

### Step 2.1 OSM → MATSim network

範例 OSM（極小 toy）在：`examples/osm_zero_to_matsim/scenario/input/toy.osm`

```bash
python3 examples/osm_zero_to_matsim/scripts/20_build_network.py \
  --osm examples/osm_zero_to_matsim/scenario/input/toy.osm \
  --out examples/osm_zero_to_matsim/scenario/input/network.xml.gz
```

這個腳本會依副檔名自動選用 reader：

- `*.osm` / `*.xml` → `BuildNetworkFromOsmXml`（OSM XML reader；WGS84→EPSG:3826）
- `*.pbf` → `BuildCarWalkNetworkFromOsm`（PBF reader；可客製 highway defaults/modes）

####（可選）快速檢查 network 是否合理

```bash
ls -lh examples/osm_zero_to_matsim/scenario/input/network.xml.gz
gunzip -c examples/osm_zero_to_matsim/scenario/input/network.xml.gz | head -40
gunzip -c examples/osm_zero_to_matsim/scenario/input/network.xml.gz | rg 'modes=\"' | head -20
```

重點看兩件事：

- node 的 `x/y` 是否已經是投影座標（台灣 EPSG:3826 會接近 `x≈300k, y≈2.7M`）
- link 是否有 `modes`，且包含 `car`

### Step 2.2 network → population（car-only）

從 network 隨機抽可開車 link，產生 `home → work → home`：

```bash
python3 examples/osm_zero_to_matsim/scripts/30_generate_population.py \
  --network examples/osm_zero_to_matsim/scenario/input/network.xml.gz \
  --out examples/osm_zero_to_matsim/scenario/input/population.xml.gz \
  --persons 50
```

####（可選）快速檢查 population

```bash
gunzip -c examples/osm_zero_to_matsim/scenario/input/population.xml.gz | head -60
```

你應該看到：

- activity 同時有 `link` 與 `x/y`
- leg mode 是 `car`

### Step 2.3 跑模擬（headless）

用最小 config：`examples/osm_zero_to_matsim/scenario/config.xml`

```bash
python3 examples/osm_zero_to_matsim/scripts/40_run_matsim.py \
  --config examples/osm_zero_to_matsim/scenario/config.xml \
  --last-iteration 0 \
  --output examples/osm_zero_to_matsim/scenario/output \
  --log-level warn
```

> 為什麼 `last-iteration 0`？先跑一個 iteration（routing→mobsim→scoring），確保 pipeline 可用，再放大。

####（可選）把 log 打開一點

如果你需要看更細節（routing、QSim progress），把 `--log-level` 改成 `info`：

```bash
python3 examples/osm_zero_to_matsim/scripts/40_run_matsim.py \
  --config examples/osm_zero_to_matsim/scenario/config.xml \
  --last-iteration 0 \
  --output examples/osm_zero_to_matsim/scenario/output \
  --log-level info
```

### Step 2.4 快速驗證輸出

```bash
python3 examples/osm_zero_to_matsim/scripts/50_quick_check.py \
  --output examples/osm_zero_to_matsim/scenario/output_car_only
```

你至少會看到（最後一個 iteration 目錄）：

- `.../output_events.xml.gz` / `.../output_plans.xml.gz`
- `.../ITERS/it.0/0.events.xml.gz`
- `.../ITERS/it.0/0.plans.xml.gz`
- `scorestats.csv` / `modestats.csv`

---

### Step 2.5 把結果打包成 SimWrapper dashboard

MATSim 的事件、路網和 compressed plans 在 `scenario/output_car_only` 裡都保留一份，這樣你可以直接把這個資料夾丟到 SimWrapper / dashboard pipeline。

1. 把最後一個 iteration 裡的事件與 plans copy 到 top-level，讓 quick-check 可以直接抓：
   ```bash
   cp examples/osm_zero_to_matsim/scenario/output_car_only/ITERS/it.0/0.events.xml.gz \
     examples/osm_zero_to_matsim/scenario/output_car_only/output_events.xml.gz
   cp examples/osm_zero_to_matsim/scenario/output_car_only/ITERS/it.0/0.plans.xml.gz \
     examples/osm_zero_to_matsim/scenario/output_car_only/output_plans.xml.gz
   ```
2. 拷貝 network（產生時的 input/network.xml.gz）到 `output_network.xml.gz`，供 dashboard script 與其他工具參照：
   ```bash
   cp examples/osm_zero_to_matsim/scenario/input/network.xml.gz \
     examples/osm_zero_to_matsim/scenario/output_car_only/output_network.xml.gz
   ```
3. 讓 `tools/generate_dashboard_yamls.py` 產生 `dashboard-*.yaml` + `*.md`：（腳本需要 pandas）
   ```bash
   cd /Users/ro9air/matsim-example-project
   NETWORK_GEOJSON=network_wgs84_congestion.geojson \
     python3 tools/generate_dashboard_yamls.py \
       --output_dir examples/osm_zero_to_matsim/scenario/output_car_only
   ```
4. `output_car_only` 也包含了給 dashboard 看的 CSV stub（`evac_cumulative`, `evac_bins`, `link_congestion_*`, `bottleneck_curves_*`, `policy_summary_transposed`），方便你拿這份資料去實作更複雜的資料產生工具。

如果你想直接看 dashboard，在 `output_car_only` 目錄下啟動 SimWrapper：

```bash
cd examples/osm_zero_to_matsim/scenario/output_car_only
simwrapper run --port 8050   # 或 simwrapper serve 8050
```

開瀏覽器到 `http://localhost:8050`，就可以看到剛剛產生的 YAML 工具所描述的 panels。這條命令依賴網路監聽權限（有些 sandbox 會回報 `Operation not permitted`），如果啟動失敗，先確認端口能綁定或者改用其它 port。

--- 

## 3) 把你的真實 OSM 套進來（從 toy 到實務）

### 3.1 準備 OSM extract（建議用 `.pbf`）

原則：**先裁切到 ROI 再建網**，避免整城/整島太大導致建網與路由時間爆炸。

你可以用慣用工具（例如 `osmium`/`osmosis`/Overpass/Geofabrik extract）先得到：

- `your_area.osm.pbf`（推薦）
- 或 `your_area.osm`（OSM XML；適合小範圍）

### 3.2 CRS（座標系）是硬需求

OSM 是 WGS84 經緯度（度），MATSim network/plans 建議是投影座標（公尺），否則：

- link `length` / `freespeed` / `capacity` 的交通語意會錯
- scoring 的時間距離成本也會錯

本 repo 預設 `EPSG:3826`（台灣 TWD97 / TM2 121）。  
如果你不是台灣場景，你需要：

1. 選定投影 CRS（常見：UTM zone）
2. 修改建網工具內的 coordinate transformation（見 `src/main/java/org/matsim/project/tools/BuildCarWalkNetworkFromOsm.java` 或 `BuildNetworkFromOsmXml.java`）
3. 同步更新 config 的 `<module name="global"><param name="coordinateSystem" .../>`

### 3.3 用腳本建網

```bash
python3 examples/osm_zero_to_matsim/scripts/20_build_network.py \
  --osm /path/to/your_area.osm.pbf \
  --out examples/osm_zero_to_matsim/scenario/input/network.xml.gz
```

---

## 4) 從 car-only 延伸到 PT/撤離/封路（對照本 repo）

本範例只示範「最小 car-only」，但本 repo 已經把重點工程化：

### 4.1 加公共運輸（GTFS → pt2matsim → SwissRailRaptor）

入口文件：

- `docs/03-public-transit/public-transit-guide.md`
- `docs/12-notes/matsim-pipeline-complete-guide.md`
- `CLAUDE.md`（pt2matsim 指令、SwissRailRaptor 除錯 checklist）

### 4.2 災難封路（Time-Variant Network Change Events）

入口 workflow：`.agent/workflows/disaster.network.md`

核心概念很單純：產生 `changeEvents.xml`（降速/降容量/封閉）→ config 啟用：

```xml
<module name="network">
  <param name="inputNetworkFile" value="network.xml.gz"/>
  <param name="inputChangeEventsFile" value="input/tsunami_changeEvents.xml"/>
  <param name="timeVariantNetwork" value="true"/>
</module>
```

### 4.3 Headless 長跑（5000+ agents、100+ iterations）

入口 workflow：`.agent/workflows/disaster.simulation.md`

### 4.4 SimWrapper Dashboard（可視化與分析）

入口 workflow：`.agent/workflows/disaster.simwrapper.md`

---

## 5) 你接下來應該先讀哪份？

- 先讀「百科」：`examples/osm_zero_to_matsim/MATSIM_WIKI.md`
- 你要跑 PT：從 `docs/12-notes/matsim-pipeline-complete-guide.md` 開始
