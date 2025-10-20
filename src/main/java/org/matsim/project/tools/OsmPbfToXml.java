package org.matsim.project.tools;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Objects;

import org.openstreetmap.osmosis.core.Osmosis;

/**
 * Minimal wrapper around Osmosis to convert an OSM PBF extract into plain OSM XML.
 *
 * <p>Usage: {@code java -cp <project-jar> org.matsim.project.tools.OsmPbfToXml <input.pbf> <output.osm>}
 */
public final class OsmPbfToXml {

	private OsmPbfToXml() {
		// utility class
	}

	public static void main(final String[] args) {
		if (args.length != 2) {
			System.err.println("Usage: OsmPbfToXml <input.osm.pbf> <output.osm>");
			System.exit(1);
		}

		final Path input = Paths.get(args[0]);
		final Path output = Paths.get(args[1]);

		if (!Files.isRegularFile(input)) {
			System.err.printf("Input file does not exist or is not a file: %s%n", input);
			System.exit(2);
		}

		final Path parent = output.toAbsolutePath().getParent();
		if (Objects.nonNull(parent)) {
			try {
				Files.createDirectories(parent);
			} catch (final Exception e) {
				System.err.printf("Failed to create output directory %s: %s%n", parent, e.getMessage());
				System.exit(3);
			}
		}

		final String[] osmosisArgs = {
				"--read-pbf", "file=" + input.toAbsolutePath(),
				"--write-xml", "file=" + output.toAbsolutePath()
		};

		try {
			Osmosis.run(osmosisArgs);
		} catch (final RuntimeException e) {
			System.err.printf("Conversion failed: %s%n", e.getMessage());
			e.printStackTrace(System.err);
			System.exit(4);
		}
	}
}
