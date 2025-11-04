# MATSim PT 模擬錯誤應對指南

## 執行日期
2025-10-29

---

## 執行日期更新
2025-11-03: 新增 PT Sequential Routing 錯誤診斷與修復

## 目錄
1. [模擬測試流程](#模擬測試流程)
2. [常見錯誤和解決方案](#常見錯誤和解決方案)
3. [警告信息處理](#警告信息處理)
4. [除錯工具和命令](#除錯工具和命令)
5. [檢查清單](#檢查清單)

---

## 模擬測試流程

### 基本測試命令
```bash
cd scenarios/taipei-metro-test
java -Xmx4g -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml
```

### 完整測試流程
```bash
# 1. 驗證檔案存在
ls -lh network-with-pt.xml.gz transitSchedule-mapped.xml.gz transitVehicles.xml

# 2. 檢查配置檔案
cat config.xml | grep -E "(Network|Schedule|Vehicles|transit)"

# 3. 運行模擬（單次迭代測試）
java -Xmx4g -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.lastIteration 0 2>&1 | tee test-run.log

# 4. 檢查輸出
ls -lh output/

# 5. 驗證 PT 運行
gunzip -c output/output_events.xml.gz | grep -E "(PersonEntersVehicle|PersonLeavesVehicle|TransitDriver)" | head -20
```

---

## 常見錯誤和解決方案

### 1. 檔案載入錯誤

#### Error: `FileNotFoundException` - transitSchedule.xml not found
**症狀**:
```
Exception in thread "main" java.io.FileNotFoundException: transitSchedule-mapped.xml.gz
```

**原因**: 配置檔案中的路徑錯誤或檔案不存在

**解決方案**:
```bash
# 檢查檔案是否存在
ls -lh scenarios/taipei-metro-test/transitSchedule-mapped.xml.gz

# 確認 config.xml 中的路徑
grep transitScheduleFile config.xml

# 如果使用相對路徑，確保從正確的目錄運行
pwd
```

#### Error: `FileNotFoundException` - network-with-pt.xml.gz not found
**解決方案**: 同上，檢查網路檔案路徑

---

### 2. PT 路由錯誤

#### Error: `No route found between stops`
**症狀**:
```
ERROR: No route found from stopFacility BL12_UP to BL14_UP
```

**原因**:
- 網路連接性問題
- 停靠站未正確映射到網路連結
- 連結缺少 "pt" 模式

**解決方案**:
```bash
# 1. 檢查停靠站的 linkRefId 是否存在於網路中
gunzip -c transitSchedule-mapped.xml.gz | grep "BL12_UP"
gunzip -c network-with-pt.xml.gz | grep "pt_BL12_UP"

# 2. 檢查連結是否有 pt 模式
gunzip -c network-with-pt.xml.gz | grep -A5 "link id=\"pt_BL12_UP\"" | grep modes

# 3. 如果網路有問題，重新準備網路
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.PrepareNetworkForPTMapping \
  network.xml.gz network-cleaned.xml.gz

# 4. 如果問題持續，重新運行 PT mapping (Plan B: SpeedyALT)
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-metro-v4.xml
```

---

### 3. 車輛相關錯誤

#### Error: `Vehicle not found`
**症狀**:
```
ERROR: Vehicle tr_1 not found in VehicleContainer
```

**原因**:
- transitVehicles.xml 未載入
- vehicles 模組配置錯誤

**解決方案**:
```bash
# 1. 檢查 config.xml 中的 vehicles 模組
cat config.xml | grep -A5 "module name=\"vehicles\""

# 2. 確認應該有:
# <module name="vehicles">
#   <param name="vehiclesFile" value="transitVehicles.xml" />
# </module>

# 3. 驗證 transitVehicles.xml 檔案內容
head -50 transitVehicles.xml
```

#### Error: `VehicleType not defined`
**解決方案**:
- 確保 transitVehicles.xml 包含 vehicleType 定義
- 檢查 transitSchedule 中的車輛引用是否與 transitVehicles 中定義的 type 匹配

---

### 4. 代理人計劃錯誤

#### Error: `No valid plan for person`
**症狀**:
```
ERROR: Person pt_commuter_bl_01 has no valid executable plan
```

**原因**:
- PT 路線格式錯誤
- 活動連結不存在於網路中
- 模式不支援

**解決方案**:
```bash
# 1. 檢查人口檔案中的 PT 路線格式
head -100 population.xml

# 2. 確保 PT leg 格式正確（不需要詳細路線，只需 mode="pt"）
# <leg mode="pt" />

# 3. 檢查活動連結是否存在
gunzip -c network-with-pt.xml.gz | grep "link id=\"pt_BL07_UP\""

# 4. 檢查 config.xml 中 qsim 的 mainMode 包含 pt
grep mainMode config.xml
# 應該看到: <param name="mainMode" value="car,pt" />
```

---

### 5. PT 代理人直線傳輸錯誤（2025-11-03 新增）

#### Problem: "PT Agents Using Straight-Line Transmission"
**症狀**:
- PT 代理人從出發站直接傳輸到目的地，不訪問任何中間站點
- 模擬可以運行，但代理人的路由不符合時刻表
- 事件日誌中看不到中間站點的 `VehicleArrivesAtFacility` 事件

**根本原因**:
```xml
<!-- 錯誤配置：PT 被設定為 teleportedModeParameters -->
<module name="routing">
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="pt"/>
    <param name="teleportedModeSpeed" value="20.0"/>
  </parameterset>
</module>
```

這導致 SwissRailRaptor 路由引擎無法啟用，代理人使用直線傳輸而不是真實的 PT 網路路由。

**診斷步驟**:
```bash
# 1. 檢查 config.xml 中是否有 PT 的 teleportedModeParameters
grep -A3 "teleportedModeParameters" config.xml | grep -i "pt"

# 2. 驗證虛擬 PT 網路是否存在
gunzip -c network-with-pt.xml.gz | grep -c "link id=\"pt_"
# 應該有數百個 pt_ 開頭的 links

# 3. 檢查時刻表中的停靠點
gunzip -c transitSchedule-mapped.xml.gz | grep "arrivalOffset\|departureOffset" | head -20

# 4. 驗證模擬事件
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "VehicleArrivesAtFacility.*pt_BL0[2-9]\|pt_BL1[0-4]" | head -20

# 如果沒有輸出，說明代理人沒有訪問中間站點
```

**解決方案**:

**第 1 步**: 移除 PT 的 teleportedModeParameters
```xml
<!-- ❌ 刪除此區塊（如果存在） -->
<!--
<parameterset type="teleportedModeParameters">
  <param name="mode" value="pt"/>
  <param name="teleportedModeSpeed" value="20.0"/>
</parameterset>
-->

<!-- ✅ 只保留 walk 相關的 teleportedModeParameters -->
<parameterset type="teleportedModeParameters">
  <param name="mode" value="walk" />
  <param name="teleportedModeSpeed" value="1.388888888" />
  <param name="beelineDistanceFactor" value="1.3" />
</parameterset>
```

**第 2 步**: 確保 SwissRailRaptor 模組配置正確
```xml
<module name="swissRailRaptor">
  <!-- 禁用 intermodal access/egress（除非 population 計畫支持） -->
  <param name="useIntermodalAccessEgress" value="false" />

  <!-- 零轉乘成本確保選擇最短路線 -->
  <param name="transferPenaltyBaseCost" value="0.0" />
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0" />

  <!-- 不使用模式映射 -->
  <param name="useModeMappingForPassengers" value="false" />
</module>
```

**第 3 步**: 驗證配置正確
```bash
# 確認檢查清單
# - [ ] PT NOT in routing.networkModes
# - [ ] PT NOT in qsim.mainMode
# - [ ] PT NOT in teleportedModeParameters
# - [ ] transit.useTransit = true
# - [ ] transit.usingTransitInMobsim = true

grep -E "networkModes|mainMode|useTransit|usingTransit" config.xml
```

**第 4 步**: 重新運行模擬並驗證
```bash
# 重新構建和運行
./mvnw clean package
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="scenarios/equil/config.xml"

# 驗證結果（應該看到所有中間站點）
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "VehicleArrivesAtFacility" | grep "pt_BL" | \
  awk -F'facility=' '{print $2}' | cut -d'"' -f2 | sort
# 預期輸出: BL01_UP, BL02_UP, BL03_UP, ..., BL23_UP (完整序列)
```

**成功標誌**:
```
✅ 事件日誌顯示所有中間站點
✅ VehicleArrivesAtFacility 按照時刻表順序出現
✅ PersonEntersVehicle 和 PersonLeavesVehicle 正確匹配
✅ 模擬完成，無 "direct transmission" 報告
```

---

### 6. 內存錯誤

#### Error: `OutOfMemoryError: Java heap space`
**症狀**:
```
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
```

**解決方案**:
```bash
# 增加 Java heap size
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# 或更大 (根據可用記憶體)
java -Xmx12g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# 對於大型網路，也可以縮放容量因子
# 在 config.xml 中設定:
# <param name="flowCapacityFactor" value="0.1" />
# <param name="storageCapacityFactor" value="0.1" />
```

---

### 6. QSim 錯誤

#### Error: `Agent stuck`
**症狀**:
```
WARN: Agent pt_commuter_bl_01 is stuck at link 81226
```

**原因**:
- 出發時間過晚，無法完成行程
- PT 服務時間不足
- 網路容量問題

**解決方案**:
```bash
# 1. 檢查 transitSchedule 中的發車時刻
gunzip -c transitSchedule-mapped.xml.gz | grep departure | head -20

# 2. 調整代理人出發時間（確保在 PT 服務時間內）
# 編輯 population.xml，調整 end_time

# 3. 增加 PT 發車頻率（如果需要）
# 需要重新運行 GTFS 轉換或手動編輯 transitSchedule

# 4. 放寬 stuck time 限制
# 在 config.xml 的 qsim 模組中添加:
# <param name="stuckTime" value="20" />  <!-- 預設 10 秒 -->
```

---

## 警告信息處理

### 預期的警告（可以忽略）

#### 1. Artificial Links 警告
```
WARN: Route requires artificial links (stops not connected)
```
**說明**: 這是正常的，V1 mapping 有 87.6% 的路線使用 artificial links。這不會影響模擬運行，只是表示某些停靠站之間沒有直接的網路路徑。

**何時需要關注**: 如果超過 95% 的路線都使用 artificial links，可能需要改善 PT mapping。

#### 2. Coordinate System 警告
```
WARN: No coordinate system defined, assuming EPSG:3826
```
**說明**: 只要 config.xml 中設定了正確的座標系統即可忽略
```xml
<module name="global">
  <param name="coordinateSystem" value="EPSG:3826" />
</module>
```

#### 3. PT Interaction 活動警告
```
WARN: Person has pt interaction activity
```
**說明**: 這是正常的，表示代理人在 PT 系統中換乘或等待。

---

### 需要關注的警告

#### 1. Link not found
```
WARN: Link pt_BL14_UP not found in network
```
**嚴重性**: 高
**影響**: 代理人無法執行計劃
**解決方案**: 檢查 transitSchedule 和 network 的一致性

#### 2. Route departure before previous arrival
```
WARN: Route departure time before vehicle arrival at previous stop
```
**嚴重性**: 中
**影響**: PT 時刻表不合理
**解決方案**: 檢查 transitSchedule 中的時刻表，可能需要重新轉換 GTFS

---

## 除錯工具和命令

### 1. 檢查 PT 事件
```bash
# 查看所有 PT 相關事件
gunzip -c output/output_events.xml.gz | grep -E "transit|PersonEnters|PersonLeaves" | head -50

# 統計各種事件類型
gunzip -c output/output_events.xml.gz | grep "event type" | awk '{print $3}' | sort | uniq -c

# 追蹤特定代理人
gunzip -c output/output_events.xml.gz | grep "person=\"pt_commuter_bl_01\""
```

### 2. 分析模式統計
```bash
# 查看模式統計
cat output/modestats.csv

# 計算 PT 使用率
gunzip -c output/output_legs.csv.gz | awk -F';' 'NR>1 {modes[$4]++} END {for(m in modes) print m, modes[m]}'
```

### 3. 檢查 log 檔案
```bash
# 查找錯誤
grep -i error output/logfile.log | head -20

# 查找警告
grep -i warn output/logfileWarningsErrors.log | head -30

# 查找特定問題
grep -i "stuck\|exception\|failed" output/logfile.log
```

### 4. 驗證輸出檔案
```bash
# 檢查所有輸出檔案大小
ls -lh output/output_*.xml.gz output/*.csv

# 如果某個檔案異常小（如 < 1KB），可能有問題
# 例如 output_transitSchedule.xml.gz 應該 > 100KB
```

---

## 檢查清單

### 運行前檢查
- [ ] 所有必需檔案存在（network, schedule, vehicles, population）
- [ ] config.xml 中所有路徑正確
- [ ] Transit 模組已啟用 (`useTransit=true`)
- [ ] Vehicles 模組已配置
- [ ] QSim mainMode 包含 "pt"
- [ ] Scoring 包含 PT 模式參數
- [ ] 足夠的 Java heap memory (推薦 4GB+)

### 運行中監控
- [ ] 檢查 console 輸出有無錯誤
- [ ] 監控記憶體使用
- [ ] 確認 QSim 正常啟動
- [ ] 確認 PT 車輛正常派遣

### 運行後驗證
- [ ] 檢查 output/ 目錄存在
- [ ] output_events.xml.gz 已生成且 > 100KB
- [ ] output_transitSchedule.xml.gz 已生成
- [ ] modestats.csv 顯示 PT 使用
- [ ] logfileWarningsErrors.log 無致命錯誤
- [ ] 檢查 output_legs.csv.gz 確認 PT trips

---

## Plan B: 重新映射（如果 V1 結果不理想）

### 何時使用 Plan B
- V1 mapping 的 artificial links 比例過高 (> 95%)
- 模擬中出現大量 "No route found" 錯誤
- PT 性能不符合預期

### 執行 Plan B Mapping
```bash
# 使用 v4 配置（SpeedyALT 路由器 + 改進參數）
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-metro-v4.xml 2>&1 | tee /tmp/pt-mapping-v4.log

# 監控進度
tail -f /tmp/pt-mapping-v4.log | grep Progress

# 預計完成時間: ~1 小時（SpeedyALT）

# 完成後，複製新檔案
cp pt2matsim/out/tp_metro_gtfs_small/transitSchedule-mapped-v4.xml.gz \
   scenarios/taipei-metro-test/transitSchedule-mapped.xml.gz

cp pt2matsim/out/tp_metro_gtfs_small/network-with-pt-v4.xml.gz \
   scenarios/taipei-metro-test/network-with-pt.xml.gz

# 重新運行模擬測試
cd scenarios/taipei-metro-test
java -Xmx4g -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml
```

### V4 vs V3 vs V1 比較

| 版本 | 路由器 | 預計時間 | 特點 |
|------|--------|----------|------|
| V1 | SpeedyALT | 1 小時 | 快速，87.6% artificial links |
| V3 | AStarLandmarks | 33+ 小時 | 更穩健但極慢，已停止 |
| V4 | SpeedyALT | ~1 小時 | 快速 + 改進參數，推薦使用 |

**推薦**: 先用 V1 測試功能，如果需要改善品質再用 V4

---

## 快速診斷命令

```bash
# 一鍵檢查系統狀態
echo "=== Files ===" && \
ls -lh network-with-pt.xml.gz transitSchedule-mapped.xml.gz transitVehicles.xml && \
echo -e "\n=== Config ===" && \
grep -E "useTransit|mainMode|vehiclesFile" config.xml && \
echo -e "\n=== Output ===" && \
ls -lh output/*.xml.gz output/*.csv 2>/dev/null | head -10

# 檢查是否有致命錯誤
echo "=== Errors ===" && \
grep -i "exception\|error" output/logfile.log 2>/dev/null | head -10

# 檢查 PT 統計
echo "=== PT Stats ===" && \
cat output/modestats.csv 2>/dev/null
```

---

## 聯絡資訊

如果遇到本指南未涵蓋的問題:
1. 檢查 MATSim 文件: https://matsim.org/docs
2. pt2matsim GitHub Issues: https://github.com/matsim-org/pt2matsim/issues
3. MATSim 郵件列表: https://matsim.org/mailinglist

---

**最後更新**: 2025-10-29
**作者**: Claude Code (Anthropic)
