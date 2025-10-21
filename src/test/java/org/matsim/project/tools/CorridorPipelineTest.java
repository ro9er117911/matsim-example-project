package org.matsim.project.tools;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertEquals;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.stream.Collectors;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitRouteStop;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitScheduleReader;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.pt2matsim.run.Gtfs2TransitSchedule;
import org.matsim.pt2matsim.run.PublicTransitMapper;

class CorridorPipelineTest {

	private static final double X_MIN = 303_600;
	private static final double X_MAX = 305_200;
	private static final double Y_MIN = 2_770_350;
	private static final double Y_MAX = 2_770_900;

	@TempDir
	Path tempDir;

	@Test
	void gtfsConversionProducesCorridorSchedule() throws Exception {
		Path gtfsDir = copyResourceDirectory("gtfs/bl_corridor");

		Path scheduleOut = tempDir.resolve("transitSchedule-unmapped.xml.gz");
		Path vehiclesOut = tempDir.resolve("transitVehicles.xml.gz");

		Gtfs2TransitSchedule.run(
				gtfsDir.toString(),
				"dayWithMostTrips",
				"EPSG:3826",
				scheduleOut.toString(),
				vehiclesOut.toString(),
				null);

		assertAll(
				() -> assertTrue(Files.exists(scheduleOut), "Schedule output should exist"),
				() -> assertTrue(Files.exists(vehiclesOut), "Vehicles output should exist")
		);

		TransitSchedule schedule = readSchedule(scheduleOut);
		assertEquals(2, schedule.getTransitLines().size(), "Expected two transit lines (metro + bus)");

		assertEquals(6, schedule.getFacilities().size(), "Expected six stops in corridor");
		for (TransitStopFacility stop : schedule.getFacilities().values()) {
			assertWithinCorridor(stop.getCoord().getX(), stop.getCoord().getY());
		}

		for (TransitLine line : schedule.getTransitLines().values()) {
			assertEquals(2, line.getRoutes().size(), "Each line should have one trip per direction");
			for (TransitRoute route : line.getRoutes().values()) {
				assertTrue(route.getStops().size() >= 2, "Route should include at least two stops");
				route.getStops().forEach(stop -> assertWithinCorridor(
						stop.getStopFacility().getCoord().getX(),
						stop.getStopFacility().getCoord().getY()));
				route.getDepartures().values().forEach(dep -> assertNotNull(dep.getDepartureTime()));
			}
		}
	}

	@Test
	void publicTransitMapperMapsCorridorStopsToLinks() throws Exception {
		Path gtfsDir = copyResourceDirectory("gtfs/bl_corridor");
		Path scheduleUnmapped = tempDir.resolve("transitSchedule-unmapped.xml.gz");
		Path vehicles = tempDir.resolve("transitVehicles.xml.gz");

		Gtfs2TransitSchedule.run(
				gtfsDir.toString(),
				"dayWithMostTrips",
				"EPSG:3826",
				scheduleUnmapped.toString(),
				vehicles.toString(),
				null);

		Path network = copyResourceFile("network/bl_corridor_network.xml");
		Path scheduleMapped = tempDir.resolve("transitSchedule-mapped.xml.gz");
		Path networkMapped = tempDir.resolve("network-mapped.xml.gz");

		Path configFile = tempDir.resolve("ptmapper-config.xml");
		writePtMapperConfig(configFile, network, scheduleUnmapped, scheduleMapped, networkMapped);

		PublicTransitMapper.run(configFile.toString());

		assertAll(
				() -> assertTrue(Files.exists(scheduleMapped), "Mapped schedule should exist"),
				() -> assertTrue(Files.exists(networkMapped), "Mapped network should exist")
		);

		TransitSchedule mappedSchedule = readSchedule(scheduleMapped);
		for (TransitLine line : mappedSchedule.getTransitLines().values()) {
			for (TransitRoute route : line.getRoutes().values()) {
				assertTrue(route.getStops().size() >= 2, "Mapped route should contain at least two stops");
				for (TransitRouteStop stop : route.getStops()) {
					assertAll(
							() -> assertNotNull(stop.getStopFacility().getLinkId(), "Stop should be linked"),
							() -> assertWithinCorridor(
									stop.getStopFacility().getCoord().getX(),
									stop.getStopFacility().getCoord().getY())
					);
				}
				for (Departure departure : route.getDepartures().values()) {
					assertNotNull(departure.getVehicleId(), "Departure should have vehicle");
				}
			}
		}
	}

	private TransitSchedule readSchedule(Path scheduleFile) {
		Config config = ConfigUtils.createConfig();
		config.global().setCoordinateSystem("EPSG:3826");
		Scenario scenario = ScenarioUtils.createScenario(config);
		new TransitScheduleReader(scenario).readFile(scheduleFile.toString());
		return scenario.getTransitSchedule();
	}

	private void assertWithinCorridor(double x, double y) {
		assertTrue(
				x >= X_MIN && x <= X_MAX,
				String.format(Locale.ENGLISH, "x=%.3f outside corridor [%f,%f]", x, X_MIN, X_MAX));
		assertTrue(
				y >= Y_MIN && y <= Y_MAX,
				String.format(Locale.ENGLISH, "y=%.3f outside corridor [%f,%f]", y, Y_MIN, Y_MAX));
	}

	private Path copyResourceDirectory(String resourceRoot) throws IOException {
		Path targetDir = tempDir.resolve(resourceRoot.substring(resourceRoot.lastIndexOf('/') + 1));
		Files.createDirectories(targetDir);

		try (InputStream indexStream = getRequiredResource(resourceRoot + "/index.txt")) {
			List<String> files = new BufferedReader(new InputStreamReader(indexStream))
					.lines()
					.filter(line -> !line.isBlank())
					.collect(Collectors.toList());
			for (String file : files) {
				copyResourceFile(resourceRoot + "/" + file, targetDir.resolve(file));
			}
		}
		return targetDir;
	}

	private Path copyResourceFile(String resourcePath) throws IOException {
		Path target = tempDir.resolve(resourcePath.substring(resourcePath.lastIndexOf('/') + 1));
		return copyResourceFile(resourcePath, target);
	}

	private Path copyResourceFile(String resourcePath, Path target) throws IOException {
		try (InputStream stream = getRequiredResource(resourcePath)) {
			Files.createDirectories(target.getParent());
			Files.copy(stream, target);
		}
		return target;
	}

	private InputStream getRequiredResource(String resourcePath) {
		InputStream stream = getClass().getClassLoader().getResourceAsStream(resourcePath);
		return Objects.requireNonNull(stream, () -> "Resource not found: " + resourcePath);
	}

	private void writePtMapperConfig(Path configFile,
			Path network,
			Path schedule,
			Path scheduleOut,
			Path networkOut) throws IOException {

		String content = """
				<?xml version="1.0" encoding="UTF-8"?>
				<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
				<config>
					<module name="PublicTransitMapping">
						<param name="inputNetworkFile" value="%s" />
						<param name="inputScheduleFile" value="%s" />
						<param name="outputNetworkFile" value="%s" />
						<param name="outputScheduleFile" value="%s" />
						<param name="maxLinkCandidateDistance" value="200.0" />
						<param name="candidateDistanceMultiplier" value="1.3" />
						<param name="nLinkThreshold" value="4" />
						<param name="routingWithCandidateDistance" value="true" />
						<param name="modeSpecificRules" value="true" />
						<param name="numOfThreads" value="1" />
						<param name="modesToKeepOnCleanUp" value="subway" />
						<param name="travelCostType" value="linkLength" />
						<parameterset type="transportModeAssignment">
							<param name="scheduleMode" value="subway" />
							<param name="networkModes" value="pt,subway" />
							<param name="maxLinkCandidateDistance" value="200.0" />
							<param name="nLinkThreshold" value="4" />
							<param name="strictLinkRule" value="false" />
						</parameterset>
					</module>
				</config>
				""".formatted(
				network.toString(),
				schedule.toString(),
				networkOut.toString(),
				scheduleOut.toString());

		Files.writeString(configFile, content);
	}
}
