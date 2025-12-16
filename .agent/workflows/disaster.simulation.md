---
description: 災難模擬執行 - Headless 模式運行大規模撤離模擬
---

# 災難模擬執行技能 (Headless)

## 觸發條件

- 執行撤離模擬
- 運行 headless 模式
- 大規模 agent 模擬 (5000+)
- 需要長時間運行 (100+ iterations)

---

## Step 1: 驗證配置完整性

```bash
# 檢查 config 檔案
xmllint --noout 5000_disatar/05_combined_evac/config_combined_5000.xml

# 驗證必要檔案存在
for f in network plans changeEvents; do
  grep -o "value=\"[^\"]*$f[^\"]*\"" config.xml | head -1
done
```

### 關鍵配置項目

```xml
<!-- 迭代次數 -->
<module name="controller">
    <param name="lastIteration" value="100"/>
    <param name="outputDirectory" value="output_staggered_iter100"/>
    <param name="overwriteFiles" value="deleteDirectoryIfExists"/>
</module>

<!-- QSim 配置 (避免卡住) -->
<module name="qsim">
    <param name="stuckTime" value="0"/>  <!-- 0=不移除卡住車輛 -->
    <param name="removeStuckVehicles" value="false"/>
    <param name="flowCapacityFactor" value="1.0"/>
    <param name="storageCapacityFactor" value="2.0"/>
</module>

<!-- PT 使用 teleportation (避免速度問題) -->
<module name="transit">
    <param name="usingTransitInMobsim" value="false"/>
</module>
```

---

## Step 2: 執行模擬

### 快速測試 (10 iterations)

```bash
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  5000_disatar/05_combined_evac/config_combined_5000_staggered_iter10.xml
```

### 完整運行 (100 iterations)

```bash
# 使用 nohup 背景執行
nohup java -Xmx16g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  5000_disatar/05_combined_evac/config_combined_5000_staggered_iter100.xml \
  > simulation.log 2>&1 &

# 監控進度
tail -f output_staggered_iter100/logfile.log
```

### 一鍵 Pipeline (含 Dashboard)

```bash
# 完整執行
./5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh

# 跳過模擬，只重生視覺化
SKIP_SIM=1 ./5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh

# 100 iterations 版本
CONFIG_FILE=5000_disatar/05_combined_evac/config_combined_5000_staggered_iter100.xml \
  ./5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh
```

---

## Step 3: 監控執行

```bash
# 查看錯誤
grep -i "error\|exception\|warn" output/logfile.log | tail -30

# 檢查進度 (iteration 數)
ls output/ITERS/ | grep -c 'it\.'

# 記憶體使用
ps aux | grep java | grep -v grep
```

---

## Step 4: 驗證結果

```bash
# 檢查收斂
cat output/scorestats.csv | tail -10

# 模式分佈
cat output/modestats.csv | tail -5

# 事件數量
gunzip -c output/output_events.xml.gz | wc -l
```

---

## 常見問題

### Agent 卡住 (Stuck)
**解決**: 設定 `stuckTime="30"` 或 `removeStuckVehicles="true"`

### 記憶體不足
**解決**: 增加 heap `-Xmx16g`，或減少 output 頻率

### 模擬太慢
**解決**: 減少 agent 數量、增加 `numberOfThreads`

### PT 車輛不動
**解決**: 設定 `usingTransitInMobsim="false"` 使用 teleportation

---

## 輸出檔案

| 檔案 | 用途 |
|------|------|
| `output_events.xml.gz` | 完整事件記錄 |
| `scorestats.csv/png` | 分數收斂 |
| `modestats.csv` | 模式分佈 |
| `output_plans.xml.gz` | 最終 agent 計畫 |

## 參考檔案

- Pipeline 腳本: `5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh`
- 配置範本: `5000_disatar/05_combined_evac/config_combined_5000*.xml`
- 完整工作流程: `5000_disatar/05_combined_evac/WORKFLOW.md`
