# Evacuation-GUI 終端機操作指南

## 快速開始

### 1. 啟動 GUI

```bash
cd /Users/ro9air/matsim-example-project
cd evacuation-gui && ../mvnw exec:java -Dexec.mainClass="org.matsim.evacuationgui.run.ScenarioManager"
```

### 2. 使用 ScenarioGenerator (命令行模式)

不打開GUI，直接從命令行生成疏散場景：

```bash
cd /Users/ro9air/matsim-example-project/evacuation-gui
../mvnw exec:java -Dexec.mainClass="org.matsim.evacuationgui.run.ScenarioGenerator" \
  -Dexec.args="/path/to/your/grips_config.xml"
```

**範例 (500m 測試場景):**
```bash
../mvnw exec:java -Dexec.mainClass="org.matsim.evacuationgui.run.ScenarioGenerator" \
  -Dexec.args="/Users/ro9air/matsim-example-project/5000_disatar/03_phase2_production/tamsui_500m_test.xml"
```

### 3. 運行 MATSim 模擬

生成場景後，使用 MATSim 運行模擬：

```bash
cd /Users/ro9air/matsim-example-project

# 需要先修復 config 中的路由設定
sed -i '' 's/abortOnInconsistency/disable/g' [output_dir]/config.xml

# 運行模擬
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsimApplication" \
  -Dexec.args="run --config=[output_dir]/config.xml"
```

## 完整工作流程範例

```bash
# 2. 準備與生成 (使用 GUI)

**場景說明**: 大台北地區 (包含淡水、文山、蘆竹)，目標 5000 人。
檔案已重置於 `./input`，並準備了預設配置檔 `generation_config.xml`。

1.  **啟動 ScenarioManager**:
    ```bash
    cd /Users/ro9air/matsim-example-project/evacuation-gui
    ../mvnw exec:java -Dexec.mainClass="org.matsim.evacuationgui.run.ScenarioManager"
    ```

2.  **方法 A: 直接載入準備好的 Config (推薦)**
    *   點擊 "Load Config"
    *   選擇檔案: `/Users/ro9air/matsim-example-project/5000_disatar/evacuation_test/generation_config.xml`
    *   這會自動填入:
        *   **Network**: `input/tamsui_to_wenshan.osm` (大台北圖資)
        *   **Area**: `input/disaster_zone_tamsui.shp`
        *   **Population**: `input/population_areas.shp`
        *   **Sample Size**: 預設 `0.1` (調整此值以控制人數，目標 5000)

3.  **方法 B: 手動填寫**
    若需手動設定，請參照上述路徑。

4.  **運行生成**:
    切換到 "Simulation" 分頁，點擊 "Run Simulation"。
    (因使用 PBF 大地圖，生成路網可能需要幾分鐘，請耐心等待)

# 3. 運行 MATSim 模擬 (大規模/穩定模式)

若 GUI 跑太慢或記憶體不足，請使用我們準備好的 headless script：

1.  確認 GUI 已生成 `output/config.xml`。
2.  執行腳本：
    ```bash
    cd /Users/ro9air/matsim-example-project/5000_disatar/evacuation_test
    ./run_headless.sh ./output/config.xml
    ```
```

```

## 4. 如何檢視路網 (可選)

你詢問了如何用 Python 或 JOSM 查看路網。

### A. 使用 Python (已為你準備腳本)
在 `evacuation_test` 資料夾中，有一個 `visualize_osm.py`。
```bash
python3 visualize_osm.py input/tamsui_to_wenshan.osm osm_visual.png
```
它會生成一張 PNG 預覽圖 (因 2GB 檔案較大，執行需數分鐘)。

### B. 使用 JOSM (推薦用於細節查看)
1.  下載並安裝 [JOSM](https://josm.openstreetmap.de/)。
2.  開啟 JOSM。
3.  `File` -> `Open...`。
4.  選擇 `/Users/ro9air/matsim-example-project/5000_disatar/evacuation_test/input/tamsui_to_wenshan.osm`。
    (注意：2GB 檔案開啟會很慢，建議只在電腦記憶體 > 16GB 時嘗試)。

### C. 轉換為 GeoJSON (只看汽車路網)
若你需要將路網轉為 GeoJSON 以便在 QGIS 或其他工具查看 (且排除非汽車道路)，請使用：
```bash
python3 osm_to_geojson.py input/tamsui_to_wenshan.osm output/car_network.geojson
```
這會生成 `output/car_network.geojson` (僅包含 motorway, primary, secondary 等汽車道路)。
**注意**: 此轉檔過程需建立節點索引，對於 2GB 檔案可能需要幾分鐘。

## 輸出檔案

成功執行後，會在輸出目錄產生：
- `network.xml.gz` - 疏散路網
- `population.xml.gz` - 人口檔案
- `config.xml` - MATSim 配置檔
- `output/` - 模擬結果 (scorestats.png, modestats.png, etc.)
