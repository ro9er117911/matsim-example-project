# TA 問答稿（災難撤離 / MATSim / ABM）

定位：資深交通模擬研究員（熟 GIS / OTP，未實作 MATSim）。

---

## Q1. MATSim 在撤離情境的「邊界」是什麼？

**A**  
MATSim 擅長處理大規模需求-供給互動與政策情境比較。  
撤離可評估「完成率、時間分布、瓶頸路段、策略差異」。  
但若要精細到車輛跟車、微觀駕駛行為，需外掛或改用微觀模型。

---

## Q2. ABM 對撤離有什麼優勢？

**A**  
ABM 可描述個體在不同時窗、不同模式、不同路徑下的集體動態。  
撤離情境中可表現「遵從率、出發時程、模式轉換」的行為差異。

---

## Q3. 這套撤離場景的核心參數在哪裡？

**A**  
在 `5000_disatar/05_combined_evac/config_optimized_iter10.xml`。  
若需快速理解，先看 `docs/06-disaster-evacuation/evacuation-key-params.md`。

---

## Q4. 封路事件如何確保生效？

**A**  
需同時設定：  
1) `network.inputChangeEventsFile` 指向封路事件檔  
2) `network.timeVariantNetwork=true`  
未啟用會導致撤離結果高估。

---

## Q5. 流量/擁擠程度是怎麼控制的？

**A**  
主要靠 `qsim.flowCapacityFactor` 與 `qsim.storageCapacityFactor`。  
這兩個值取決於樣本比例與實際車輛數估計。  
目前基準設定為 0.06（對應 5000 agents 的樣本比例）。

---

## Q6. 撤離「出發時窗」怎麼調？

**A**  
出發時窗來自人口活動鏈與計畫設定。  
調整活動開始時間或活動鏈，即可改變出發分布。  
若需更長撤離觀察時間，調高 `qsim.endTime`。

---

## Q7. 為什麼 PT 是 teleport 而不在 mobsim？

**A**  
`transit.useTransit=true`，但 `usingTransitInMobsim=false`。  
這會以 teleport 方式處理 PT，省計算成本。  
若要真實 PT 擁擠與路網互動，需開啟 mobsim 並準備完整 PT 設定。

---

## Q8. 行為效用（scoring）如何解讀？

**A**  
`scoring` 中的 `lateArrival`、`performing` 與 `modeParams`  
決定代理人對時間、行為與模式的偏好。  
本場景對 walk 設較高不效用，避免不合理的步行偏好。

---

## Q9. 迭代數越多越好嗎？

**A**  
不一定。  
`lastIteration` 越高越穩定，但也更耗時。  
交接時建議保留 10、100、1000 三個基準版本做比較。

---

## Q10. 撤離結果如何驗證？

**A**  
以「撤離完成率、平均撤離時間、瓶頸路段」為主。  
可用 `output_events.xml.gz` 搭配分析腳本與 dashboard 檢查。  
若有在地資料或已知瓶頸，可做交叉比對。

---

## Q11. 這套流程最容易踩的坑？

**A**  
1) 封路事件未生效  
2) 需求建構不清（起點與時窗錯置）  
3) 容量倍率不匹配導致擁擠偏誤  
4) 迭代不足造成輸出不穩定

---

## Q12. 如果要加新策略（如改避難所）？

**A**  
需同步調整需求、目的地與封路策略。  
建議以 baseline 先重跑，再逐步替換單一策略變因。

---

## Q13. MATSim 怎麼「吃」 OSM 跟 GTFS？

**A**  
OSM 主要用來建路網（link/node、道路屬性與速度/容量初始值）。  
GTFS 主要用來建 PT 時刻表與路線，並透過 PT 映射把站點掛到路網。  
簡化版流程：OSM -> network.xml；GTFS -> transitSchedule.xml + transitVehicles.xml；最後在 config 指向這些檔案。

---

## Q14. queue 模型在這邊代表什麼？

**A**  
MATSim 的 queue 模型是「排隊式流量守恆」的簡化動力學。  
重點是：  
1) link 有容量與儲存上限  
2) 進出流量受限  
3) 擁擠用「排隊」表現，而非細節車距或跟車行為  
對撤離情境，它提供穩定且可擴展的大規模交通動態。

---

## Q15. 若 capacity=1000，流量=1001 就會塞住嗎？

**A**  
不會是「一超過就完全卡死」，而是進出流量被限制。  
超過容量的車輛會在 link 上形成排隊並等待釋放，  
結果是 travel time 延長、排隊長度增加，但不是瞬間停止。

---

## Q16. kinematicWaves 怎麼傳遞塞車波？

**A**  
kinematicWaves 以「守恆方程」描述流量與密度的關係，  
擁擠會形成 shockwave，並沿著 link 以可計算速度向上游傳遞。  
它較能表現「塞車波」的時空演化，但對短 link 更敏感。

---

## Q17. queue 與 kinematicWaves 的差別是什麼？

**A**  
queue：  
- 偏流量守恆與排隊，計算穩定、適合大規模  
- 對短 link 較穩定  
kinematicWaves：  
- 可描述塞車波傳遞  
- 更接近連續流量理論，但對路網品質要求高

---

## Q18. 速度用 m/s、capacity 用小時，單位不會衝突嗎？

**A**  
不會。  
MATSim 內部會在計算時做單位換算。  
速度多用 m/s，容量多以 veh/hour 表示，只要設定一致即可。  
真正要注意的是「同一組參數的量級是否合理」，而非單位格式本身。
