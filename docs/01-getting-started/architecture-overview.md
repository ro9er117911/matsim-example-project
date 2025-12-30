# 架構概覽

本文件整理專案入口、資料流程與輸出結構。

---

## 一、入口與三階段流程

| 類別 | 入口 | 說明 |
|---|---|---|
| 基本入口 | `RunMatsim.java` | 簡單場景或測試 |
| CLI 入口 | `RunMatsimApplication.java` | 參數化執行 |
| 範例入口 | `RunMatsimFromExamplesUtils.java` | 範例/測試 |

共通流程：
1. **Config**：讀取與調整設定
2. **Scenario**：建置 network / population
3. **Controler**：執行模擬與輸出

---

## 二、資料流程

```
GTFS → transitSchedule.xml
OSM/SHP → network.xml
population.xml → Controler → output/
```

PT 相關流程請見 `docs/03-gtfs-public-transit/public-transit-guide.md`。

---

## 三、輸出結構

```
output/
├── output_config.xml
├── output_events.xml.gz
├── output_plans.xml.gz
├── output_network.xml.gz
├── scorestats.csv
├── modestats.csv
└── ITERS/
```

---

## 四、測試架構

- JUnit 5
- `RunMatsimTest`
- `MatsimTestUtils`

---

## 五、技術堆疊

- Java 21
- Maven
- MATSim 2025.0
- pt2matsim 25.8
- SwissRailRaptor

---

## 六、座標系統

預設使用 **EPSG:3826**：

```xml
<module name="global">
  <param name="coordinateSystem" value="EPSG:3826"/>
</module>
```
