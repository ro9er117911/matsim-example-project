# MATSim Project - 專案架構概覽

## 專案基本資訊

**專案座標**:
- Group ID: `org.matsim`
- Artifact ID: `matsim-example-project`
- Version: `0.0.1-SNAPSHOT`
- Parent: `matsim-all:2025.0`

**技術棧**:
- Java 21 (release flag)
- Maven 3.9.8 (via wrapper)
- MATSim 2025.0
- JUnit 5 (Jupiter)
- pt2matsim 25.8 (vendored)

**專案位置**: `/Users/ro9air/matsim-example-project`

## 核心架構模式

### 三階段模擬生命週期

所有模擬執行都遵循 **Config → Scenario → Controler** 流程：

1. **Config Phase** - 載入/修改模擬參數
2. **Scenario Phase** - 載入/修改資料結構 (網路、人口、運輸時刻表)
3. **Controler Phase** - 配置/執行模擬

此模式確保配置、資料、執行邏輯的明確分離。

### 應用程式入口點

專案提供三個主要入口點：

| 入口點 | 用途 | 特點 |
|--------|------|------|
| `RunMatsim.java` | 基本執行 | 手動設定，適合學習和原型開發 |
| `RunMatsimApplication.java` | CLI 執行 | 繼承 MATSimApplication，支援命令列參數 |
| `MATSimGUI.java` | GUI 執行 | 圖形介面，shaded JAR 的主類別 |

## 目錄結構

```
matsim-example-project/
├── src/
│   ├── main/java/org/matsim/
│   │   ├── project/           # 核心應用程式
│   │   │   ├── RunMatsim*.java          # 入口點
│   │   │   └── tools/                   # PT 工具鏈
│   │   └── gui/               # GUI 啟動器
│   └── test/java/org/matsim/project/    # 測試
├── scenarios/                 # 模擬場景
│   ├── equil/                # 完整測試場景 (台北捷運藍線)
│   ├── taipei-metro-test/    # Metro 對應測試
│   └── corridor/             # 最小測試場景
├── pt2matsim/                # PT 工具鏈工作區
│   ├── work/                 # 工具和配置
│   ├── data/                 # 輸入資料 (GTFS, OSM)
│   └── out/                  # 處理輸出
├── agent-work-logs/          # Agent 工作日誌 (本目錄)
└── output/                   # 模擬輸出

```

## 建置產出

**主要產出**: `matsim-example-project-0.0.1-SNAPSHOT.jar` (218 MB)
- 類型: Shaded executable JAR (包含所有依賴)
- 主類別: `org.matsim.gui.MATSimGUI`
- 位置: 專案根目錄

**建置命令**:
```bash
./mvnw clean package    # 建置 shaded JAR
./mvnw test            # 執行測試
```

## 依賴概覽

**總依賴數**: 331 (包含遞移依賴)

**主要依賴類別**:
- MATSim Core + 11 個 Contrib 模組
- Geotools 31.3 (地理空間處理)
- pt2matsim 25.8 (vendored, system scope)
- Osmosis 0.49.2 (OSM 處理)
- Guice 7.0.0 (依賴注入)
- JUnit 5.10.2 (測試)

**特殊依賴**: pt2matsim 為 system-scoped，位於 `pt2matsim/work/pt2matsim-25.8-shaded.jar`

## 關鍵配置

**座標系統**: EPSG:3826 (台灣 TWD97/TM2)
**預設迭代次數**: 0 (測試場景) 或 10+ (正式場景)
**輸出覆寫模式**: `deleteDirectoryIfExists` (開發模式)

## 模組職責劃分

### 核心模組
- `RunMatsim*` - 編排與入口點
- `tools/*` - 獨立命令列工具 (水平隔離)
- `gui/*` - GUI 呈現層

### PT 工具鏈 (tools/)
- `GtfsToMatsim` - GTFS 轉換
- `ConvertGtfsCoordinates` - 座標轉換
- `MergeGtfsSchedules` - 時刻表合併
- `PrepareNetworkForPTMapping` - 網路清理
- `CleanSubwayNetwork` - 地鐵網路提取
- `PreRoutePt` - PT 路徑預計算
- `OsmPbfToXml` - OSM 格式轉換

## CI/CD

**GitHub Actions** (主要):
- Java 21 (Zulu)
- Maven cache 啟用
- 觸發: push/PR to master
- 命令: `mvn -B verify`

**過時配置**: Travis CI, GitLab CI (使用 JDK 7，需更新)

## 下一步建議

**短期改進**:
1. 修正 `${parent.version}` → `${project.parent.version}`
2. 移除或更新過時的 CI 配置
3. 考慮將 shaded JAR 輸出至 `target/` 目錄

**長期考慮**:
1. pt2matsim 發布至 Maven Central 或 JitPack
2. 審查是否所有 contrib 模組都有使用
3. 考慮建立 build profiles (development/production)

## 相關文檔

- 詳細架構分析: `architecture-analysis.md`
- 建置系統分析: `build-system-analysis.md`
- 模組清單: `module-inventory.md`
