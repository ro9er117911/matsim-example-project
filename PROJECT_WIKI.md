# 專案架構引用維基 (Project Architecture Wiki)

這是一份專案的系統性導覽地圖，旨在協助新進人員快速掌握專案結構、核心文件位置與標準作業流程 (SOP)。

---

## 🗺️ 專案地圖 (Project Map)

本專案主要分為 **核心文件**、**災難模擬專案**、**公共運輸管線** 與 **自動化流程** 四大區塊。

### 📂 1. 核心文件庫 (`docs/`)

所有基礎知識與通用操作指南皆位於此。

*   **新手必讀**:
    *   [1-quick-start.md](docs/1-quick-start.md): 安裝環境與執行第一個模擬。
    *   [2-architecture.md](docs/2-architecture.md): 了解系統架構與設計邏輯。
*   **進階指南**:
    *   [3-public-transit.md](docs/3-public-transit.md): GTFS 轉 MATSim 的標準流程。
    *   [5-configuration.md](docs/5-configuration.md): 詳細參數設定說明書。
    *   [simwrapper_workflow.md](docs/simwrapper_workflow.md): **推薦** 視覺化儀表板製作教學。

---

### 🌋 2. 災難模擬專案 (`5000_disatar/`)

此目錄為一個獨立且完整的專案單元，包含從原始資料、網路建置到模擬分析的所有資源。

#### 📖 核心聖經 (The Bible)
> **[NETWORK_README.md](5000_disatar/00_docs/NETWORK_README.md)**
>
> 這是本目錄最重要的文件！詳細記錄了：
> *   目錄結構說明
> *   原始資料 (OSM, GTFS) 位置
> *   路網建置 (Phase 1 & Phase 2) 的完整指令與參數
> *   問題排解記錄 (Troubleshooting Log)

#### 🏗️ 專案結構導覽
*   **文件**: [`00_docs/`](5000_disatar/00_docs/) - 包含上述核心文件。
*   **原始資料**: `01_raw_data/` - 存放 OSM, GTFS, Agent JSON 原始檔。
*   **生產環境**: [`03_phase2_production/`](5000_disatar/03_phase2_production/) - **最終產出的網路檔 (`network-with-pt.xml`) 與時刻表位於此**。
*   **疏散模擬**: [`05_combined_evac/`](5000_disatar/05_combined_evac/) - 包含疏散模擬的 Config、Scripts 與 Pipeline。
    *   另請參閱此處的 [WORKFLOW.md](5000_disatar/05_combined_evac/WORKFLOW.md) 了解疏散模擬細節。

---

### 🤖 3. 標準作業流程 (Workflows)

位於 `.agent/workflows/` 的文件定義了特定任務的標準操作步驟 (SOP)。

| 任務類型 | 文件連結 | 說明 |
| :--- | :--- | :--- |
| **路網修改** | [disaster.network.md](.agent/workflows/disaster.network.md) | **災難場景建置 SOP**。<br>教你如何根據溢淹深度圖或海岸線距離，建立時變路網 (Time-Variant Network) 來模擬道路封閉。 |
| **模擬執行** | [disaster.simulation.md](.agent/workflows/disaster.simulation.md) | **大規模模擬 SOP**。<br>如何在 Headless 模式下執行 5000+ Agent 的長時間模擬，包含 Config 檢查與效能優化參數。 |
| **視覺化** | [disaster.simwrapper.md](.agent/workflows/disaster.simwrapper.md) | **分析產出 SOP**。<br>從模擬結果生成 SimWrapper Dashboard 的完整流程，包含熱力圖、撤離曲線等分析圖表製作。 |

---

### 🚌 4. 公共運輸管線 (`pt2matsim/`)

處理 GTFS 資料轉換的核心工具庫。

*   **工具路徑**: `pt2matsim/work/pt2matsim-25.8-shaded.jar` - 所有轉換指令 (Mapper, Schedule Generator) 皆呼叫此 JAR 檔。
*   **使用方式**: 請參考 [NETWORK_README.md](5000_disatar/00_docs/NETWORK_README.md) 中的 Phase 1 & Phase 2 指令範例。

---

## 🚀 快速上手路徑 (Learning Path)

如果你是...

1.  **剛加入專案的新人**:
    *   先讀 [README.md](README.md) (專案首頁)。
    *   再讀 [docs/1-quick-start.md](docs/1-quick-start.md) 跑通範例。

2.  **要負責建置災難路網**:
    *   熟讀 [5000_disatar/00_docs/NETWORK_README.md](5000_disatar/00_docs/NETWORK_README.md)。
    *   參考 [.agent/workflows/disaster.network.md](.agent/workflows/disaster.network.md) 處理道路封閉。

3.  **要執行大規模模擬**:
    *   參考 [5000_disatar/05_combined_evac/WORKFLOW.md](5000_disatar/05_combined_evac/WORKFLOW.md)。
    *   照著 [.agent/workflows/disaster.simulation.md](.agent/workflows/disaster.simulation.md) 步驟操作。

4.  **要製作分析報告**:
    *   使用 [.agent/workflows/disaster.simwrapper.md](.agent/workflows/disaster.simwrapper.md) 生成儀表板。
