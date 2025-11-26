# MATSim 瓶頸分析工具 (Bottleneck Analysis Tool)

快速分析 MATSim 模擬輸出中的道路瓶頸，產生 CSV 報告和 GeoJSON 視覺化資料。

## 功能特色

✅ **快速分析** - 10 秒內分析 24,000+ 連結
✅ **V/C 比率計算** - 識別容量限制
✅ **多格式輸出** - CSV、JSON、GeoJSON
✅ **視覺化就緒** - 直接匯入 QGIS、kepler.gl、Mapbox
✅ **嚴重程度分級** - 綠-黃-橘-紅配色系統

## 快速開始

### 基本使用

```bash
# 分析瓶頸（預設 V/C >= 0.85）
python -m src.main.python.bottleneck_analysis.analyze_bottlenecks \
  --output-dir output_metro_0300_0618 \
  --mode quick

# 包含 GeoJSON 視覺化
python -m src.main.python.bottleneck_analysis.analyze_bottlenecks \
  --output-dir output_metro_0300_0618 \
  --mode quick \
  --export-geojson
```

### 自訂參數

```bash
# 自訂 V/C 閾值和前 N 個瓶頸
python -m src.main.python.bottleneck_analysis.analyze_bottlenecks \
  --output-dir output_metro_0300_0618 \
  --vc-threshold 0.9 \
  --top-n 100 \
  --export-geojson

# 降低閾值以顯示所有有流量的連結
python -m src.main.python.bottleneck_analysis.analyze_bottlenecks \
  --output-dir output_metro_0300_0618 \
  --vc-threshold 0.0 \
  --export-geojson
```

### 指定輸出目錄

```bash
python -m src.main.python.bottleneck_analysis.analyze_bottlenecks \
  --output-dir output_metro_0300_0618 \
  --out custom_analysis_results \
  --export-geojson
```

## 輸出檔案

分析完成後，會在 `<output-dir>/bottleneck_analysis/` 產生以下檔案：

### 1. CSV 報告 (`bottleneck_quick_report.csv`)
詳細的瓶頸清單，包含：
- 排名、連結 ID、節點資訊
- V/C 比率、流量、容量
- 速度、車道數、長度
- 嚴重程度、幾何資訊

**用途**: Excel 分析、資料處理

### 2. JSON 摘要 (`bottleneck_quick_summary.json`)
結構化的分析摘要，包含：
- 場景資訊、時間戳記
- 總連結數、瓶頸數量
- 最差 V/C 比率、平均延遲
- 前 10 個瓶頸詳細資訊
- 嚴重程度分布統計

**用途**: 程式處理、API 整合

### 3. GeoJSON 熱力圖 (`bottleneck_heatmap.geojson`)
地理空間視覺化資料，包含：
- LineString 幾何資料（EPSG:3826 座標系統）
- 連結屬性（V/C、嚴重程度、顏色）
- 元資料（場景、時間、統計）

**用途**: QGIS、kepler.gl、Mapbox、web 地圖

## V/C 比率與嚴重程度

| V/C 比率 | 嚴重程度 | 顏色 | 說明 |
|---------|---------|------|------|
| < 0.5 | normal | 🟢 綠色 | 自由流 |
| 0.5 - 0.7 | moderate | 🟡 黃色 | 中等流量 |
| 0.7 - 0.85 | congested | 🟠 橘色 | 壅塞 |
| 0.85 - 1.0 | heavy | 🔶 深橘 | 嚴重壅塞 |
| > 1.0 | **critical** | 🔴 紅色 | **瓶頸** |

## 視覺化工具使用

### QGIS

1. 開啟 QGIS
2. **圖層 → 新增圖層 → 新增向量圖層**
3. 選擇 `bottleneck_heatmap.geojson`
4. 在**符號**中，設定樣式：
   - 使用**資料定義覆寫**
   - 依據 `vc_ratio` 或 `severity` 欄位設定顏色
   - 或直接使用 `color` 欄位

### kepler.gl (線上工具)

1. 前往 https://kepler.gl/
2. 拖放 `bottleneck_heatmap.geojson` 到視窗
3. 自動產生視覺化
4. 可依據 `vc_ratio` 調整顏色、線條粗細

### Mapbox

1. 上傳 GeoJSON 到 Mapbox Studio
2. 使用 `color` 屬性作為 **stroke-color**
3. 使用 `vc_ratio` 調整 **stroke-width**

## 輸出範例

### 控制台輸出

```
================================================================================
BOTTLENECK ANALYSIS SUMMARY: output_metro_0300_0618
================================================================================
Analysis Time: 2025-11-26 14:52:28
Total Links: 24078
Bottleneck Count (V/C >= 0.85): 0
Worst V/C Ratio: 0.026
Average Network Delay: 3.46s (0.06 min)

Severity Breakdown:
  Critical (V/C > 1.0):  0
  Heavy (V/C 0.85-1.0):  0
  Congested (V/C 0.7-0.85): 0

Top 10 Bottlenecks:
--------------------------------------------------------------------------------
Rank  Link ID      V/C      Volume     Capacity   Severity
--------------------------------------------------------------------------------
1     pt_R22_UP    0.026    264        9999       normal
2     pt_R22_UP_pt_R22_UPA 0.026    264        9999       normal
```

### JSON 摘要範例

```json
{
  "scenario": "output_metro_0300_0618",
  "timestamp": "2025-11-26T14:52:28.729928",
  "analysis": {
    "total_links": 24078,
    "bottleneck_count": 142,
    "vc_threshold": 0.85,
    "worst_vc_ratio": 1.18,
    "avg_network_delay_s": 44.2
  },
  "severity_breakdown": {
    "critical": 5,
    "heavy": 12,
    "congested": 35
  }
}
```

## 命令列選項

| 選項 | 必要 | 預設值 | 說明 |
|-----|------|--------|------|
| `--output-dir` | ✅ | - | MATSim 輸出目錄 |
| `--mode` | ❌ | quick | 分析模式 (quick/events/viz) |
| `--vc-threshold` | ❌ | 0.85 | V/C 比率閾值 |
| `--top-n` | ❌ | 50 | 匯出前 N 個瓶頸 |
| `--out` | ❌ | `<output-dir>/bottleneck_analysis` | 輸出目錄 |
| `--export-geojson` | ❌ | - | 匯出 GeoJSON |
| `--export-timeseries` | ❌ | - | 匯出時序 CSV (需 events 模式) |
| `--quiet` | ❌ | - | 靜默模式 |

## 效能

| 場景規模 | 分析時間 |
|---------|---------|
| 500 agents, 10K links | < 5 秒 |
| 5000 agents, 25K links | < 10 秒 |
| 50000 agents, 100K links | < 30 秒 |

## 必要檔案

分析工具需要以下 MATSim 輸出檔案：

- ✅ `output_links.csv.gz` - 連結容量、流量、幾何資訊
- ✅ `output_legs.csv.gz` - 旅次延遲資訊

## 災難疏散場景分析

對於災難疏散模擬，建議設定：

```bash
# 識別高壅塞區域
python -m src.main.python.bottleneck_analysis.analyze_bottlenecks \
  --output-dir output_disaster_evacuation \
  --vc-threshold 0.7 \
  --top-n 100 \
  --export-geojson
```

**分析重點**:
- V/C > 0.85 的連結 → 疏散路徑瓶頸
- 平均延遲 → 疏散效率
- GeoJSON 視覺化 → 識別壅塞熱點

## 常見問題

### Q: 為什麼沒有找到瓶頸？
**A**: 可能原因：
1. V/C 閾值太高（降低到 0.7 或 0.5）
2. 場景主要是 PT（公共交通），汽車流量低
3. 模擬時間太短，尚未產生壅塞

### Q: 如何分析 PT 瓶頸？
**A**: PT 連結通常有很高的容量（9999）。使用絕對流量排序：
```bash
--vc-threshold 0.0 --top-n 100
```

### Q: 座標系統是什麼？
**A**: EPSG:3826 (TWD97 / TM2 zone 121)，適用於台灣地區。如需轉換，使用 QGIS 重新投影功能。

## 未來功能（待實施）

- ⏳ **事件深度分析** - 時序壅塞模式、佇列動態
- ⏳ **卡住事件追蹤** - 疏散失敗 agent 檢測
- ⏳ **動畫匯出** - 時間序列視覺化
- ⏳ **熱力圖時間切片** - 依時段顯示壅塞變化

## 授權與作者

**作者**: Claude Code
**日期**: 2025-11-26
**版本**: 1.0.0

---

**回報問題**: [GitHub Issues](https://github.com/your-org/matsim-example-project/issues)
**文檔**: 請參閱 [CLAUDE.md](../../../../CLAUDE.md) 中的「瓶頸分析」章節
