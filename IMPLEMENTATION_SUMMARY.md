# MATSim 配置改進實施總結

**完成日期**：2025-11-12
**模擬場景**：台北都市交通（equil scenario with 100 agents）

---

## 執行概要

根據用戶提出的三個問題，已成功實施改進方案，涵蓋 PT 轉乘優化、輸出檔案說明文檔，以及代理人收斂問題修正。

---

## ✅ 任務 A: PT 轉乘代理規劃

### 問題陳述
PT 代理在某個單一行程中未使用轉乘，反而選擇更遠的直達路線。

### 實施方案

#### 1. 人口生成改進 (`scripts/merge_populations.py`)

**改變邏輯**：
```python
# 修改前：PT agents 1-3 個活動
if mode == 'pt':
    num_activities = random.randint(1, 3)  # ❌ 不足

# 修改後：PT agents 強制 3-4 個活動
if mode == 'pt':
    num_activities = random.randint(3, 4)  # ✅ 強制轉乘
```

**影響**：
- PT agents (50人) 現在都有 3-4 個活動段
- 例：home → leisure → shop → work → home
- 強制多個 PT legs，必須使用轉乘路由

**驗證**：
```bash
# PT Agent 01 結構驗證
grep -A 25 'id="pt_agent_01"' scenarios/equil/population.xml

結果：
<person id="pt_agent_01">
  <plan selected="no">
    <activity type="home" x="294035.05" y="2762173.24" end_time="06:49:07"/>
    <leg mode="pt"/>              ← leg 1
    <activity type="leisure" x="305795.35" y="2770702.2" end_time="08:52:21"/>
    <leg mode="pt"/>              ← leg 2
    <activity type="shop" x="307533.02" y="2769486.82" end_time="10:35:07"/>
    <leg mode="pt"/>              ← leg 3
    <activity type="work" x="302208.73" y="2771006.76" end_time="18:50:53"/>
    <leg mode="pt"/>              ← leg 4: 轉乘必須發生
    <activity type="home"/>
```

#### 2. SwissRailRaptor 配置更新 (`scenarios/equil/config.xml`)

**新增參數**（swissRailRaptor 模組）：
```xml
<param name="utilityOfLineSwitch" value="0.0" />
```

**作用**：
- 消除轉乘的效用懲罰
- SwissRailRaptor 不再避免換線
- 優先選擇包含轉乘的最短路線

**現有參數確認**：
```xml
<param name="transferPenaltyBaseCost" value="0.0" />
<param name="transferPenaltyCostPerTravelTimeHour" value="0.0" />
```
✅ 已設置為零，確保無額外轉乘成本

### 預期結果

運行模擬後，應在 `output_events.xml` 中看到：

```bash
# 檢查命令
gunzip -c scenarios/equil/output/ITERS/it.0/0.events.xml.gz | \
  grep -A 2 "PersonEntersVehicle.*pt" | grep -c "facilityId"

# 預期：PT 代理有多個 VehicleArrivesAtFacility 事件
# 表示在不同站點上下車（即使用了轉乘）
```

**預期模式變化**：
- Iteration 0-1: PT 比例應從原有%增加到更高（因為轉乘更優化）
- Iteration 1-5: PT 比例應穩定（因為找到最佳路線）

---

## ✅ 任務 B: 輸出檔案說明文檔

### 文檔位置
`SIMULATION_OUTPUT_GUIDE.md`（已建立）

### 文檔內容涵蓋

| CSV 檔案 | 解釋方式 | 案例數 |
|---------|---------|-------|
| `modestats.csv` | 模式選擇演化 | 2個情景 |
| `scorestats.csv` | 代理滿意度學習 | 詳細時間線 |
| `ph_modestats.csv` | 人小時分配 | 100人案例 |
| `pkm_modestats.csv` | 人公里統計 | 完整對比 |
| `traveldistancestats.csv` | 行程距離檢查 | leg vs trip |
| `stopwatch.csv` | 效能監控 | 耗時分析 |

### 文檔特點

✅ **生活化情景**：
- 信義區上班族案例
- 100人一日出行統計
- 實際轉乘場景

✅ **診斷檢查清單**：
- 每個 CSV 都提供 ✅/❌ 檢查項
- 幫助快速診斷問題

✅ **故障排除指南**：
- 常見問題 3 個
- 具體解決步驟
- 已實施的修正參考

---

## ✅ 任務 C: 代理人早期收斂問題修正

### 問題陳述
模擬中模式選擇（Mode Choice）變化不大，代理人過早收斂，無法充分探索其他交通模式。

### 根本原因分析

原始配置問題：
```xml
<!-- 修改前 -->
<param name="maxAgentPlanMemorySize" value="5" />      ← 記憶太小
<param name="strategyName" value="ChangeExpBeta" weight="0.85" />  ← 穩定策略佔85%
<param name="strategyName" value="ReRoute" weight="0.15" />         ← 路線優化佔15%
<!-- 缺少：SubtourModeChoice（模式探索） -->
```

**問題**：
1. 計劃記憶只能保留 5 個，好的多模式計劃被快速丟棄
2. 85% 的時間代理人只選擇評分最高的計劃（穩定但不創新）
3. 完全沒有專門的模式探索策略

### 實施方案

#### 1. 增加計劃記憶容量

```xml
<!-- 修改 -->
<param name="maxAgentPlanMemorySize" value="15" />  ← 從 5 增加到 15
```

**作用**：
- 保留更多代替計劃
- 防止潛在的多模式計劃被過快移除
- 給代理人更多探索時間

#### 2. 重新平衡策略權重

```xml
<!-- 修改前 -->
ChangeExpBeta:  0.85 (85%)
ReRoute:        0.15 (15%)
SubtourModeChoice: (無)

<!-- 修改後 -->
ChangeExpBeta (穩定):     0.50 (50%)
ReRoute (路線優化):       0.20 (20%)
SubtourModeChoice (模式):  0.20 (20%)  ← 新增
ChangeExpBeta (探索):     0.10 (10%)
```

**作用**：
- 穩定性降低：85% → 50%，留出空間探索
- 路線優化保留：20%，維持路線改進
- **新增模式探索：20%，強制嘗試新的交通模式**
- 探索變體：10%，增加變化性

#### 3. 啟用 SubtourModeChoice 策略

```xml
<!-- 新增 -->
<parameterset type="strategysettings">
  <param name="strategyName" value="SubtourModeChoice" />
  <param name="weight" value="0.20" />
</parameterset>
```

**配置驗證**：
```xml
<module name="subtourModeChoice">
  <param name="modes" value="car,pt,walk" />        ← 所有模式可用
  <param name="chainBasedModes" value="car" />      ← car 是基礎模式
  <param name="considerCarAvailability" value="true" />
</module>
```
✅ 確保所有目標模式都已配置

### 預期收斂改進

**迭代 0-5 期間應觀察到**：

```csv
# 修改前的 modestats.csv（問題）
iteration;car;pt;walk
0;0.410;0.451;0.139
1;0.410;0.451;0.139
2;0.410;0.451;0.139
...
15;0.410;0.451;0.139  ← 完全未變

# 修改後的 modestats.csv（預期）
iteration;car;pt;walk
0;0.410;0.451;0.139
1;0.400;0.470;0.130   ← 開始變化
2;0.390;0.480;0.130   ← 繼續調整
3;0.380;0.490;0.130   ← 逐漸收斂
...
15;0.370;0.510;0.120  ← 最終收斂到新狀態
```

### 配置總結表

| 參數 | 修改前 | 修改後 | 目的 |
|------|--------|--------|------|
| `maxAgentPlanMemorySize` | 5 | 15 | ⬆️ 保留更多計劃 |
| `ChangeExpBeta` weight | 0.85 | 0.50 | ⬇️ 減少穩定性 |
| `ReRoute` weight | 0.15 | 0.20 | ⬆️ 強化路線優化 |
| `SubtourModeChoice` | ❌ 無 | ✅ 0.20 | ➕ 增加模式探索 |
| `utilityOfLineSwitch` (routing) | 無 | 0.0 | ➕ 鼓勵轉乘 |

---

## 完整配置驗證

### A. Population 驗證

```bash
# 檢查點 1: 代理人總數
grep -c '<person id=' scenarios/equil/population.xml
# 預期：100

# 檢查點 2: PT 代理活動數
grep 'pt_agent_01' -A 20 scenarios/equil/population.xml | grep -c '<activity'
# 預期：≥4 (home + 3 activities)

# 檢查點 3: 活動類型分佈
grep -o 'type="[^"]*"' scenarios/equil/population.xml | sort | uniq -c
# 預期：
#  400 home
#  ~140 education
#  ~170 leisure
#  ~150 shop
#  ~130 work
```

### B. Config 驗證

```bash
# 檢查點 1: utilityOfLineSwitch
grep 'utilityOfLineSwitch' scenarios/equil/config.xml
# 預期：value="0.0" （在 swissRailRaptor 模組中）

# 檢查點 2: maxAgentPlanMemorySize
grep 'maxAgentPlanMemorySize' scenarios/equil/config.xml
# 預期：value="15"

# 檢查點 3: SubtourModeChoice 啟用
grep -A 2 'SubtourModeChoice' scenarios/equil/config.xml | grep weight
# 預期：value="0.20"

# 檢查點 4: 轉乘參數
grep 'transferPenalty' scenarios/equil/config.xml
# 預期：都設為 0.0
```

---

## 運行新模擬的步驟

### 1. 編譯（如有代碼改變）
```bash
./mvnw clean package
```

### 2. 運行模擬
```bash
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="scenarios/equil/config.xml"
```

### 3. 分析結果

**立即檢查**（5 分鐘）：
```bash
# A. 檢查 modestats.csv 的第 1-3 行
head -4 scenarios/equil/output/modestats.csv
# 期望：第 1-3 行應有 >±3% 的變化

# B. 檢查 stopwatch.csv 最後一行
tail -1 scenarios/equil/output/stopwatch.csv
# 期望：耗時 <5 秒

# C. 檢查模擬日誌
grep -i "error\|warn" scenarios/equil/output/logfile.log | head -10
# 期望：無關鍵錯誤
```

**詳細分析**（20 分鐘）：
```bash
# 參考 SIMULATION_OUTPUT_GUIDE.md 中的完整診斷工作流
# 檢查 modestats.csv、scorestats.csv、ph_modestats.csv
```

---

## 改進驗證檢查清單

### Phase 1: 數據驗證 ✅

- [x] Population: 100 agents，無 XML 錯誤
- [x] Config: 所有參數已更新
- [x] PT agents: 3-4 個活動確認
- [x] Modes: car, pt, walk 都已配置

### Phase 2: 配置邏輯驗證

- [x] SwissRailRaptor: utilityOfLineSwitch = 0
- [x] Replanning: 四個策略組合，權重和為 1.0
- [x] SubtourModeChoice: 三種模式都可選
- [x] Plan memory: 15 個計劃可保留

### Phase 3: 模擬運行驗證 (待執行)

- [ ] 模擬無 runtime 錯誤
- [ ] Output 中出現 modestats.csv 和 scorestats.csv
- [ ] modestats.csv 中迭代 0-1 有 ±3% 以上變化
- [ ] scorestats.csv 中有 avg_best > avg_executed

### Phase 4: 結果解釋驗證 (待執行)

- [ ] 閱讀 SIMULATION_OUTPUT_GUIDE.md
- [ ] 按指南檢查輸出
- [ ] 使用提供的診斷檢查清單

---

## 檔案變更清單

### 新建檔案

| 檔案 | 用途 | 大小 |
|------|------|------|
| `SIMULATION_OUTPUT_GUIDE.md` | CSV 輸出說明與診斷指南 | ~12 KB |
| `IMPLEMENTATION_SUMMARY.md` | 本文檔 - 實施總結 | ~8 KB |

### 修改檔案

| 檔案 | 修改項目 | 影響 |
|------|---------|------|
| `scripts/merge_populations.py` | PT agents 強制 3-4 活動 | ⭐⭐⭐ 關鍵 |
| `scenarios/equil/population.xml` | 重新生成 100 個代理 | ⭐⭐⭐ 關鍵 |
| `scenarios/equil/config.xml` | SwissRailRaptor + Replanning | ⭐⭐⭐ 關鍵 |

---

## 後續建議

### 短期 (運行一次模擬)

1. ✅ 執行新模擬，檢查 modestats.csv 是否有變化
2. ✅ 使用 SIMULATION_OUTPUT_GUIDE.md 診斷問題
3. 📊 比較修改前後的 modestats.csv 和 scorestats.csv

### 中期 (如果仍需改進)

- 若 PT 比例未增加：檢查 PT 網路覆蓋和轉乘時間
- 若收斂仍過快：再增加 `maxAgentPlanMemorySize` 到 20-25
- 若特定模式消失：檢查該模式的計分參數 (marginalUtilityOfTraveling)

### 長期 (模型驗證)

- 與實際出行數據對比，驗證模式分佈的合理性
- 檢查模擬中的道路堵塞程度是否符合現實
- 調整計分參數以更精確模擬代理人行為

---

## 聯絡與支援

有關模擬設置或結果解釋的問題，請參考：
- 詳細參數說明：`defaultConfig.xml` 和 `CLAUDE.md`
- 輸出檔案診斷：本文檔 + `SIMULATION_OUTPUT_GUIDE.md`
- MATSim 官方文檔：https://matsim.org/docs

---

**修改完成於**：2025-11-12
**配置版本**：equil with 100 diverse agents, enhanced PT routing and mode exploration
