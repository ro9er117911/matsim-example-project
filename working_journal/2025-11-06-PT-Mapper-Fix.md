# 2025-11-06 PT Mapper 修復與網絡生成

## 問題描述

PT mapper 進程卡住，已運行 38+ 小時無法完成：
- 原因：網絡不連通，路由算法無限循環
- 32 個地鐵站（30%）在 OSM 數據範圍外
- 預計完成時間：96 小時（不可接受）

## 解決方案執行記錄

### 階段 1：診斷與終止卡住進程

**時間**：11:00-11:10

**操作**：
```bash
# 1. 檢查運行時間
ps aux | grep PublicTransitMapper
# 進程 93331: 運行 2303 分鐘（38 小時）

# 2. 檢查日誌
tail pt2matsim/output_v1/ptmapper.log
# 大量 "Network is not connected" 警告

# 3. 終止進程
kill 93331
```

**發現**：
- 日誌文件 512 MB
- 路由失敗：SpeedyALT 找不到連接路徑
- 網絡不連通問題嚴重

---

### 階段 2：數據範圍分析

**時間**：11:10-11:20

**分析結果**：
```python
# GTFS 站點範圍
Lat: 24.95761 to 25.16808
Lon: 121.41077 to 121.61827

# OSM 數據範圍
Lat: 25.02713 to 25.16766  ← 南邊缺少 7.8 公里
Lon: 121.37043 to 121.63994

# 缺失站點（32 個）
- 板南線西段：頂埔、永寧、土城、海山、亞東醫院、府中、板橋、新埔
- 松山新店線南段：新店、新店區公所、七張、小碧潭、大坪林、景美、萬隆
```

**決策**：裁切 GTFS 數據到 OSM 範圍內（用戶要求）

---

### 階段 3：GTFS 數據過濾

**時間**：11:20-11:30

**工具開發**：
```bash
# 創建過濾腳本
/tmp/filter_gtfs_to_osm_bounds.py
```

**過濾結果**：
- 輸入：722 個站點設施
- 輸出：541 個站點（75%）
- 過濾掉：181 個站點（25%）
- 班次：5,440 保留，282 過濾
- 路線：6 條全部保留

**輸出**：
```
pt2matsim/data/gtfs/tp_metro_gtfs_osm_filtered.zip
```

---

### 階段 4：方案 1 - 放寬網絡模式

**時間**：11:30-11:45

**配置修改**：
```xml
<!-- 原本：只使用 pt,subway -->
<param name="networkModes" value="pt,subway"/>

<!-- 修改為：可使用所有相關模式 -->
<param name="networkModes" value="pt,subway,rail,car,bus"/>
```

**測試結果**：
- 啟動成功
- 進度：9/1309 路線（0.69%）完成
- 速度：4.4 分鐘/路線
- **預計時間：96 小時** ❌ 不可行

---

### 階段 5：方案 2 - 人工鏈接模式（最終方案）

**時間**：12:10-12:15

**策略**：
使用 `maxLinkCandidateDistance = 0.0` 強制創建獨立虛擬鏈接

**配置**：
```xml
<!-- pt2matsim/work/ptmapper-config-artificial.xml -->
<param name="maxLinkCandidateDistance" value="0.0"/>
<param name="modeSpecificRules" value="false"/>
<param name="nLinkThreshold" value="1"/>
<param name="routingWithCandidateDistance" value="false"/>
```

**執行時間**：**1 分鐘** ✅

**結果**：
```
Artificial Links: 473 created
Stop Facilities: 241 total (100% preserved)
Transit Routes: 1,309 mapped (100% success)
Routes with failures: 0
```

**輸出文件**：
```
pt2matsim/output_v2/
├── network-with-pt.xml.gz         (2.4 MB) ← 包含 PT 的完整網絡
├── transitSchedule-mapped.xml.gz  (351 KB) ← 已映射的時刻表
└── network-street.xml.gz          (2.4 MB) ← 純道路網絡
```

---

## 技術細節

### 人工鏈接（Artificial Links）原理

當 `maxLinkCandidateDistance = 0.0` 時：
1. pt2matsim 無法在真實路網上找到候選鏈接
2. 自動為每個站點創建虛擬 loop link（pt_ 前綴）
3. 虛擬鏈接形成獨立的 PT 網絡拓撲
4. 避免了路由算法陷入不連通子網

**優點**：
- 快速（1 分鐘 vs 96 小時）
- 100% 成功率
- 適合純 PT 場景或網絡不連通情況

**缺點**：
- 失去真實路網拓撲
- PT 與道路網絡獨立（agents 需要 access/egress）
- 不適合多模式交通建模

---

## 關鍵文件路徑

### 輸入數據
```
pt2matsim/data/gtfs/tp_metro_gtfs_osm_filtered.zip  # 過濾後的 GTFS
pt2matsim/output_v1/network-prepared.xml.gz          # 基礎路網
```

### 輸出數據（用於模擬）
```
pt2matsim/output_v2/network-with-pt.xml.gz          # ⭐ 模擬用網絡
pt2matsim/output_v2/transitSchedule-mapped.xml.gz   # ⭐ 模擬用時刻表
pt2matsim/output_v2/network-street.xml.gz           # 純道路網絡（備用）
```

### 配置文件
```
pt2matsim/work/ptmapper-config-artificial.xml       # 人工鏈接配置
pt2matsim/work/ptmapper-config-v2-simple.xml        # 放寬模式配置（未使用）
```

### 日誌
```
pt2matsim/output_v2/ptmapper_artificial.log         # 成功運行日誌
pt2matsim/output_v2/ptmapper_final.log              # 失敗嘗試日誌（203K 行）
```

---

## 教訓與最佳實踐

### ✅ 成功因素
1. **快速終止不可行方案**：發現 96 小時預估後立即切換策略
2. **用戶需求優先**：採用裁切數據而非擴展 OSM（符合用戶要求）
3. **選擇合適工具**：人工鏈接模式適合此場景

### ⚠️ 避免陷阱
1. **不要盲目等待**：路由算法卡住時不會自動恢復
2. **檢查網絡連通性**：使用 `NetworkUtils.cleanNetwork()` 預檢
3. **日誌文件爆炸**：200K+ 行警告應觸發提前終止

### 📋 決策樹
```
網絡連通性檢查
├─ 完全連通 → 使用真實路網映射
├─ 部分連通 → 放寬模式限制 + 人工鏈接補充
└─ 不連通   → 純人工鏈接模式（本次方案）
```

---

## 後續建議

### 短期（當前可用）
使用生成的文件進行模擬：
- Network: `pt2matsim/output_v2/network-with-pt.xml.gz`
- Schedule: `pt2matsim/output_v2/transitSchedule-mapped.xml.gz`
- Vehicles: 需要從原始 GTFS 生成

### 中期（完整覆蓋）
下載 Taiwan OSM extract 覆蓋所有 108 個捷運站：
```bash
wget https://download.geofabrik.de/asia/taiwan-latest.osm.pbf
osmium extract -b 121.40,24.95,121.65,25.17 taiwan-latest.osm.pbf \
  -o taipei_expanded.osm.pbf
```

### 長期（真實拓撲）
執行完整多模式網絡生成：
```bash
# 使用 Osm2MultimodalNetwork
java -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  taipei_expanded.osm config.xml

# 再次執行 PT mapping（使用真實路網模式）
```

---

## 性能對比

| 方案 | 配置 | 執行時間 | 成功率 | 適用場景 |
|------|------|----------|--------|----------|
| 原始（卡住） | 默認 | 38+ 小時（未完成） | 0% | - |
| 方案 1（放寬模式） | 多模式 | 96 小時（預估） | 未知 | 部分連通網絡 |
| **方案 2（人工鏈接）** | artificial | **1 分鐘** | **100%** | **不連通網絡** ✅ |

---

## 命令速查

### 檢查 PT mapper 狀態
```bash
# 查看進程
ps aux | grep PublicTransitMapper

# 檢查日誌
tail -f pt2matsim/output_v2/ptmapper_artificial.log

# 檢查進度
grep "Progress" pt2matsim/output_v2/ptmapper_artificial.log | tail -10
```

### 驗證輸出
```bash
# 查看文件大小
ls -lh pt2matsim/output_v2/*.xml.gz

# 統計網絡鏈接
gunzip -c pt2matsim/output_v2/network-with-pt.xml.gz | grep -c '<link '

# 統計 PT 路線
gunzip -c pt2matsim/output_v2/transitSchedule-mapped.xml.gz | grep -c '<transitRoute '
```

### 重新運行（如需要）
```bash
# 使用人工鏈接模式
bash /tmp/run_ptmapper_artificial.sh

# 查看結果
tail -50 pt2matsim/output_v2/ptmapper_artificial.log
```

---

## 相關文檔

- [CLAUDE.md PT Mapping 配置](../CLAUDE.md#pt-mapping-with-pt2matsim)
- [EARLY_STOP_STRATEGY.md](../EARLY_STOP_STRATEGY.md)
- pt2matsim 文檔：https://github.com/matsim-org/pt2matsim

---

**日誌創建時間**：2025-11-06 12:15  
**完成時間**：2025-11-06 12:15  
**總耗時**：1.25 小時（含診斷、過濾、測試多方案）
