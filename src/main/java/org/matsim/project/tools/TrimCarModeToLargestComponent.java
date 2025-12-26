package org.matsim.project.tools;

import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.io.MatsimNetworkReader;
import org.matsim.core.network.io.NetworkWriter;
import org.matsim.core.scenario.ScenarioUtils;

import java.util.HashSet;
import java.util.Set;

/**
 * Removes the "car" mode from links that are outside the largest connected
 * car component, while preserving other modes (bus/subway/pt/walk).
 */
public class TrimCarModeToLargestComponent {

	public static void main(String[] args) {
		if (args.length < 2) {
			System.err.println("Usage: TrimCarModeToLargestComponent <input-network> <output-network>");
			System.err.println("Example: TrimCarModeToLargestComponent network-with-pt.xml.gz network-with-pt-car-connected.xml.gz");
			System.exit(1);
		}

		String inputNetwork = args[0];
		String outputNetwork = args[1];

		System.out.println("Loading network: " + inputNetwork);
		var scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
		new MatsimNetworkReader(scenario.getNetwork()).readFile(inputNetwork);
		Network original = scenario.getNetwork();

		System.out.println("Creating car-only copy for cleaning...");
		var carScenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
		new MatsimNetworkReader(carScenario.getNetwork()).readFile(inputNetwork);
		Network carOnly = carScenario.getNetwork();
		for (Link link : carOnly.getLinks().values()) {
			if (link.getAllowedModes().contains("car")) {
				link.setAllowedModes(Set.of("car"));
			} else {
				link.setAllowedModes(Set.of());
			}
		}

		System.out.println("Cleaning car network to largest component...");
		NetworkUtils.cleanNetwork(carOnly, Set.of("car"));

		Set<String> carLinkIds = new HashSet<>();
		for (Link link : carOnly.getLinks().values()) {
			if (link.getAllowedModes().contains("car")) {
				carLinkIds.add(link.getId().toString());
			}
		}

		int removedCarMode = 0;
		for (Link link : original.getLinks().values()) {
			Set<String> modes = new HashSet<>(link.getAllowedModes());
			if (modes.contains("car") && !carLinkIds.contains(link.getId().toString())) {
				modes.remove("car");
				link.setAllowedModes(modes);
				removedCarMode++;
			}
		}

		System.out.println("Removed 'car' mode from " + removedCarMode + " links outside main component.");
		System.out.println("Writing network: " + outputNetwork);
		new NetworkWriter(original).write(outputNetwork);
	}
}
