# PT Mapping 研究與調優

## 研究目標

了解並優化 pt2matsim PublicTransitMapper 的參數，以最小化人工連結並確保準確的站點對應。

## 背景知識

### PT Mapping 挑戰

**問題**: GTFS 時刻表中的站點有座標但沒有網路連結分配。PT mapping 必須找到適當的網路連結並建立運輸車輛的網路路線。

**為何困難**:
- 地鐵站點通常在地下，與地面道路網路對齊不良
- OSM 資料的鐵路幾何可能不精確
- 站點可能距離最近的網路連結數百公尺遠
- 需要在準確性和計算時間之間平衡

### 演算法概述

1. **連結候選選擇**: 為每個站點尋找附近的連結
2. **路線計算**: 計算連續站點之間的網路路線
3. **合理性檢查**: 驗證路線匹配時刻表行駛時間
4. **人工連結建立**: 如果沒有有效路線則建立人工連結
5. **網路清理**: 移除未使用的連結，驗證連通性

## 參數演化

### 版本歷史

| 版本 | maxDist | nLinks | costFactor | multiplier | Router | 結果 |
|------|---------|--------|------------|------------|--------|------|
| v1 | 150m | 8 | 5.0 | 1.6 | SpeedyALT | 基線 |
| v2 | 300m | 10 | 10.0 | 2.0 | SpeedyALT | 較少人工連結 |
| v3 | 300m | 10 | 15.0 | 2.5 | SpeedyALT | 更快 (6 執行緒) |
| v4 | 300m | 12 | 15.0 | 3.0 | SpeedyALT | 最寬鬆 (目前) |

### 關鍵發現

#### 1. maxLinkCandidateDistance (連結候選距離)

**實驗**:
- 90m (預設): 許多站點沒有候選連結
- 150m: 改善但仍有差距
- 300m: 大部分地鐵站點有足夠的候選

**建議**:
- **公車**: 50-100m (跟隨道路)
- **電車**: 100-150m (混合交通)
- **鐵路**: 150-250m (等級分離)
- **地鐵**: 200-300m (地下，對齊差異)

**原理**: 地鐵站點經常與地面網路幾何不對齊

#### 2. nLinkThreshold (連結數門檻)

**實驗**:
- 4: 對於密集網路太少
- 6 (預設): 適合公車
- 8-10: 適合地鐵
- 12: 最佳覆蓋範圍 (台北案例)

**建議**:
- **公車**: 4-6
- **電車**: 6-8
- **鐵路**: 8-10
- **地鐵**: 10-12

**原理**: 更多候選 = 路徑演算法有更多選擇

#### 3. maxTravelCostFactor (行駛成本係數)

**實驗**:
- 5.0 (預設): 經常建立人工連結
- 10.0: 顯著減少人工連結
- 15.0: 接受現實的繞路

**建議**:
- **公車**: 3-5 (應該跟隨道路)
- **電車**: 5-8
- **鐵路**: 8-12
- **地鐵**: 10-15

**原理**: 地鐵網路可能需要繞路以遵循實際軌道

#### 4. candidateDistanceMultiplier (候選距離倍增器)

**實驗**:
- 1.6 (預設): 最小搜尋擴展
- 2.0: 溫和擴展
- 3.0: 積極擴展

**效果**: 在找到 N 個候選後擴展搜尋半徑

**建議**:
- 密集網路: 1.3-1.6
- 中等網路: 1.6-2.0
- 稀疏網路: 2.0-3.0

#### 5. networkRouter (路徑演算法)

**選項**:
- **AStarLandmarks**: 穩健，處理斷開網路，但慢 (~10 小時)
- **SpeedyALT**: 快速 (~1.5 小時)，但需要連通網路

**實驗結果** (台北捷運 1300 站點):
| Router | 時間 | 人工連結 | 備註 |
|--------|------|----------|------|
| AStarLandmarks | ~10 小時 | 較少 | 更穩健 |
| SpeedyALT | ~1.5 小時 | 稍多 | 需要網路準備 |

**建議**:
- 使用 SpeedyALT + PrepareNetworkForPTMapping
- 節省 ~8.5 小時

## 模式特定策略

### 地鐵/捷運 (最寬鬆)

```xml
<parameterset type="transportModeAssignment">
  <param name="scheduleMode" value="subway" />
  <param name="networkModes" value="pt,subway" />
  <param name="maxLinkCandidateDistance" value="300.0" />
  <param name="nLinkThreshold" value="12" />
  <param name="strictLinkRule" value="false" />
</parameterset>
```

**原理**:
- 地下系統，對齊差異大
- 需要大搜尋半徑
- 需要更多候選

### 鐵路 (中等寬鬆)

```xml
<parameterset type="transportModeAssignment">
  <param name="scheduleMode" value="rail" />
  <param name="networkModes" value="pt,rail" />
  <param name="maxLinkCandidateDistance" value="250.0" />
  <param name="nLinkThreshold" value="10" />
</parameterset>
```

### 電車 (中等)

```xml
<parameterset type="transportModeAssignment">
  <param name="scheduleMode" value="tram" />
  <param name="networkModes" value="pt,tram" />
  <param name="maxLinkCandidateDistance" value="150.0" />
  <param name="nLinkThreshold" value="8" />
</parameterset>
```

### 公車 (嚴格)

```xml
<parameterset type="transportModeAssignment">
  <param name="scheduleMode" value="bus" />
  <param name="networkModes" value="car,bus" />
  <param name="maxLinkCandidateDistance" value="100.0" />
  <param name="nLinkThreshold" value="6" />
  <param name="strictLinkRule" value="false" />
</parameterset>
```

**原理**: 公車跟隨道路，應該容易對應

## 實驗工作流程

### 最小可行實驗 (MVE)

**目標**: 快速測試參數變化而不執行完整 mapping

**設置**:
1. 建立小型測試走廊 (2-6 站點)
2. 使用 CleanSubwayNetwork 減少網路
3. 測試參數變化
4. 測量: 人工連結數、mapping 時間、站點覆蓋率

**範例** (CorridorPipelineTest):
```java
// 測試資料: 6 站點，2 條線，最小網路
// 在 <30 秒內驗證完整管線
```

### A/B 測試框架

**比較兩個配置**:

```bash
# 配置 A: 保守
maxLinkCandidateDistance=150.0
nLinkThreshold=8

# 配置 B: 寬鬆
maxLinkCandidateDistance=300.0
nLinkThreshold=12

# 比較指標:
# - 人工連結百分比
# - Mapping 時間
# - 合理性檢查警告數
```

### 迭代調優流程

```
1. 基線 Mapping
   ↓
2. 分析日誌:
   - 哪些站點沒有候選?
   - 建立了多少人工連結?
   - 哪些路線失敗?
   ↓
3. 調整參數:
   - 增加距離/候選 → 減少人工連結
   - 切換 router → 改變時間/品質權衡
   ↓
4. 重新 Mapping
   ↓
5. 驗證改善
   ↓
6. 重複直到滿意
```

## 診斷工具

### CheckMappedSchedulePlausibility

```bash
java -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  network-with-pt.xml.gz \
  transitSchedule-mapped.xml.gz
```

**檢查**:
- 路線遵循網路連通性
- 行駛時間匹配時刻表
- 沒有過多的人工連結

### 日誌分析

**重要訊息**:

```
INFO PTMapper: Processing 1005 routes...
INFO PTMapper: Created 347 artificial links (26% of routes)
WARN PTMapper: Network is not connected for mode 'pt'
```

**解讀**:
- 26% 人工連結 → 太高，調整參數
- "not connected" → 執行 PrepareNetworkForPTMapping

### 視覺化檢查

使用 MATSim GUI 或 SimWrapper 視覺化:
- PT 路線在網路上
- 人工連結位置
- 站點分佈

## 案例研究: 台北捷運

### 挑戰

1. **大型網路**: 1300+ 站點 (所有線路)
2. **地下對齊**: 站點與地面道路不匹配
3. **混合模式**: 地鐵 + 公車在相同網路

### 解決方案

**初始嘗試** (v1):
- 150m, 8 候選, AStarLandmarks
- 結果: ~10 小時，~30% 人工連結

**優化後** (v4):
- 300m, 12 候選, SpeedyALT
- 結果: ~1.5 小時，~15% 人工連結 ✅

**關鍵改變**:
1. PrepareNetworkForPTMapping → 解決連通性
2. CleanSubwayNetwork → 減少雜訊
3. 增加搜尋參數 → 更多候選
4. SpeedyALT → 快 7 倍

### 效能提升

| 階段 | 時間 | 品質 |
|------|------|------|
| v1 (基線) | 10 小時 | 30% 人工 |
| v2 (增加距離) | 8 小時 | 22% 人工 |
| v3 (SpeedyALT) | 1.5 小時 | 18% 人工 |
| v4 (最終) | 1.5 小時 | 15% 人工 ✅ |

## 最佳實踐

### 1. 總是先準備網路

```bash
# 必要步驟!
java -cp project.jar \
  org.matsim.project.tools.PrepareNetworkForPTMapping \
  network.xml.gz network-ready.xml.gz
```

### 2. 從小處開始

```bash
# 先測試走廊
java -cp project.jar \
  org.matsim.project.tools.CleanSubwayNetwork \
  network-full.xml.gz network-subway.xml.gz

# 在小網路上 mapping
# 驗證結果
# 然後擴展到完整網路
```

### 3. 使用模式特定規則

```xml
<param name="modeSpecificRules" value="true" />

<!-- 不同模式不同參數 -->
<parameterset type="transportModeAssignment">
  <param name="scheduleMode" value="subway" />
  <!-- 地鐵專用參數 -->
</parameterset>
```

### 4. 監控進度

```bash
# 使用 tail 監控日誌
tail -f ptmapper.log

# 尋找:
# - "Processing route X/Y"
# - 人工連結警告
# - 連通性錯誤
```

### 5. 驗證結果

```bash
# 執行合理性檢查
java -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  network.xml.gz schedule.xml.gz

# 在 GUI 中視覺化
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# 執行測試模擬 (1 次迭代)
# 檢查 PT 使用是否合理
```

## 未來研究方向

### 1. 自動參數調優

- 基於網路密度自動調整參數
- 機器學習預測最佳參數

### 2. 改進的路徑演算法

- 結合 SpeedyALT 的速度和 AStarLandmarks 的穩健性
- 考慮 PT 路線的先驗知識

### 3. 品質指標

- 開發客觀的 mapping 品質分數
- 自動檢測有問題的對應

### 4. 增量 Mapping

- 支援只 re-map 更改的路線
- 加快迭代實驗

## 相關文檔

- PT 工具鏈規格: `../product-manager/pt-toolchain-specification.md`
- 配置調優指南: `configuration-tuning-guide.md`
- 實驗工作流程: `experimental-workflows.md`
