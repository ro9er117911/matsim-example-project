# MATSim 人口代理改進 - 詳細 TODO 清單

**Created:** 2025-11-05
**Target Week:** 2025-11-05 ~ 2025-11-09
**Status:** 待執行 (Pending Execution)

---

## ✅ Phase 1：快速修復 - 走路時間限制

**預計時間：** 1-2 小時
**難度：** 🟢 容易 (Easy)
**修改檔案：** 2 個
**風險：** 低

### 1.1 修改 generate_test_population.py - 第 264 行

**檔案：** `src/main/python/generate_test_population.py`
**行號：** 264
**當前：** `MAX_WALK_DURATION_MIN = 30`
**改為：** `MAX_WALK_DURATION_MIN = 20`

```python
# BEFORE
MAX_WALK_DURATION_MIN = 30          # Car agents shouldn't have walk leg > 30 min

# AFTER
MAX_WALK_DURATION_MIN = 20          # Car agents shouldn't have walk leg > 20 min
```

**驗證方式：**
```bash
grep "MAX_WALK_DURATION_MIN" src/main/python/generate_test_population.py
# 應該看到：MAX_WALK_DURATION_MIN = 20
```

---

### 1.2 修改 validate_population.py - 第 217 行

**檔案：** `src/main/python/validate_population.py`
**行號：** 217
**當前：** `MAX_WALK_LEG_DURATION_MIN = 30`
**改為：** `MAX_WALK_LEG_DURATION_MIN = 20`

```python
# BEFORE
MAX_WALK_LEG_DURATION_MIN = 30  # Car agents shouldn't walk >30 minutes

# AFTER
MAX_WALK_LEG_DURATION_MIN = 20  # Car agents shouldn't walk >20 minutes
```

**驗證方式：**
```bash
grep "MAX_WALK_LEG_DURATION_MIN" src/main/python/validate_population.py
# 應該看到：MAX_WALK_LEG_DURATION_MIN = 20
```

---

### 1.3 重新生成人口文件

**指令：**
```bash
cd /Users/ro9air/matsim-example-project
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py 2>&1 | tee phase1_generation.log
```

**預期輸出：**
```
Generating 20 single-line PT agents...
Generating 10 PT transfer agents...
Generating 15 car agents...
Generating 5 walk agents...

POPULATION GENERATION COMPLETE
================================================================================

✓ Output file: scenarios/equil/test_population_50.xml

Agent Generation Summary:
  PT single-line agents:
    - Created: 20/20
    - Skipped: 0
  PT transfer agents (multi-line):
    - Created: ? (可能 < 10 因為走路時間限制)
    - Skipped: ?
  Car agents:
    - Created: 15/15
    - Skipped: 0
  Walk agents:
    - Created: 5/5
    - Skipped: 0

  TOTAL AGENTS:
    - Created: ? (可能 < 50)
    - Skipped: ?
```

**記錄關鍵數字：**
- [ ] PT single-line created: ___/20
- [ ] PT transfer created: ___/10
- [ ] Car created: ___/15
- [ ] Walk created: ___/5
- [ ] **總計：** ___/50

---

### 1.4 驗證新人口文件

**指令：**
```bash
python src/main/python/validate_population.py scenarios/equil/test_population_50.xml 2>&1 | tee phase1_validation.log
```

**預期輸出格式：**
```
POPULATION VALIDATION
================================================================================

Validating agents...
Checking spatial constraints...
Checking mode consistency...
Checking leg durations...
Checking PT transfer agents...
Checking temporal constraints...

VALIDATION REPORT
================================================================================

Population Summary:
  Total agents: ?
  Total activities: ?
  Total legs: ?

Total Errors: 0
Total Warnings: ?
```

**檢查清單：**
- [ ] `Total Errors: 0`（沒有錯誤，只允許警告）
- [ ] 無 "walk leg exceeds" 錯誤訊息
- [ ] 檢查警告訊息（應該比之前少）

---

### 1.5 分析日誌並記錄結果

**檢查項目：**
```bash
# 確認走路腿限制的變更
grep "walk leg" phase1_validation.log

# 確認代理生成統計
grep "Created:" phase1_generation.log

# 檢查是否有時間相關警告
grep "Excessive\|exceeds\|duration" phase1_validation.log
```

**記錄數據：**
- [ ] 轉運代理數變化：6 → ___
- [ ] 是否有新的走路時間警告：是 / 否
- [ ] 是否有代理被跳過：是 / 否
- [ ] 被跳過的代理列表：_________

---

### 1.6 提交 Phase 1 改動

**指令：**
```bash
git add src/main/python/generate_test_population.py \
        src/main/python/validate_population.py \
        scenarios/equil/test_population_50.xml

git commit -m "Phase 1: Reduce max walk leg duration from 30 to 20 minutes

Changes:
- generate_test_population.py: MAX_WALK_DURATION_MIN = 20 (line 264)
- validate_population.py: MAX_WALK_LEG_DURATION_MIN = 20 (line 217)
- Regenerated test_population_50.xml with new constraints

Impact:
- Total agents: 50 → ? (某些代理因走路時間被拒絕)
- Warnings: ? (比之前少)
- Errors: 0

🤖 Generated with Claude Code"
```

**驗證提交：**
```bash
git log --oneline -1
# 應該看到新的 commit
```

---

## ✅ Phase 2：OSM 邊界驗證與修復

**預計時間：** 1-2 小時
**難度：** 🟡 中等 (Medium)
**修改檔案：** 1-2 個
**風險：** 中等（影響汽車代理選擇）

### 2.1 讀取網絡檔案並提取邊界

**指令（使用 Python）：**
```python
import gzip
import xml.etree.ElementTree as ET

# 讀取網絡檔案
with gzip.open('scenarios/equil/network-with-pt.xml.gz', 'rt') as f:
    tree = ET.parse(f)
    root = tree.getroot()

# 提取所有 link 的座標範圍
min_x, max_x = float('inf'), float('-inf')
min_y, max_y = float('inf'), float('-inf')

link_count = 0
for link in root.findall('.//link'):
    from_node = root.find(f".//node[@id='{link.get('from')}']")
    to_node = root.find(f".//node[@id='{link.get('to')}']")

    if from_node is not None:
        x, y = float(from_node.get('x')), float(from_node.get('y'))
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
        link_count += 1

print(f"Network bounds from {link_count} links:")
print(f"  X: {min_x:.0f} ~ {max_x:.0f} (range: {max_x - min_x:.0f} m)")
print(f"  Y: {min_y:.0f} ~ {max_y:.0f} (range: {max_y - min_y:.0f} m)")
```

**記錄結果：**
- [ ] Network X range: _______ ~ _______
- [ ] Network Y range: _______ ~ _______
- [ ] Link count: _______

---

### 2.2 檢查現有 OSM_BOUNDS

**檔案：** `src/main/python/generate_test_population.py`
**行號：** 71-80

```python
# 現有邊界
OSM_BOUNDS = {
    'top_left': (288137, 2783823),
    'bottom_left': (287627, 2768820),
    'bottom_right': (314701, 2769311),
    'top_right': (314401, 2784363),
}
```

**提取邊界範圍：**
- [ ] X min: 287627
- [ ] X max: 314701
- [ ] X range: 27,074 m (27 km)
- [ ] Y min: 2768820
- [ ] Y max: 2783823
- [ ] Y range: 15,003 m (15 km)

---

### 2.3 比對所有站點座標

**指令：**
```bash
python << 'EOF'
from generate_test_population import STATIONS, OSM_BOUNDS

xs = [OSM_BOUNDS[k][0] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]
ys = [OSM_BOUNDS[k][1] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]
x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)

print(f"OSM Bounds: X=[{x_min}, {x_max}], Y=[{y_min}, {y_max}]\n")
print(f"{'Station':<10} {'Name':<20} {'X':<10} {'Y':<10} {'Status':<15}")
print("=" * 70)

outside_count = 0
for station_id in sorted(STATIONS.keys()):
    name, x, y = STATIONS[station_id]
    inside = x_min <= x <= x_max and y_min <= y <= y_max
    status = "INSIDE ✓" if inside else "OUTSIDE ✗"
    if not inside:
        outside_count += 1
    print(f"{station_id:<10} {name:<20} {x:<10.0f} {y:<10.0f} {status:<15}")

print(f"\nSummary: {len(STATIONS) - outside_count}/48 stations INSIDE, {outside_count} OUTSIDE")
EOF
```

**記錄邊界外的站點：**
- [ ] 邊界外站點列表：_________
- [ ] 邊界外站點數：_____/48
- [ ] 主要問題區域（北/南/東/西）：_____

---

### 2.4 決定修復方案

**選項 A：擴大邊界**
- 目標：包含所有或大多數站點
- 方法：調整 OSM_BOUNDS 座標
- 優點：保持所有站點可用
- 缺點：可能包含不存在的區域

**選項 B：排除邊界外站點**
- 目標：保持當前邊界，不修改站點過濾
- 方法：保持代碼不變（汽車代理自動過濾）
- 優點：嚴格遵守網絡邊界
- 缺點：可用站點減少（可能 < 30 個）

**建議方案：** _____（A 或 B）

**理由：** ___________

---

### 2.5 修改 OSM_BOUNDS（如果選擇方案 A）

**檔案：** `src/main/python/generate_test_population.py`
**行號：** 71-80

```python
# BEFORE
OSM_BOUNDS = {
    'top_left': (288137, 2783823),
    'bottom_left': (287627, 2768820),
    'bottom_right': (314701, 2769311),
    'top_right': (314401, 2784363),
}

# AFTER（根據步驟 2.1 的結果調整）
OSM_BOUNDS = {
    'top_left': (_______, _______),
    'bottom_left': (_______, _______),
    'bottom_right': (_______, _______),
    'top_right': (_______, _______),
}
```

**修改依據：**
- [ ] 新邊界基於網絡邊界（如果方案 A）
- [ ] 新邊界包含 BL02, BL06（南邊擴展）

---

### 2.6 重新生成人口文件

**指令：**
```bash
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py 2>&1 | tee phase2_generation.log
```

**檢查汽車站點：**
```bash
grep "Car-valid" phase2_generation.log
```

**記錄數據：**
- [ ] Car-valid stations: ___/48
- [ ] 變化：之前 32 → 現在 ___（應該增加）

---

### 2.7 驗證汽車代理邊界

**指令：**
```bash
python src/main/python/validate_population.py scenarios/equil/test_population_50.xml 2>&1 | tee phase2_validation.log
```

**檢查項目：**
```bash
grep "outside\|OUTSIDE" phase2_validation.log
# 應該看不到任何邊界外錯誤
```

**記錄結果：**
- [ ] 邊界外汽車代理：0
- [ ] 驗證通過：是 / 否

---

### 2.8 提交 Phase 2 改動

**指令（如果修改了 OSM_BOUNDS）：**
```bash
git add src/main/python/generate_test_population.py \
        scenarios/equil/test_population_50.xml

git commit -m "Phase 2: Verify and adjust OSM bounds for car agents

Changes:
- OSM_BOUNDS expanded to include all road network stations
- Car-valid stations: 32 → ? (increased)

Result:
- All car agents' home and work within bounds ✓
- Validation: 0 boundary errors
- Total agents: ?/50

🤖 Generated with Claude Code"
```

---

## ✅ Phase 3：PT 轉運深度修復

**預計時間：** 2-4 小時
**難度：** 🔴 困難 (Hard)
**修改檔案：** 2-3 個
**風險：** 中等（可能導致 XML 格式變更）

### 3.1 提取實際停靠點 ID

**指令（使用 Python）：**
```python
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict

# 讀取轉運時間表
with gzip.open('scenarios/equil/transitSchedule-mapped.xml.gz', 'rt') as f:
    tree = ET.parse(f)
    root = tree.getroot()

# 建立停靠設施 ID 映射
stop_mapping = {}  # station_name -> [pt_link_ids]

for facility in root.findall('.//stopFacility'):
    facility_id = facility.get('id')
    link_ref = facility.find('linkRefId')
    if link_ref is not None:
        link_id = link_ref.text
        # 例如：pt_BL02_UP
        stop_mapping[facility_id] = link_id

print("Stop Facility Mapping:")
for facility_id, link_id in sorted(stop_mapping.items())[:10]:
    print(f"  {facility_id} → {link_id}")

print(f"\nTotal stops found: {len(stop_mapping)}")
```

**記錄映射：**
- [ ] 停靠點總數：_____
- [ ] 樣本映射：BL02_UP → ________
- [ ] 樣本映射：G14_UP → ________

---

### 3.2 創建站點 ID → PT Link ID 映射函數

**修改檔案：** `src/main/python/generate_test_population.py`
**位置：** 在 `is_valid_car_trip()` 函數之後（大約第 245 行）

**新增函數：**
```python
# PT Stop Facility Mapping
# 將 STATION_ID (如 'BL02') 映射到 PT link ID (如 'pt_BL02_UP')
PT_STOP_MAPPING = {
    # BL Line
    'BL02': ('pt_BL02_UP', 'pt_BL02_DN'),
    'BL06': ('pt_BL06_UP', 'pt_BL06_DN'),
    'BL10': ('pt_BL10_UP', 'pt_BL10_DN'),
    'BL11': ('pt_BL11_UP', 'pt_BL11_DN'),
    'BL12': ('pt_BL12_UP', 'pt_BL12_DN'),
    'BL14': ('pt_BL14_UP', 'pt_BL14_DN'),
    'BL15': ('pt_BL15_UP', 'pt_BL15_DN'),
    'BL16': ('pt_BL16_UP', 'pt_BL16_DN'),
    'BL19': ('pt_BL19_UP', 'pt_BL19_DN'),
    'BL22': ('pt_BL22_UP', 'pt_BL22_DN'),
    # G Line (continues...)
    # ... (需要完整列出所有 48 個站點)
}

def get_pt_stop_link_ids(station_id, direction='UP'):
    """Get PT stop facility link IDs for a station.

    Args:
        station_id: Station ID (e.g., 'BL02')
        direction: 'UP' or 'DN' (upstream/downstream in route)

    Returns:
        Link ID (e.g., 'pt_BL02_UP')
    """
    if station_id not in PT_STOP_MAPPING:
        return None

    up_link, dn_link = PT_STOP_MAPPING[station_id]
    return up_link if direction == 'UP' else dn_link
```

**任務：**
- [ ] 完整 PT_STOP_MAPPING 映射表（所有 48 個站點）
- [ ] `get_pt_stop_link_ids()` 函數實現
- [ ] 測試函數（驗證返回正確的 link ID）

---

### 3.3 修改 generate_pt_agent() 函數

**檔案：** `src/main/python/generate_test_population.py`
**行號：** 144-164

**BEFORE：**
```python
def generate_pt_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a PT agent"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    # ... 省略 ...

    xml = f'''	<!-- PT Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) -->
	<person id="pt_agent_{agent_id:02d}">
		<plan selected="yes">
			<!-- Morning trip: home to work -->
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="walk" />
			<activity type="pt interaction" x="{home_x:.2f}" y="{home_y:.2f}" max_dur="00:05:00" />
			<leg mode="pt" />
			<activity type="pt interaction" x="{work_x:.2f}" y="{work_y:.2f}" max_dur="00:05:00" />
			<!-- ... -->
```

**AFTER：**
```python
def generate_pt_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a PT agent with proper stop facility IDs"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    # Get PT stop link IDs (use 'UP' direction for boarding)
    home_link = get_pt_stop_link_ids(home_station, 'UP')
    work_link = get_pt_stop_link_ids(work_station, 'UP')

    if home_link is None or work_link is None:
        return None  # Station not in PT network

    morning_depart = format_time(departure_hour, departure_min)

    # ... 其他代碼保持不變 ...

    xml = f'''	<!-- PT Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) -->
	<person id="pt_agent_{agent_id:02d}">
		<plan selected="yes">
			<!-- Morning trip: home to work -->
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="walk" />
			<activity type="pt interaction" link="{home_link}" max_dur="00:05:00" />
			<leg mode="pt" />
			<activity type="pt interaction" link="{work_link}" max_dur="00:05:00" />
			<!-- ... -->
```

**修改重點：**
- [ ] 添加 `home_link` 和 `work_link` 提取
- [ ] 檢查返回值是否為 None（站點無效）
- [ ] 將 `x="{x}" y="{y}"` 改為 `link="{link}"`

---

### 3.4 修改 generate_transfer_pt_agent() 函數

**檔案：** `src/main/python/generate_test_population.py`
**行號：** 166-238

**類似上面的改動：**
- [ ] 添加 4 個 link 變數（home, transfer1, transfer2, work）
- [ ] 使用 `get_pt_stop_link_ids()` 提取
- [ ] 驗證所有 link 都有效
- [ ] 將所有 `<activity type="pt interaction">` 改為使用 `link` 屬性

---

### 3.5 調查缺失的轉運代理

**分析：** 為什麼只生成 6 個轉運代理（缺少 4 個）？

**指令：**
```python
from generate_test_population import (
    PT_TRANSFER_ROUTES, MAX_TRIP_TIME_MINUTES,
    get_station_distance_m, estimate_trip_time_minutes
)

print("PT Transfer Routes Analysis:")
print(f"{'Route':<50} {'Distance':<15} {'Time':<10} {'Status':<15}")
print("=" * 90)

for i, (home, t1, t2, work) in enumerate(PT_TRANSFER_ROUTES):
    total_distance = (
        get_station_distance_m(home, t1) +
        get_station_distance_m(t1, t2) +
        get_station_distance_m(t2, work)
    )
    total_time = estimate_trip_time_minutes(total_distance, 'pt') + 8  # +8 for transfer wait

    route_name = f"{home}→{t1}→{t2}→{work}"
    status = "✓ OK" if total_time <= MAX_TRIP_TIME_MINUTES else "✗ TOO LONG"

    print(f"{route_name:<50} {total_distance:<15.0f} {total_time:<10.1f} {status:<15}")
```

**記錄結果：**
- [ ] 超過時間限制的路線：_________
- [ ] 超時幅度：_____ 分鐘
- [ ] 原因分類：
  - [ ] 距離太遠
  - [ ] 轉運等待時間太長
  - [ ] 速度模型不準確

---

### 3.6 修復轉運時間估計

**選項 A：提高 PT 速度模型**
```python
# BEFORE
MODE_SPEEDS_M_PER_MIN = {
    'pt': 500,     # ~30 km/h with stops
    'car': 417,
    'walk': 84,
}

# AFTER
MODE_SPEEDS_M_PER_MIN = {
    'pt': 550,     # ~33 km/h with stops (提高)
    'car': 417,
    'walk': 84,
}
```

**選項 B：降低轉運等待時間**
```python
# BEFORE (line 182 in generate_transfer_pt_agent)
transfer_time = 8  # 5 min walk + 3 min wait for next train

# AFTER
transfer_time = 5  # 3 min walk + 2 min wait for next train
```

**選項 C：提高時間上限**
```python
# BEFORE
MAX_TRIP_TIME_MINUTES = 40

# AFTER
MAX_TRIP_TIME_MINUTES = 45
```

**推薦選項：** A（提高 PT 速度）

**實施方法：**
- [ ] 編輯第 91-95 行，改 `'pt': 500` 為 `'pt': 550`
- [ ] 重新生成人口
- [ ] 檢查轉運代理數是否增加

---

### 3.7 重新生成人口文件

**指令：**
```bash
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py 2>&1 | tee phase3_generation.log
```

**檢查轉運代理：**
```bash
grep "PT transfer agents" phase3_generation.log
# 應該看到：Created: 10/10（現在完整）
```

**記錄數據：**
- [ ] PT transfer created: ___/10（應該 = 10）
- [ ] 轉運代理缺失：是 / 否

---

### 3.8 驗證 PT 停靠點 ID

**指令：**
```bash
# 檢查 XML 中的 link 屬性
grep 'activity type="pt interaction"' scenarios/equil/test_population_50.xml | head -5

# 應該看到：
# <activity type="pt interaction" link="pt_BL02_UP" max_dur="00:05:00" />
# 而不是：
# <activity type="pt interaction" x="..." y="..." max_dur="00:05:00" />
```

**驗證結果：**
- [ ] 所有 PT 活動都使用 `link` 屬性（不是 `x`, `y`）
- [ ] 所有 link ID 格式為 `pt_STATION_DIR`
- [ ] 沒有座標屬性：是 / 否

---

### 3.9 執行驗證

**指令：**
```bash
python src/main/python/validate_population.py scenarios/equil/test_population_50.xml 2>&1 | tee phase3_validation.log
```

**檢查項目：**
- [ ] 0 個錯誤
- [ ] 查看轉運代理統計（應該 = 10）
- [ ] 無 PT 活動缺少 link ID 的錯誤

---

### 3.10 提交 Phase 3 改動

**指令：**
```bash
git add src/main/python/generate_test_population.py \
        scenarios/equil/test_population_50.xml

git commit -m "Phase 3: Fix PT transfer agents and use proper stop facility IDs

Changes:
- Added PT_STOP_MAPPING for all 48 stations
- Added get_pt_stop_link_ids() function
- Updated generate_pt_agent() to use link IDs instead of coordinates
- Updated generate_transfer_pt_agent() similarly
- Increased PT speed model from 500 to 550 m/min to fix transfer timing

Result:
- All PT agents use valid stop facility link IDs ✓
- All 10 transfer routes now generate agents (was 6) ✓
- All 4 missing transfer agents recovered ✓
- Total agents: ?/50

🤖 Generated with Claude Code"
```

---

## ✅ Phase 4：整體驗證與測試

**預計時間：** 1-2 小時
**難度：** 🟢 容易 (Easy)
**修改檔案：** 0 個（僅執行和測試）
**風險：** 低

### 4.1 完整驗證

**指令：**
```bash
python src/main/python/validate_population.py scenarios/equil/test_population_50.xml 2>&1 | tee phase4_validation.log
```

**檢查清單：**
```bash
# 0 個錯誤
grep "Total Errors:" phase4_validation.log
# 應該看到：Total Errors: 0

# 檢查代理數
grep "Total agents:" phase4_validation.log
# 應該看到：Total agents: 50（理想）或接近

# 檢查警告（應該很少）
grep "Total Warnings:" phase4_validation.log

# 驗證沒有邊界外錯誤
grep "outside\|OUTSIDE" phase4_validation.log | wc -l
# 應該 = 0

# 驗證轉運代理有 4 個 PT 腿
grep "PT transfer agent" phase4_validation.log
```

**記錄結果：**
- [ ] Total Errors: _____（應該 = 0）
- [ ] Total Agents: _____（應該 = 50）
- [ ] Total Warnings: _____
- [ ] 邊界外錯誤：_____（應該 = 0）
- [ ] 驗證狀態：✓ 通過 / ✗ 失敗

---

### 4.2 構建項目

**指令：**
```bash
cd /Users/ro9air/matsim-example-project
./mvnw clean package -q 2>&1 | tail -20
```

**預期輸出：**
```
[INFO] BUILD SUCCESS
[INFO] Total time: XX seconds
[INFO] Final Memory: XXM/XXXM
```

**驗證：**
- [ ] BUILD SUCCESS
- [ ] 沒有編譯錯誤
- [ ] target/matsim-example-project-0.0.1-SNAPSHOT.jar 已創建

---

### 4.3 運行短期模擬測試

**指令：**
```bash
cd scenarios/equil/
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.lastIteration 2 \
  --config:controller.snapshotFormat null 2>&1 | tee simulation.log
```

**預期運行時間：** 2-3 分鐘

**監視輸出：**
```bash
# 實時查看進度
tail -f simulation.log
```

**預期輸出：**
```
Iteration 0 starting ...
  (iteration runs)
Iteration 0 finished after XXX sec.

Iteration 1 starting ...
Iteration 1 finished after XXX sec.

Iteration 2 starting ...
Iteration 2 finished after XXX sec.
```

**記錄：**
- [ ] 迭代 0 耗時：_____ 秒
- [ ] 迭代 1 耗時：_____ 秒
- [ ] 迭代 2 耗時：_____ 秒

---

### 4.4 檢查模擬錯誤日誌

**指令：**
```bash
# 檢查致命錯誤
grep -i "error\|exception\|failed" output/logfile.log | head -20

# 檢查 ClassCastException（PT 路由問題的指標）
grep "ClassCastException" output/logfile.log

# 檢查路由失敗
grep -i "routing.*fail\|cannot.*route" output/logfile.log
```

**結果檢查：**
- [ ] ClassCastException：0 個（應該沒有）
- [ ] 路由失敗：0 個（應該沒有）
- [ ] 總錯誤數：_____

---

### 4.5 檢查統計結果

**指令：**
```bash
cd output/

# 查看代理分數演化
echo "=== Agent Scores Evolution ==="
head -6 scorestats.csv
echo ""

# 查看模式選擇
echo "=== Mode Statistics ==="
head -6 modestats.csv
echo ""

# 查看旅程距離
echo "=== Travel Distance ==="
head -6 traveldistancestats.csv
```

**記錄結果：**

| Iteration | avg_executed | avg_best | 說明 |
|-----------|--------------|----------|------|
| 0 | _____ | _____ | 輸入人口 |
| 1 | _____ | _____ | 代理開始重新規劃 |
| 2 | _____ | _____ | 收斂 |

**代理分數預期：**
- Iteration 0: 20-30（輸入人口，可能有負分）
- Iteration 1: 30-40（開始改善）
- Iteration 2: 40-50（逐步改善）

**記錄模式統計：**
```bash
# 按模式計算腿數
head -6 modestats.csv | tail -3
```

- [ ] Car legs: _____ (應該 ~30)
- [ ] PT legs: _____ (應該 ~60+，不是走路回退)
- [ ] Walk legs: _____ (應該 ~30-40)

---

### 4.6 Via 導出測試

**指令：**
```bash
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out forVia \
  --dt 5 2>&1 | tee via_export.log
```

**預期輸出：**
```
[Stage 1] Parsing plans...
[Stage 2] Parsing events...
[Stage 3] Filtering events...
[Stage 4] Building tracks...
✓ Export complete!
```

**驗證檔案：**
```bash
ls -lh forVia/
```

**預期檔案：**
- [ ] output_events.xml (1-2 MB)
- [ ] output_network.xml.gz (3-4 MB)
- [ ] tracks_dt5s.csv (100+ KB)
- [ ] legs_table.csv
- [ ] filtered_vehicles.csv
- [ ] vehicle_usage_report.txt

---

### 4.7 最終驗證清單

- [ ] 所有驗證通過（0 個錯誤）
- [ ] 模擬成功完成（3 個迭代）
- [ ] 沒有 ClassCastException
- [ ] 代理分數逐次改善
- [ ] PT 代理使用公共運輸（非走路）
- [ ] Via 導出成功
- [ ] 所有輸出檔案已創建

---

### 4.8 最終提交

**指令：**
```bash
git add scenarios/equil/test_population_50.xml \
        scenarios/equil/output \
        working_journal/

git commit -m "Phase 4: Complete validation and testing - all improvements verified

Testing Results:
- Population validation: ✓ 0 errors, 50 agents
- Simulation (2 iterations): ✓ Successful
- Agent scores: Iteration 0 → 2, improving
- PT agents: Using transit (not walk fallback)
- Car agents: All within OSM bounds
- Via export: ✓ Successful

Summary:
✓ Walk duration limit: < 20 minutes
✓ Car agents: All within OSM bounds
✓ PT agents: Using valid stop facility IDs
✓ Transfer agents: All 10 generated successfully
✓ Simulation: No routing failures
✓ Visualization: Via export ready

Ready for full 50-iteration production run!

🤖 Generated with Claude Code"
```

---

## 📊 進度追蹤表 (Progress Tracking)

```
Phase | Task | Status | Date | Notes
------|------|--------|------|-------
1     | Walk duration limit | [ ] | |
1.1   | Modify generate_test_population.py | [ ] | |
1.2   | Modify validate_population.py | [ ] | |
1.3   | Regenerate population | [ ] | |
1.4   | Validate | [ ] | |
1.5   | Analyze results | [ ] | |
1.6   | Commit Phase 1 | [ ] | |
------|------|--------|------|-------
2     | OSM bounds | [ ] | |
2.1   | Extract network bounds | [ ] | |
2.2   | Check current bounds | [ ] | |
2.3   | Compare all stations | [ ] | |
2.4   | Decide approach (A/B) | [ ] | |
2.5   | Modify OSM_BOUNDS | [ ] | |
2.6   | Regenerate population | [ ] | |
2.7   | Validate | [ ] | |
2.8   | Commit Phase 2 | [ ] | |
------|------|--------|------|-------
3     | PT transfer fix | [ ] | |
3.1   | Extract stop IDs | [ ] | |
3.2   | Create mapping | [ ] | |
3.3   | Modify generate_pt_agent | [ ] | |
3.4   | Modify generate_transfer_pt_agent | [ ] | |
3.5   | Investigate missing agents | [ ] | |
3.6   | Fix transfer timing | [ ] | |
3.7   | Regenerate population | [ ] | |
3.8   | Verify link IDs | [ ] | |
3.9   | Validate | [ ] | |
3.10  | Commit Phase 3 | [ ] | |
------|------|--------|------|-------
4     | Final testing | [ ] | |
4.1   | Full validation | [ ] | |
4.2   | Build project | [ ] | |
4.3   | Run simulation | [ ] | |
4.4   | Check logs | [ ] | |
4.5   | Analyze results | [ ] | |
4.6   | Via export | [ ] | |
4.7   | Final checklist | [ ] | |
4.8   | Final commit | [ ] | |
```

---

*Created: 2025-11-05*
*Ready for Execution: Next Week*
*Expected Completion: 2025-11-09*
