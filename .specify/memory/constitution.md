# MATSim 災難模擬專案 Constitution

## Core Principles

### I. Data Safety First
**絕不直接讀取大型檔案** (`*.xml.gz`, events, osm, pbf`)
使用 `head`, `zcat | head`, `rg` 進行預覽與搜尋

### II. Coordinate Consistency
所有資料使用 **EPSG:3826** (TWD97, Taiwan)
視覺化輸出轉換為 **EPSG:4326** (WGS84)

### III. Modular Pipeline
每個工作流程獨立可執行：
- `/disaster.network` → 路網修改
- `/disaster.simulation` → 模擬執行
- `/disaster.simwrapper` → 可視化處理

### IV. Validation Gates
每個步驟需驗證：
- 檔案存在性檢查
- 輸出格式驗證
- 結果合理性確認

### V. Reproducibility
- 使用 config 檔案版本控制
- Pipeline 腳本可重複執行
- 支援 `SKIP_SIM=1` 重生視覺化

## Technology Stack

| 組件 | 技術 |
|------|------|
| 模擬核心 | Java 21 + MATSim 2025.0 |
| 建置系統 | Maven |
| PT 轉換 | pt2matsim (vendored JAR) |
| 工具腳本 | Python 3 + Shell |
| 可視化 | SimWrapper |

## Disaster Simulation Workflow

```
1. 準備封閉區域資料 (溢淹圖/海岸線)
   ↓
2. 生成 changeEvents.xml (time-variant network)
   ↓
3. 配置 config.xml (staggered evacuation)
   ↓
4. 執行 headless 模擬
   ↓
5. 生成 dashboard YAML + GeoJSON
   ↓
6. SimWrapper 可視化
```

## Key Configuration Patterns

### Time-Variant Network
```xml
<module name="network">
    <param name="inputChangeEventsFile" value="changeEvents.xml"/>
    <param name="timeVariantNetwork" value="true"/>
</module>
```

### Headless Execution
```xml
<module name="qsim">
    <param name="stuckTime" value="0"/>
    <param name="storageCapacityFactor" value="2.0"/>
</module>
<module name="transit">
    <param name="usingTransitInMobsim" value="false"/>
</module>
```

## Governance

- 專案遵循 `CLAUDE.md` 作為主要開發指南
- 工作流程定義於 `.agent/workflows/disaster.*.md`
- 配置參考 `defaultConfig.xml`

**Version**: 1.0.0 | **Created**: 2025-12-15
