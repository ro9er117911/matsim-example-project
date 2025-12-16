package org.matsim.project.tools;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.network.algorithms.NetworkCleaner;
import org.matsim.core.network.io.NetworkWriter;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.geometry.CoordinateTransformation;
import org.matsim.core.utils.geometry.transformations.GeotoolsTransformation;
import org.matsim.core.utils.io.OsmNetworkReader;

/**
 * Build MATSim network from OSM XML file using OsmNetworkReader.
 */
@SuppressWarnings("deprecation")
public class BuildNetworkFromOsmXml {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: BuildNetworkFromOsmXml <input.osm> <output_network.xml.gz>");
            System.exit(1);
        }

        String input = args[0];
        String output = args[1];

        // Create scenario with TWD97 coordinate system
        var config = ConfigUtils.createConfig();
        config.global().setCoordinateSystem("EPSG:3826");
        Scenario scenario = ScenarioUtils.createScenario(config);
        Network network = scenario.getNetwork();

        // Coordinate transformation: WGS84 -> TWD97
        CoordinateTransformation ct = new GeotoolsTransformation("EPSG:4326", "EPSG:3826");

        // Create OSM reader
        OsmNetworkReader reader = new OsmNetworkReader(network, ct, true, true);

        // Use default highway settings (no custom settings to avoid API issues)
        // The reader already has sensible defaults built in

        System.out.println("Parsing OSM file: " + input);
        reader.parse(input);
        System.out.println(
                "Initial network: " + network.getNodes().size() + " nodes, " + network.getLinks().size() + " links");

        // Clean network (remove disconnected parts)
        System.out.println("Cleaning network...");
        new NetworkCleaner().run(network);
        System.out.println(
                "Cleaned network: " + network.getNodes().size() + " nodes, " + network.getLinks().size() + " links");

        // Write output
        System.out.println("Writing network to: " + output);
        new NetworkWriter(network).write(output);
        System.out.println("Done.");
    }
}
