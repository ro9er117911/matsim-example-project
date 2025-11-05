# MATSim 配置調優指南

## 概述

本指南提供系統化方法來調優 MATSim 模擬配置以實現特定目標：
- 加快開發迭代
- 提高模擬真實性
- 優化計算資源使用
- 改善特定模式的模擬

## 快速參考

### 開發模式 (快速迭代)

```xml
<!-- 最小迭代 -->
<module name="controller">
  <param name="lastIteration" value="1" />
  <param name="overwriteFiles" value="deleteDirectoryIfExists" />
</module>

<!-- 減少輸出 -->
<module name="controller">
  <param name="writeEventsInterval" value="10" />
  <param name="writePlansInterval" value="10" />
  <param name="writeTripsInterval" value="10" />
</module>

<!-- 簡化策略 -->
<module name="strategy">
  <parameterset type="strategysettings">
    <param name="strategyName" value="ChangeExpBeta" />
    <param name="weight" value="1.0" />
  </parameterset>
</module>
```

**預期**: 模擬在幾分鐘內完成，適合測試配置變更

---

### 生產模式 (真實結果)

```xml
<!-- 足夠的迭代達到穩定 -->
<module name="controller">
  <param name="lastIteration" value="100" />
  <param name="overwriteFiles" value="failIfDirectoryExists" />
</module>

<!-- 定期輸出 -->
<module name="controller">
  <param name="writeEventsInterval" value="10" />
  <param name="writePlansInterval" value="10" />
</module>

<!-- 完整策略組合 -->
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
    <param name="strategyName" value="TimeAllocationMutator" />
    <param name="weight" value="0.10" />
  </parameterset>
  <parameterset type="strategysettings">
    <param name="strategyName" value="ChangeSingleTripMode" />
    <param name="weight" value="0.05" />
  </parameterset>
</module>
```

---

## 控制器模組調優

### 迭代次數

**參數**: `controller.lastIteration`

**效果**:
- 更多迭代 → 更好的收斂，但更長的運行時間
- 更少迭代 → 快速測試，但可能不穩定

**建議**:
| 場景 | 迭代次數 | 原因 |
|------|----------|------|
| 配置測試 | 0-1 | 僅驗證設置 |
| 初步結果 | 10-30 | 快速反饋 |
| 研究結果 | 100-300 | 確保收斂 |
| 政策評估 | 500+ | 高信心 |

**診斷**:
- 查看 `scorestats.csv` 中的分數穩定性
- 如果分數仍在變化 → 增加迭代次數

### 輸出控制

**參數**:
- `writeEventsInterval`: 每 N 次迭代寫入事件檔案
- `writePlansInterval`: 每 N 次迭代寫入計劃檔案

**磁碟空間權衡**:
```
事件檔案大小 ~ 10 MB (小場景) 到 10+ GB (大場景)
```

**建議**:
- 小場景 (<1000 代理): 每次迭代
- 中場景 (1000-10000): 每 5-10 次迭代
- 大場景 (>10000): 每 10-20 次迭代，最後一次

**範例**:
```xml
<param name="writeEventsInterval" value="10" />
<param name="writePlansInterval" value="10" />
<!-- 將總輸出減少 90% -->
```

### 記憶體與快取

**QSim 配置**:
```xml
<module name="qsim">
  <param name="numberOfThreads" value="4" />
  <param name="flowCapacityFactor" value="1.0" />
  <param name="storageCapacityFactor" value="1.0" />
</module>
```

**執行緒數**:
- 理想: CPU 核心數 - 1
- 範例: 8 核心 CPU → 6-7 執行緒
- 避免超訂閱 (超過實際核心)

**容量因子**:
- `flowCapacityFactor`: 調整連結流量容量
- `storageCapacityFactor`: 調整連結儲存容量
- 值 < 1.0 用於樣本場景

**範例** (10% 樣本):
```xml
<param name="flowCapacityFactor" value="0.1" />
<param name="storageCapacityFactor" value="0.1" />
```

---

## 公共運輸調優

### 啟用 PT

```xml
<module name="transit">
  <param name="useTransit" value="true" />
  <param name="transitScheduleFile" value="transitSchedule.xml" />
  <param name="vehiclesFile" value="transitVehicles.xml" />
</module>

<module name="vehicles">
  <param name="vehiclesFile" value="transitVehicles.xml" />
</module>
```

### PT 路徑器配置

**選項 1: SwissRailRaptor (推薦 PT)**

```xml
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="true" />
  <param name="useModeMappingForPassengers" value="false" />

  <parameterset type="intermodalAccessEgress">
    <param name="mode" value="walk" />
    <param name="maxRadius" value="1000" />
  </parameterset>
</module>
```

**優點**:
- 專為 PT 設計
- 處理轉乘
- 快速

**選項 2: 標準 PT 路徑器**

```xml
<module name="planscalcroute">
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="pt" />
    <param name="beelineDistanceFactor" value="1.3" />
  </parameterset>
</module>
```

### PT 車輛來源

```xml
<module name="qsim">
  <param name="vehiclesSource" value="modeVehicleTypesFromVehiclesData" />
  <param name="mainMode" value="car,pt" />
</module>
```

**選項**:
- `defaultVehicleType`: 使用預設車輛
- `fromVehiclesData`: 從 vehicles 檔案讀取
- `modeVehicleTypesFromVehiclesData`: 按模式類型 (推薦)

---

## 模式選擇調優

### SubtourModeChoice 配置

```xml
<module name="subtourModeChoice">
  <param name="chainBasedModes" value="car,bike" />
  <param name="modes" value="car,pt,bike,walk" />
  <param name="considerCarAvailability" value="true" />
</module>
```

**參數**:
- `chainBasedModes`: 需要車輛鏈的模式 (car, bike)
- `modes`: 所有可用模式
- `considerCarAvailability`: 考慮擁車

### 模式參數

```xml
<module name="routing">
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk" />
    <param name="teleportedModeSpeed" value="1.5" />  <!-- m/s -->
    <param name="beelineDistanceFactor" value="1.3" />
  </parameterset>

  <parameterset type="teleportedModeParameters">
    <param name="mode" value="bike" />
    <param name="teleportedModeSpeed" value="4.0" />
  </parameterset>
</module>
```

---

## 評分函數調優

### 活動評分

```xml
<module name="scoring">
  <parameterset type="activityParams">
    <param name="activityType" value="home" />
    <param name="typicalDuration" value="12:00:00" />
    <param name="priority" value="1.0" />
  </parameterset>

  <parameterset type="activityParams">
    <param name="activityType" value="work" />
    <param name="typicalDuration" value="08:00:00" />
    <param name="openingTime" value="08:00:00" />
    <param name="closingTime" value="18:00:00" />
    <param name="priority" value="1.0" />
  </parameterset>
</module>
```

**典型持續時間**:
- 決定活動的效用
- 較短/較長持續時間 → 較低效用

**開放/關閉時間**:
- 太早/太晚到達 → 懲罰
- 模擬真實約束

### 模式效用

```xml
<module name="scoring">
  <!-- 時間成本 (負值 = 懲罰) -->
  <param name="traveling" value="-6.0" />
  <param name="performing" value="6.0" />

  <!-- 模式特定常數 (調整模式分擔) -->
  <parameterset type="modeParams">
    <param name="mode" value="car" />
    <param name="constant" value="0.0" />
    <param name="marginalUtilityOfTraveling_util_hr" value="-6.0" />
  </parameterset>

  <parameterset type="modeParams">
    <param name="mode" value="pt" />
    <param name="constant" value="-0.5" />  <!-- PT 稍不便 -->
    <param name="marginalUtilityOfTraveling_util_hr" value="-6.0" />
  </parameterset>

  <parameterset type="modeParams">
    <param name="mode" value="walk" />
    <param name="constant" value="0.0" />
    <param name="marginalUtilityOfTraveling_util_hr" value="-12.0" />  <!-- 步行成本高 -->
  </parameterset>
</module>
```

**調整模式分擔**:
- 增加 PT `constant` (較不負) → 更多 PT 使用
- 增加行駛成本 (較負) → 較短行程
- 平衡以匹配觀察資料

### 金錢評分

```xml
<param name="marginalUtilityOfMoney" value="1.0" />
<param name="monetaryDistanceRate" value="-0.0002" />  <!-- 每公尺 -->
```

**用途**:
- 道路定價
- 停車費
- PT 票價

---

## 策略調優

### 策略組合

```xml
<module name="strategy">
  <param name="fractionOfIterationsToDisableInnovation" value="0.8" />

  <!-- 主要: 選擇最佳計劃 -->
  <parameterset type="strategysettings">
    <param name="strategyName" value="ChangeExpBeta" />
    <param name="weight" value="0.7" />
  </parameterset>

  <!-- 重新路徑 -->
  <parameterset type="strategysettings">
    <param name="strategyName" value="ReRoute" />
    <param name="weight" value="0.15" />
    <param name="disableAfterIteration" value="80" />
  </parameterset>

  <!-- 時間變異 -->
  <parameterset type="strategysettings">
    <param name="strategyName" value="TimeAllocationMutator" />
    <param name="weight" value="0.10" />
    <param name="disableAfterIteration" value="80" />
  </parameterset>

  <!-- 模式變更 -->
  <parameterset type="strategysettings">
    <param name="strategyName" value="ChangeSingleTripMode" />
    <param name="weight" value="0.05" />
    <param name="disableAfterIteration" value="80" />
  </parameterset>
</module>
```

**權重解釋**:
- 總和 = 1.0
- 較高權重 → 更常使用該策略
- ChangeExpBeta 應該是主導 (0.6-0.8)

**創新禁用**:
- 80% 迭代後禁用創新 (ReRoute, Mutators)
- 允許最後 20% 收斂

### 時間變異

```xml
<module name="timeAllocationMutator">
  <param name="mutationRange" value="7200.0" />  <!-- 2 小時 (秒) -->
</module>
```

**範圍**:
- 太小 → 探索不足
- 太大 → 混亂的時間安排
- 典型: 1-2 小時

---

## 網路調優

### 網路簡化

**用於大型網路**:

```xml
<module name="network">
  <param name="inputNetworkFile" value="network.xml" />
  <!-- 考慮預先清理網路 -->
</module>
```

**手動簡化**:
```bash
# 使用 CleanSubwayNetwork 減少 PT 網路
java -cp project.jar \
  org.matsim.project.tools.CleanSubwayNetwork \
  network-full.xml.gz network-subway.xml.gz
```

### 連結屬性

重要屬性:
- `freespeed`: 影響行駛時間
- `capacity`: 影響擁塞
- `length`: 影響距離成本
- `modes`: 哪些模式可以使用連結

---

## 診斷與監控

### 關鍵輸出檔案

**分數追蹤**:
```bash
# 繪製平均分數隨時間
cat output/scorestats.csv

# 尋找:
# - 分數增加 (良好)
# - 收斂 (平穩) (良好)
# - 振盪 (需調整策略)
```

**模式分擔**:
```bash
cat output/modestats.csv

# 檢查模式分擔是否現實
# 調整評分參數以匹配觀察
```

**行程距離**:
```bash
cat output/traveldistancestats.csv

# 驗證行程距離合理
```

### 常見問題

**問題: 分數下降**
- 檢查策略權重
- 減少變異範圍
- 增加 ChangeExpBeta 權重

**問題: 沒有 PT 使用**
- 檢查 PT 路線是否對應到網路
- 降低 PT constant (較不負)
- 增加 car 成本

**問題: 模擬緩慢**
- 減少迭代次數
- 增加輸出間隔
- 減少執行緒數 (避免爭用)
- 使用樣本人口

---

## 實驗範本

### 範本 1: 測試新功能

```xml
<module name="controller">
  <param name="lastIteration" value="1" />
  <param name="overwriteFiles" value="deleteDirectoryIfExists" />
</module>
```

**用途**: 驗證配置載入，無錯誤

### 範本 2: 快速原型

```xml
<module name="controller">
  <param name="lastIteration" value="10" />
</module>

<module name="strategy">
  <parameterset type="strategysettings">
    <param name="strategyName" value="ChangeExpBeta" />
    <param name="weight" value="1.0" />
  </parameterset>
</module>
```

**用途**: 快速反饋，僅選擇邏輯

### 範本 3: 完整評估

```xml
<module name="controller">
  <param name="lastIteration" value="200" />
  <param name="writeEventsInterval" value="20" />
</module>

<!-- 完整策略組合 (如上所示) -->
```

**用途**: 發表品質結果

---

## 相關文檔

- PT Mapping 研究: `pt-mapping-research.md`
- 開發指南: `../dev-master/development-guide.md`
- PT 工具鏈: `../product-manager/pt-toolchain-specification.md`
