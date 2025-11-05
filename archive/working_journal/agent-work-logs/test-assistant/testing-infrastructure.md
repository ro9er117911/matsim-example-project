# MATSim Project - 測試基礎設施

## 測試框架概覽

**測試類別總數**: 2
**測試方法總數**: 3
**測試程式碼行數**: 318
**測試框架**: JUnit 5 (Jupiter 5.10.2)
**MATSim 測試工具**: MatsimTestUtils (2025.0)

## 測試組織結構

```
src/test/
├── java/org/matsim/project/
│   ├── RunMatsimTest.java (94 行)           # 整合測試
│   └── tools/
│       └── CorridorPipelineTest.java (224 行)  # PT 管線測試
└── resources/
    ├── gtfs/bl_corridor/                    # GTFS 測試資料
    │   ├── agency.txt, stops.txt, routes.txt
    │   ├── trips.txt, stop_times.txt, calendar.txt
    │   ├── index.txt
    │   └── bl_corridor.gtfs.zip
    └── network/
        └── bl_corridor_network.xml          # 測試網路
```

## 測試覆蓋範圍

### 已覆蓋

1. **整合測試** (RunMatsimTest)
   - 完整模擬生命週期
   - 使用 MATSim 內建 "equil" 場景
   - 人口計劃分數驗證
   - 事件檔案位元組級比較

2. **PT 管線測試** (CorridorPipelineTest)
   - GTFS → MATSim 轉換
   - PT 對應工作流程
   - 站點設施創建
   - 地理邊界檢查
   - 路線生成驗證

### 測試缺口

- ❌ 無工具類別單元測試 (`tools/`)
- ❌ 無座標轉換工具測試 (ConvertGtfsCoordinates)
- ❌ 無網路準備工具測試 (PrepareNetworkForPTMapping)
- ❌ 無替代入口點測試 (RunMatsimApplication)
- ❌ 無性能/壓力測試
- ❌ 無負面測試案例 (無效 GTFS, 錯誤網路)

## 測試工具與模式

### JUnit 5 現代化實踐

```java
// 現代註解
@Test
@RegisterExtension  // 取代 JUnit 4 的 @Rule
@TempDir           // 自動臨時目錄管理

// 分組斷言
assertAll(
    () -> assertTrue(condition1),
    () -> assertEquals(expected, actual)
);
```

### MatsimTestUtils 用法

```java
@RegisterExtension
private MatsimTestUtils utils = new MatsimTestUtils();

// 提供功能:
utils.getInputDirectory()   // 參考/預期資料
utils.getOutputDirectory()  // 測試輸出 (自動清理)
```

### 測試資源隔離模式

```java
private Path copyResourceDirectory(String resourceRoot) {
    // 從 classpath 複製到 tempDir
    // 確保測試隔離
    // 可修改檔案而不影響其他測試
}
```

## 關鍵測試案例

### 1. RunMatsimTest.test()

**驗證內容**:
- 完整模擬執行 (1 次迭代)
- 人口分數匹配 (容差 0.001)
- 事件檔案精確匹配

**執行時間**: <10 秒

**測試資料**: MATSim 內建 "equil" 場景

### 2. CorridorPipelineTest.gtfsConversionProducesCorridorSchedule()

**驗證內容**:
- 6 個站點設施
- 2 條運輸線 (地鐵 + 公車)
- 每條線 2 個路線 (東向/西向)
- 地理邊界: X∈[303600,305200], Y∈[2770350,2770900]

**測試資料**: 台北藍線走廊 (忠孝新生-忠孝復興)

### 3. CorridorPipelineTest.publicTransitMapperMapsCorridorStopsToLinks()

**驗證內容**:
- 完整 GTFS → MATSim → PT Mapping 管線
- 站點對應到網路連結 (linkId not null)
- 車輛分配到發車班次
- 對應後時刻表的合理性

**PT Mapper 配置**:
```xml
<param name="maxLinkCandidateDistance" value="200.0" />
<param name="nLinkThreshold" value="4" />
<param name="modeSpecificRules" value="true" />
```

## 測試資料清單

### bl_corridor 測試裝置

**網路**:
- 檔案: `bl_corridor_network.xml`
- 節點: BL14, BL15 (兩個捷運站)
- 連結: 1.2km 雙向，modes="pt,subway"
- 座標系統: EPSG:3826

**GTFS**:
- 檔案: `gtfs/bl_corridor/*.txt` + zip
- 代理商: MRT
- 站點: 6 個 (2 地鐵 + 4 公車)
- 路線: 2 條 (BL 地鐵線, B1 公車路線)
- 班次: 4 個 (2 方向 × 2 路線)

## CI/CD 整合

### GitHub Actions 配置

```yaml
# .github/workflows/maven.yml
- uses: actions/setup-java@v3
  with:
    java-version: 21
    distribution: 'zulu'
- run: mvn -B verify
```

**狀態**: ✅ 正常運作

### GitLab CI 配置

```yaml
# .gitlab-ci.yml
image: maven:3-jdk-7  # ❌ 過時!
```

**狀態**: ❌ 需更新至 Java 21

## 測試執行命令

```bash
# 執行所有測試
./mvnw test

# 執行特定測試
./mvnw test -Dtest=RunMatsimTest
./mvnw test -Dtest=CorridorPipelineTest

# 包含整合測試
./mvnw verify
```

**預期執行時間**: <30 秒 (完整測試套件)

## 測試最佳實踐

### 已採用 ✅

1. JUnit 5 現代註解
2. 透過臨時目錄隔離測試
3. 資源隔離 (複製到 temp)
4. 描述性斷言訊息
5. 快速執行 (1 次迭代)
6. 端到端測試哲學

### 建議改進 📋

1. **新增單元測試**
   ```java
   @Test
   void convertCoordinates_WGS84toEPSG3826() {
       // 測試座標轉換邏輯
   }
   ```

2. **參數化測試**
   ```java
   @ParameterizedTest
   @CsvSource({"1,expected1", "10,expected10"})
   void testWithDifferentIterations(int iterations, String expected) {
       // 不同迭代次數測試
   }
   ```

3. **新增負面測試**
   ```java
   @Test
   void invalidGtfs_throwsException() {
       assertThrows(IllegalArgumentException.class, () -> {
           GtfsToMatsim.convert(invalidGtfsPath);
       });
   }
   ```

4. **測試文檔**
   - 建立 `src/test/README.md`
   - 說明測試場景
   - 記錄如何更新參考資料

5. **測試日誌配置**
   - 建立 `src/test/resources/log4j2-test.xml`
   - 減少測試執行時的雜訊

## 測試指標

| 指標 | 數值 |
|------|------|
| 測試類別數 | 2 |
| 測試方法數 | 3 |
| 測試斷言數 | 25 |
| 測試資源檔案數 | 9 |
| 測試對程式碼比率 | ~1:10 |
| 估計執行時間 | <30 秒 |

## 測試覆蓋率改進建議

### 高優先級

1. **工具類別單元測試**
   - ConvertGtfsCoordinates
   - PrepareNetworkForPTMapping
   - CleanSubwayNetwork
   - MergeGtfsSchedules

2. **CLI 介面測試**
   - RunMatsimApplication

3. **負面測試**
   - 無效 GTFS 處理
   - 網路連通性錯誤處理

### 中優先級

4. **效能基準測試**
   - 追蹤模擬執行時間
   - 檢測效能退化

5. **參考資料管理**
   - 記錄如何生成參考資料
   - 版本控制參考資料更新

## 相關文檔

- 測試覆蓋率分析: `test-coverage-analysis.md`
- 測試最佳實踐: `testing-best-practices.md`
- 開發指南: `../dev-master/development-guide.md`
