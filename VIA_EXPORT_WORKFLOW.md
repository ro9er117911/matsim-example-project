# Via 平台導出工作流 - Via Export Workflow

**Date:** 2025-11-05
**Status:** 🟢 Ready to Export

---

## 📊 當前狀態 (Current State)

### 輸入文件 (Input Files)
已從模擬完成的 `scenarios/equil/output/` 目錄中獲取所有必要的文件：

```
scenarios/equil/output/
├── output_plans.xml.gz            (29 KB)   ← Agent final plans
├── output_events.xml.gz           (2.9 MB)  ← Simulation events
├── output_transitSchedule.xml.gz  (285 KB)  ← Transit schedule
├── output_transitVehicles.xml.gz  (7.5 KB)  ← Vehicle definitions
└── output_network.xml.gz          (3.5 MB)  ← Network topology
```

所有文件由剛才完成的 5 次迭代模擬生成。

### 目標 (Target)
導出到 `scenarios/equil/forVia/`（隔離的、受保護的導出目錄）：

```
scenarios/equil/forVia/
├── output_events.xml              ← For Via import
├── output_network.xml.gz          ← For Via import
├── tracks_dt5s.csv                ← Agent trajectories
├── legs_table.csv                 ← Trip segments
├── filtered_vehicles.csv          ← Active vehicles
└── vehicle_usage_report.txt       ← Summary statistics
```

---

## 🚀 執行步驟 (Execution Steps)

### Step 1: 複製命令到終端機 (Copy & Execute)

選擇以下任一方式：

#### ✨ **推薦方式：格式化多行命令**（易讀易修改）

複製以下整個區塊，貼到終端機：

```bash
cd /Users/ro9air/matsim-example-project && \
python src/main/python/build_agent_tracks.py \
  --plans scenarios/equil/output/output_plans.xml.gz \
  --events scenarios/equil/output/output_events.xml.gz \
  --schedule scenarios/equil/output/output_transitSchedule.xml.gz \
  --vehicles scenarios/equil/output/output_transitVehicles.xml.gz \
  --network scenarios/equil/output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia \
  --dt 5
```

#### 或：單行命令（複製最簡單）

```bash
cd /Users/ro9air/matsim-example-project && python src/main/python/build_agent_tracks.py --plans scenarios/equil/output/output_plans.xml.gz --events scenarios/equil/output/output_events.xml.gz --schedule scenarios/equil/output/output_transitSchedule.xml.gz --vehicles scenarios/equil/output/output_transitVehicles.xml.gz --network scenarios/equil/output/output_network.xml.gz --export-filtered-events --out scenarios/equil/forVia --dt 5
```

#### 或：運行 Shell 腳本

```bash
cd /Users/ro9air/matsim-example-project
./EXPORT_VIA_COMMAND.sh
```

### Step 2: 等待導出完成

**預期運行時間：30 秒 ~ 2 分鐘**

進度輸出應該如下所示：

```
========================================================================
Starting Via Export from Simulation Output
========================================================================

Input files:
  Plans:    scenarios/equil/output/output_plans.xml.gz
  Events:   scenarios/equil/output/output_events.xml.gz
  ...

[1/4] Parsing population and plans...
  ✓ Loaded 46 agents

[2/4] Parsing events...
  ✓ Processed 1,200+ events

[3/4] Filtering events...
  ✓ Filtered to 1,200+ relevant events

[4/4] Building agent tracks...
  ✓ Created trajectory CSV

========================================================================
✓ Via Export Complete!
========================================================================
```

### Step 3: 驗證輸出文件

導出完成後，檢查 forVia 文件夾：

```bash
ls -lh scenarios/equil/forVia/
```

**應該看到：**

```
-rw-r--r--  1.2M  output_events.xml         ← Via Import #1
-rw-r--r--  3.5M  output_network.xml.gz     ← Via Import #2
-rw-r--r--  100K  tracks_dt5s.csv
-rw-r--r--  50K   legs_table.csv
-rw-r--r--  15K   filtered_vehicles.csv
-rw-r--r--  10K   vehicle_usage_report.txt
```

---

## 📊 命令參數說明 (Parameter Details)

| 參數 | 值 | 說明 |
|------|-----|------|
| `--plans` | `scenarios/equil/output/output_plans.xml.gz` | MATSim 最終計劃 |
| `--events` | `scenarios/equil/output/output_events.xml.gz` | 完整模擬事件 |
| `--schedule` | `scenarios/equil/output/output_transitSchedule.xml.gz` | 公交時間表 |
| `--vehicles` | `scenarios/equil/output/output_transitVehicles.xml.gz` | 車輛定義 |
| `--network` | `scenarios/equil/output/output_network.xml.gz` | 網絡拓樸 |
| `--export-filtered-events` | (flag) | 生成 Via 友好的事件文件 |
| `--out` | `scenarios/equil/forVia` | 輸出目錄 |
| `--dt` | `5` | 軌跡採樣間隔（秒） |

---

## 🎯 導出後的步驟 (Post-Export Steps)

### 方式 1：在 Via 平台可視化

1. 打開 Via 平台儀表板
2. 創建新的可視化
3. 加載 events：`scenarios/equil/forVia/output_events.xml`
4. 加載 network：`scenarios/equil/forVia/output_network.xml.gz`
5. 按下播放按鈕播放動畫

### 方式 2：分析 CSV 文件

```bash
# 查看代理軌跡（每 5 秒採樣一次）
head -50 scenarios/equil/forVia/tracks_dt5s.csv

# 查看活躍車輛
head scenarios/equil/forVia/filtered_vehicles.csv

# 查看統計信息
cat scenarios/equil/forVia/vehicle_usage_report.txt
```

---

## ✅ 常見檢查清單 (Verification Checklist)

### 導出前：
- [ ] 確認 `scenarios/equil/output/` 存在且包含所有輸出文件
- [ ] 確認 Python 環境已安裝（`python --version`）
- [ ] 確認在項目根目錄（`/Users/ro9air/matsim-example-project`）

### 導出中：
- [ ] 無誤差消息（可能有警告，沒關係）
- [ ] 進度消息清晰可見
- [ ] 運行時間在預期範圍內（<2 分鐘）

### 導出後：
- [ ] `scenarios/equil/forVia/` 文件夾存在
- [ ] `output_events.xml` 文件存在（>1MB）
- [ ] `output_network.xml.gz` 文件存在（>3MB）
- [ ] 所有 CSV 文件都存在

如果任何檢查失敗，查看錯誤消息或重新運行命令。

---

## 🔄 重新導出（如果需要）

```bash
# 清理舊的導出（可選）
rm -rf scenarios/equil/forVia/*

# 重新運行導出命令
cd /Users/ro9air/matsim-example-project && \
python src/main/python/build_agent_tracks.py \
  --plans scenarios/equil/output/output_plans.xml.gz \
  --events scenarios/equil/output/output_events.xml.gz \
  --schedule scenarios/equil/output/output_transitSchedule.xml.gz \
  --vehicles scenarios/equil/output/output_transitVehicles.xml.gz \
  --network scenarios/equil/output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia \
  --dt 5
```

---

## 📁 文件參考 (File Reference)

### 快速執行文件
- **[VIA_EXPORT_QUICK_COMMAND.txt](VIA_EXPORT_QUICK_COMMAND.txt)** - 可複製貼上的命令
- **[EXPORT_VIA_COMMAND.sh](EXPORT_VIA_COMMAND.sh)** - 可執行的 Shell 腳本

### 文檔
- **[SIMULATION_GUIDE_IMPROVED_POPULATION.md](SIMULATION_GUIDE_IMPROVED_POPULATION.md)** - 完整模擬指南
- **[working_journal/Via-Export-Quick-Start.md](working_journal/Via-Export-Quick-Start.md)** - Via 快速開始
- **[VIA_EXPORT_SETUP.md](VIA_EXPORT_SETUP.md)** - 詳細設置指南

### Python 工具
- **[src/main/python/build_agent_tracks.py](src/main/python/build_agent_tracks.py)** - 主要導出工具

---

## 💾 數據流 (Data Flow)

```
MATSim Simulation Output
│
├─ output_plans.xml.gz      ┐
├─ output_events.xml.gz     │
├─ output_transitSchedule   │ ── build_agent_tracks.py ──┐
├─ output_transitVehicles   │                            │
└─ output_network.xml.gz    ┘                            │
                                                          ↓
                                              Via Export Files
                                                  ┌─────────────────────────┐
                                                  │ output_events.xml       │
                                                  │ output_network.xml.gz   │
                                                  │ tracks_dt5s.csv         │
                                                  │ legs_table.csv          │
                                                  │ filtered_vehicles.csv   │
                                                  └─────────────────────────┘
                                                          ↓
                                                    Via Platform
                                                  (Visualization)
```

---

## 🎯 最終檢查單

✅ **準備就緒**

所有文件已驗證：
- ✓ 模擬輸出存在於 `scenarios/equil/output/`
- ✓ Python 導出工具可用
- ✓ forVia 輸出目錄可訪問
- ✓ Shell 腳本已標記為可執行

**現在您可以直接執行以下命令：**

```bash
cd /Users/ro9air/matsim-example-project && \
python src/main/python/build_agent_tracks.py \
  --plans scenarios/equil/output/output_plans.xml.gz \
  --events scenarios/equil/output/output_events.xml.gz \
  --schedule scenarios/equil/output/output_transitSchedule.xml.gz \
  --vehicles scenarios/equil/output/output_transitVehicles.xml.gz \
  --network scenarios/equil/output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia \
  --dt 5
```

**預期結果：** 2-3 分鐘後，`scenarios/equil/forVia/` 將包含所有可視化文件。

---

*Generated: 2025-11-05*
*Status: 🟢 Ready for Immediate Execution*
