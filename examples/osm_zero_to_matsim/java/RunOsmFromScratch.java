/*
 * 核心 Java（教學用）：展示 MATSim 最小 pipeline
 *
 * 用途：
 * - 給熟悉 OSM 的工程師快速對照：Config → Scenario → Controler → run()
 * - 示範「你可以在哪裡插 hook」：改 config、改 scenario、加 module
 *
 * 注意：
 * - 本檔案放在 examples/ 內，預設不參與 Maven 編譯。
 * - 若你想把它變成可直接執行的 main class，請移到：
 *     src/main/java/<你的package>/RunOsmFromScratch.java
 *   然後用 `./mvnw -q -DskipTests package` 建 jar。
 */

import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy.OverwriteFileSetting;
import org.matsim.core.scenario.ScenarioUtils;

public final class RunOsmFromScratch {

    public static void main(String[] args) {
        String configPath = args.length > 0 ? args[0] : "examples/osm_zero_to_matsim/scenario/config.xml";

        // 1) Config：載入 config.xml（module-based）
        Config config = ConfigUtils.loadConfig(configPath);
        config.controller().setOverwriteFileSetting(OverwriteFileSetting.deleteDirectoryIfExists);

        // 2) Scenario：把 network / plans 等 input 讀進記憶體
        Scenario scenario = ScenarioUtils.loadScenario(config);

        // 3) Controler：組裝 mobsim/scoring/replanning 等模組
        Controler controler = new Controler(scenario);

        // 你可以在這裡加 module，例如：
        // controler.addOverridingModule(new OTFVisLiveModule()); // GUI 視覺化
        // controler.addOverridingModule(new SimWrapperModule()); // Web dashboard

        // 4) Run
        controler.run();
    }
}

