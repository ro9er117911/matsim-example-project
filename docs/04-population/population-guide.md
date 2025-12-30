# Population 產生與結構指南

本文件整理 population.xml 的結構、常見代理人模板、生成工具與驗證流程，並涵蓋 ABM 軌跡壓縮轉換的實務做法。

## 輸入與輸出

### 輸入
- `network.xml(.gz)`（若要使用 link-based activity/route）
- GTFS/站點資料（用於產生 PT 旅次）

### 輸出
- `population.xml(.gz)`

---

## 一、population.xml 結構

```xml
<population>
  <person id="agent_001">
    <plan selected="yes">
      <activity type="home" x="300000" y="2770000" end_time="07:30:00"/>
      <leg mode="pt"/>
      <activity type="work" x="305000" y="2771000" end_time="17:00:00"/>
      <leg mode="car"/>
      <activity type="home" x="300000" y="2770000"/>
    </plan>
  </person>
</population>
```

重點：
- **activity** 描述停留點；**leg** 描述移動模式
- 最後一個 activity 通常不設 `end_time`
- PT 旅次需包含 `pt interaction` 活動（上下車）

---

## 二、常見代理人模板

### 1) PT 代理人（含轉乘）

```xml
<leg mode="walk"/>
<activity type="pt interaction" x="..." y="..." max_dur="00:05:00"/>
<leg mode="pt">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
</leg>
```

### 2) Car 代理人

```xml
<activity type="home" x="..." y="..." end_time="07:30:00"/>
<leg mode="car"/>
<activity type="work" x="..." y="..." end_time="17:00:00"/>
```

### 3) Walk 代理人

```xml
<activity type="home" x="..." y="..." end_time="08:00:00"/>
<leg mode="walk"/>
<activity type="work" x="..." y="..." end_time="14:00:00"/>
```

---

## 三、人口生成工具與路徑

### 測試場景（台北）
- `src/main/python/generate_test_population.py`
- 輸出：`scenarios/corridor/taipei_test/test_population_50.xml`

### 5000 災難撤離
- `5000_disatar/05_scripts/json_to_population.py`
- `5000_disatar/05_scripts/generate_evacuation_population.py`
- `5000_disatar/05_scripts/augment_population.py`

---

## 四、空間與時間約束（避免不合理旅次）

在 `generate_test_population.py` 內常見設定：

```python
OSM_BOUNDS = {
  'top_left': (288137, 2783823),
  'bottom_left': (287627, 2768820),
  'bottom_right': (314701, 2769311),
  'top_right': (314401, 2784363),
}
MAX_TRIP_TIME_MINUTES = 40
MODE_SPEEDS_M_PER_MIN = {
  'pt': 500,
  'car': 417,
  'walk': 84,
}
```

用途：
- car 代理人限制在 OSM 邊界內
- 避免超長或不合理旅次

---

## 五、ABM 軌跡 → MATSim Plan（壓縮策略）

**不要**把「每 3 秒一個座標」直接寫成大量活動，會導致效能崩潰與行為失真。建議壓縮為：

```xml
<activity type="start" x="起點" y="起點" end_time="03:18:00"/>
<leg mode="car"/>
<activity type="end" x="終點" y="終點"/>
```

若需保留原路徑，可將座標序列做 map-matching，寫入 `route`：

```xml
<leg mode="car" dep_time="03:18:00" trav_time="00:22:05">
  <route type="links" start_link="L_start" end_link="L_end">
    L2 L3 L4 L5
  </route>
</leg>
```

---

## 六、驗證工具

```bash
python src/main/python/validate_population.py <population.xml>

tools/validate-agent-journey.sh <population.xml> <network.xml.gz>

python3 5000_disatar/05_scripts/validation/validate_population_routes.py \
  --plans <population.xml.gz> \
  --network <network.xml.gz>
```

---

## 七、常見問題與修正

### 1) Agents 超出路網範圍
- **解法**：限制 car station 範圍或重新採樣座標

### 2) trip 過長 / 不合理
- **解法**：縮短最大旅行時間或調整速度模型

### 3) link-based 活動找不到 link
- **解法**：改用座標型 activity，或先做 link ID 驗證

### 4) PT 代理人無轉乘互動
- **解法**：補上 `pt interaction` 與 `routingMode` 屬性
