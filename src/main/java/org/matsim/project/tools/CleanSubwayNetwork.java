package org.matsim.project.tools;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.NetworkWriter;
import org.matsim.api.core.v01.network.Node;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.io.MatsimNetworkReader;
import org.matsim.core.scenario.ScenarioUtils;

import java.util.HashSet;
import java.util.Set;

/**
 * Extracts and cleans the subway network from a multimodal network.
 * Only keeps links with 'subway' or 'pt' modes and ensures connectivity.
 */
public class CleanSubwayNetwork {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: CleanSubwayNetwork <input-network> <output-network>");
            System.err.println("Example: CleanSubwayNetwork network.xml.gz network-subway-only.xml.gz");
            System.exit(1);
        }

        String inputNetwork = args[0];
        String outputNetwork = args[1];

        System.out.println("Loading network from: " + inputNetwork);
        Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        new MatsimNetworkReader(scenario.getNetwork()).readFile(inputNetwork);
        Network originalNetwork = scenario.getNetwork();

        System.out.println("Original network: " + originalNetwork.getLinks().size() + " links, "
                + originalNetwork.getNodes().size() + " nodes");

        // Create new network for subway only
        Network subwayNetwork = NetworkUtils.createNetwork();

        // Copy nodes that are used by subway links
        Set<Node> subwayNodes = new HashSet<>();

        System.out.println("Extracting subway links...");
        int subwayLinkCount = 0;
        for (Link link : originalNetwork.getLinks().values()) {
            Set<String> modes = link.getAllowedModes();
            // Keep links that have subway or pt mode
            if (modes.contains("subway") || modes.contains("pt")) {
                subwayNodes.add(link.getFromNode());
                subwayNodes.add(link.getToNode());
                subwayLinkCount++;
            }
        }

        System.out.println("Found " + subwayLinkCount + " subway/pt links using " + subwayNodes.size() + " nodes");

        // Add nodes to new network
        System.out.println("Adding nodes to subway network...");
        for (Node node : subwayNodes) {
            Node newNode = subwayNetwork.getFactory().createNode(node.getId(), node.getCoord());
            subwayNetwork.addNode(newNode);
        }

        // Add links to new network
        System.out.println("Adding links to subway network...");
        for (Link link : originalNetwork.getLinks().values()) {
            Set<String> modes = link.getAllowedModes();
            if (modes.contains("subway") || modes.contains("pt")) {
                Node fromNode = subwayNetwork.getNodes().get(link.getFromNode().getId());
                Node toNode = subwayNetwork.getNodes().get(link.getToNode().getId());

                if (fromNode != null && toNode != null) {
                    Link newLink = subwayNetwork.getFactory().createLink(
                        link.getId(),
                        fromNode,
                        toNode
                    );
                    newLink.setLength(link.getLength());
                    newLink.setFreespeed(link.getFreespeed());
                    newLink.setCapacity(link.getCapacity());
                    newLink.setNumberOfLanes(link.getNumberOfLanes());

                    // Set modes to pt,subway for compatibility
                    Set<String> newModes = new HashSet<>();
                    newModes.add("pt");
                    newModes.add("subway");
                    newLink.setAllowedModes(newModes);

                    subwayNetwork.addLink(newLink);
                }
            }
        }

        System.out.println("Subway network: " + subwayNetwork.getLinks().size() + " links, "
                + subwayNetwork.getNodes().size() + " nodes");

        // Clean network - remove unconnected components
        System.out.println("Cleaning network for mode 'pt'...");
        Set<String> modesToClean = new HashSet<>();
        modesToClean.add("pt");
        NetworkUtils.cleanNetwork(subwayNetwork, modesToClean);

        System.out.println("After cleaning: " + subwayNetwork.getLinks().size() + " links, "
                + subwayNetwork.getNodes().size() + " nodes");

        // Write output
        System.out.println("Writing subway network to: " + outputNetwork);
        new NetworkWriter(subwayNetwork).write(outputNetwork);

        System.out.println("Done!");
    }
}
