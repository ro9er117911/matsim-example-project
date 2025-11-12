## 在最簡化 MATSim 專案中加入 SwissRailRaptor 進行真實公車路由

> 本指南以 `matsim-example-project` 為例，示範如何把 SwissRailRaptor (SRR) 整合至現有 MATSim 專案，並提供可立即執行的設定範例與驗收步驟。

---

### 1. 依賴與建置

1. **升級 parent 版本**  
   在 `pom.xml` 的 `<parent>` 欄位使用近期的週版，例如：
   ```xml
   <parent>
     <groupId>org.matsim</groupId>
     <artifactId>matsim-all</artifactId>
     <version>2026.0-2025w46</version>
   </parent>
   ```
2. **新增 SBB SwissRailRaptor 相關依賴**  
   近期版本已內建於 `matsim-all`，無須額外 dependency；若使用較舊版，可加入：
   ```xml
   <dependency>
     <groupId>ch.sbb.matsim</groupId>
     <artifactId>sbb-matsim</artifactId>
     <version>${matsim.version}</version>
   </dependency>
   ```
3. **Maven 注意事項**  
   - 若需要 snapshot，確保 `<repositories>` 中包含 `https://repo.matsim.org/repository/matsim-snapshots/`。  
   - 建議 `./mvnw -U clean install` 以強制更新。

---

### 2. Config 調整

在使用 SRR 的設定檔（如 `scenarios/equil/config_pt_only.xml`）加入／確認以下模組：

```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="usingTransitInMobsim" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="transitScheduleFile" value="transitSchedule-mapped.xml.gz"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="plans">
  <param name="inputPlansFile" value="test_population_full_transfer.xml"/>
  <param name="handlingOfPlansWithoutRoutingMode" value="reject"/>
</module>

<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>
  <param name="transferPenaltyBaseCost" value="0.0"/>
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>
</module>

<module name="transitRouter">
  <param name="additionalTransferTime" value="900.0"/> <!-- 15 分鐘緩衝 -->
</module>
```

> 注意：若使用目前的穩定版，`access/egress` 參數集尚未開放；需 intermodal 時可將 `useIntermodalAccessEgress` 設為 `false`，並在 plans 中自行提供 `pt interaction` 節點或 routingMode。

---

### 3. 人口檔與 routingMode

SwissRailRaptor 需要知道每段 leg 的 routing mode（尤其在啟用 `handlingOfPlansWithoutRoutingMode=reject` 時）。範例如：

```xml
<leg mode="pt">
  <attributes>
    <attribute name="routingMode" class="java.lang.String">pt</attribute>
  </attributes>
</leg>
```

車輛或步行 legs 也應對應 `routingMode="car"`、`"walk"`。若採純座標 + SRR 自動推導的 workflow，可在人口檔僅保留 `home -> pt -> work` 兩 act，讓 Router 於第一次迭代補齊 access/egress 站點。

---

### 4. 最小可執行範例

1. **產生人口**  
   ```bash
   python src/main/python/generate_test_population.py
   ```
2. **建置**  
   ```bash
   ./mvnw clean install
   ```
3. **執行模擬**  
   ```bash
   ./mvnw exec:java \
     -Dexec.mainClass=org.matsim.project.RunMatsim \
     -Dexec.args="scenarios/equil/config_pt_only.xml"
   ```

---

### 5. 驗收步驟

1. **功能驗證**  
   - `./mvnw -Dtest=CorridorPipelineTest test`（或專案中的 PT 測試）應成功。  
   - 瑞士路由器會於 log 出現 `SwissRailRaptor data preparation done` 等訊息。
2. **成果檢查**  
   - `output/output_trips.csv.gz` 中 `main_mode` 應包含 `pt`，並有 `first_pt_boarding_stop` 欄位。  
   - `output/output_plans.xml.gz` 內會新增 `pt interaction` 活動及具體路線。
3. **迭代結果**  
   - 若 `config_pt_only.xml` 設 `lastIteration=8`，觀察 `output/ITERS/it.8/8.events.xml.gz` 的 PT 事件是否正常產生。

---

### 6. 常見問題

| 問題 | 原因 | 解決 |
|------|------|------|
| `VerifyException: plans without routing mode` | 未在 plans 中提供 `routingMode` | 加入 `<attribute name="routingMode"...>` 或設成 `reject` 後補齊 |
| `Unsupported parameterset-type: accessEgressSettings` | 目前版本未支援 intermodal 參數集 | 刪除 `<parameterset type="accessEgressSettings">`，或升級到支援版本 |
| `TestEngine with ID 'junit-jupiter' failed to discover tests` | 自訂 DisplayNameGenerator 未實作新方法 | 改用 `SafeDisplayNameGenerator` 或升級 JUnit |

---

如需更進階的多模式配置（例如搭配 `drt`、`rail` 等），可參考 MATSim 官方 wiki 及 SBB 擴充 repo 之範例。此報告涵蓋從依賴設定、人口路徑、執行命令到驗收的完整流程，可用於任何最小化的 MATSim 專案。祝模擬順利！ 
