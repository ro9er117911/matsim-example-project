# All PT Test Scenario

這是一個使用 **台北捷運虛擬網絡** 的測試場景。

## 場景文件

```
scenarios/corridor/all_pt_test/
├── config.xml                      ← 配置文件
├── network-with-pt.xml.gz          ← 網絡（OSM 道路 + PT 虛擬鏈接）
├── transitSchedule-mapped.xml.gz   ← PT 時刻表
├── transitVehicles.xml             ← PT 車輛
└── test_population_10.xml          ← 10 個測試 agents
```

## 場景特點

- **10 個 agents**：全部使用 PT 模式通勤
- **路線範圍**：板南線（頂埔 → 南港）
- **虛擬 PT 網絡**：使用人工鏈接（473 個 pt_ links）
- **模擬時長**：5 iterations

## 運行方式

### 方法 1：使用 Maven（推薦）

```bash
cd /Users/ro9air/matsim-example-project
./mvnw compile exec:java \
  -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="scenarios/corridor/all_pt_test/config.xml"
```

### 方法 2：使用 Shaded JAR

```bash
cd /Users/ro9air/matsim-example-project

# 先打包
./mvnw clean package

# 運行
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/all_pt_test/config.xml
```

### 方法 3：使用 IDE

1. 打開 `src/main/java/org/matsim/project/RunMatsim.java`
2. 設置運行參數：`scenarios/corridor/all_pt_test/config.xml`
3. 運行

## 輸出

模擬結果將保存在：

```
scenarios/corridor/all_pt_test/output/
├── ITERS/                     ← 每個 iteration 的輸出
│   ├── it.0/
│   ├── it.1/
│   ...
│   └── it.5/
├── output_events.xml.gz       ← 完整事件日誌
├── output_plans.xml.gz        ← 最終 plans
├── output_network.xml.gz      ← 網絡
└── output_transitSchedule.xml.gz  ← PT 時刻表
```

## Agents 描述

| Agent ID | 起點 | 終點 | 出發時間 |
|----------|------|------|----------|
| pt_agent_01 | 頂埔 | 龍山寺 | 07:00 |
| pt_agent_02 | 板橋 | 台北車站 | 07:30 |
| pt_agent_03 | 江子翠 | 西門 | 08:00 |
| pt_agent_04 | 府中 | 忠孝新生 | 07:15 |
| pt_agent_05 | 永寧 | 善導寺 | 07:45 |
| pt_agent_06 | 土城 | 南港 | 06:30 |
| pt_agent_07 | 海山 | 市政府 | 08:15 |
| pt_agent_08 | 亞東醫院 | 國父紀念館 | 07:00 |
| pt_agent_09 | 新埔 | 忠孝復興 | 07:30 |
| pt_agent_10 | 龍山寺 | 昆陽 | 06:45 |

## 配置重點

### PT 路由設置

```xml
<module name="transit">
  <param name="useTransit" value="true" />
  <param name="routingAlgorithmType" value="SwissRailRaptor" />
  <param name="usingTransitInMobsim" value="true" />
</module>

<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false" />
  <param name="transferPenaltyBaseCost" value="0.0" />
</module>
```

### 重要注意事項

1. **PT 不在 teleportedModeParameters**：PT 由 SwissRailRaptor 路由
2. **mainMode 只有 car**：PT 在獨立的虛擬網絡上
3. **虛擬鏈接**：所有 PT 站點使用 `pt_` 前綴的人工鏈接

## 驗證

運行成功後，檢查：

```bash
# 查看 events
gunzip -c output/output_events.xml.gz | grep "PersonEntersVehicle" | head -10

# 應該看到 agents 進入 PT 車輛
# <event time="25200.0" type="PersonEntersVehicle" person="pt_agent_01" vehicle="veh_..." />
```

## 相關文檔

- [PT Mapper 修復日誌](../../../working_journal/2025-11-06-PT-Mapper-Fix.md)
- [CLAUDE.md](../../../CLAUDE.md)
