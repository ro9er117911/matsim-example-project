# 常見問題排解

本文件聚焦模擬執行與資料一致性問題，避免與各主題指南重複。

---

## 一、資料一致性

### 1) Activity link 找不到
**現象**：`Link id=XXX not found in network`  
**處理**：
- 改用座標型 activity
- 或先驗證 link 是否存在

```bash
grep -o 'link="[^"]*"' population.xml | sort -u > plan_links.txt
zcat network.xml.gz | grep '<link id=' | grep -o 'id="[^"]*"' | sort -u > network_links.txt
comm -23 plan_links.txt network_links.txt
```

### 2) CRS 不一致
**現象**：活動點落在路網外
**處理**：確保 network / population / GTFS 都為 EPSG:3826

---

## 二、模擬行為問題

### 1) Stuck agents
**現象**：`Agent XXX is stuck and removed`  
**處理**：
- 檢查路網連通性與活動點位置
- 視需求增加 `qsim.stuckTime`

### 2) 記憶體不足
**現象**：`OutOfMemoryError`  
**處理**：提高 JVM 記憶體、縮小區域或降低代理人數

---

## 三、PT 相關問題

PT 映射與路由問題請見：
- `docs/03-gtfs-public-transit/public-transit-guide.md`
- `docs/08-configuration/configuration-reference.md`

---

## 四、工具與編輯器

VS Code 大檔案崩潰處理：`docs/10-troubleshooting/vs-code-crash-diagnosis.md`
