package org.matsim.project.evacuation;

import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * Phase 3: Run Evacuation Simulation with Within-Day Replanning.
 * 
 * This runner enables agents to dynamically replan their routes when
 * roads are closed due to tsunami flooding.
 * 
 * Usage:
 * java -cp matsim.jar org.matsim.project.evacuation.RunEvacuationWithReplan
 * config.xml
 */
public class RunEvacuationWithReplan {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: RunEvacuationWithReplan <config.xml>");
            System.exit(1);
        }

        String configFile = args[0];

        // Load config
        Config config = ConfigUtils.loadConfig(configFile);

        // Ensure time-variant network is enabled
        config.network().setTimeVariantNetwork(true);

        // Overwrite output files
        config.controller().setOverwriteFileSetting(
                OutputDirectoryHierarchy.OverwriteFileSetting.deleteDirectoryIfExists);

        // Load scenario
        Scenario scenario = ScenarioUtils.loadScenario(config);

        // Create controler
        Controler controler = new Controler(scenario);

        // Add Within-Day Replanning module
        controler.addOverridingModule(new TsunamiWithinDayModule());

        System.out.println("=========================================");
        System.out.println("Phase 3: Evacuation with Within-Day Replanning");
        System.out.println("=========================================");
        System.out.println("Config: " + configFile);
        System.out.println("Time-variant network: " + config.network().isTimeVariantNetwork());
        System.out.println("Change events: " + config.network().getChangeEventsInputFile());
        System.out.println("=========================================");

        // Run simulation
        controler.run();
    }
}
