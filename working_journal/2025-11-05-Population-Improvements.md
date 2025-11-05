# MATSim 人口代理改進計劃 - Population Improvements Roadmap

**Date:** 2025-11-05
**Status:** ✅ Analysis Complete, Ready for Execution
**Target Completion:** 2025-11-09 (End of Week)

---

## 🔍 問題分析 (Issue Analysis)

### 問題 1️⃣：走路時間超限 (Walk Duration Over Limit)

**現象：**
- 許多代理使用走路模式
- 某些走路段超過合理時間限制

**根本原因：**
- 目前設定：`MAX_WALK_DURATION_MIN = 30` 分鐘 (line 264 in generate_test_population.py)
- 驗證上限：`MAX_WALK_LEG_DURATION_MIN = 30` 分鐘 (line 217 in validate_population.py)
- **用戶要求改為：20 分鐘**

**技術細節：**
- 人口文件中所有 `<leg mode="walk" />` 都缺少 `trav_time` 屬性
- 實際旅程時間由 MATSim 路由引擎在運行時計算
- 驗證工具無法檢測 XML 中的時間（因為沒有記錄）
- 時間限制只在**生成階段**強制執行

**影響：**
- PT 代理每人 6 個走路腿（access + transfer + egress × 2 方向）
- 汽車代理沒有走路腿
- 走路代理有 2 個短走路腿
- 限制從 30 → 20 分鐘可能導致某些 PT 路線被拒絕

---

### 問題 2-1️⃣：汽車代理 OD 在 OSM 範圍外 (Car Agents Outside OSM Bounds)

**現象：**
- 汽車代理被分配到不存在於道路網絡的地點
- 代理會「直接走路在不存在的地圖上」

**根本原因分析：**

**邊界定義（generate_test_population.py lines 71-80）：**
```python
OSM_BOUNDS = {
    'top_left': (288137, 2783823),      # 西北
    'bottom_left': (287627, 2768820),   # 西南
    'bottom_right': (314701, 2769311),  # 東南
    'top_right': (314401, 2784363),     # 東北
}
# X 範圍：287627 ~ 314701 (27 km)
# Y 範圍：2768820 ~ 2783823 (15 km)
```

**問題站點（超出邊界）：**
- BL02 (永寧)：y = 2762173 **< 2768820** (南邊超出 ~6 km)
- BL06 (府中)：y = 2766793 **< 2768820** (南邊超出 ~2 km)
- R22 (北投)：可能超出北邊界
- R28 (淡水)：可能超出北邊界

**驗證邏輯（正確）：**
```python
# generate_test_population.py lines 176-181
if mode == 'car':
    if not is_within_osm_bounds(home_x, home_y):
        return False
    if not is_within_osm_bounds(work_x, work_y):
        return False
```
✓ 邏輯正確，可用站點已過濾

**根本問題：**
- OSM_BOUNDS 座標**可能不准確**（需要與實際網絡邊界驗證）
- 邊界不對稱 (27km × 15km) 導致某些方向的站點被排除

---

### 問題 2-2️⃣：PT 代理不使用轉運 (PT Agents Not Using Transfers)

**現象：**
- PT 代理直接選擇走路而非使用公共運輸
- 轉運功能沒有被正確使用

**根本原因（多層次）：**

#### 層次 1：人口文件格式不相容 (Format Incompatibility)
```xml
<!-- 目前的做法（問題） -->
<activity type="pt interaction" x="302208.73" y="2771006.76" max_dur="00:05:00" />
<leg mode="pt" />
<activity type="pt interaction" x="303804.19" y="2770590.71" max_dur="00:05:00" />

<!-- 應該的做法（需修復） -->
<activity type="pt interaction" link="pt_BL12_UP" max_dur="00:05:00" />
<leg mode="pt" />
<activity type="pt interaction" link="pt_BL14_UP" max_dur="00:05:00" />
```

**問題詳解：**
- `<activity type="pt interaction">` 是**合成的活動**，不對應真實停靠站
- 應該使用 `link="pt_STATION_ID"` 指向 `transitSchedule.xml` 中的實際停靠點
- 沒有有效的 link ID，SwissRailRaptor 無法驗證停靠點
- 路由失敗 → 回退到走路模式

#### 層次 2：SwissRailRaptor 配置
```xml
<!-- scenarios/equil/config.xml lines 82-94 -->
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false" />
  <param name="transferPenaltyBaseCost" value="0.0" />
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0" />
  <param name="useModeMappingForPassengers" value="false" />
</module>
```
✓ 配置正確，但依賴於人口文件中的有效 link ID

#### 層次 3：轉運代理生成不完全 (Incomplete Transfer Agent Generation)
```
預期：10 個 PT 轉運路線 → 10 個轉運代理
實際：只生成了 6 個轉運代理
缺少：pt_transfer_agent_01, _03, _05, _08 (4 個)
```

**原因假設：**
- 某些路線總旅程時間超過 `MAX_TRIP_TIME_MINUTES = 40` 分鐘
- 這些路線在生成過程中被跳過

---

## 📊 當前人口統計 (Population Statistics)

**test_population_50.xml 當前狀態：**
```
代理類型                     生成/預期    狀態
────────────────────────────────────────
PT 單線代理                  20/20      ✓ 完整
PT 轉運代理                  6/10       ✗ 缺少 4 個
汽車代理                     15/15      ✓ 完整
走路代理                     5/5        ✓ 完整
────────────────────────────────────────
總計                        46/50      ✗ 缺少 4 個代理
```

**走路腿統計：**
- PT 代理：6 腿/代理 (access → pt → pt interaction → pt → egress) × 2 方向
- 汽車代理：0 腿/代理
- 走路代理：2 腿/代理 (home → work, work → home)
- **總走路腿數：** 20×6 + 6×6 + 5×2 = 192 腿

**OSM 邊界內的汽車站點：**
- 過濾結果：32/48 站點（某些站點超出邊界）
- 所有 15 個汽車代理的 home 和 work 都在有效站點內 ✓

---

## 🛠️ 改進計劃 (Improvement Plan)

### Phase 1：快速修復 - 走路時間限制 (1-2 小時)

**修改檔案：**

1. **generate_test_population.py**
   - Line 264：`MAX_WALK_DURATION_MIN = 30` → `MAX_WALK_DURATION_MIN = 20`

2. **validate_population.py**
   - Line 217：`MAX_WALK_LEG_DURATION_MIN = 30` → `MAX_WALK_LEG_DURATION_MIN = 20`

**執行步驟：**
```bash
# 1. 修改代碼（見上）
# 2. 重新生成人口
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py

# 3. 驗證
python src/main/python/validate_population.py scenarios/equil/test_population_50.xml
```

**預期結果：**
- 某些 PT 代理因走路時間過長被拒絕
- 總代理數可能減少（例如 46 → 40）
- 驗證報告顯示新的走路腿時間限制

**成功標準：**
- ✓ 無代理有走路腿超過 20 分鐘
- ✓ 驗證報告 0 個超時警告

---

### Phase 2：OSM 邊界驗證與修復 (1-2 小時)

**分析步驟：**

1. **提取實際網絡邊界**
   - 讀取 `scenarios/equil/network-with-pt.xml.gz`
   - 掃描所有 `<link>` 元素，提取座標範圍
   - 找出網絡的實際邊界

2. **檢查所有站點座標**
   - 對比 STATIONS 字典中所有 48 個站點
   - 識別哪些在當前 OSM_BOUNDS 外
   - 記錄超出的距離

3. **決定修復方案**

**方案 A：擴大邊界（推薦）**
- 修改 OSM_BOUNDS 以包含所有或大多數站點
- 包含 BL02, BL06（南邊）
- 可能保持某些極端站點（北邊）排除

**方案 B：排除邊界外站點（嚴格）**
- 保持當前邊界
- 汽車代理只使用 32 個內部站點
- 降低多樣性

**推薦：** 先嘗試方案 A（擴大邊界），確保網絡完整覆蓋

**修改點：**
```python
# generate_test_population.py lines 71-80
OSM_BOUNDS = {
    'top_left': (288137, 2783823),      # 需要驗證
    'bottom_left': (287627, 2768820),   # 可能需要向南擴展
    'bottom_right': (314701, 2769311),  # 可能需要向南擴展
    'top_right': (314401, 2784363),     # 需要驗證
}
```

**驗證命令：**
```bash
# 生成並檢查汽車有效站點
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py | grep "Car-valid"

# 預期看到更多有效站點（目前 32/48）
```

**成功標準：**
- ✓ 邊界座標已驗證（與網絡邊界匹配）
- ✓ 所有汽車代理的 home 和 work 都在邊界內
- ✓ 驗證報告 0 個邊界外錯誤

---

### Phase 3：PT 轉運深度修復 (2-4 小時)

**3-1：人口文件格式修復**

**目標：** 從座標轉換到有效的停靠點 link ID

**步驟：**
1. 編寫腳本提取 `transitSchedule-mapped.xml.gz` 中的實際停靠點
2. 建立映射：STATION_ID → pt_STATION_UP/DN
3. 修改人口生成函數使用 link 屬性

**代碼修改位置：**
- `generate_test_population.py`
  - Line 144-164：`generate_pt_agent()` 函數
  - Line 166-238：`generate_transfer_pt_agent()` 函數

**修改方向：**
```python
# BEFORE
xml = f'''
<activity type="pt interaction" x="{home_x:.2f}" y="{home_y:.2f}" max_dur="00:05:00" />
<leg mode="pt" />
<activity type="pt interaction" x="{work_x:.2f}" y="{work_y:.2f}" max_dur="00:05:00" />
'''

# AFTER
home_link = get_stop_link_id(home_station)  # e.g., "pt_BL02_UP"
work_link = get_stop_link_id(work_station)  # e.g., "pt_BL14_UP"

xml = f'''
<activity type="pt interaction" link="{home_link}" max_dur="00:05:00" />
<leg mode="pt" />
<activity type="pt interaction" link="{work_link}" max_dur="00:05:00" />
'''
```

**3-2：補全缺失的轉運代理**

**調查：**
- 10 個 `PT_TRANSFER_ROUTES` 中，為什麼只生成 6 個？
- 檢查各路線的估計旅程時間：`estimate_trip_time_minutes(distance, 'pt')`

**可能的原因：**
1. 某些路線總時間 > 40 分鐘（MAX_TRIP_TIME_MINUTES）
2. 轉運時間估計過高
3. 距離計算有誤

**修復選項：**

| 選項 | 方法 | 影響 |
|------|------|------|
| A | 增加 PT 速度模型 | 從 500 m/min 提高到 550+ m/min |
| B | 降低轉運 wait 時間 | 從 8 分鐘降低到 5 分鐘 |
| C | 提高 MAX_TRIP_TIME_MINUTES | 從 40 → 45 或 50 分鐘 |
| D | 調整具體路線 | 排除某些極長路線 |

**推薦：** 先嘗試選項 A（提高 PT 速度），保持現有路由

**修改點：**
```python
# generate_test_population.py line 92
MODE_SPEEDS_M_PER_MIN = {
    'pt': 500,     # 考慮改為 550 m/min （33 km/h）
    'car': 417,
    'walk': 84,
}
```

**3-3：強制驗證轉運特性**

**檢查清單：**
- ✓ 所有 10 個轉運代理都被生成（不再缺少）
- ✓ 每個轉運代理有 4 個 PT 腿（2 早上 + 2 晚上）
- ✓ 轉運代理確實需要轉運（不能用單線完成）
- ✓ 所有 PT 活動都有有效的 link ID

**驗證命令：**
```python
# 在 validate_population.py 中添加新檢查
def _validate_pt_transfers(self):
    """驗證所有 PT 轉運代理的正確性"""
    for agent_id in self.agents.keys():
        if agent_id.startswith('pt_transfer_agent_'):
            legs = self.agents[agent_id]['legs']
            pt_legs = [leg for leg in legs if leg['mode'] == 'pt']

            # 應該有 4 個 PT 腿（2 早上 + 2 晚上）
            if len(pt_legs) != 4:
                self.errors.append(f"{agent_id}: Expected 4 PT legs, got {len(pt_legs)}")

            # 驗證活動有 link 屬性（不是座標）
            activities = self.agents[agent_id]['activities']
            for activity in activities:
                if activity['type'] == 'pt interaction':
                    if 'link' not in activity:
                        self.errors.append(f"{agent_id}: pt interaction missing link ID")
```

**成功標準：**
- ✓ 所有 PT 代理有有效的 link 屬性（pt_STATION_ID）
- ✓ 10 個轉運代理全部生成（無缺失）
- ✓ 每個轉運代理有 4 個 PT 腿
- ✓ SwissRailRaptor 能識別有效停靠點

---

### Phase 4：整體驗證與測試 (1-2 小時)

**4-1：完整驗證**
```bash
python src/main/python/validate_population.py scenarios/equil/test_population_50.xml
```

**檢查清單：**
- [ ] 0 個錯誤（只允許警告）
- [ ] 所有代理的走路腿 < 20 分鐘
- [ ] 所有汽車代理的 OD 在 OSM 邊界內
- [ ] 所有 PT 代理有有效的 link ID
- [ ] 所有轉運代理有 4 個 PT 腿

**4-2：簡短模擬測試**
```bash
cd scenarios/equil/
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.lastIteration 2 \
  --config:controller.snapshotFormat null
```

**檢查輸出：**
- [ ] 模擬成功完成（iteration 0, 1, 2）
- [ ] 無 ClassCastException 錯誤
- [ ] 無 "Network is not connected" 致命錯誤
- [ ] 無路由失敗日誌

**4-3：檢查結果統計**
```bash
cd output/
# 查看代理分數演化
head -5 scorestats.csv

# 查看模式選擇
head -5 modestats.csv

# 查看錯誤日誌
grep -i "error\|failed" ../logfile.log | wc -l
```

**預期結果：**
```
Iteration | avg_executed | Interpretation
0         | 20-30        | Input population (may have issues)
1         | 30-40        | Agents start replanning
2         | 40-50        | Agents converging to better plans

modestats.csv:
  car: ~30 legs
  pt: ~60+ legs (should NOT be walk fallback)
  walk: ~30-40 legs
```

**4-4：Via 導出驗證**
```bash
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out forVia \
  --dt 5
```

**成功標準：**
- ✓ 驗證 100% 通過（0 個錯誤）
- ✓ 模擬運行無關鍵錯誤
- ✓ 代理分數逐次改善
- ✓ PT 代理使用公共運輸（不是走路回退）
- ✓ Via 導出成功

---

## 📋 詳細 TODO 清單 (Detailed Todo List)

見檔案：[2025-11-05-Population-Improvements-TODO.md](2025-11-05-Population-Improvements-TODO.md)

---

## 📈 進度追蹤 (Progress Tracking)

### Week 1 (2025-11-05 ~ 2025-11-09)

**Phase 1：走路時間限制**
- [ ] 代碼修改完成
- [ ] 人口重新生成
- [ ] 驗證通過
- [ ] 提交 (Commit)

**Phase 2：OSM 邊界**
- [ ] 邊界驗證完成
- [ ] 修正決策完成
- [ ] 人口重新生成
- [ ] 驗證通過
- [ ] 提交 (Commit)

**Phase 3：PT 轉運修復**
- [ ] 停靠點 ID 映射建立
- [ ] 人口文件格式更新
- [ ] 缺失代理調查完成
- [ ] 轉運代理全部生成
- [ ] 驗證通過
- [ ] 提交 (Commit)

**Phase 4：整體測試**
- [ ] 完整驗證通過
- [ ] 簡短模擬測試完成
- [ ] Via 導出成功
- [ ] 最終提交 (Commit)

---

## 🎯 成功指標 (Success Criteria)

| 指標 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| 走路時間上限 | 20 分鐘 | 20 分鐘 | 20 分鐘 | 20 分鐘 ✓ |
| 汽車代理邊界 | - | ✓ | ✓ | ✓ |
| PT 停靠點 ID | - | - | ✓ | ✓ |
| 轉運代理數 | 6 | 6 | 10 | 10 ✓ |
| 驗證錯誤數 | 0 | 0 | 0 | 0 ✓ |
| 模擬成功 | - | - | - | ✓ |
| Via 導出 | - | - | - | ✓ |

---

## 📚 參考檔案 (Reference Files)

**人口生成工具：**
- [src/main/python/generate_test_population.py](../../src/main/python/generate_test_population.py)

**驗證工具：**
- [src/main/python/validate_population.py](../../src/main/python/validate_population.py)

**配置：**
- [scenarios/equil/config.xml](../../scenarios/equil/config.xml)

**數據：**
- [scenarios/equil/network-with-pt.xml.gz](../../scenarios/equil/network-with-pt.xml.gz)
- [scenarios/equil/transitSchedule-mapped.xml.gz](../../scenarios/equil/transitSchedule-mapped.xml.gz)

---

*Last Updated: 2025-11-05*
*Next Review: After Phase 1 Completion*
