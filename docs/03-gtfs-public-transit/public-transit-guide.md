# 公共運輸（GTFS → MATSim）整合指南

本文件整理 GTFS 轉換、合併與 PT 映射流程，並提供台北案例的參數建議與常見問題解法。

## 輸入與輸出

### 輸入
- **GTFS**：`agency.txt`、`stops.txt`、`routes.txt`、`trips.txt`、`stop_times.txt`（必備）
- **路網**：`network.xml.gz`（必須包含 walk/car 等地面路網）

### 輸出
- `transitSchedule.xml(.gz)`
- `transitVehicles.xml`
- `network-with-pt.xml(.gz)`（含 PT 連結）

---

## 一、工具與位置

### Java 工具（`src/main/java/org/matsim/project/tools/`）
- `GtfsToMatsim`：GTFS → schedule/vehicles
- `MergeGtfsSchedules`：合併多份 schedule
- `PrepareNetworkForPTMapping`：清理路網並加 PT modes
- `CleanSubwayNetwork`：抽出捷運/鐵道子網

### pt2matsim JAR
- `pt2matsim/work/pt2matsim-25.8-shaded.jar`
- 常用指令：`CreateDefaultPTMapperConfig`、`PublicTransitMapper`、`CheckMappedSchedulePlausibility`

### Python 工具
- `src/main/python/validate_gtfs.py`：GTFS 完整性驗證
- `src/main/python/merge_gtfs.py`：GTFS 合併（含 ID 前綴）
- `tools/clip_gtfs_bbox.py`、`scripts/clip_gtfs_scientific.py`：範圍裁切與過濾

---

## 二、GTFS 準備與驗證

### 1) 必備檔案檢查

```bash
python src/main/python/validate_gtfs.py <gtfs_dir>
```

**必須存在**：`stop_times.txt`。沒有時刻表，無法產生可用的 `transitSchedule.xml`。

### 2) stop_times 與 trips 一致性

```bash
python3 - << 'PY'
import pandas as pd
from pathlib import Path

gtfs_dir = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')
trips = pd.read_csv(gtfs_dir / 'trips.txt', dtype=str)
stop_times = pd.read_csv(gtfs_dir / 'stop_times.txt', dtype=str)

trip_ids_trips = set(trips['trip_id'])
trip_ids_stop = set(stop_times['trip_id'])
ratio = len(trip_ids_trips & trip_ids_stop) / max(len(trip_ids_trips), 1) * 100
print(f"stop_times 匹配度: {ratio:.1f}%")
PY
```

### 3) 資料來源注意事項

- `gtfs_tw_v5` 缺少 `stop_times.txt`，**不可用於 MATSim**。
- 可用資料：`tp_metro_gtfs`、或從 **交通部 PTX** 取得完整 GTFS。
- 若包含非台北系統（高雄/台中/桃園等），需先清理避免映射錯誤。

---

## 三、GTFS 合併（多系統）

```bash
python src/main/python/merge_gtfs.py \
  pt2matsim/data/gtfs/tp_metro_gtfs/ \
  pt2matsim/data/gtfs/taipei_bus_gtfs/ \
  pt2matsim/data/gtfs/merged_gtfs/ \
  --prefix1 MRT_ \
  --prefix2 BUS_ \
  --transfer-distance 150 \
  --transfer-time 240
```

合併後請重新執行 `validate_gtfs.py` 確認完整性。

---

## 四、準備 PT 對應路網

### 1) 建立多模式路網

PT 映射需要地面路網（car/walk），否則會出現 **No route found**。

### 2) 清理與加 PT modes

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="input_network.xml.gz output_network_clean.xml.gz"
```

---

## 五、GTFS → MATSim Schedule

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.GtfsToMatsim" \
  -Dexec.args="<gtfs_zip_or_dir> output/transitSchedule.xml output/transitVehicles.xml"
```

若分別處理捷運與公車，可先各自轉換，再用 `MergeGtfsSchedules` 合併。

---

## 六、PT Mapper 參數與執行

### 1) 建立 Mapper 設定檔

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim/work/ptmapper-config.xml
```

### 2) 參數建議（台北）

| 參數 | 捷運建議 | 公車建議 | 作用 |
|---|---|---|---|
| `maxLinkCandidateDistance` | 300 | 600 | 站點找 link 的最大距離 (m) |
| `nLinkThreshold` | 12 | 15 | 每站候選 link 數 |
| `maxTravelCostFactor` | 15 | 30 | 找不到路徑時允許繞行倍數 |
| `strictLinkRule` | true | false | 公車可走 car link（避免 OSM 標籤缺失） |
| `networkRouter` | AStarLandmarks | AStarLandmarks | 路由穩定性較佳 |

### 3) 執行映射

```bash
java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config.xml
```

---

## 七、資源與早停策略

PT 映射為高負載流程，建議分階段執行與監控：

- **GTFS 轉換**：8–12 GB RAM
- **PT 映射**：12–16 GB RAM（大型路網可提高至 24 GB）
- **超時控制**：使用 `timeout` 避免長時間卡死

基本資源檢查：

```bash
free -h
df -h .
nproc
```

範例：

```bash
timeout 2h java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config.xml
```

---

## 八、驗證與檢查

### 1) 合理性檢查

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  output/network-with-pt.xml.gz output/transitSchedule-mapped.xml.gz
```

### 2) 基本統計

```bash
zcat output/transitSchedule-mapped.xml.gz | grep -c '<transitRoute'
zcat output/network-with-pt.xml.gz | grep -c 'modes="pt"'
```

---

## 九、常見問題與解法

### 1) `stop_times.txt` 缺失或不匹配
- **現象**：轉換後 schedule 幾乎為空
- **解法**：補齊 stop_times，並檢查 `trip_id` 匹配度

### 2) `No route found` / 大量人工連結
- **原因**：站點太遠、路網不連通、router 太嚴格
- **解法**：提高 `maxLinkCandidateDistance` 與 `maxTravelCostFactor`，並先清理路網連通性

### 3) 公車路徑斷裂
- **原因**：OSM 缺少 bus 標籤
- **解法**：`strictLinkRule=false`，允許公車走 car link

### 4) 映射時間過長或記憶體不足
- **解法**：縮小區域、提高 JVM 記憶體、分批處理（先捷運後公車）

---

## 十、SwissRailRaptor 設定重點

### 1) 必要模組

```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="transitScheduleFile" value="transitSchedule-mapped.xml.gz"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>
  <param name="transferPenaltyBaseCost" value="0.0"/>
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>
</module>
```

### 2) routingMode 屬性（避免 routing mode 錯誤）

```xml
<leg mode="pt">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
</leg>
```

---

## 十一、與模擬設定的連接

完成映射後，在 `config.xml` 指定：
- `transit.useTransit = true`
- `transit.routingAlgorithmType = SwissRailRaptor`
- `transit.transitScheduleFile` / `transit.vehiclesFile`
- `qsim.usingTransitInMobsim = true`

更完整的模擬參數請見 `docs/08-configuration/configuration-reference.md`。
