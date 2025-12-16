package org.matsim.project.tools;

import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.NetworkWriter;
import org.matsim.contrib.osm.networkReader.LinkProperties;
import org.matsim.contrib.osm.networkReader.SupersonicOsmNetworkReader;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.algorithms.NetworkCleaner;
import org.matsim.core.network.io.MatsimNetworkReader;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Build a multimodal (car + walk) network from OSM, keeping small alleys/paths.
 * - Walk is allowed on every link.
 * - Car is disallowed on pedestrian-only links (footway/path/steps/pedestrian/cycleway).
 *
 * Usage:
 *   args[0] = input OSM (.osm or .pbf)
 *   args[1] = output raw MATSim network (.xml or .xml.gz)
 *   args[2] = output cleaned network (optional, will run NetworkCleaner on car+walk)
 */
public class BuildCarWalkNetworkFromOsm {

	public static void main(String[] args) {
		if (args.length < 2) {
			System.err.println("Usage: BuildCarWalkNetworkFromOsm <input.osm/pbf> <output_raw.xml[.gz]> [output_clean.xml[.gz]]");
			System.exit(1);
		}

		String input = args[0];
		String outputRaw = args[1];
		String outputClean = args.length > 2 ? args[2] : null;

		// Coordinate transform WGS84 -> TWD97 / EPSG:3826
		var ct = TransformationFactory.getCoordinateTransformation(TransformationFactory.WGS84, "EPSG:3826");

		// Start with default link properties, then override to ensure small paths are kept
		var props = new ConcurrentHashMap<>(LinkProperties.createLinkProperties());
		// Driveable small roads
		props.put("residential", new LinkProperties(LinkProperties.LEVEL_RESIDENTIAL, 1, 30.0 / 3.6, 1500, false));
		props.put("service", new LinkProperties(LinkProperties.LEVEL_RESIDENTIAL, 1, 20.0 / 3.6, 800, false));
		props.put("unclassified", new LinkProperties(LinkProperties.LEVEL_UNCLASSIFIED, 1, 30.0 / 3.6, 1200, false));
		props.put("living_street", new LinkProperties(LinkProperties.LEVEL_LIVING_STREET, 1, 10.0 / 3.6, 600, false));
		props.put("track", new LinkProperties(LinkProperties.LEVEL_PATH, 1, 20.0 / 3.6, 600, false));
		// Walk/bike-only links (kept for connectivity, car will be disallowed in hook)
		props.put("path", new LinkProperties(LinkProperties.LEVEL_PATH, 1, 5.0 / 3.6, 600, false));
		props.put("footway", new LinkProperties(LinkProperties.LEVEL_PATH, 1, 5.0 / 3.6, 600, false));
		props.put("pedestrian", new LinkProperties(LinkProperties.LEVEL_PATH, 1, 5.0 / 3.6, 600, false));
		props.put("steps", new LinkProperties(LinkProperties.LEVEL_PATH, 1, 2.0 / 3.6, 400, false));
		props.put("cycleway", new LinkProperties(LinkProperties.LEVEL_PATH, 1, 15.0 / 3.6, 800, false));

		// Sets for mode assignment
		Set<String> walkOnly = Set.of("footway", "path", "pedestrian", "steps", "cycleway");
		Set<String> driveable = new HashSet<>(Arrays.asList(
				"motorway", "motorway_link", "trunk", "trunk_link",
				"primary", "primary_link", "secondary", "secondary_link",
				"tertiary", "tertiary_link", "unclassified",
				"residential", "service", "living_street", "track"
		));

		SupersonicOsmNetworkReader reader = new SupersonicOsmNetworkReader.Builder()
				.setCoordinateTransformation(ct)
				// include all links; no bbox filtering here
				.setIncludeLinkAtCoordWithHierarchy((coord, level) -> true)
				.setLinkProperties(props)
				.setAfterLinkCreated((link, osmTags, isReverse) -> {
					String highway = osmTags.get("highway");
					Set<String> modes = new HashSet<>();
					// Walk allowed everywhere
					modes.add(TransportMode.walk);
					// Car allowed only on driveable classes
					if (highway != null && driveable.contains(highway)) {
						modes.add(TransportMode.car);
					}
					link.setAllowedModes(modes);
					// Keep key OSM tags for validation/debugging
					if (highway != null) {
						link.getAttributes().putAttribute("osm:way:highway", highway);
					}
					if (osmTags.containsKey("name")) {
						link.getAttributes().putAttribute("osm:way:name", osmTags.get("name"));
					}
					if (osmTags.containsKey("id")) {
						link.getAttributes().putAttribute("osm:way:id", osmTags.get("id"));
					}
				})
				.build();

		Network raw = reader.read(input);
		new NetworkWriter(raw).write(outputRaw);

		if (outputClean != null) {
			Network cleaned = NetworkUtils.createNetwork();
			new MatsimNetworkReader(cleaned).readFile(outputRaw);
			// clean on car+walk to drop isolated fragments
			new NetworkCleaner().run(cleaned);
			new NetworkWriter(cleaned).write(outputClean);
		}
	}
}
