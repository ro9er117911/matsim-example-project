TL;DR：把「每 3 秒一個座標」當成 plan 是錯的。先把每個 agent 的軌跡壓縮成「起點活動 → 一個 car leg（附路徑）→ 終點活動」，再輸出成 population.xml，必要時用 map-matching 把座標轉成 link 序列。

---

## 1. 先釐清 MATSim 角度下，現在這包資料有什麼問題

你現在的 plan 結構：

* 幾百個
  `<activity type="stop" x="..." y="..." end_time="hh:mm:ss"/>`
* 中間夾滿 `<leg mode="car"/>`

這在 MATSim 眼中代表：

* 一堆「極短活動＋極短車程」交錯
* QSim 根本不會照你這些 3 秒座標去「重播」，只會當成一連串不合理的活動切換
* 效能也會直接炸掉（幾千人 × 幾千個 activity）

結論：不能用「每 3 秒一個 activity」去餵 MATSim。
要先把軌跡壓縮成「活動層級」的 plan。

---

## 2. 正確的抽象：把 3 秒座標軌跡 → 1 個 trip（或少數幾個 trip）

對於「短時間大量人群移動」：

* 把每個 agent 的 3 秒軌跡視為「一趟 car trip」
* plan 結構簡化為：

```xml
<person id="4441">
  <plan type="typical">
    <activity type="start" x="起點x" y="起點y" end_time="3:18:00"/>
    <leg mode="car">
      <!-- 可選：附上 route -->
    </leg>
    <activity type="end" x="終點x" y="終點y"/>
  </plan>
</person>
```

關鍵：

* 起點活動：用第一個座標 + 第一個時間
* 終點活動：用最後一個座標 + 最後一個時間（通常不設 end_time）
* 中間所有「stop」通通丟掉，在需要時只留下「路徑資訊」放進 leg.route

---

## 3. 兩層轉換流程概述

### 第 1 層：從 3 秒座標壓縮出 OD + 時間

對每個 agent 的原始資料（或你現在這個超長 XML）：

1. 取出所有 `(t_k, x_k, y_k)`，依時間排序。
2. 定義：

   * `t_start = t_0`
   * `t_end   = t_last`
   * `coord_start = (x_0, y_0)`
   * `coord_end   = (x_last, y_last)`
3. 建一個「壓縮後的 plan」：

   * `activity(type="start", coord_start, end_time=t_start)`
   * `leg(mode="car")`
   * `activity(type="end", coord_end)`   ← 不再給 end_time

做到這裡，你就已經可以產出一個「最簡 population.xml」，讓 MATSim 自己 route。

---

### 第 2 層（可選，但比較貼近你原軌跡）：做 map-matching → route.links

如果你不想讓 MATSim 自己算路，而是想「大致跟原來軌跡走同一條路」，就用 3 秒座標做 map-matching，產生 link 序列：

1. 有 network.xml（同一座標系）。
2. 對每個 agent 的座標序列：

   * 對每個 `(x_k, y_k)` 找最近的 link Id `L_k`（用 KD-Tree 或 R-tree 加速）。
   * 把連續重複的 `L_k` 壓縮，例如：`L1, L1, L1, L2, L2, L3 → L1, L2, L3`。
3. 定義：

   * `startLinkId = 序列中的第一個 link`
   * `endLinkId   = 序列中的最後一個 link`
   * `intermediateLinks = 中間那串`
4. 在 plan 的 leg 裡加上 route，例如 XML 版：

```xml
<leg mode="car" dep_time="03:18:00" trav_time="0:22:05">
  <route type="links" start_link="L_start" end_link="L_end">
    L2 L3 L4 L5 ... L_(n-1)
  </route>
</leg>
```

* `trav_time` 可設成 `t_end - t_start`（例如 `0:22:05`）。
* QSim 會照 link 序列跑，不保證 3 秒對齊，但流向與路線會和你的原始軌跡相近。

---

## 4. 直接從你這種「塞滿 stop 的 XML」壓縮出正常 population.xml

假設你手上已經是一整包像上面那樣的 XML（home → 一堆 stop → home），可以做「XML 壓縮轉換」，邏輯如下：

對每個 `<person>`：

1. 抓第一個 `<activity>`（type="home"、end_time="3:18:00"）→ 當起點活動。
2. 抓最後一個 `<activity>`（type="home"、end_time="3:40:05"）→ 當終點活動。

   * 轉寫時把 `end_time` 移除。
3. 中間全部的 `<activity type="stop">` 與 `<leg>` 丟掉。
4. 插入一個 `<leg mode="car"/>` 介於起點與終點中間。

輸出結果示意：

```xml
<person id="4441">
  <plan type="typical">
    <activity type="home" x="290263.62" y="2782083.89" end_time="3:18:00"/>
    <leg mode="car"/>
    <activity type="home" x="296239.71" y="2768305.82"/>
  </plan>
</person>
```

這樣就變成「一趟車程」而不是數百個 3 秒切片。

---

## 5. 最小 Java 實作範例（用 MATSim API 生 population.xml）

假設你已經先把每個 agent 的軌跡轉成「起點 / 終點 / t_start / t_end / link 序列」的中間檔（CSV 或 JSON），以下是最小 Java 範例（可以放在 matsim-example-project 裡建一個 class）：

```java
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.population.*;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.population.routes.RouteUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.network.io.MatsimNetworkReader;
import org.matsim.core.population.io.PopulationWriter;

import java.util.Arrays;
import java.util.List;

public class BuildShortHorizonPopulation {
    public static void main(String[] args) {
        String networkFile    = "network.xml";
        String outputPopFile  = "population_short.xml";

        Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        new MatsimNetworkReader(scenario.getNetwork()).readFile(networkFile);

        Population population = scenario.getPopulation();
        PopulationFactory pf  = population.getFactory();

        // === 這裡示範 1 個 agent，實際上用迴圈處理你的 5000 人 ===
        String personId = "4441";
        Coord startCoord = new Coord(290263.62, 2782083.89);
        Coord endCoord   = new Coord(296239.71, 2768305.82);
        double depTime   = Time.parseTime("03:18:00");  // t_start
        double arrTime   = Time.parseTime("03:40:05");  // t_end

        Person person = pf.createPerson(Id.createPersonId(personId));
        Plan plan     = pf.createPlan();

        Activity actStart = pf.createActivityFromCoord("home", startCoord);
        actStart.setEndTime(depTime);
        plan.addActivity(actStart);

        Leg leg = pf.createLeg("car");

        // 可選：如果已有 link 序列，就塞進 route
        // List<Id<Link>> links = Arrays.asList(
        //         Id.createLinkId("L2"),
        //         Id.createLinkId("L3"),
        //         Id.createLinkId("L4")
        // );
        // Id<Link> startLinkId = Id.createLinkId("L_start");
        // Id<Link> endLinkId   = Id.createLinkId("L_end");
        // NetworkRoute route = RouteUtils.createLinkNetworkRouteImpl(startLinkId, endLinkId);
        // route.setLinkIds(startLinkId, links, endLinkId);
        // route.setTravelTime(arrTime - depTime);
        // leg.setRoute(route);

        plan.addLeg(leg);

        Activity actEnd = pf.createActivityFromCoord("home", endCoord);
        // 通常最後一個 activity 不設 end_time
        plan.addActivity(actEnd);

        person.addPlan(plan);
        population.addPerson(person);

        new PopulationWriter(population, scenario.getNetwork()).write(outputPopFile);
    }
}
```

這個 class 的驗收標準：

1. 可以成功編譯並執行，產生 `population_short.xml`。
2. 用 MATSim 跑一個最小 config（指到你的 network + population_short.xml），QSim 能跑完。
3. 用 via / OTFVis 看人車流，確實在你設定的起訖範圍內移動。

---

## 6. 資料量與效能注意

* 原本：每人幾百個 activity × 5000 人 → 幾百萬個節點，QSim 很容易爆。
* 壓縮後：每人 2 個 activity + 1 個 leg × 5000 人 → 完全合理。
* 若需要更細的行為（例如中途換 mode、進避難點再出來），再額外加少量「中繼活動」，而不是每 3 秒一個。

---

### 3 個關鍵檢核

1. 每個 person 最終 plan 是否只剩「少量活動（起點／終點／少數中繼）＋對應 legs」，而不是幾百個 `type="stop"`。
2. population.xml 能通過 MATSim 解析並跑完 QSim，不出現「plan 太細碎」「活動時間不合理」類錯誤。
3. 用可視化檢查，5000 人的移動時空分布是否與原始軌跡在「宏觀上」一致（起訖位置分布、路徑走向、時間範圍）。
