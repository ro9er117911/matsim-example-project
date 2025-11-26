package org.matsim.project.tools;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.io.MatsimNetworkReader;
import org.matsim.core.network.io.NetworkWriter;
import org.matsim.core.scenario.ScenarioUtils;

import java.util.HashSet;
import java.util.Set;

/**
 * CLI utility to clean a network for car/PT connectivity and write it back out.
 * Usage:
 *   CleanNetworkForCar inputNetwork.xml[.gz] outputNetwork.xml[.gz]
 */
public class CleanNetworkForCar {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: CleanNetworkForCar <input-network> <output-network>");
            System.exit(1);
        }

        String input = args[0];
        String output = args[1];

        Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        new MatsimNetworkReader(scenario.getNetwork()).readFile(input);
        Network network = scenario.getNetwork();

        System.out.println("Loaded network: nodes=" + network.getNodes().size() + " links=" + network.getLinks().size());

        Set<String> modesToClean = new HashSet<>(Set.of("car", "pt", "bus", "subway", "rail", "tram", "light_rail"));
        System.out.println("Cleaning network for modes: " + modesToClean);
        NetworkUtils.cleanNetwork(network, modesToClean);

        System.out.println("After cleaning: nodes=" + network.getNodes().size() + " links=" + network.getLinks().size());
        new NetworkWriter(network).write(output);
        System.out.println("Wrote cleaned network to: " + output);
    }
}
