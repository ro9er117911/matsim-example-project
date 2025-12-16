# config_metro_0300_0618_100000_v3.xml — 調整說明（大規模疏散/災難撤離）

調整目標：在僅有「車 / 公車捷運 (pt) / 走路」三種模式下，更好地呈現高壅塞、長時窗的疏散行為，同時給模式選擇與路徑/時間調整一些探索空間。

## 主要更動與理由
- **更長的模擬時窗**：`startTime=00:00:00`, `endTime=36:00:00`  
  避免短時窗掩蓋疏散序列，允許跨日/長時間的清空動態。
- **多迭代收斂與後期平滑**：`lastIteration=50`，`fractionOfIterationsToStartScoreMSA=0.9`  
  讓模式/路徑有探索空間，但後期用 MSA 平滑分數避免震盪。
- **交通流動更貼近壅塞**：`trafficDynamics=kinematicWaves`、`linkDynamics=PassingQ`  
  允許波動/回堵；PassingQ 可避免過度僵塞，同時保留擁堵效果。
- **Stuck 偵測敏感度提高**：`stuckTime=600s`，`removeStuckVehicles=false`  
  早期偵測瓶頸，不直接移除車輛，以呈現真實塞車/阻塞。
- **模式選擇與路徑/時間探索**：  
  - `SubtourModeChoice` 策略加入（0.2），讓行程可在車/pt/走路間切換。  
  - `ChangeExpBeta` (0.5) + `ReRoute` (0.3) 平衡模式與路徑/時間調整。  
  - `fractionOfIterationsToDisableInnovation=0.8` 在後段關閉創新，利於收斂。
- **走路成本調整**：`walk` 的旅行效用設為 -12 utils/hr，避免「走路零成本」導致模式偏誤。
- **PT 參與與主模式**：`mainMode=car,pt` 確保 QSim 內有車與 PT 交通流；時窗足夠長，PT 更容易被選用。

## 預期效應
- 更長時窗與 kinematicWaves 會在瓶頸處形成明顯的壅塞波，Stuck 會較早出現，利於評估疏散瓶頸。
- 模式選擇（SubtourModeChoice）提供車/pt/走路切換機會，可觀察 PT 是否被利用或因壅塞而被放棄。
- MSA 與創新關閉機制在後期穩定結果，減少模式/路徑震盪。
- 走路成本調整後，PT 與車的相對吸引力更合理，不會因走路零成本而過度偏好步行。

## 仍需注意
- `flowCapacityFactor` / `storageCapacityFactor` 目前維持 1.0（假設族群規模與網路容量相符）。若是樣本縮放，需同步調低並對應外部計數/容量假設。
- `lastIteration=50` 為權衡計算時間與收斂品質；若硬體允許且需要更穩定結果，可再提高。
- PT 供給與路網品質（排程、運能）仍決定 PT 是否被大量採用；若要強制更多 PT，需檢查排班、容量與接駁可達性。 
