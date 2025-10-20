package org.matsim.project.tools;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.misc.OptionalTime;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitRouteStop;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitScheduleFactory;
import org.matsim.pt.transitSchedule.api.TransitScheduleReader;
import org.matsim.pt.transitSchedule.api.TransitScheduleWriter;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.vehicles.MatsimVehicleReader;
import org.matsim.vehicles.MatsimVehicleWriter;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleType;
import org.matsim.vehicles.VehicleUtils;
import org.matsim.vehicles.Vehicles;
import org.matsim.vehicles.VehiclesFactory;
import org.matsim.utils.objectattributes.attributable.AttributesUtils;

/**
 * Utility to merge multiple MATSim transit schedules (e.g. GTFS conversions) into one schedule and
 * create a matching vehicles file.
 *
 * <p>Usage:
 * {@code java -cp <project-jar> org.matsim.project.tools.MergeGtfsSchedules <outputSchedule> <outputVehicles> <schedule1> [<schedule2> ...]}
 */
public final class MergeGtfsSchedules {

	private MergeGtfsSchedules() {
		// utility class
	}

	public static void main(final String[] args) {
		if (args.length < 6 || (args.length - 2) % 2 != 0) {
			System.err.println("Usage: MergeGtfsSchedules <outputSchedule> <outputVehicles> <schedule1> <vehicles1> <schedule2> <vehicles2> [<scheduleN> <vehiclesN>]");
			System.exit(1);
		}

		final Path outputSchedule = Paths.get(args[0]);
		final Path outputVehicles = Paths.get(args[1]);
		final List<Path> scheduleInputs = new ArrayList<>();
		final List<Path> vehicleInputs = new ArrayList<>();
		for (int i = 2; i < args.length; i += 2) {
			final Path schedulePath = Paths.get(args[i]);
			final Path vehiclesPath = Paths.get(args[i + 1]);
			scheduleInputs.add(schedulePath);
			vehicleInputs.add(vehiclesPath);
		}

		scheduleInputs.stream()
				.filter(path -> !Files.isRegularFile(path))
				.findFirst()
				.ifPresent(path -> {
					System.err.printf("Input schedule file not found: %s%n", path);
					System.exit(2);
				});

		vehicleInputs.stream()
				.filter(path -> !Files.isRegularFile(path))
				.findFirst()
				.ifPresent(path -> {
					System.err.printf("Input vehicles file not found: %s%n", path);
					System.exit(3);
				});

		final Path scheduleDir = outputSchedule.toAbsolutePath().getParent();
		final Path vehiclesDir = outputVehicles.toAbsolutePath().getParent();
		try {
			if (Objects.nonNull(scheduleDir)) {
				Files.createDirectories(scheduleDir);
			}
			if (Objects.nonNull(vehiclesDir)) {
				Files.createDirectories(vehiclesDir);
			}
		} catch (final Exception e) {
			System.err.printf("Failed to create output directories: %s%n", e.getMessage());
			System.exit(4);
		}

		final Config mergedConfig = ConfigUtils.createConfig();
		final Scenario mergedScenario = ScenarioUtils.createScenario(mergedConfig);
		final TransitSchedule mergedSchedule = mergedScenario.getTransitSchedule();
		final Vehicles mergedVehicles = mergedScenario.getTransitVehicles();

		for (int i = 0; i < scheduleInputs.size(); i++) {
			final Path schedulePath = scheduleInputs.get(i);
			final Path vehiclesPath = vehicleInputs.get(i);

			final Config feedConfig = ConfigUtils.createConfig();
			final Scenario feedScenario = ScenarioUtils.createScenario(feedConfig);
			new TransitScheduleReader(feedScenario).readFile(schedulePath.toString());
			new MatsimVehicleReader(feedScenario.getTransitVehicles()).readFile(vehiclesPath.toString());

			final String prefix = derivePrefix(schedulePath, i);
			mergeFeed(mergedSchedule, mergedVehicles, feedScenario.getTransitSchedule(), feedScenario.getTransitVehicles(), prefix);
		}

		new TransitScheduleWriter(mergedSchedule).writeFile(outputSchedule.toString());
		new MatsimVehicleWriter(mergedVehicles).writeFile(outputVehicles.toString());
	}

	private static void mergeFeed(final TransitSchedule targetSchedule, final Vehicles targetVehicles,
			final TransitSchedule sourceSchedule, final Vehicles sourceVehicles, final String prefix) {
		final TransitScheduleFactory scheduleFactory = targetSchedule.getFactory();
		final VehiclesFactory vehiclesFactory = targetVehicles.getFactory();

		final Map<Id<TransitStopFacility>, TransitStopFacility> stopMapping = new HashMap<>();
		sourceSchedule.getFacilities().values().forEach(stop -> {
			final Id<TransitStopFacility> newId = Id.create(prefix + "_" + stop.getId(), TransitStopFacility.class);
			final TransitStopFacility newStop = scheduleFactory.createTransitStopFacility(newId, stop.getCoord(), stop.getIsBlockingLane());
			newStop.setName(stop.getName());
			newStop.setLinkId(stop.getLinkId());
			AttributesUtils.copyAttributesFromTo(stop, newStop);
			targetSchedule.addStopFacility(newStop);
			stopMapping.put(stop.getId(), newStop);
		});

		final Map<Id<VehicleType>, VehicleType> vehicleTypeMapping = new HashMap<>();
		sourceVehicles.getVehicleTypes().values().forEach(type -> {
			final Id<VehicleType> newTypeId = Id.create(prefix + "_" + type.getId(), VehicleType.class);
			final VehicleType newType = vehiclesFactory.createVehicleType(newTypeId);
			VehicleUtils.copyFromTo(type, newType);
			AttributesUtils.copyAttributesFromTo(type, newType);
			targetVehicles.addVehicleType(newType);
			vehicleTypeMapping.put(type.getId(), newType);
		});

		final Map<Id<Vehicle>, Id<Vehicle>> vehicleIdMapping = new HashMap<>();
		sourceVehicles.getVehicles().values().forEach(vehicle -> {
			final Id<Vehicle> newVehicleId = Id.create(prefix + "_" + vehicle.getId(), Vehicle.class);
			final VehicleType mappedType = vehicleTypeMapping.get(vehicle.getType().getId());
			final Vehicle newVehicle = vehiclesFactory.createVehicle(newVehicleId, mappedType);
			AttributesUtils.copyAttributesFromTo(vehicle, newVehicle);
			targetVehicles.addVehicle(newVehicle);
			vehicleIdMapping.put(vehicle.getId(), newVehicleId);
		});

		sourceSchedule.getTransitLines().values().forEach(line -> {
			final Id<TransitLine> newLineId = Id.create(prefix + "_" + line.getId(), TransitLine.class);
			final TransitLine newLine = scheduleFactory.createTransitLine(newLineId);
			newLine.setName(line.getName());
			AttributesUtils.copyAttributesFromTo(line, newLine);
			targetSchedule.addTransitLine(newLine);

			line.getRoutes().values().forEach(route -> {
				final Id<TransitRoute> newRouteId = Id.create(prefix + "_" + route.getId(), TransitRoute.class);
				final List<TransitRouteStop> newStops = new ArrayList<>(route.getStops().size());
				for (TransitRouteStop stop : route.getStops()) {
					final TransitStopFacility mappedStop = stopMapping.get(stop.getStopFacility().getId());
					final OptionalTime arrival = stop.getArrivalOffset();
					final OptionalTime departure = stop.getDepartureOffset();
					final TransitRouteStop newStop = scheduleFactory.createTransitRouteStop(mappedStop, arrival, departure);
					newStop.setAllowBoarding(stop.isAllowBoarding());
					newStop.setAllowAlighting(stop.isAllowAlighting());
					newStop.setAwaitDepartureTime(stop.isAwaitDepartureTime());
					newStops.add(newStop);
				}

				final NetworkRoute networkRoute = route.getRoute();
				final TransitRoute newRoute = scheduleFactory.createTransitRoute(newRouteId, networkRoute, newStops, route.getTransportMode());
				newRoute.setDescription(route.getDescription());
				AttributesUtils.copyAttributesFromTo(route, newRoute);
				newLine.addRoute(newRoute);

				route.getDepartures().values().forEach(departure -> {
					final Id<Departure> newDepartureId = Id.create(prefix + "_" + departure.getId(), Departure.class);
					final Departure newDeparture = scheduleFactory.createDeparture(newDepartureId, departure.getDepartureTime());
					AttributesUtils.copyAttributesFromTo(departure, newDeparture);
					final Id<Vehicle> vehicleId = departure.getVehicleId();
					if (vehicleId != null) {
						final Id<Vehicle> mappedVehicleId = vehicleIdMapping.get(vehicleId);
						if (mappedVehicleId != null) {
							newDeparture.setVehicleId(mappedVehicleId);
						}
					}
					newRoute.addDeparture(newDeparture);
				});
			});
		});
	}

	private static String derivePrefix(final Path schedulePath, final int index) {
		final Path parent = schedulePath.getParent();
		final String candidate = parent != null ? parent.getFileName().toString() : schedulePath.getFileName().toString();
		final String sanitized = candidate.replaceAll("[^A-Za-z0-9]", "_");
		final String base = sanitized.isBlank() ? "feed" + index : sanitized;
		return base;
	}
}
