package org.matsim.pt2matsim.run;

import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt2matsim.config.PublicTransitMappingConfigGroup;
import org.matsim.pt2matsim.mapping.PTMapper;
import org.matsim.pt2matsim.mapping.networkRouter.ScheduleRoutersFactory;
import org.matsim.pt2matsim.mapping.networkRouter.ScheduleRoutersGtfsShapes;
import org.matsim.pt2matsim.tools.NetworkTools;
import org.matsim.pt2matsim.tools.ScheduleTools;
import org.matsim.pt2matsim.tools.ShapeTools;
import org.matsim.pt2matsim.tools.lib.RouteShape;

import java.util.Map;

/**
 * PT Mapper with GTFS shapes.txt support for v6 mapping.
 * 
 * This uses ScheduleRoutersGtfsShapes to guide routing along GTFS shapes,
 * eliminating artificial links where possible.
 * 
 * Usage:
 * java -Xmx8G -cp pt2matsim-*.jar
 * org.matsim.pt2matsim.run.RunPTMapperWithShapes \
 * ptmapper-config-v6.xml \
 * shapes.txt \
 * EPSG:3826
 */
public class RunPTMapperWithShapes {

    public static void main(String[] args) {
        if (args.length < 3) {
            System.out.println("Usage: RunPTMapperWithShapes <config.xml> <shapes.txt> <coordSystem>");
            System.out.println("  config.xml    - ptmapper config file");
            System.out.println("  shapes.txt    - GTFS shapes.txt file");
            System.out.println("  coordSystem   - Coordinate system (e.g., EPSG:3826)");
            System.exit(1);
        }

        String configFile = args[0];
        String shapesFile = args[1];
        String coordSys = args[2];

        // Optional parameters
        double maxWeightDistance = args.length > 3 ? Double.parseDouble(args[3]) : 50.0;
        double cutBuffer = args.length > 4 ? Double.parseDouble(args[4]) : 200.0;

        System.out.println("=".repeat(60));
        System.out.println("PT Mapper with GTFS Shapes Support (v6)");
        System.out.println("=".repeat(60));
        System.out.println("Config: " + configFile);
        System.out.println("Shapes: " + shapesFile);
        System.out.println("CRS: " + coordSys);
        System.out.println("maxWeightDistance: " + maxWeightDistance);
        System.out.println("cutBuffer: " + cutBuffer);
        System.out.println();

        // Load config
        Config config = ConfigUtils.loadConfig(configFile);
        PublicTransitMappingConfigGroup ptmConfig = ConfigUtils.addOrGetModule(
                config, PublicTransitMappingConfigGroup.class);

        // Load network and schedule
        System.out.println("Loading network: " + ptmConfig.getInputNetworkFile());
        Network network = NetworkTools.readNetwork(ptmConfig.getInputNetworkFile());
        System.out.println("  Nodes: " + network.getNodes().size());
        System.out.println("  Links: " + network.getLinks().size());

        System.out.println("Loading schedule: " + ptmConfig.getInputScheduleFile());
        TransitSchedule schedule = ScheduleTools.readTransitSchedule(ptmConfig.getInputScheduleFile());
        System.out.println("  Lines: " + schedule.getTransitLines().size());

        // Load GTFS shapes
        System.out.println("Loading shapes: " + shapesFile);
        Map<Id<RouteShape>, RouteShape> shapes = ShapeTools.readShapesFile(shapesFile, coordSys);
        System.out.println("  Shapes loaded: " + shapes.size());

        // Create shapes-aware router factory
        System.out.println();
        System.out.println("Creating ScheduleRoutersGtfsShapes factory...");
        ScheduleRoutersFactory routersFactory = new ScheduleRoutersGtfsShapes.Factory(
                schedule, network, shapes,
                ptmConfig.getTransportModeAssignment(),
                ptmConfig.getTravelCostType(),
                maxWeightDistance,
                cutBuffer);

        // Run mapping
        System.out.println();
        System.out.println("=".repeat(60));
        System.out.println("Starting PT Mapping with shapes...");
        System.out.println("=".repeat(60));

        PTMapper ptMapper = new PTMapper(schedule, network);
        ptMapper.run(ptmConfig, null, routersFactory);

        // Write outputs
        System.out.println();
        System.out.println("Writing outputs...");
        NetworkTools.writeNetwork(network, ptmConfig.getOutputNetworkFile());
        System.out.println("  Network: " + ptmConfig.getOutputNetworkFile());

        ScheduleTools.writeTransitSchedule(ptMapper.getSchedule(), ptmConfig.getOutputScheduleFile());
        System.out.println("  Schedule: " + ptmConfig.getOutputScheduleFile());

        System.out.println();
        System.out.println("=".repeat(60));
        System.out.println("✓ PT Mapping with shapes complete!");
        System.out.println("=".repeat(60));
    }
}
