# 100 Agents Simulation Guide

## 概述

已成功生成100個agents的population，包含：
- ✅ **20個單線PT agents** (PT-only，無car availability)
- ✅ **30個轉乘PT agents** (PT-only，無car availability) ← **達成目標！**
- ✅ **40個car agents**
- ✅ **10個walk agents**

## 檔案位置

- **Population XML**: `scenarios/corridor/taipei_test/test_population_100.xml`
- **生成腳本**: `src/main/python/generate_test_population_100.py`
- **Config檔案**: `scenarios/corridor/taipei_test/config.xml`

## 重要特性

### 1. PT-only Agents（無car availability）
- 所有50個PT agents（單線+轉乘）都是PT-ONLY
- 不會在replanning過程中切換到car mode
- 確保轉乘功能得到充分驗證

### 2. SwissRailRaptor 配置正確
```xml
<module name="swissRailRaptor">
  <!-- ✓ 正確：人口計劃只有 <leg mode="pt"/> -->
  <param name="useIntermodalAccessEgress" value="false" />

  <!-- ✓ 零轉乘成本，確保選擇最短路線 -->
  <param name="transferPenaltyBaseCost" value="0.0" />
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0" />
</module>
```

### 3. 30個轉乘routes示例

```
短距離轉乘（高成功率）：
- BL10 → BL14 → O07 → O09 (BL → O transfer)
- BL11 → BL12 → R10 → R15 (BL → R transfer)
- G07 → G10 → R08 → R11 (G → R transfer)
- O03 → O06 → R07 → R10 (O → R transfer)

中距離轉乘：
- BL02 → BL12 → G12 → G19 (BL → G longer)
- G02 → G10 → R08 → R15 (G → R longer)
- BR03 → BR09 → R05 → R11 (BR → R longer)
```

## 執行步驟

### 步驟 1: 編譯專案（如果尚未編譯）

```bash
cd /home/user/matsim-example-project
mvn clean package -DskipTests
```

或使用Maven wrapper（如果有）：
```bash
./mvnw clean package -DskipTests
```

### 步驟 2: 運行模擬

```bash
cd /home/user/matsim-example-project

# 使用編譯好的jar執行（推薦）
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config.xml \
  --config:plans.inputPlansFile test_population_100.xml \
  --config:controller.lastIteration 5 \
  --config:controller.outputDirectory ./output_100agents

# 或使用Maven執行
mvn exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="scenarios/corridor/taipei_test/config.xml \
    --config:plans.inputPlansFile test_population_100.xml \
    --config:controller.lastIteration 5 \
    --config:controller.outputDirectory ./output_100agents"
```

**參數說明**：
- `--config:plans.inputPlansFile test_population_100.xml`: 使用100個agents的population
- `--config:controller.lastIteration 5`: 只運行5次迭代（測試用）
- `--config:controller.outputDirectory ./output_100agents`: 輸出目錄

### 步驟 3: 驗證轉乘功能

模擬完成後，檢查events檔案驗證轉乘：

```bash
# 提取所有PT agents的boarding events
gunzip -c output_100agents/output_events.xml.gz | \
  grep "PersonEntersVehicle" | \
  grep "pt_" | \
  head -100

# 統計每個轉乘agent的boarding次數
gunzip -c output_100agents/output_events.xml.gz | \
  grep "PersonEntersVehicle" | \
  grep "pt_transfer_agent" | \
  awk -F'"' '{print $4}' | \
  sort | uniq -c

# 驗證轉乘成功的agents
gunzip -c output_100agents/output_events.xml.gz | \
  grep "PersonEntersVehicle" | \
  grep "pt_transfer_agent" | \
  awk -F'"' '{print $4, $8}' | \
  awk '{agent=$1; vehicle=$2; if (agent != prev_agent && prev_agent != "") print prev_agent, count; if (agent != prev_agent) count=0; count++; prev_agent=agent} END {print agent, count}' | \
  awk '$2 >= 2 {print}'  # 顯示boarding ≥ 2次的agents（有轉乘）
```

**預期結果**：
- 單線PT agents: 每個應該有2個`PersonEntersVehicle`事件（往返各1次）
- 轉乘PT agents: 每個應該有**4-6個**`PersonEntersVehicle`事件（轉乘1-2次）

### 步驟 4: 生成Via視覺化輸出

```bash
cd /home/user/matsim-example-project

# 創建輸出目錄
mkdir -p forVia_100test

# 使用build_agent_tracks.py生成Via輸出
python src/main/python/build_agent_tracks.py \
  --plans output_100agents/output_plans.xml.gz \
  --events output_100agents/output_events.xml.gz \
  --network scenarios/corridor/taipei_test/network-with-pt.xml.gz \
  --schedule scenarios/corridor/taipei_test/transitSchedule-mapped.xml.gz \
  --vehicles scenarios/corridor/taipei_test/transitVehicles.xml \
  --export-filtered-events \
  --out forVia_100test \
  --dt 5
```

**生成的檔案**（在`forVia_100test/`）：
- `output_events.xml` - 過濾後的events（只包含100個agents）
- `output_network.xml.gz` - 網路拓撲
- `tracks_dt5s.csv` - Agent軌跡（每5秒一個點）
- `legs_table.csv` - 行程片段表
- `filtered_vehicles.csv` - 使用的車輛清單
- `vehicle_usage_report.txt` - 統計報告

## 驗證轉乘的關鍵指標

### 1. Events檔案檢查

```bash
# 檢查pt_transfer_agent_21的完整行程
gunzip -c output_100agents/output_events.xml.gz | \
  grep "person=\"pt_transfer_agent_21\"" | \
  grep -E "PersonEntersVehicle|PersonLeavesVehicle|VehicleArrivesAtFacility|VehicleDepartsAtFacility"
```

**預期看到的序列**：
```
PersonEntersVehicle (veh_XXX_subway) ← 第一段PT
VehicleArrivesAtFacility (transfer station)
PersonLeavesVehicle (veh_XXX_subway) ← 離開第一輛車
PersonEntersVehicle (veh_YYY_subway) ← 轉乘到第二輛車
PersonLeavesVehicle (veh_YYY_subway) ← 抵達目的地
```

### 2. Plans檔案檢查

```bash
# 檢查最終plan的mode分布
gunzip -c output_100agents/output_plans.xml.gz | \
  grep 'selected="yes"' -A 20 | \
  grep '<leg mode=' | \
  awk -F'"' '{print $2}' | \
  sort | uniq -c
```

**預期結果**：
```
  100 car    (40個car agents × 往返2次 = 80)
  100 pt     (50個PT agents × 往返2次 = 100)
  20 walk    (10個walk agents × 往返2次 = 20)
```

## 常見問題排查

### Q1: PT agents沒有boarding events
**原因**: useIntermodalAccessEgress配置錯誤

**解決**: 確認`config.xml`中：
```xml
<param name="useIntermodalAccessEgress" value="false" />
```

### Q2: 轉乘agents只有2個boarding events（沒有轉乘）
**原因**:
1. stopAreaId不一致
2. 轉乘成本太高
3. SwissRailRaptor未啟用

**解決**:
- 檢查`transitSchedule-mapped.xml.gz`中的stopAreaId
- 確認transferPenaltyBaseCost = 0.0
- 確認transit.routingAlgorithmType = "SwissRailRaptor"

### Q3: 編譯失敗
**原因**: 網路連線問題，無法下載Maven依賴

**解決**:
1. 檢查網路連線
2. 配置Maven mirror（如果在中國）
3. 或使用已編譯好的jar檔案

## 參考資料

- **工作日誌**: `working_journal/2025-11-11-Summary.md`
- **SwissRailRaptor指南**: `working_journal/2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md`
- **轉乘驗證**: `working_journal/2025-11-11-PT-Transfer-Validation.md`
- **CLAUDE.md**: 專案完整配置指南（第433-485行有useIntermodalAccessEgress說明）

## 下一步

1. ✅ 完成：生成100個agents（20單線PT + 30轉乘PT + 40 car + 10 walk）
2. ⏳ 待執行：運行模擬（等待網路連線恢復）
3. ⏳ 待執行：驗證30+個agents成功轉乘
4. ⏳ 待執行：生成Via輸出到`forVia_100test/`

---

**Last Updated**: 2025-11-12
**Status**: Population generated ✅ | Simulation pending (network issue) ⏳
**Contact**: Check CLAUDE.md for more details
