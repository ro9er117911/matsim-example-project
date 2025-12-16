---
description: 災難模擬路網修改 - 建立時變路網(time-variant network)與道路封閉事件
---

# 災難路網修改技能

## 觸發條件

- 需要建立海嘯/地震撤離模擬
- 需要動態封閉道路
- 建立 time-variant network change events
- 根據溢淹深度分階段封路

---

## Step 1: 準備封閉區域資料

### 方法 A: 溢淹深度分階段 (推薦)

使用溢淹潛勢圖的 `Max_depth` 欄位：

```bash
python3 5000_disatar/05_combined_evac/tools/generate_change_events_depth.py \
  --network scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz \
  --inundation 5000_disatar/evacuation_shp/2025年海嘯溢淹潛勢圖資/2025年海嘯溢淹潛勢更新模擬.shp \
  --output input/tsunami_changeEvents_2025.xml \
  --geojson-output output/inundation_closure_2025.geojson \
  --roi "121.35,25.10,121.52,25.22"
```

#### 深度分階段配置

| 深度 | 降速時間 | 封閉時間 | 速度係數 |
|------|----------|----------|----------|
| >3m | 03:00:00 | 03:05:00 | 0% |
| 2-3m | 03:01:00 | 03:06:00 | 30% |
| 1-2m | 03:02:00 | 03:07:00 | 40% |
| 0.5-1m | 03:03:00 | 03:08:00 | 50% |

### 方法 B: 海岸線距離分階段

```bash
python3 5000_disatar/05_combined_evac/tools/generate_change_events.py \
  --network <network.xml.gz> \
  --shoreline input/tamsui_shoreline.geojson \
  --output input/tsunami_changeEvents.xml \
  --geojson-output output/coastal_closure.geojson
```

---

## Step 2: 配置 Time-Variant Network

在 config.xml 加入：

```xml
<module name="network">
    <param name="inputNetworkFile" value="network.xml.gz"/>
    <param name="inputChangeEventsFile" value="input/tsunami_changeEvents.xml"/>
    <param name="timeVariantNetwork" value="true"/>
</module>
```

---

## Step 3: 驗證封閉事件

```bash
# 檢查事件檔案格式
head -50 input/tsunami_changeEvents.xml

# 驗證 link 數量
grep -c '<link ' input/tsunami_changeEvents.xml

# 檢查時間配置
grep 'startTime' input/tsunami_changeEvents.xml | sort -u
```

---

## 常見問題

### 封閉區域呈矩形
**解決**: 使用真實 OSM 海岸線或溢淹潛勢圖，不用固定座標

### Link 未被封閉
**檢查**: 確認 network 與 shp 使用相同 CRS (EPSG:3826)

### 封閉時間錯誤
**解決**: 調整 generate_change_events 腳本的時間參數

---

## 輸出檔案

| 檔案 | 用途 |
|------|------|
| `tsunami_changeEvents.xml` | MATSim 時變網路事件 |
| `coastal_closure.geojson` | 封閉區域可視化 |
| `inundation_closure_2025.geojson` | 溢淹分級可視化 |

## 參考檔案

- 完整工作流程: `5000_disatar/05_combined_evac/WORKFLOW.md`
- 工具腳本: `5000_disatar/05_combined_evac/tools/generate_change_events*.py`
