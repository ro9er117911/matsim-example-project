/*
 * *********************************************************************** *
 * project: org.matsim.*                                                   *
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 * copyright       : (C) 2014 by the members listed in the COPYING,        *
 *                   LICENSE and WARRANTY file.                            *
 * email           : info at matsim dot org                                *
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *   See also COPYING, LICENSE and WARRANTY file                           *
 *                                                                         *
 * *********************************************************************** *
 */

package org.matsim.pt2matsim.run;

import java.util.logging.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
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

import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ExecutionException;

/**
 * Public Transit Mapper with GTFS shapes.txt support.
 * 
 * This variant uses ScheduleRoutersGtfsShapes to guide PT routing along
 * GTFS shapes, reducing artificial links.
 *
 * Usage:
 * java -cp pt2matsim.jar org.matsim.pt2matsim.run.PublicTransitMapperWithShapes
 * \
 * config.xml shapes.txt EPSG:3826 [maxWeightDistance] [cutBuffer]
 *
 * @author polettif, modified for shapes support
 */
public final class PublicTransitMapperWithShapes {

    private static final Logger log = Logger.getLogger(PublicTransitMapperWithShapes.class.getName());

    private PublicTransitMapperWithShapes() {
    }

    /**
     * Routes the unmapped MATSim Transit Schedule to the network using GTFS shapes.
     *
     * @param args <br/>
     *             [0] PublicTransitMapping config file<br/>
     *             [1] GTFS shapes.txt file<br/>
     *             [2] Coordinate system (e.g., EPSG:3826)<br/>
     *             [3] (optional) maxWeightDistance, default 50.0<br/>
     *             [4] (optional) cutBuffer, default 200.0<br/>
     */
    public static void main(String[] args) {
        if (args.length < 3) {
            System.out.println(
                    "Usage: PublicTransitMapperWithShapes <config.xml> <shapes.txt> <coordSystem> [maxWeightDistance] [cutBuffer]");
            System.out.println("  config.xml      - PublicTransitMapping config file");
            System.out.println("  shapes.txt      - GTFS shapes.txt file");
            System.out.println("  coordSystem     - Coordinate system (e.g., EPSG:3826)");
            System.out.println("  maxWeightDistance - (optional) max distance weight, default 50.0");
            System.out.println("  cutBuffer       - (optional) buffer for network cut, default 200.0");
            System.exit(1);
        }

        String configFile = args[0];
        String shapesFile = args[1];
        String coordSystem = args[2];
        double maxWeightDistance = args.length > 3 ? Double.parseDouble(args[3]) : 50.0;
        double cutBuffer = args.length > 4 ? Double.parseDouble(args[4]) : 200.0;

        run(configFile, shapesFile, coordSystem, maxWeightDistance, cutBuffer);
    }

    /**
     * Routes the unmapped MATSim Transit Schedule to the network using GTFS shapes.
     */
    public static void run(String configFile, String shapesFile, String coordSystem,
            double maxWeightDistance, double cutBuffer) {

        log.info("============================================================");
        log.info("Public Transit Mapper with GTFS Shapes Support");
        log.info("============================================================");
        log.info("Config: " + configFile);
        log.info("Shapes: " + shapesFile);
        log.info("Coord System: " + coordSystem);
        log.info("maxWeightDistance: " + maxWeightDistance);
        log.info("cutBuffer: " + cutBuffer);
        log.info("");

        // Load config, input schedule and input network
        Config configAll = ConfigUtils.loadConfig(configFile, new PublicTransitMappingConfigGroup());
        PublicTransitMappingConfigGroup config = ConfigUtils.addOrGetModule(configAll,
                PublicTransitMappingConfigGroup.class);
        TransitSchedule schedule = config.getInputScheduleFile() == null ? null
                : ScheduleTools.readTransitSchedule(config.getInputScheduleFile());
        Network network = config.getInputNetworkFile() == null ? null
                : NetworkTools.readNetwork(config.getInputNetworkFile());

        // Load GTFS shapes
        log.info("Loading GTFS shapes from: " + shapesFile);
        Map<Id<RouteShape>, RouteShape> shapes = ShapeTools.readShapesFile(shapesFile, coordSystem);
        log.info("Loaded " + shapes.size() + " shapes");

        // Create shapes-aware router factory
        log.info("Creating ScheduleRoutersGtfsShapes factory...");
        ScheduleRoutersFactory routersFactory = new ScheduleRoutersGtfsShapes.Factory(
                schedule, network, shapes,
                config.getTransportModeAssignment(),
                config.getTravelCostType(),
                maxWeightDistance,
                cutBuffer);

        // Run PTMapper with shapes router
        log.info("");
        log.info("============================================================");
        log.info("Starting PT Mapping with GTFS Shapes...");
        log.info("============================================================");

        PTMapper ptMapper = new PTMapper(schedule, network);
        try {
            ptMapper.run(config, null, routersFactory);
        } catch (InterruptedException | ExecutionException e) {
            log.severe("PT Mapping failed: " + e.getMessage());
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
        }
        if (config.getOutputNetworkFile() != null && config.getOutputScheduleFile() != null) {
            log.info("Writing schedule and network to file...");
            try {
                ScheduleTools.writeTransitSchedule(ptMapper.getSchedule(), config.getOutputScheduleFile());
                NetworkTools.writeNetwork(network, config.getOutputNetworkFile());
            } catch (Exception e) {
                log.severe("Cannot write to output directory!");
            }
            if (config.getOutputStreetNetworkFile() != null) {
                NetworkTools.writeNetwork(
                        NetworkTools.createFilteredNetworkByLinkMode(network, Collections.singleton(TransportMode.car)),
                        config.getOutputStreetNetworkFile());
            }
        } else {
            log.info("No output paths defined, schedule and network are not written to files.");
        }

        log.info("");
        log.info("============================================================");
        log.info("PT Mapping with GTFS Shapes Complete!");
        log.info("============================================================");
    }
}
