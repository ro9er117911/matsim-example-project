package org.matsim.project.tools;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitRouteStop;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitScheduleReader;
import org.matsim.pt.transitSchedule.api.TransitScheduleWriter;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.pt2matsim.run.Gtfs2TransitSchedule;

/**
 * Convert a GTFS feed (zip) into MATSim transitSchedule and transitVehicles files.
 * Additionally creates a simple population if none exists inside the output directory.
 */
public final class GtfsToMatsim {

	private GtfsToMatsim() {
	}

	public static void main(final String[] args) throws Exception {
		final Arguments arguments = Arguments.parse(args);

		final Path gtfsZip = arguments.gtfsZip;
		final Path networkPath = arguments.network;
		final Path outDir = arguments.outDir;
		final String targetCrs = arguments.targetCrs;

		validateFile(gtfsZip, "GTFS zip");
		validateFile(networkPath, "Network file");
		Files.createDirectories(outDir);

		try (ZipInputStream zis = new ZipInputStream(Files.newInputStream(gtfsZip))) {
			ZipEntry entry = zis.getNextEntry();
			if (entry == null) {
				throw new IllegalArgumentException("GTFS zip is empty: " + gtfsZip);
			}
		}

		Path tempDirectory = Files.createTempDirectory("gtfs-" + UUID.randomUUID());
		try {
			unzip(gtfsZip, tempDirectory);

			Path scheduleOut = outDir.resolve("transitSchedule.xml");
			Path vehiclesOut = outDir.resolve("transitVehicles.xml");

			Gtfs2TransitSchedule.run(
					tempDirectory.toString(),
					arguments.sampleSelector,
					targetCrs,
					scheduleOut.toString(),
					vehiclesOut.toString(),
					null);

			String networkFileName = networkPath.getFileName().toString();
			String networkTargetName = networkFileName.endsWith(".gz") ? "network.xml.gz" : "network.xml";
			Files.copy(networkPath, outDir.resolve(networkTargetName), java.nio.file.StandardCopyOption.REPLACE_EXISTING);

			Path populationPath = outDir.resolve("population.xml");
			if (Files.notExists(populationPath)) {
				createSamplePopulation(scheduleOut, targetCrs, populationPath);
			}

			System.out.printf(Locale.US,
					"[INFO] Conversion complete.%n  schedule=%s%n  vehicles=%s%n  network=%s%n  population=%s%n",
					scheduleOut, vehiclesOut, outDir.resolve(networkTargetName), populationPath);
		} finally {
			deleteDirectoryRecursively(tempDirectory);
		}
	}

	private static void createSamplePopulation(Path scheduleFile, String crs, Path populationPath) {
		Config config = ConfigUtils.createConfig();
		config.global().setCoordinateSystem(crs);
		Scenario scenario = ScenarioUtils.createScenario(config);
		new TransitScheduleReader(scenario).readFile(scheduleFile.toString());
		TransitSchedule schedule = scenario.getTransitSchedule();

		TransitStopFacility homeStop = schedule.getFacilities().values().iterator().next();
		TransitStopFacility workStop = schedule.getFacilities().values().stream()
				.skip(schedule.getFacilities().size() > 1 ? 1 : 0)
				.findFirst()
				.orElse(homeStop);

		double departureTime = 8 * 3600;
		for (int i = 0; i < 100; i++) {
			Person person = scenario.getPopulation().getFactory().createPerson(Id.createPersonId(i));
			Plan plan = scenario.getPopulation().getFactory().createPlan();

			Activity home = PopulationUtils.createActivityFromCoord("h", toCoord(homeStop));
			home.setEndTime(departureTime + 60 * i);
			plan.addActivity(home);

			Leg leg = PopulationUtils.createLeg("pt");
			plan.addLeg(leg);

			Activity work = PopulationUtils.createActivityFromCoord("w", toCoord(workStop));
			work.setEndTime(departureTime + 8 * 3600 + 60 * i);
			plan.addActivity(work);

			Leg legBack = PopulationUtils.createLeg("pt");
			plan.addLeg(legBack);

			Activity homeReturn = PopulationUtils.createActivityFromCoord("h", toCoord(homeStop));
			plan.addActivity(homeReturn);

			person.addPlan(plan);
			scenario.getPopulation().addPerson(person);
		}

		PopulationUtils.writePopulation(scenario.getPopulation(), populationPath.toString());
	}

	private static Coord toCoord(TransitStopFacility stop) {
		return stop.getCoord();
	}

	private static void unzip(Path zip, Path targetDir) throws IOException {
		try (ZipInputStream zis = new ZipInputStream(Files.newInputStream(zip))) {
			ZipEntry entry;
			while ((entry = zis.getNextEntry()) != null) {
				if (entry.isDirectory()) {
					continue;
				}
				Path outPath = targetDir.resolve(entry.getName());
				Files.createDirectories(outPath.getParent());
				Files.copy(zis, outPath);
			}
		}
	}

	private static void deleteDirectoryRecursively(Path dir) throws IOException {
		if (Files.notExists(dir)) {
			return;
		}
		Files.walk(dir)
				.sorted((a, b) -> b.compareTo(a))
				.forEach(path -> {
					try {
						Files.deleteIfExists(path);
					} catch (IOException ignored) {
					}
				});
	}

	private static void validateFile(Path path, String label) {
		if (Files.notExists(path)) {
			throw new IllegalArgumentException(label + " not found: " + path);
		}
	}

	private static final class Arguments {
		final Path gtfsZip;
		final Path network;
		final Path outDir;
		final String targetCrs;
		final String sampleSelector;

		private Arguments(Path gtfsZip, Path network, Path outDir, String targetCrs, String sampleSelector) {
			this.gtfsZip = gtfsZip;
			this.network = network;
			this.outDir = outDir;
			this.targetCrs = targetCrs;
			this.sampleSelector = sampleSelector;
		}

		static Arguments parse(String[] args) {
			Path gtfsZip = null;
			Path network = null;
			Path outDir = null;
			String targetCrs = "EPSG:3826";
			String sampleSelector = "dayWithMostTrips";

			for (int i = 0; i < args.length; i++) {
				switch (args[i]) {
					case "--gtfsZip" -> gtfsZip = Paths.get(args[++i]);
					case "--network" -> network = Paths.get(args[++i]);
					case "--outDir" -> outDir = Paths.get(args[++i]);
					case "--targetCRS" -> targetCrs = args[++i];
					case "--sample" -> sampleSelector = args[++i];
					default -> throw new IllegalArgumentException("Unknown argument: " + args[i]);
				}
			}

			if (gtfsZip == null || network == null || outDir == null) {
				throw new IllegalArgumentException(
						"Usage: --gtfsZip <path> --network <path> --outDir <dir> [--targetCRS EPSG:3826] [--sample dayWithMostTrips]");
			}

			return new Arguments(gtfsZip, network, outDir, targetCrs, sampleSelector);
		}
	}
}
