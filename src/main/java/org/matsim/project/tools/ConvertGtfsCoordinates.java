package org.matsim.project.tools;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVPrinter;
import org.apache.commons.csv.CSVRecord;
import org.matsim.api.core.v01.Coord;
import org.matsim.core.utils.geometry.CoordinateTransformation;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;

/**
 * Converts GTFS stop or shape coordinates from WGS84 latitude/longitude to a projected CRS
 * (default: EPSG:3826) and appends the projected coordinates as additional columns.
 *
 * <p>Usage:
 * {@code java -cp <project-jar> org.matsim.project.tools.ConvertGtfsCoordinates <stops|shapes> <inputFile> <outputFile> [targetCRS]}
 */
public final class ConvertGtfsCoordinates {

	private static final DecimalFormat COORD_FORMAT;

	static {
		final DecimalFormatSymbols symbols = new DecimalFormatSymbols(Locale.US);
		COORD_FORMAT = new DecimalFormat("0.###", symbols);
	}

	private ConvertGtfsCoordinates() {
		// utility class
	}

	public static void main(final String[] args) throws Exception {
		if (args.length < 3) {
			System.err.println("Usage: ConvertGtfsCoordinates <stops|shapes> <inputFile> <outputFile> [targetCRS]");
			System.exit(1);
		}

		final GtfsType gtfsType = GtfsType.from(args[0]);
		final Path input = Paths.get(args[1]);
		final Path output = Paths.get(args[2]);
		final String targetCrs = args.length >= 4 ? args[3] : "EPSG:3826";

		if (!Files.isRegularFile(input)) {
			System.err.printf("Input file does not exist: %s%n", input);
			System.exit(2);
		}

		final Path parent = output.toAbsolutePath().getParent();
		if (Objects.nonNull(parent)) {
			Files.createDirectories(parent);
		}

		final CoordinateTransformation transformation = TransformationFactory.getCoordinateTransformation(
				TransformationFactory.WGS84, targetCrs);

		final String xColumn = appendCrsSuffix(gtfsType.xColumn(), targetCrs);
		final String yColumn = appendCrsSuffix(gtfsType.yColumn(), targetCrs);

		final CSVFormat inputFormat = CSVFormat.DEFAULT.builder()
				.setHeader()
				.setSkipHeaderRecord(true)
				.build();

		final List<String> header;
		final List<Map<String, String>> rows = new ArrayList<>();

		int converted = 0;
		int skipped = 0;

		try (BufferedReader reader = Files.newBufferedReader(input, StandardCharsets.UTF_8);
		     CSVParser parser = inputFormat.parse(reader)) {

			header = new ArrayList<>(parser.getHeaderNames());
			if (!header.contains(gtfsType.latColumn()) || !header.contains(gtfsType.lonColumn())) {
				System.err.printf("Required columns %s and %s missing in %s%n",
						gtfsType.latColumn(), gtfsType.lonColumn(), input);
				System.exit(3);
				return;
			}

			if (!header.contains(xColumn)) {
				header.add(xColumn);
			}
			if (!header.contains(yColumn)) {
				header.add(yColumn);
			}

			for (CSVRecord record : parser) {
				final Map<String, String> values = new HashMap<>(record.toMap());
				final String latRaw = record.get(gtfsType.latColumn());
				final String lonRaw = record.get(gtfsType.lonColumn());
				try {
					final double lat = Double.parseDouble(latRaw);
					final double lon = Double.parseDouble(lonRaw);
					final Coord projected = transformation.transform(new Coord(lon, lat));
					values.put(xColumn, COORD_FORMAT.format(projected.getX()));
					values.put(yColumn, COORD_FORMAT.format(projected.getY()));
					converted++;
				} catch (RuntimeException ex) {
					skipped++;
					values.put(xColumn, "");
					values.put(yColumn, "");
				}
				rows.add(values);
			}
		}

		final CSVFormat outputFormat = CSVFormat.DEFAULT.builder()
				.setHeader(header.toArray(String[]::new))
				.build();

		try (BufferedWriter writer = Files.newBufferedWriter(output, StandardCharsets.UTF_8);
		     CSVPrinter printer = new CSVPrinter(writer, outputFormat)) {
			for (Map<String, String> row : rows) {
				final List<String> record = new ArrayList<>(header.size());
				for (String column : header) {
					record.add(row.getOrDefault(column, ""));
				}
				printer.printRecord(record);
			}
		}

		System.out.printf(Locale.US,
				"Converted %d rows from %s to %s (skipped %d rows) -> %s%n",
				converted, input, targetCrs, skipped, output);
	}

	private static String appendCrsSuffix(final String base, final String targetCrs) {
		final String suffix = targetCrs.toUpperCase(Locale.ROOT).replaceAll("[^A-Z0-9]", "");
		return base + "_" + suffix;
	}

	private enum GtfsType {
		STOPS("stop_lat", "stop_lon", "stop_x", "stop_y"),
		SHAPES("shape_pt_lat", "shape_pt_lon", "shape_pt_x", "shape_pt_y");

		private final String latColumn;
		private final String lonColumn;
		private final String xColumn;
		private final String yColumn;

		GtfsType(final String latColumn, final String lonColumn, final String xColumn, final String yColumn) {
			this.latColumn = latColumn;
			this.lonColumn = lonColumn;
			this.xColumn = xColumn;
			this.yColumn = yColumn;
		}

		public String latColumn() {
			return latColumn;
		}

		public String lonColumn() {
			return lonColumn;
		}

		public String xColumn() {
			return xColumn;
		}

		public String yColumn() {
			return yColumn;
		}

		public static GtfsType from(final String raw) {
			return switch (raw.toLowerCase(Locale.ROOT)) {
				case "stops" -> STOPS;
				case "shapes" -> SHAPES;
				default -> throw new IllegalArgumentException(
						"Unknown GTFS type: " + raw + ". Expected 'stops' or 'shapes'.");
			};
		}
	}
}
