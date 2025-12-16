package org.matsim.project.examples.osm;

import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy.OverwriteFileSetting;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * Minimal, headless MATSim runner for the OSM-from-scratch example.
 *
 * <p>This intentionally does NOT add SimWrapper/OTFVis modules to keep the example
 * as dependency-light and stable as possible.</p>
 *
 * <p>Usage:
 * <pre>
 *   java -cp matsim-example-project-0.0.1-SNAPSHOT.jar \
 *     org.matsim.project.examples.osm.RunOsmFromScratchHeadless \
 *     examples/osm_zero_to_matsim/scenario/config.xml \
 *     --config:controller.lastIteration 5 \
 *     --config:controller.outputDirectory examples/osm_zero_to_matsim/scenario/output
 * </pre>
 * </p>
 */
public final class RunOsmFromScratchHeadless {

	private RunOsmFromScratchHeadless() {
	}

	public static void main(String[] args) {
		if (args == null || args.length == 0 || args[0] == null) {
			System.err.println("Usage: RunOsmFromScratchHeadless <config.xml> [--config:... overrides]");
			System.exit(2);
		}

		Config config = ConfigUtils.loadConfig(args);
		config.controller().setOverwriteFileSetting(OverwriteFileSetting.deleteDirectoryIfExists);

		Scenario scenario = ScenarioUtils.loadScenario(config);
		Controler controler = new Controler(scenario);
		controler.run();
	}
}

