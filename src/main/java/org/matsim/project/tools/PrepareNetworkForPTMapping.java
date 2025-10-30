package org.matsim.project.tools;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.NetworkWriter;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.io.MatsimNetworkReader;
import org.matsim.core.scenario.ScenarioUtils;

import java.util.HashSet;
import java.util.Set;

/**
 * Prepares a network for PT mapping by:
 * 1. Loading the network
 * 2. Cleaning it for PT connectivity
 * 3. Ensuring all PT links have proper modes
 * 4. Writing the cleaned network
 */
public class PrepareNetworkForPTMapping {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: PrepareNetworkForPTMapping <input-network> <output-network>");
            System.err.println("Example: PrepareNetworkForPTMapping network.xml.gz network-cleaned.xml.gz");
            System.exit(1);
        }

        String inputNetwork = args[0];
        String outputNetwork = args[1];

        System.out.println("=".repeat(80));
        System.out.println("Preparing Network for PT Mapping");
        System.out.println("=".repeat(80));

        System.out.println("\nLoading network from: " + inputNetwork);
        Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        new MatsimNetworkReader(scenario.getNetwork()).readFile(inputNetwork);
        Network network = scenario.getNetwork();

        System.out.println("Original network:");
        System.out.println("  - Links: " + network.getLinks().size());
        System.out.println("  - Nodes: " + network.getNodes().size());

        // Count PT links
        int ptLinkCount = 0;
        int subwayLinkCount = 0;
        Set<String> allModes = new HashSet<>();

        for (Link link : network.getLinks().values()) {
            Set<String> modes = link.getAllowedModes();
            allModes.addAll(modes);
            if (modes.contains("pt")) ptLinkCount++;
            if (modes.contains("subway")) subwayLinkCount++;
        }

        System.out.println("\nMode statistics:");
        System.out.println("  - Links with 'pt' mode: " + ptLinkCount);
        System.out.println("  - Links with 'subway' mode: " + subwayLinkCount);
        System.out.println("  - All modes found: " + allModes);

        // Ensure all subway links also have pt mode
        System.out.println("\n" + "=".repeat(80));
        System.out.println("Step 1: Ensuring all subway links have 'pt' mode...");
        System.out.println("=".repeat(80));

        int linksUpdated = 0;
        for (Link link : network.getLinks().values()) {
            Set<String> modes = new HashSet<>(link.getAllowedModes());
            if (modes.contains("subway") && !modes.contains("pt")) {
                modes.add("pt");
                link.setAllowedModes(modes);
                linksUpdated++;
            }
        }
        System.out.println("Updated " + linksUpdated + " links to include 'pt' mode");

        // Clean network for PT connectivity
        System.out.println("\n" + "=".repeat(80));
        System.out.println("Step 2: Cleaning network for 'pt' mode connectivity...");
        System.out.println("=".repeat(80));

        Set<String> modesToClean = new HashSet<>();
        modesToClean.add("pt");

        System.out.println("Running NetworkUtils.cleanNetwork() for modes: " + modesToClean);
        NetworkUtils.cleanNetwork(network, modesToClean);

        System.out.println("\nAfter cleaning:");
        System.out.println("  - Links: " + network.getLinks().size());
        System.out.println("  - Nodes: " + network.getNodes().size());

        // Recount PT links
        ptLinkCount = 0;
        subwayLinkCount = 0;
        for (Link link : network.getLinks().values()) {
            Set<String> modes = link.getAllowedModes();
            if (modes.contains("pt")) ptLinkCount++;
            if (modes.contains("subway")) subwayLinkCount++;
        }

        System.out.println("\nFinal mode statistics:");
        System.out.println("  - Links with 'pt' mode: " + ptLinkCount);
        System.out.println("  - Links with 'subway' mode: " + subwayLinkCount);

        // Write cleaned network
        System.out.println("\n" + "=".repeat(80));
        System.out.println("Step 3: Writing cleaned network...");
        System.out.println("=".repeat(80));
        System.out.println("Output file: " + outputNetwork);

        new NetworkWriter(network).write(outputNetwork);

        System.out.println("\n" + "=".repeat(80));
        System.out.println("✓ Network preparation completed successfully!");
        System.out.println("=".repeat(80));
        System.out.println("\nNext step: Run PT mapping with the cleaned network:");
        System.out.println("  java -Xmx8g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \\");
        System.out.println("    org.matsim.pt2matsim.run.PublicTransitMapper \\");
        System.out.println("    pt2matsim/work/ptmapper-config-metro-v2.xml");
        System.out.println();
    }
}
