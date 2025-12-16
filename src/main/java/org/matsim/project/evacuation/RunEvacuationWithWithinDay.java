package org.matsim.project.evacuation;

import org.apache.logging.log4j.core.tools.picocli.CommandLine;
import org.matsim.api.core.v01.Scenario;
import org.matsim.application.MATSimApplication;
import org.matsim.core.config.Config;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy.OverwriteFileSetting;
import org.matsim.simwrapper.SimWrapperModule;

/**
 * MATSim Application for Tsunami Evacuation with Within-Day Replanning.
 * 
 * This runner:
 * 1. Loads a config with time-variant network (NetworkChangeEvents)
 * 2. Enables the TsunamiWithinDayModule for periodic replanning
 * 3. Agents will reroute when they encounter flooded roads
 * 
 * Usage:
 * java -cp matsim.jar org.matsim.project.evacuation.RunEvacuationWithWithinDay
 * config.xml
 */
@CommandLine.Command(header = ":: Tsunami Evacuation with Within-Day Replanning ::", version = "1.0")
public class RunEvacuationWithWithinDay extends MATSimApplication {

    public RunEvacuationWithWithinDay() {
        super("5000_disatar/05_combined_evac/config_combined_5000.xml");
    }

    public static void main(String[] args) {
        MATSimApplication.run(RunEvacuationWithWithinDay.class, args);
    }

    @Override
    protected Config prepareConfig(Config config) {
        // Set overwrite policy
        config.controller().setOverwriteFileSetting(OverwriteFileSetting.deleteDirectoryIfExists);

        // Ensure time-variant network is enabled
        config.network().setTimeVariantNetwork(true);

        // Reduce iterations for testing
        if (config.controller().getLastIteration() > 5) {
            config.controller().setLastIteration(0);
        }

        return config;
    }

    @Override
    protected void prepareScenario(Scenario scenario) {
        // Sanitize network attributes for Avro/SimWrapper compatibility
        for (org.matsim.api.core.v01.network.Link link : scenario.getNetwork().getLinks().values()) {
            for (String key : link.getAttributes().getAsMap().keySet().toArray(new String[0])) {
                if (key.contains(":")) {
                    link.getAttributes().removeAttribute(key);
                }
            }
        }
        for (org.matsim.api.core.v01.network.Node node : scenario.getNetwork().getNodes().values()) {
            for (String key : node.getAttributes().getAsMap().keySet().toArray(new String[0])) {
                if (key.contains(":")) {
                    node.getAttributes().removeAttribute(key);
                }
            }
        }
    }

    @Override
    protected void prepareControler(Controler controler) {
        // Add SimWrapper for visualization
        controler.addOverridingModule(new SimWrapperModule());

        // Add Within-Day Replanning Module for tsunami evacuation
        controler.addOverridingModule(new TsunamiWithinDayModule());

        System.out.println("========================================");
        System.out.println("Tsunami Evacuation Mode ENABLED");
        System.out.println("  - Time-variant network: ON");
        System.out.println("  - Within-day replanning: ON (every 300s)");
        System.out.println("  - Alert time: 03:00:00");
        System.out.println("========================================");
    }
}
