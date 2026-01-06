# MATSim 路網建置指南（OSM + 台灣國土測繪 SHP）

本文件整理 MATSim 路網的建置流程，涵蓋 OSM 與台灣國土測繪 SHP 兩種來源，並統一路徑、輸出與驗證方式。

## 輸入與輸出

### 輸入
- **OSM**：`.osm.pbf` 或 `.osm`
- **SHP**：道路 `*_ROAD.shp`、節點 `*_RDNODE.shp`

### 輸出
- `network.xml.gz`（MATSim 路網，含 modes、長度、容量、車道）

### 座標系統
- 統一使用 **EPSG:3826 (TWD97 / TM2 zone 121)**

---

## 一、OSM → MATSim 路網

### 1) 轉換指令（pt2matsim）

```bash
java -Xmx4g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  5000_disatar/01_raw_data/osm/disaster_bbox.osm.pbf \
  5000_disatar/03_phase2_production/networks/network.xml \
  EPSG:3826 \
  5000_disatar/03_phase2_production/configs/osm2network-config-v2.xml
```

### 2) 清理路網（避免多連通分量）

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="input_network.xml.gz output_network_clean.xml.gz"
```

常用修正工具（依需求擇一）：
- `5000_disatar/05_scripts/02_osm_network/fix_network_capacity.py`：修正 0 capacity
- `5000_disatar/05_scripts/02_osm_network/merge_short_links.py`：合併極短 link
- `5000_disatar/05_scripts/02_osm_network/clean_car_components.py`：保留最大 car SCC
- `5000_disatar/05_scripts/02_osm_network/make_subway_exclusive.py`：建立 subway-only network

### 3) 驗證

```bash
zcat output_network_clean.xml.gz | grep -c '<node '
zcat output_network_clean.xml.gz | grep -c '<link '

gunzip -c output_network_clean.xml.gz | grep -o 'modes="[^"]*"' | sort | uniq -c
```

---

## 二、SHP → MATSim 路網（台灣國土測繪圖資）

### 1) 先檢查欄位與 CRS

```bash
python3 5000_disatar/05_scripts/02_osm_network/inspect_shapefile_schema.py \
  5000_disatar/01_raw_data/taipei_shp_map
```

台北資料常見檔名為 `A_ROAD.shp` / `A_RDNODE.shp`，嘉義資料為 `Q_ROAD.shp` / `Q_RDNODE.shp`。

### 2) 轉換指令

```bash
python3 5000_disatar/05_scripts/02_osm_network/convert_shapefile_to_network.py \
  --input 5000_disatar/01_raw_data/taipei_shp_map \
  --output 5000_disatar/01_raw_data/taipei_shp_map/output/network.xml.gz \
  --road-file A_ROAD.shp \
  --node-file A_RDNODE.shp \
  --modes "car,walk"
```

一鍵執行版本：

```bash
bash 5000_disatar/01_raw_data/taipei_shp_map/shp_to_network_pipeline.sh
```

### 3) 驗證輸出

```bash
zcat 5000_disatar/01_raw_data/taipei_shp_map/output/network.xml.gz | grep -c '<node '
zcat 5000_disatar/01_raw_data/taipei_shp_map/output/network.xml.gz | grep -c '<link '
```

---

## 三、新北市路網與整合（雙北完整路網）

### 1) 新北市路網建置
新北市資料編碼為 `cp950`，需指定編碼轉換：

```bash
python3 5000_disatar/05_scripts/02_osm_network/build_combined_network.py \
  -i 5000_disatar/01_raw_data/newTPE_shp_map \
  -o 5000_disatar/01_raw_data/newTPE_shp_map/output/network.xml.gz \
  --encoding cp950
```

### 2) 雙北路網整合
使用 `build_combined_network.py` 同時輸入多個目錄：

```bash
python3 5000_disatar/05_scripts/02_osm_network/build_combined_network.py \
  -i 5000_disatar/01_raw_data/taipei_shp_map 5000_disatar/01_raw_data/newTPE_shp_map \
  -o 5000_disatar/01_raw_data/combined_network.xml.gz
```

### 3) 清理與驗證
整合後必須執行 `NetworkCleaner` 確保連通性：

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="5000_disatar/01_raw_data/combined_network.xml.gz 5000_disatar/01_raw_data/combined_network_clean.xml.gz"
```

---

## 四、常見問題與解法

### 1) 欄位名稱不一致

**現象**：找不到 `ROADID/ROADCLASS/FNODE/TNODE/NODEID`。  
**解法**：先用 `inspect_shapefile_schema.py` 確認欄位，必要時調整 `convert_shapefile_to_network.py` 的候選欄位清單。

### 2) FNODE/TNODE 找不到對應節點

**現象**：大量 link 被跳過。  
**解法**：確認節點 ID 欄位是否正確；必要時改用「最近節點匹配」策略（腳本已有 `find_nearest_node` 實作可用）。

### 3) CRS 不一致或長度異常

**現象**：邊界值不合理、link 長度極端。  
**解法**：讀檔後統一投影：

```python
roads = roads.to_crs("EPSG:3826")
```

### 4) 單行道欄位編碼不同

**現象**：`ONEWAY` 不是 0/1。  
**解法**：先看欄位 unique values，建立對應表再輸出。

### 5) 幾何型別或資料品質問題

**現象**：非 LineString/MultiLineString 造成跳過。  
**解法**：先濾除非線狀幾何，必要時修復：

```python
roads = roads[roads.geometry.type.isin(["LineString","MultiLineString"])]
roads["geometry"] = roads.buffer(0)
```

### 6) 路網不連通

**現象**：`Network is not connected` 警告。  
**解法**：使用 `PrepareNetworkForPTMapping` 或 `NetworkCleaner` 保留最大連通分量。

---

- **OSM 生產版**：`5000_disatar/03_phase2_production/networks/`
- **SHP 測試版**：`5000_disatar/01_raw_data/taipei_shp_map/output/`
- **雙北整合版**：`5000_disatar/01_raw_data/combined_network_clean.xml.gz`

若要用於模擬，請在對應 `config.xml` 指向正確的 `inputNetworkFile`。
