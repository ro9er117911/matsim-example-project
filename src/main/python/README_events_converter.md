# MATSim Events to JSON/Parquet Converter

> [!NOTE]
> 原始設計為 Via 平台相容格式，但 Via 已被 **SimWrapper** 取代為主要可視化框架。
> 此轉換器仍可用於生成 JSON/Parquet 格式供其他分析工具使用。

自動化轉換 MATSim `output_events.xml` 為 JSON 和 Parquet 格式（原為 Via 平台相容格式）。

## 功能特色

- ✅ **標準四模式輸出**: 統一為 `['BUS', 'CAR', 'RAIL', 'WALK']` 四種標準模式
- ✅ **網絡精確路徑**: 基於 network.xml 的精確路由重建（使用 NetworkX）
- ✅ **座標轉換**: 自動將 TWD97 (EPSG:3826) 轉換為 WGS84 (EPSG:4326) 經緯度
- ✅ **智能模式映射**: 自動從 vehicle ID 識別並統一公交模式（SUBWAY/METRO/TRAM/TRAIN → RAIL）
- ✅ **時間取樣**: 3 秒間隔取樣（與參考資料一致）
- ✅ **壓縮格式支援**: 自動處理 `.xml` 和 `.xml.gz` 壓縮檔
- ✅ **Agent ID 映射**: 自動提取字串 ID 中的數字（如 `pt_agent_01` → `1`）
- ✅ **高效壓縮**: Parquet 輸出僅為 JSON 的 ~14%（86% 壓縮率）

## 安裝依賴

```bash
pip3 install pyproj pandas pyarrow networkx
```

## 使用方式

### 基本用法

```bash
python3 src/main/python/events_to_json_parquet.py \
  --events scenarios/equil/forVia/output_events.xml \
  --network scenarios/equil/network-with-pt.xml \
  --json-out output/5000_abm_format_outcome.json \
  --parquet-out output/5000_abm_format_outcome.parquet
```

### 處理壓縮檔案

```bash
python3 src/main/python/events_to_json_parquet.py \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --json-out 5000_disatar/AGENT/INPUT/5000_abm_format_outcome.json \
  --parquet-out 5000_disatar/AGENT/OUTPUT/5000_abm_format_outcome.parquet
```

### 參數說明

| 參數 | 必填 | 說明 |
|------|------|------|
| `--events` | ✓ | MATSim output_events.xml 或 .xml.gz 路徑 |
| `--network` | ✓ | MATSim network.xml 或 .xml.gz 路徑（用於精確路徑重建） |
| `--json-out` | ✓ | 輸出 JSON 檔案路徑 |
| `--parquet-out` | ✓ | 輸出 Parquet 檔案路徑 |

## 輸出格式

### JSON 格式

```json
[
  {
    "agent_id": 1,
    "weekday_path": [
      {
        "position": [25.0019, 121.5390],
        "mode": "WALK"
      },
      {
        "position": [25.0020, 121.5392],
        "mode": "PT"
      }
    ],
    "weekday_timestamp": [21600, 21603, 21606, ...]
  }
]
```

**欄位說明**:
- `agent_id`: 整數型 agent ID
- `weekday_path`: 軌跡點陣列
  - `position`: `[latitude, longitude]` WGS84 經緯度
  - `mode`: 交通模式（CAR, WALK, PT, BUS, SUBWAY 等大寫字串）
- `weekday_timestamp`: 時間戳陣列（秒），與 `weekday_path` 長度相同

### Parquet 格式

| 欄位 | 類型 | 說明 |
|------|------|------|
| `agent_id` | int64 | Agent 識別碼 |
| `modes` | ndarray(int8) | 模式編碼陣列（1=CAR, 2=WALK, 3=PT, 4=BUS, 5=SUBWAY） |
| `timestamps` | ndarray(int32) | 時間戳陣列（秒） |
| `geometry` | ndarray(dict) | 座標陣列，每個元素為 `{'x': lat, 'y': lon}` |

## 轉換流程

```
┌─────────────────────┐
│ output_events.xml   │  316 events, 10 agents
└──────────┬──────────┘
           │
           ↓ Step 1: Parse events
┌─────────────────────┐
│ Event grouping      │  Group by person_id
└──────────┬──────────┘
           │
           ↓ Step 2: Parse network
┌─────────────────────┐
│ network.xml         │  2,422 nodes, 4,108 links
│ NetworkX Graph      │  Build routing graph
└──────────┬──────────┘
           │
           ↓ Step 3: Coordinate transform
┌─────────────────────┐
│ TWD97 → WGS84       │  pyproj Transformer
└──────────┬──────────┘
           │
           ↓ Step 4: Reconstruct trajectories
┌─────────────────────┐
│ Activity-Leg chains │  actend → departure → arrival → actstart
│ Network routing     │  Find shortest path between links
│ Position sampling   │  Sample every 3 seconds
└──────────┬──────────┘
           │
           ↓ Step 5: Export
┌─────────────────────┐     ┌─────────────────────┐
│ JSON output         │     │ Parquet output      │
│ 1.65 MB (10 agents) │     │ 0.23 MB (86% saved) │
└─────────────────────┘     └─────────────────────┘
```

## 驗證結果（測試案例）

### 輸入
- **Events**: 316 個事件，10 個 agents
- **Network**: 2,422 nodes, 4,108 links

### 輸出
- **JSON**: 1.65 MB, 10 agents, 每人平均 330 軌跡點
- **Parquet**: 0.23 MB (86.0% 壓縮)
- **座標範圍**:
  - Latitude: 23.47° ~ 25.17° (台灣範圍 ✓)
  - Longitude: 121.40° ~ 121.55° (台灣範圍 ✓)
- **取樣間隔**: 3 秒

## 技術細節

### 軌跡重建邏輯

腳本會處理以下事件序列：

1. **活動結束 (actend)** → 提取起點座標
2. **出發 (departure)** → 記錄交通模式 (walk, pt, car)
3. **路徑查找**:
   - 使用 NetworkX 在網絡圖中查找最短路徑
   - 沿路徑插值產生連續軌跡點
4. **到達 (arrival)** → 標記終點
5. **活動開始 (actstart)** → 下一段行程起點

### Agent ID 提取規則

- `"pt_agent_01"` → 提取後綴數字 → `1`
- `"car_agent_02"` → `2`
- `"4441"` → 直接轉換 → `4441`
- 無法解析時使用 hash 值

### 模式編碼（四種標準模式）

輸出統一為 **`['BUS', 'CAR', 'RAIL', 'WALK']`** 四種模式，與範本格式一致。

| MATSim 來源 | 映射規則 | JSON 輸出 | Parquet Code |
|-------------|---------|-----------|--------------|
| **car** (legMode) | 直接映射 | **CAR** | 1 |
| **walk** (legMode) | 直接映射 | **WALK** | 2 |
| **transit_walk, access_walk, egress_walk** | 合併為步行 | **WALK** | 2 |
| **activity** (actstart) | 停留視為步行 | **WALK** | 2 |
| **bus** (vehicle ID 含 "bus") | 直接映射 | **BUS** | 4 |
| **subway, metro** (vehicle ID) | 統一為軌道 | **RAIL** | 3 |
| **tram, train, rail** (vehicle ID) | 統一為軌道 | **RAIL** | 3 |
| **pt** (無法識別的公交) | 降級為軌道 | **RAIL** | 3 |

**模式識別邏輯**:
1. MATSim events 中的 `legMode` 對所有公交都標記為 `"pt"`
2. 腳本查找 `PersonEntersVehicle` 事件的 `vehicle` 屬性：
   - `bus_veh_22_bus` → **BUS**
   - `metro_veh_6843_subway` → **RAIL**
   - `train_veh_123` → **RAIL**
   - 無法識別 → **RAIL**（降級處理）

**驗證結果**（測試案例）:
```
BUS:    99 軌跡點 (0.8%)
RAIL:  835 軌跡點 (7.0%)  ← 包含所有 subway/metro/train
WALK: 11,028 軌跡點 (92.2%) ← 包含步行 + 活動停留
CAR:    0 軌跡點 (測試數據無 car)
```

## 常見問題

### Q: 為什麼只有四種模式？SUBWAY 和 METRO 呢？

**A: 為了與範本格式統一！** 輸出採用標準四模式分類 `['BUS', 'CAR', 'RAIL', 'WALK']`：

```xml
<!-- MATSim events 範例 -->
<event type="departure" legMode="pt" ... />  <!-- ❌ 只知道是 PT -->
<event type="PersonEntersVehicle" vehicle="bus_veh_22_bus" ... />        <!-- ✅ BUS -->
<event type="PersonEntersVehicle" vehicle="metro_veh_6843_subway" ... /> <!-- ✅ RAIL -->
<event type="PersonEntersVehicle" vehicle="tram_veh_456" ... />          <!-- ✅ RAIL -->
```

**映射規則**:
- **BUS** 保持獨立（公車）
- **SUBWAY, METRO, TRAM, TRAIN** 統一為 **RAIL**（軌道交通）
- 無法識別的 PT vehicle → 降級為 **RAIL**

**驗證結果**（測試案例）:
```
模式分布:
  BUS:    99 點 (vehicle ID 含 "bus")
  RAIL:  835 點 (subway/metro 統一為 RAIL)
  WALK: 11,028 點 (步行 + 活動停留)
  CAR:    0 點 (測試數據無 car agent)
```

**優點**:
1. 簡化模式分類，便於分析
2. 與範本 `['BUS', 'CAR', 'RAIL', 'WALK']` 完全一致
3. 符合交通分類慣例（軌道交通歸為一類）

### Q: 如何處理大型 events 檔案（100萬+ 事件）？

A: 腳本支援流式處理壓縮檔案，但非常大的檔案可能需要調整記憶體設定。建議：
- 使用 `.xml.gz` 壓縮格式
- 確保有足夠記憶體（建議 8GB+）
- 考慮分批處理（例如按時間窗口分割）

### Q: 如果 network.xml 不可用怎麼辦？

A: 腳本會自動降級到線性插值模式（直線連接起終點）。雖然不如網絡路由精確，但仍可產生可用的軌跡數據。

### Q: 輸出的座標系統是什麼？

A: 輸出統一使用 WGS84 (EPSG:4326) 經緯度格式：
- `position[0]` = latitude (緯度)
- `position[1]` = longitude (經度)

### Q: 如何驗證輸出正確性？

A: 使用以下 Python 腳本快速檢查：

```python
import json
import pandas as pd

# 檢查 JSON
with open('output.json') as f:
    data = json.load(f)
    print(f"Agents: {len(data)}")
    print(f"First agent trajectory points: {len(data[0]['weekday_path'])}")
    print(f"Coordinate sample: {data[0]['weekday_path'][0]['position']}")

# 檢查 Parquet
df = pd.read_parquet('output.parquet')
print(f"\nParquet agents: {len(df)}")
print(df.dtypes)
```

## 效能指標

| 資料規模 | 處理時間（估計） | 記憶體使用（估計） |
|---------|-----------------|-------------------|
| 10 agents, 300 events | < 5 秒 | < 100 MB |
| 100 agents, 3K events | ~10 秒 | ~200 MB |
| 5000 agents, 310K events | ~3 分鐘 | ~2 GB |

*實際效能取決於 network 複雜度和硬體規格*

## 參考資料

- 參考輸入格式: `/Users/ro9air/matsim-example-project/scenarios/equil/forVia/output_events.xml`
- 參考 Population: `/Users/ro9air/matsim-example-project/5000_disatar/output_test/population.xml`
- 參考 JSON 輸出: `/Users/ro9air/matsim-example-project/5000_disatar/AGENT/INPUT/5000_abm_format_outcome.json`
- 參考 Parquet 輸出: `/Users/ro9air/matsim-example-project/5000_disatar/AGENT/OUTPUT/5000_abm_format_outcome.parquet`

## 授權

本腳本為 MATSim example project 的一部分，遵循相同的開源授權條款。
