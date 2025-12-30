# MATSim 範例專案

這是一個多代理人交通模擬 (Multi-Agent Transport Simulation, MATSim) 專案，專注於模擬城市交通系統，**特別是災難撤離情境模擬**。

## 🌟 專案亮點

- 🌊 **災難撤離模擬** - 海嘯/洪水情境下的大規模撤離模擬
- 📊 **SimWrapper 視覺化** - 現代化的網頁儀表板分析平台
- 🚇 **台北捷運整合** - 完整的大眾運輸路網模擬
- ⚡ **時變路網** - 動態道路封閉事件模擬

## 快速開始

```bash
# 建置專案
./mvnw clean package

# 執行 MATSim GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# 執行特定場景
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/corridor/taipei_test/config.xml
```

## 技術棧

| 類別 | 技術 |
|------|------|
| 程式語言 | Java 21 |
| 建置系統 | Maven |
| 模擬框架 | MATSim 2025.0 |
| 大眾運輸 | pt2matsim, SwissRailRaptor |
| 視覺化 | **SimWrapper** (取代 Via) |
| 座標系統 | EPSG:3826 (TWD97) |

## 專案結構

```
matsim-example-project/
├── src/main/java/               # Java 原始碼
│   └── org/matsim/project/
│       ├── RunMatsim.java       # 基本進入點
│       ├── RunMatsimApplication.java  # CLI 進入點
│       ├── evacuation/          # 🆕 災難撤離模組
│       └── tools/               # 路網建置工具
├── 5000_disatar/                # 🆕 災難模擬專案 (5000 代理人)
│   ├── 03_phase2_production/    # 生產級路網
│   └── 05_combined_evac/        # 綜合撤離場景
├── scenarios/                   # 場景設定檔
├── scripts/                     # 🆕 自動化腳本
├── tools/                       # 🆕 分析工具
├── examples/                    # 🆕 範例專案
└── PROJECT_WIKI.md              # 🆕 專案導覽地圖
```

## 文件說明

📚 **詳細指南請見**:

| 文件 | 說明 |
|------|------|
| [`docs/README.md`](docs/README.md) | 專案文件總覽與索引 |
| [`PROJECT_WIKI.md`](PROJECT_WIKI.md) | 專案導覽與流程圖 |
| [`CLAUDE.md`](CLAUDE.md) | AI 助手專用指引 |
| [`CHANGELOG.md`](CHANGELOG.md) | 變更紀錄 |

### 災難模擬文件
- [`docs/06-disaster-evacuation/evacuation-guide.md`](docs/06-disaster-evacuation/evacuation-guide.md) - 撤離情境說明
- [`5000_disatar/05_combined_evac/WORKFLOW.md`](5000_disatar/05_combined_evac/WORKFLOW.md) - 撤離模擬工作流

## 功能特色

### 核心功能
- ✅ **大眾運輸模擬** - 完整的 GTFS 到 MATSim 處理流程
- ✅ **多運具路網** - 支援汽車、大眾運輸、步行
- ✅ **SwissRailRaptor** - 快速的大眾運輸路徑演算法
- ✅ **台北捷運** - 包含 5 條捷運線 (BL, G, O, R, BR)

### 災難模擬 (新增)
- ✅ **時變路網** - 動態道路封閉事件
- ✅ **海嘯撤離** - 基於淹水深度的道路關閉
- ✅ **大規模模擬** - 支援 5000+ 代理人
- ✅ **撤離分析** - 累積撤離曲線、熱力圖

### 視覺化 (SimWrapper)
- ✅ **網頁儀表板** - 無需安裝，瀏覽器直接開啟
- ✅ **互動式地圖** - 路網、軌跡、熱力圖
- ✅ **統計圖表** - 撤離時間、運具分配
- ✅ **自動生成** - 模擬結束自動產生 dashboard

## SimWrapper 視覺化

本專案使用 **SimWrapper** 作為主要視覺化平台（取代 Via）：

```bash
# 啟動 SimWrapper 伺服器
npx simwrapper serve --port 8000

# 開啟瀏覽器
open http://localhost:8000
```

輸出目錄會自動包含：
- `dashboard-*.yaml` - 儀表板設定
- `network.avro` - 路網視覺化
- `*.csv` - 統計資料

流程與檔案說明請見 `docs/05-simulation/simwrapper.md`。

## 開發設定

### 前置需求
- Java 21
- Maven 3.6+
- Git
- Node.js (SimWrapper 用)

### 執行測試
```bash
./mvnw test
```

## 範例場景

### 基本測試
```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/corridor/taipei_test/config.xml
```

### 災難撤離模擬 (5000 代理人)
```bash
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  5000_disatar/05_combined_evac/config_optimized_iter1000.xml
```

## 最近更新

| 日期 | 更新內容 |
|------|----------|
| **2025-12** | 🆕 災難撤離模擬、SimWrapper 整合、專案重構 |
| 2025-11-17 | 文件整合與重組 |
| 2025-11-12 | 100 代理人人口資料 |
| 2025-11-05 | 大眾運輸轉乘改進 |

完整歷史請參閱 [`CHANGELOG.md`](CHANGELOG.md)

## 授權

- **MATSim 程式碼** (`src/`): [GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
- **輸入/輸出檔案**: [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/)

---

**Built with MATSim** | [matsim.org](https://matsim.org) | Version 2025.0
