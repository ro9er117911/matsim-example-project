# MATSim 範例專案

這是一個多代理人交通模擬 (Multi-Agent Transport Simulation, MATSim) 專案，專注於模擬城市交通系統。

## 快速開始

```bash
# 建置專案
./mvnw clean package

# 執行 MATSim GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# 執行特定場景
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml
```

## 技術棧

- **Java 21** - 程式語言
- **Maven** - 建置系統
- **MATSim 2025.0** - 模擬框架
- **pt2matsim** - GTFS 轉 MATSim 轉換器

## 專案結構

```
matsim-example-project/
├── src/main/java/               # Java 原始碼
│   └── org/matsim/project/
│       ├── RunMatsim.java       # 基本進入點
│       ├── RunMatsimApplication.java  # CLI 進入點
│       └── tools/               # 大眾運輸轉換工具
├── scenarios/                   # 場景設定檔
│   ├── equil/                  # 範例場景
│   └── corridor/taipei_test/   # 台北捷運測試場景
├── pt2matsim/                   # GTFS 轉換流程資料
├── docs/                        # 文件
├── output/                      # 模擬結果輸出
└── defaultConfig.xml            # 完整設定參考檔
```

## 文件說明

📚 **詳細指南請見 [`docs/`](docs/) 目錄**:

### 入門指南
1. [快速開始指南](docs/1-quick-start.md) - 安裝與首次執行
2. [架構總覽](docs/2-architecture.md) - 系統設計
3. [設定參考](docs/5-configuration.md) - 所有設定選項說明
4. [疑難排解](docs/6-troubleshooting.md) - 常見問題

### 專題指南
- [模擬指南](docs/simulation-guide.md) - 執行 46/100 代理人的模擬
- [Via 匯出指南](docs/via-export.md) - 匯出資料至 Via 可視化平台
- [大眾運輸指南](docs/3-public-transit.md) - GTFS 轉 MATSim 工作流
- [代理人開發](docs/4-agent-development.md) - 建立人口資料
- [人口生成](docs/agent-generation.md) - 人口生成腳本
- [產出分析](docs/output-analysis.md) - 分析模擬結果
- [提早終止策略](docs/early-stop-strategy.md) - 提早終止模擬的模式
- [代理人旅程指南](docs/agent-journey-guide.md) - 建構代理人旅程

📝 **AI 助手專用**: 關於本專案的特定指引請參閱 [`CLAUDE.md`](CLAUDE.md)

📅 **變更紀錄**: 最近的變更請參閱 [`CHANGELOG.md`](CHANGELOG.md)

## 功能特色

- ✅ **大眾運輸模擬** - 完整的 GTFS 到 MATSim 處理流程
- ✅ **多運具路網** - 支援汽車、大眾運輸、步行
- ✅ **SwissRailRaptor** - 快速的大眾運輸路徑演算法
- ✅ **台北捷運** - 包含 5 條捷運線 (BL, G, O, R, BR)
- ✅ **測試人口** - 內含 50 代理人的測試場景
- ✅ **Python 工具** - 用於人口生成與分析

## 開發設定

### 前置需求

- Java 21
- Maven 3.6+
- Git

### IDE 設定

**IntelliJ IDEA**:
```
File → New → Project from Version Control
貼上儲存庫 URL → Clone
```

**Eclipse**:
```
File → Import → Git → Projects from Git → Clone URI
File → Import → Maven → Existing Maven Projects
```

### 執行測試

```bash
# 執行所有測試
./mvnw test

# 執行特定測試
./mvnw test -Dtest=RunMatsimTest
```

## 範例場景

### Equil 測試場景
```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml
```

### 台北捷運測試 (50 代理人)
```bash
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config.xml \
  --config:plans.inputPlansFile test_population_50.xml
```

## 產生自訂人口

```bash
# 編輯 src/main/python/generate_test_population.py 修改車站或路線
python src/main/python/generate_test_population.py

# 產出檔案: scenarios/corridor/taipei_test/test_population_50.xml
```

## 座標系統

預設使用: **EPSG:3826** (TWD97 / TM2 zone 121, Taiwan)

## 產出分析

模擬結束後，可檢查以下檔案：
- `output/scorestats.png` - 收斂狀況
- `output/modestats.png` - 運具分配統計
- `output/output_trips.csv.gz` - 旅次資料
- `output/output_events.xml.gz` - 所有事件紀錄

## 貢獻方式

1. Fork 本儲存庫
2. 建立功能分支 (feature branch)
3. 進行修改
4. 執行測試: `./mvnw test`
5. 提交 Pull Request

## 支援

- 📖 **文件**: [`docs/`](docs/)
- 🐛 **問題回報**: GitHub Issues
- 💬 **MATSim 協助**: matsim@googlegroups.com
- 🌐 **MATSim 文件**: https://matsim.org/docs

## 授權

- **MATSim 程式碼** (`src/`): [GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
- **輸入/輸出檔案** (`scenarios/`, `output/`): [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/)
- **原始資料** (`original-input-data/`): 依各自的授權規定

## 最近更新

完整專案歷史請參閱 [`CHANGELOG.md`](CHANGELOG.md)，包含：
- **2025-11-17**: 文件整合與重組
- **2025-11-12**: 100 代理人人口資料 (含 30 位轉乘代理人)
- **2025-11-05**: Via 匯出功能增強 (雙重過濾)
- **2025-11-05**: 改進 46 代理人人口資料 (含大眾運輸轉乘)
- **2025-11-03**: 修正大眾運輸 SwissRailRaptor 設定

---

**Built with MATSim** | [matsim.org](https://matsim.org) | Version 2025.0
