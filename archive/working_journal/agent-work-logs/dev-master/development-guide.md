# MATSim Project - 開發者指南

## 開發環境設定

### 必要條件

- **Java**: 21 (建議使用 Zulu 或 Eclipse Temurin)
- **Maven**: 3.9.8 (透過 wrapper 提供)
- **IDE**: IntelliJ IDEA 或 Eclipse
- **記憶體**: 最少 8 GB RAM (PT mapping 需要 10+ GB)

### 專案匯入

```bash
# Clone 專案
git clone <repository-url>
cd matsim-example-project

# 建置專案
./mvnw clean package

# 執行測試
./mvnw test
```

**IntelliJ IDEA**:
1. File → Open → 選擇 `pom.xml`
2. 作為專案開啟
3. IDE 會自動下載依賴並設定

**Eclipse**:
```bash
./mvnw eclipse:eclipse
# 然後匯入現有 Maven 專案
```

## 專案結構導覽

### 原始碼組織

```
src/main/java/org/matsim/
├── project/                     # 主套件
│   ├── RunMatsim.java           # 基本入口點
│   ├── RunMatsimApplication.java # CLI 入口點
│   ├── RunMatsimFromExamplesUtils.java # 測試入口點
│   └── tools/                   # PT 工具鏈
│       ├── GtfsToMatsim.java         # GTFS 轉換
│       ├── ConvertGtfsCoordinates.java # 座標轉換
│       ├── MergeGtfsSchedules.java    # 時刻表合併
│       ├── PrepareNetworkForPTMapping.java # 網路準備
│       ├── CleanSubwayNetwork.java    # 地鐵網路提取
│       ├── PreRoutePt.java            # PT 預路徑
│       └── OsmPbfToXml.java           # OSM 轉換
└── gui/                         # GUI 套件
    └── MATSimGUI.java           # GUI 啟動器
```

### 關鍵設計模式

#### 1. 三階段模擬模式 (Config → Scenario → Controler)

**所有模擬必須遵循此順序**:

```java
// Phase 1: Config
Config config = ConfigUtils.loadConfig(configFile);
// 自訂配置...

// Phase 2: Scenario
Scenario scenario = ScenarioUtils.loadScenario(config);
// 自訂場景...

// Phase 3: Controler
Controler controler = new Controler(scenario);
// 自訂控制器...
controler.run();
```

**為什麼**: 確保配置→資料→執行的明確分離

#### 2. Template Method 模式 (RunMatsimApplication)

```java
public class RunMatsimApplication extends MATSimApplication {
    @Override
    protected Config prepareConfig(Config config) {
        // Hook 1: 修改配置
        return config;
    }

    @Override
    protected void prepareScenario(Scenario scenario) {
        // Hook 2: 修改場景
    }

    @Override
    protected void prepareControler(Controler controler) {
        // Hook 3: 新增模組、事件處理器
    }
}
```

**使用時機**: 需要 CLI 支援和標準化自訂點

#### 3. Command 模式 (工具套件)

```java
public final class ToolName {
    private ToolName() {}  // 防止實例化

    public static void main(String[] args) {
        // 解析參數 → 驗證 → 執行 → 回報
    }
}
```

**特點**:
- Final 類別 + private 建構子
- 無共享狀態
- 單一職責
- 獨立命令列工具

## 開發工作流程

### 1. 新增功能

```bash
# 1. 建立功能分支
git checkout -b feature/new-feature

# 2. 實作功能 (遵循三階段模式)
# 編輯檔案...

# 3. 執行測試
./mvnw test

# 4. 建置驗證
./mvnw clean package

# 5. 提交變更
git add .
git commit -m "Add new feature"

# 6. 推送並建立 PR
git push origin feature/new-feature
```

### 2. 除錯模擬

```java
// 啟用詳細日誌
config.controller().setWriteEventsInterval(1);
config.controller().setWritePlansInterval(1);

// 減少迭代次數快速測試
config.controller().setLastIteration(1);

// 啟用視覺化
controler.addOverridingModule(new OTFVisLiveModule());
```

### 3. 測試新場景

```bash
# 使用最小配置快速測試
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config_min.xml

# 增加記憶體執行大型場景
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/equil/config.xml
```

## 編碼標準

### Java 風格

```java
// 類別命名: PascalCase
public class GtfsToMatsim { }

// 方法命名: camelCase
public void convertGtfsToMatsim() { }

// 常數命名: UPPER_SNAKE_CASE
private static final String DEFAULT_CRS = "EPSG:3826";

// 套件命名: lowercase
package org.matsim.project.tools;
```

### MATSim 慣例

```java
// 使用 MATSim 的工具類別
Config config = ConfigUtils.loadConfig(args[0]);
Scenario scenario = ScenarioUtils.loadScenario(config);
Population population = PopulationUtils.createPopulation(config);

// 座標系統: 統一使用 EPSG:3826
config.global().setCoordinateSystem("EPSG:3826");

// 覆寫設定: 開發時使用 deleteDirectoryIfExists
config.controller().setOverwriteFileSetting(
    OverwriteFileSetting.deleteDirectoryIfExists);
```

### 檔案編碼

- **原始碼**: UTF-8
- **資源檔**: UTF-8
- **配置檔**: UTF-8 (Maven 強制執行)

## 常見開發任務

### 新增自訂評分函數

```java
@Override
protected void prepareControler(Controler controler) {
    controler.addOverridingModule(new AbstractModule() {
        @Override
        public void install() {
            bind(ScoringFunctionFactory.class)
                .to(MyCustomScoringFunctionFactory.class);
        }
    });
}
```

### 新增事件處理器

```java
@Override
protected void prepareControler(Controler controler) {
    controler.addOverridingModule(new AbstractModule() {
        @Override
        public void install() {
            addEventHandlerBinding()
                .toInstance(new MyEventHandler());
        }
    });
}
```

### 修改網路

```java
@Override
protected void prepareScenario(Scenario scenario) {
    Network network = scenario.getNetwork();

    // 新增節點
    Node node = network.getFactory()
        .createNode(Id.createNodeId("newNode"), coord);
    network.addNode(node);

    // 新增連結
    Link link = network.getFactory()
        .createLink(Id.createLinkId("newLink"), fromNode, toNode);
    link.setAllowedModes(Set.of("car", "pt"));
    network.addLink(link);
}
```

### 建立簡單人口

```java
Population population = scenario.getPopulation();
PopulationFactory factory = population.getFactory();

Person person = factory.createPerson(Id.createPersonId("person1"));
Plan plan = factory.createPlan();

// 活動-腿-活動 模式
Activity home = factory.createActivityFromLinkId("home", linkId);
home.setEndTime(8 * 3600); // 08:00
plan.addActivity(home);

Leg leg = factory.createLeg("car");
plan.addLeg(leg);

Activity work = factory.createActivityFromLinkId("work", linkId);
work.setEndTime(17 * 3600); // 17:00
plan.addActivity(work);

person.addPlan(plan);
population.addPerson(person);
```

## PT 工具鏈開發

### GTFS 轉換工作流程

```bash
# 1. 準備 GTFS 資料
# 放置於 pt2matsim/data/gtfs/

# 2. 執行轉換
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  --gtfsZip data.gtfs.zip \
  --network network.xml.gz \
  --outDir output/ \
  --targetCRS EPSG:3826

# 3. 準備網路
java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.PrepareNetworkForPTMapping \
  network.xml.gz network-ready.xml.gz

# 4. PT 對應
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config.xml
```

### 建立新工具

```java
package org.matsim.project.tools;

public final class MyNewTool {
    private MyNewTool() {}  // 防止實例化

    public static void main(String[] args) {
        // 1. 參數驗證
        if (args.length < 2) {
            System.err.println("Usage: MyNewTool <input> <output>");
            System.exit(1);
        }

        // 2. 載入輸入
        String inputPath = args[0];
        String outputPath = args[1];

        // 3. 處理
        processData(inputPath, outputPath);

        // 4. 回報
        System.out.println("Processing complete!");
    }

    private static void processData(String in, String out) {
        // 實作邏輯...
    }
}
```

## 效能考量

### 記憶體管理

```bash
# 小場景 (<500 代理人)
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# 中型場景 (500-5000 代理人)
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# 大型場景 (>5000 代理人)
java -Xmx16g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# PT Mapping
java -Xmx10g -cp pt2matsim-25.8-shaded.jar ...
```

### 快速迭代技巧

```xml
<!-- 減少迭代次數 -->
<param name="lastIteration" value="1" />

<!-- 減少輸出 -->
<param name="writeEventsInterval" value="10" />
<param name="writePlansInterval" value="10" />

<!-- 使用樣本人口 -->
<!-- 只載入 10% 的代理人進行測試 -->
```

## 常見問題排解

### 建置問題

**問題**: `pt2matsim` 依賴找不到
```bash
# 確認 JAR 存在
ls -lh pt2matsim/work/pt2matsim-25.8-shaded.jar
# 應該顯示 85 MB 的檔案
```

**問題**: Geotools CRS 錯誤
```
解決方案: 使用 shade plugin (已配置)
確保 META-INF/services 正確合併
```

### 執行問題

**問題**: OutOfMemoryError
```bash
# 增加 heap 大小
java -Xmx16g -jar ...
```

**問題**: PT stops 沒有 linkId
```bash
# 執行 PT mapping
java -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper config.xml
```

## 相關文檔

- 入口點指南: `entry-points-guide.md`
- PT 工具實作: `pt-tools-implementation.md`
- 測試指南: `../test-assistant/testing-infrastructure.md`
- 專案架構: `../project-structure-specialist/architecture-analysis.md`
