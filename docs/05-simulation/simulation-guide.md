# MATSim 模擬執行指南

本文件整理模擬執行流程、常用指令、輸出檢查與效能設定，並包含災難撤離情境的執行入口。

## 輸入與輸出

### 輸入
- `config.xml`（模擬設定）
- `network.xml(.gz)`
- `population.xml(.gz)`
- `transitSchedule.xml(.gz)`、`transitVehicles.xml`（若啟用 PT）
- `changeEvents.xml`（若啟用時變路網）

### 輸出
- `output_*` 目錄（events、plans、network、ITERS）

---

## 一、建置與執行

### 1) 建置

```bash
./mvnw clean package
```

### 2) 執行（範例場景）

```bash
# 台北測試場景（可視需求調整記憶體）
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config.xml
```

---

## 二、災難撤離情境（5000_disatar）

### 1) 推薦流程

```bash
# 含 SimWrapper 分析的完整流程
./5000_disatar/05_combined_evac/run_staggered_iter10_pipeline.sh
```

### 2) 直接執行

```bash
scripts/run_simulation.sh 5000_disatar/05_combined_evac/config_optimized_iter10.xml
```

相關工作流請見 `5000_disatar/05_combined_evac/WORKFLOW.md`。

---

## 三、效能與資源設定

- **JVM 記憶體**：
  - 5k agents：`-Xmx8g` 到 `-Xmx16g`
- **輸出目錄**：`controller.outputDirectory`
- **迭代數**：`controller.lastIteration`

範例：

```bash
java -Xmx12g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  config.xml \
  --config:controller.lastIteration 10 \
  --config:controller.outputDirectory output_test
```

---

## 四、輸出檢查

```bash
# 迭代收斂
cat output/scorestats.csv

# 運具比例
cat output/modestats.csv

# 事件檢查
zcat output/output_events.xml.gz | head -50

# 錯誤檢查
grep -i "error\|exception" output/logfileWarningsErrors.log
```

---

## 五、收斂與提前停止

- 迭代曲線趨於平穩時，可減少迭代數加速測試。
- 若出現大量 stuck agents 或路網錯誤，優先回到 network / population 檢查。

---

## 六、SimWrapper 視覺化

SimWrapper 請參考 `docs/05-simulation/simwrapper.md`。
