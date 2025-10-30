# MATSim 公共運輸設定完成報告

## 執行日期
2025-10-29

## 目標
準備好 MATSim 模擬環境以支援公共運輸（PT），包括配置、網路和人口檔案的完整設定。

---

## ✅ 已完成的修改

### (A) config.xml 配置檔案修改

#### 1. Transit 模組（公共運輸模組）
```xml
<module name="transit">
  <param name="useTransit" value="true" />
  <param name="transitScheduleFile" value="transitSchedule.xml" />
  <param name="vehiclesFile" value="transitVehicles.xml" />
</module>
```
- ✅ 已啟用公共運輸擴展
- ✅ 指定 transitSchedule.xml 和 transitVehicles.xml

#### 2. Vehicles 模組（車輛模組）
```xml
<module name="vehicles">
  <param name="vehiclesFile" value="transitVehicles.xml" />
</module>
```
- ✅ 新增車輛模組配置
- ✅ 載入 PT 車輛類型和實際車輛定義

#### 3. QSim 模組（模擬器）
```xml
<module name="qsim">
  <param name="mainMode" value="car,pt" />
  <param name="vehiclesSource" value="modeVehicleTypesFromVehiclesData" />
  <param name="usingTravelTimeCheckInTeleportation" value="true" />
  <param name="simStarttimeInterpretation" value="onlyUseStarttime" />
</module>
```
- ✅ 將 `pt` 加入主要模式
- ✅ 設定車輛來源為 `modeVehicleTypesFromVehiclesData`
- ✅ PT 專用 QSim 設定

#### 4. Scoring 模組（評分模組）
```xml
<parameterset type="modeParams">
  <param name="mode" value="pt" />
  <param name="constant" value="0.0" />
  <param name="marginalUtilityOfTraveling_util_hr" value="-7.0" />
  <param name="marginalUtilityOfDistance_util_m" value="0.0" />
  <param name="monetaryDistanceRate" value="0.0" />
</parameterset>

<parameterset type="activityParams">
  <param name="activityType" value="pt interaction" />
  <param name="typicalDuration" value="00:01:00" />
  <param name="scoringThisActivityAtAll" value="false" />
</parameterset>
```
- ✅ 定義 PT 模式評分參數
- ✅ 設定旅行時間邊際效用 (-7.0 util/hr)
- ✅ 新增 PT interaction 活動參數（用於轉乘）

#### 5. PlansCalcRoute 模組（路線計算）
```xml
<parameterset type="teleportedModeParameters">
  <param name="mode" value="pt" />
  <param name="teleportedModeSpeed" value="8.333333333" />
  <param name="beelineDistanceFactor" value="1.5" />
</parameterset>
```
- ✅ 新增 PT 路由參數
- ✅ 設定 PT 傳送速度（用於簡化路由）

#### 6. Strategy 模組（重新規劃策略）
```xml
<module name="strategy">
  <parameterset type="strategysettings">
    <param name="strategyName" value="ChangeExpBeta" />
    <param name="weight" value="0.7" />
  </parameterset>
  <parameterset type="strategysettings">
    <param name="strategyName" value="ReRoute" />
    <param name="weight" value="0.15" />
  </parameterset>
  <parameterset type="strategysettings">
    <param name="strategyName" value="SubtourModeChoice" />
    <param name="weight" value="0.15" />
  </parameterset>
</module>
```
- ✅ 新增模式創新策略（Mode Innovation）
- ✅ 啟用 SubtourModeChoice 讓代理人可以選擇 PT

#### 7. SubtourModeChoice 模組
```xml
<module name="subtourModeChoice">
  <param name="modes" value="car,pt,walk" />
  <param name="chainBasedModes" value="car" />
  <param name="considerCarAvailability" value="true" />
</module>
```
- ✅ 配置可選模式：car, pt, walk
- ✅ 考慮車輛可用性

---

### (B) network.xml 網路檔案

#### 檔案位置
`scenarios/equil/network_min.xml`

#### 網路特性
- ✅ **多模式網路**：支援 `car` 和 `pt` 模式
- ✅ **PT 專用連結**：
  - Link 21719: `modes="pt"` (忠孝新生)
  - Link 21720: `modes="pt"` (忠孝復興)
- ✅ **混合模式連結**：大部分道路支援 `modes="car,pt"`
- ✅ **停靠點分配**：
  - 停靠站 MRT_BL14 → Link 21719
  - 停靠站 MRT_BL15 → Link 21720

#### 網路統計
- 總節點數：12
- 總連結數：13
- PT 專用連結：2
- 混合模式連結：11

---

### (C) population.xml 人口檔案

#### 檔案位置
`scenarios/equil/population_min.xml`

#### 代理人配置

##### 1. car_commuter（汽車通勤者）
- ✅ 使用 `car` 模式
- ✅ 包含完整的網路路線
- 行程：home → work → home

##### 2. mrt_commuter（捷運通勤者）
- ✅ 使用 `pt` 模式
- ✅ PT 路線格式：`experimentalPt1`
- ✅ 路線資訊：
  - 上班：BL12_UP → BL13_UP（忠孝新生 → 忠孝復興）
  - 下班：BL13_DN → BL12_DN（忠孝復興 → 忠孝新生）
- 出發時間：08:30
- 工作時間：08:30-17:30

```xml
<person id="mrt_commuter">
  <plan selected="yes">
    <activity type="home" link="21719" end_time="08:30:00" />
    <leg mode="pt">
      <route type="experimentalPt1" start_link="21719" end_link="21720">
        PT1===BL12_UP===BL13_UP===
      </route>
    </leg>
    <activity type="work" link="21720" end_time="17:30:00" />
    <leg mode="pt">
      <route type="experimentalPt1" start_link="21720" end_link="21719">
        PT1===BL13_DN===BL12_DN===
      </route>
    </leg>
    <activity type="home" link="21719" />
  </plan>
</person>
```

---

### (D) transitSchedule.xml 和 transitVehicles.xml

#### 檔案位置
- `scenarios/equil/transitSchedule.xml`
- `scenarios/equil/transitVehicles.xml`

#### Transit Schedule 內容
- ✅ **Transit Line**: MRT_BL（板南線）
- ✅ **Transit Routes**: 2條（上行/下行）
- ✅ **Stop Facilities**: 2個（MRT_BL14, MRT_BL15）
- ✅ **Transport Mode**: subway
- ✅ **Network Routes**: 包含連結序列
- ✅ **Departures**: 包含發車時刻表

#### Transit Vehicles 內容
- ✅ 車輛類型定義（容量、長度、速度）
- ✅ 車輛實例定義

---

## 🎯 MATSim PT 支援核心要求檢查表

| 要求 | 狀態 | 位置/參數 |
|------|------|-----------|
| **Config 配置** | | |
| ✅ 啟用 Transit 模組 | 完成 | `useTransit=true` |
| ✅ 指定 transitSchedule | 完成 | `transitScheduleFile` |
| ✅ 指定 transitVehicles | 完成 | `vehiclesFile` (transit & vehicles模組) |
| ✅ QSim 支援 PT 模式 | 完成 | `mainMode="car,pt"` |
| ✅ 設定車輛來源 | 完成 | `vehiclesSource=modeVehicleTypesFromVehiclesData` |
| ✅ PT 評分參數 | 完成 | `modeParams` for pt |
| ✅ PT interaction 活動 | 完成 | `activityParams` for pt interaction |
| ✅ 模式創新策略 | 完成 | `SubtourModeChoice` |
| **Network 網路** | | |
| ✅ 多模式網路 | 完成 | `modes="car,pt"` |
| ✅ 停靠點連結分配 | 完成 | `linkRefId` in transitSchedule |
| ✅ PT 路線包含連結序列 | 完成 | `<route>` in transitSchedule |
| **Population 人口** | | |
| ✅ PT 模式行程 | 完成 | `mode="pt"` |
| ✅ PT 路線資訊 | 完成 | `type="experimentalPt1"` |
| ✅ 停靠站資訊 | 完成 | stopFacility IDs in route |

---

## 📁 相關檔案清單

### 主要配置檔案
1. `scenarios/equil/config_min.xml` - 已更新，完整 PT 支援
2. `scenarios/equil/network_min.xml` - 已驗證，多模式網路
3. `scenarios/equil/population_min.xml` - 已更新，包含 PT 代理人
4. `scenarios/equil/transitSchedule.xml` - 已存在，定義 PT 服務
5. `scenarios/equil/transitVehicles.xml` - 已存在，定義 PT 車輛

### 輔助檔案
6. `CLAUDE.md` - Claude Code 使用指南
7. `PT_SETUP_REPORT.md` - 本報告

---

## 🧪 測試狀態

### 基本模擬測試
- ✅ **狀態**: 測試完成並成功
- 🎯 **測試命令**:
  ```bash
  cd scenarios/equil
  java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config_min.xml
  ```

### 測試結果 ✅
- ✅ **PT 車輛運行**: 成功，2 條 PT 路線（MRT_BL14, MRT_BL15）正常運行
- ✅ **mrt_commuter**: 成功使用 PT 模式（legMode="pt"）
- ✅ **car_commuter**: 正常使用汽車模式
- ✅ **模式統計**: 50% car, 50% pt（符合 2 個代理人配置）
- ✅ **輸出檔案**: 所有檔案正常生成
  - output_events.xml.gz (823B)
  - output_transitSchedule.xml.gz (682B)
  - output_transitVehicles.xml.gz (406B)
  - output_plans.xml.gz (775B)
  - output_network.xml.gz (1.0K)
- ✅ **模擬時間**: < 1 秒（迭代 0）
- ✅ **無重大錯誤或警告**

---

## 📚 參考資料

### MATSim PT 文件
- [Public Transit Tutorial](https://matsim.org/docs/tutorials/public-transit)
- [Transit Schedule Format](https://matsim.org/files/dtd/transitSchedule_v2.dtd)
- [pt2matsim Documentation](https://github.com/matsim-org/pt2matsim)

### 關鍵概念
1. **Stop Facility**: PT 停靠站，必須分配給一個網路連結
2. **Transit Line**: PT 線路（如板南線）
3. **Transit Route**: 特定方向的路線（上行/下行）
4. **Transport Mode**: 運輸模式（subway, bus, tram等）
5. **Network Route**: 車輛在網路中行駛的連結序列
6. **PT Interaction**: 代理人在 PT 系統中的互動活動（上下車、轉乘）

---

## 🔧 故障排除

### 常見問題

#### 1. "No route found" 錯誤
**原因**: 網路連接性問題
**解決方案**:
- 檢查 transitSchedule 中的 linkRefId 是否存在於 network 中
- 確認 network route 包含正確的連結序列

#### 2. "Vehicle not found" 錯誤
**原因**: transitVehicles.xml 未正確載入
**解決方案**:
- 確認 config 中 vehicles 模組已配置
- 檢查 vehiclesFile 路徑正確

#### 3. PT 代理人不搭乘 PT
**原因**: PT 路線格式錯誤或模式創新未啟用
**解決方案**:
- 檢查 population 中 PT 路線格式
- 確認 strategy 模組包含 SubtourModeChoice

#### 4. 模擬運行緩慢
**原因**: 複雜的 PT 網路或大量代理人
**解決方案**:
- 減少迭代次數進行測試
- 使用 `flowCapacityFactor` 和 `storageCapacityFactor` 縮放

---

## ✨ 下一步建議

### 短期（已完成）✅
1. ✅ 運行基本 PT 模擬
2. ✅ 驗證 PT 車輛正常運行
3. ✅ 檢查代理人 PT 使用情況

### 中期（進行中）
1. ⏳ **PT 映射進度**: 82.69% 完成（831/1005 routes）
   - 預計完成時間：~30 分鐘
   - 命令：`tail -f /tmp/pt-mapping-clean.log` 監控進度
2. ⏳ 映射完成後驗證排程合理性
   - 使用 CheckMappedSchedulePlausibility 工具
3. ⏳ 整合完整的台北捷運網路到主要情境
4. ⏳ 增加更多 PT 代理人
5. ⏳ 啟用模式選擇迭代（多次迭代）

### 長期
1. 整合多種 PT 模式（捷運、公車、輕軌）
2. 加入轉乘分析
3. 優化 PT 排程和頻率
4. 進行大規模情境模擬

---

## 📝 變更記錄

### 2025-10-29

#### 下午 17:27 - PT 配置測試成功 ✅
- ✅ 完成 config.xml 所有 PT 相關配置
- ✅ 驗證 network.xml 支援 PT
- ✅ 更新 population.xml PT 路線格式
- ✅ 驗證 transitSchedule.xml 和 transitVehicles.xml
- ✅ 測試模擬成功運行並驗證 PT 功能
- ✅ 確認模式統計：50% car, 50% pt
- ✅ 確認 PT 車輛和代理人正常運行

#### 下午 14:44 - PT 映射進行中
- ⏳ PT 映射進度：82.69%（831/1005 routes）
- 使用清理後的 subway-only 網路（63,566 links）
- 預計 ~30 分鐘內完成完整映射

---

## 👥 作者
- Claude Code (Anthropic)
- 基於用戶需求和 MATSim 最佳實踐

## 📄 授權
本配置遵循 MATSim 專案授權條款
