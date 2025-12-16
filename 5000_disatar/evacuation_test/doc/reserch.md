TL;DR：GUI 撤離模組（ScenarioManager）是一個「從 OSM → 劃區 → 生成人口 → 路網裁切 → 自動產生 evacuation scenario → 跑多迭代 → 做 GIS 分析」的一條龍工具，但有很多內建假設。你已經有「淡水→文山」的大量代理人，如果改用這個 GUI，要接受它的建模方式，而不是把你現有的 plans 直接塞進去。

---

## 一、你從「已跑通大規模模擬」切到 GUI 撤離模組，要特別注意的點

1. **需求生成方式完全不同：不能直接吃你現有的 plans/population.xml**

   * 目前版本明講：GUI 只能自己根據「人口 shp 或 GUI 畫的圓圈＋人口數」生成人口與 agents，**沒支援使用既有的 MATSim demand**。
   * 每個 agent = 一個要撤離的人（通常是開車），只有一個 evacuation trip，沒有你的「日常活動鏈」。
   * 實務上代表：

     * 你原本 Tamsui→Wenshan 的活動時間表、回家、上班等行程，在 evacuation contribution 裡會全部消失，只剩「在撤離區裡某個 link 起跑 → 出區域超級節點」。

2. **目的地概念改變：不是「文山區」而是「離開淹水圈」**

   * 撤離模組把區域外所有出口 link 接到一個 super-node/super-link，所有路徑都指向這個 super-link。
   * 對淡水→文山 scenario 的翻譯：

     * GUI 模組的核心目的是「從危險區撤離到安全圈外」，不是「精確疏散到文山某幾個避難點」。
     * 若你要維持「淡水撤離到文山」的語意，你必須把「需要撤離的區域」劃在淡水一帶，並讓「安全區」包含往南一路到文山的出口；真正的文山細節，要自己在路網與分析上補，不會在 GUI 裡精細表達。

3. **只支援 mainTrafficType = VEHICULAR 或 PEDESTRIAN 的純場景**

   * 設定 mainTrafficType 會讓模組產生「專門給車」或「專門給行人」的 network，重新設定 free speed、lane 數、容量等。
   * 混合模式（你原本有 car + PT + walk 等），在這個 GUI 裡會被大幅簡化；
   * PT 疏運要用「Bus Stop Editor」，但限制很大（後面解釋）。

4. **人口與樣本比例的假設：Worst-case 車流 vs. 你的 calibrated demand**

   * 書裡 Hamburg 案例是：每個 agent 代表一台車，假設「Wilhelmsburg 登記的所有車都要開出來」，且禁止外車進來，視為 worst-case。
   * 再用 sampleSize（1.0 / 0.1 / 0.01）把人口壓縮成可算的量。
   * 你現在的 Tamsui→Wenshan 如果是「基於常態 OD＋增量撤離」，轉成 GUI 模組時會變成：「假設整個撤離圈裡所有車都在某個時間窗內出來」。
   * 這會大幅改變擁塞程度與結果解讀，要把這當成「上界壓力測試」而不是「忠實重現你原本 scenario」。

5. **出發時間分佈：需要用 GUI 裡的 distribution 來近似你的 pre-movement 模型**

   * GUI 支援 3 種 departure time distribution：Dirac-delta、normal、log-normal。
   * 撤離議題裡，作者建議 log-normal 用來模擬：

     * 一開始很多人同時動起來
     * 之後愈來愈少人出發
   * 你如果原本有自定義 pre-movement 邏輯（例如 household-based、反應時間 function），在 GUI 裡只能用這三種分佈＋ earliest/latest 秒數去近似。

6. **路網會被「切成撤離網」＋加 super-link：對路徑與瓶頸位置要重想一次**

   * ScenarioManager 會用你畫的 evacuation area 去「裁切 OSM network」，只保留區內＋出區的 links，然後把所有出口 link 用大容量虛擬 link 接到 super-node。
   * 你原來為了 Tamsui→Wenshan 設的高速公路、匝道、替代路徑，在被裁切+接 super-node 後，可能會出現：

     * 某些你重視的路徑被當作「區外」而整段不在 evacuation net 裡；
     * 超級節點處的負荷不再是你原來 network geometry 直觀可見的瓶頸。

7. **迭代的詮釋不同：這裡的 100 iterations 是「預先想像災時條件」的學習，而不是 day-to-day**

   * 模組說明：雖然真實撤離不會有 day-to-day 學習，但他們把多迭代詮釋成「居民事先預想哪裡會塞，所以不會選那些路」。
   * 建議 thumb rule：大概 100 iterations 就足夠當作「疏散時間下界」，不要拿 iteration 0 的結果做決策（那常常充滿假路徑與人工瓶頸）。

8. **分析模組產出的指標結構和你現在的 output 不一樣**

   * GUI 的 analysis tab 預設會輸出：

     * Cumulative arrival curve（時間 vs. 已撤離人數）；
     * 網格化的 evacuation time / clearance time map；
     * link utilization 分級顏色圖。
   * 這三個指標都是「以撤離區網格和道路為主體的」視角，和你原本可能針對幹道路廊、特定 OD pair 的評估角度不同，要先對齊評估問題再解讀。

---

## 二、逐塊解釋：ScenarioManager GUI 每一個模組到底在幹嘛（對應你會碰到的事）

以下照 Chapter 41 後半段 GUI 流程拆解。

### 1. Scenario Configuration（第一個 tab）

在畫面上你會看到類似圖 41.1(a) 的欄位：

核心欄位對你而言代表：

* **networkFile（OSM 路網）**

  * 給一個涵蓋淡水＋文山＋中間走廊的 OSM 檔（例如 geofabrik 的 taipei 或自裁的片段）。
  * 這裡只能給 OSM XML，不能直接給已經處理好的 MATSim network.xml。

* **mainTrafficType（VEHICULAR / PEDESTRIAN）**

  * 車撤離就選 VEHICULAR（預設）；
  * 若要做「行人撤離淡水老街往山上」，才選 PEDESTRIAN，模組會幫你重設 free speed 等。

* **evacuationAreaFile（撤離區 polygon）**

  * 可以預先準備 ESRI shp，也可以之後在 GUI 裡用「Evacuation Area」工具畫出來再存成 shp。
  * 對淡水 scenario：

    * 這個 polygon 定義「什麼叫淡水淹水／必須撤離的區」，而不是整個大台北。

* **populationFile（人口分布 shp）**

  * 一樣是 ESRI shp，每個 polygon 有「人口數」屬性。
  * 或是用 Population Editor 用圓圈＋人口數畫出來，ScenarioManager 幫你生成這個 shp。

* **outputDir**

  * 之後產生的 MATSim network.xml、plans、events 及分析結果都會丟在這裡。

* **sampleSize（樣本比例）**

  * 1.0 = 全人口；0.1 = 抽十分之一、0.01 = 抽百分之一。

* **departureTimeDistribution（出發時間分布）**

  * 選 Dirac-delta / normal / log-normal，並填 µ、σ、earliest、latest。
  * 特別：log-normal 的 µ、σ其實是「底層 normal 的參數」，若你習慣用期望值＋變異數思考，書裡給了公式讓你從 E[X]、Var[X] 算回 µ、σ。

這一頁存檔之後，就是一個 `grips_config` XML（example 見 Hamburg case 的 scenario.xml）。

---

### 2. Evacuation Area（第二個 tab）

* 這個模組是一個小型 GIS 編輯器：

  * 背景圖可用 WMS 或 OSM tile。
  * 你在 map 上畫一個 polygon 或 circle 定義「撤離區」。

* 技術後處理：

  * 之後這個 polygon 會被用來「裁切 network」，只保留區內路段＋從區內連出去的出口 link。
  * 所有出口 link 再用「超大容量、等長度」的虛擬 link 接到 super-node，形成 multi-source → single-destination 的最短路徑問題。

對你來說要注意：

* 若你希望某些幹道（例如台64/65、國三）被視為撤離路線的一部分，它們的入口要落在 polygon 邊界內，否則會被當作區外不算在 evacuation network 裡。

---

### 3. Population（第三個 tab）

* Population Editor 類似 Evacuation Area Editor，但你畫的是「多個圓圈＋每個圈的人數」。
* 模組會：

  * 在每個圓圈內，隨機打點生成對應數量的 agents；
  * 再用 `getNearestLink()` 把每個 agent snap 到最近的 network link 當作出發 link。

限制與含意：

* 沒有 household 結構、沒有原生社經屬性，全部只是「空間分佈＋人口數」。
* 不能直接用你原來的 plans.xml，因此如果你有「依家庭、工作地」建好的結構，這裡全部會被壓平。

---

### 4. Road Closures（第四個 tab）

* 這是「用 GUI 畫 network change events」的介面。
* 你可以對任意 link 設定：

  * 關閉方向（單向或雙向）；
  * 何時關閉（time-dependent）。
* 對應 MATSim 裡的 `NetworkChangeEvents` 機制，會在模擬過程中調整容量、speed 或乾脆關閉。

對淡水 scenario 的典型用法：

* 規劃「只有南向開放的逆向車道」（如颱風撤離時常見）；
* 封閉你不希望被使用的穿越巷弄，把 flow 強迫導向你想測的幹道。

---

### 5. Bus Stop Editor（第五個 tab，PT 疏散）

* 在地圖上點選位置設 bus stop，再填：

  * 第一次發車時間；
  * 總共幾班車；
  * 每班車容量。

* GUI 會幫你生成一個 MATSim `transitSchedule` 給 PT 模組用。

重要限制：

1. 每台 bus 只服務一個 bus stop。
2. 每台 bus 只走「從該站到安全區的最短路徑」，沒有針對動態壅塞做線路優化。

換句話說，目前這個 PT 支援比較適合「特殊接駁車」而不是複雜公車／捷運網路。

---

### 6. Simulation（第六個 tab）

* 這裡就是按一下「Run」讓 ScenarioManager：

  1. 根據 OSM＋evac area＋population 生出 MATSim network、plans。
  2. 加上 road closures 與 bus schedule。
  3. 跑多迭代 evacuation 模擬（預設 100～1000 迭代）。
  4. 每 10 iter 存一次 events 檔供之後分析。

* 每個 agent 的 plan：

  * car/walk 的話就是「home link → super-link」的 route；
  * 搭 bus 的話是更複雜的 PT plan，但仍然只是「到安全區」的單次行程。

* score function 主要是 travel time（可能加上距離），越短分數越高。

---

### 7. Analysis（最後一個 tab）

* 提供數個內建分析：

  1. **Cumulative arrival curve**：時間 vs. 已到達安全區的人數，用來看「何時 50% / 90% 撤離成功」。
  2. **Evacuation time map**：在撤離區上套一個網格（cell size 可變），算每個 cell 的平均撤離時間，顏色越紅代表越慢。
  3. **Clearance time map**：每個 cell「最後一個經過該 cell 的 evacuee 離開的時間」，用來看哪裡最晚清空。
  4. **Link utilization map**：對 links 做分級著色，看整體流量分佈，辨識主要撤離路線與瓶頸。

* 支援對不同 iteration 的 events 做分析，例如只看 iteration 100 的穩定結果。

對你來說：

* 這一套 analysis 是非常適合回答「哪一塊淡水區域最危險、哪幾條路廊是撤離主幹、ASET>RSET 嗎」這類問題。
* 但它不會直接對應你原來的「多日 OD、尖離峰、PT service level」等指標，必須重新設計你要看的 performance 指標。

---

## 三、總結：把你現在的 Tamsui→Wenshan scenario 映射到 GUI 模組的實務建議

1. 把 GUI 撤離模組當成「專門做單次大撤離壓力測試的 pipeline」，不要期待它 1:1 還原你所有日常情境。
2. 先從小區域＋小樣本（sampleSize 0.1 或 0.01）做 dry-run，把以下幾件事情釐清：

   * 撤離區 polygon 劃到哪裡路網才合理；
   * 哪些路要在 Road Closures 裡封掉或逆向；
   * departure time distribution 如何選，才對得上你的情境假設。
3. 把 GUI 產出的結果當作「補充視角」：特別是 evacuation time map、clearance time、link utilization，用來給政策決策或簡報一個容易理解的圖像，而不是替代你原本的完整 MAS scenario。


核心概念：撤離模組 **沒有「多個安全區」的概念**，也沒有真正的「目的地」。它的邏輯是：

定義一塊「危險區」（evacuation area）。
所有代理人只要**離開這塊危險區**、通過其邊界上的出口 link，就被視為「抵達安全區」。
安全區其實是「危險區外的整個路網」。
模組會把所有出口 link 接到一個虛擬 super-node/super-link，形成單一出口的最短路徑問題。

因此 GUI 模組中看不到「設定安全區」這個按鈕。你只能畫「危險區」，安全區＝危險區以外的一切。

---

## 如何設定「安全區」的等價物

手段一：**調整危險區的 polygon 範圍**

危險區畫在哪裡，安全區就在哪裡以外。

若你想「淡水撤離往文山」，GUI 模組的設計就是：

把淡水（你想撤離的那塊）畫為危險區 polygon。
文山不需要畫，可以留在「危險區之外」，它自然屬於安全區。
代理人會沿最短可行路徑往危險區外逃，逃到文山方向是你用路網與封路配置引導的，而不是 GUI 的多目的地設定。

---

## 可以設定多個安全區嗎？

嚴格意義：**不行**。
原因：

安全區不是一個「目的地集合」，它只是「危險區外」。
撤離模組最終會把所有出口 link（危險區的外邊界）導向同一個 super-link。
多目標 evacuation routing 在這個模組裡沒有內建。

但可以「模擬」出類似多安全區的效果：

### 方法 A：劃出多塊危險區（不連在一起）

如果你畫兩塊不相連的危險區（例如：淡水＋八里），GUI 會視為兩個 evacuation sub-areas，各自有出口，跑起來像兩個安全區方向。

限制：

依然導向同一 super-node，不能讓 A 區的人去安全區 A，B 區的人去安全區 B。
只是網路結構不同，因此會自然形成不同方向的壅塞流。

這種方式只適合「你只是想測多個群體同時撤離、但目的地不重要」的場景。

---

### 方法 B：利用路網＋封路強迫不同群體往不同「安全方向」

範例：

淡水區人口 1 → 引導往文山方向（解封南向主幹道、封閉西側）。
淡水區人口 2 → 引導往汐止方向（打開東側匝道、封閉南側）。

本質上不是多安全區，而是「多出口方向」，但 GUI 的 behavior ≈ 多安全區。

---

### 方法 C：後處理「出口 link clusters」當作虛擬安全區

你可以在外部（Python / QGIS / MATSim 事件後處理）定義：

出口 cluster 1 = 往文山方向的出口 links
出口 cluster 2 = 往北投方向的出口 links
出口 cluster 3 = 往關渡方向的出口 links

分析時把 agent 抵達哪一組出口 link 當成「達到不同安全區」。

這是目前實務研究（包含 Hamburg）的標準做法。

GUI 雖然只有一個 super-node，但你可以在 raw network 裡保留原本的出口 link id，後處理分群。

---

## 結論：GUI 模組的限制與你可行的策略

1. 模組不支援多安全區。
2. 只能靠「危險區 polygon」定義誰要撤離。
3. 安全區＝危險區以外的整個路網。
4. 若你需要多個出口方向或多類安全區，使用：

   * 危險區多區塊（有限效果）
   * 路網＋封路策略（有效控制方向）
   * 後處理分群（最乾淨的方法）

你的問題其實是在問：
能不能做「destination choice」而不是「escape boundary crossing」。

答案：GUI 模組原生沒有，但可以透過路網與出口 cluster 達到。

可延伸方向：如果你需要真正的多目的地 evacuation（例如：不同 shelter），必須跳出 GUI，用 MATSim 標準 config＋多個 activity location（shelter nodes）自行建置。

