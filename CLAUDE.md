# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MATSim (Multi-Agent Transport Simulation) project for modeling urban transportation systems. It uses Java 21 with Maven and MATSim version 2025.0.

## Build & Test Commands

```bash
# Build the shaded executable jar
./mvnw clean package

# Run all tests
./mvnw test

# Run a specific test class
./mvnw test -Dtest=RunMatsimTest

# Clean build artifacts
./mvnw clean
```

## Running Simulations

```bash
# Launch MATSim GUI (after building)
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# Run simulation with specific config
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml

# Run with increased memory (for large scenarios)
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml

# Run specific main class directly
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" -Dexec.args="scenarios/equil/config_min.xml"
```

## Architecture

### Entry Points

The project provides multiple ways to run MATSim simulations:

1. **RunMatsim.java** - Basic entry point with manual Config/Scenario/Controler setup. Loads config, creates scenario, and runs simulation with three customization hooks (config, scenario, controler).

2. **RunMatsimApplication.java** - Modern entry point extending `MATSimApplication` with CLI support via picocli. Uses template method pattern with `prepareConfig()`, `prepareScenario()`, and `prepareControler()` hooks.

3. **RunMatsimFromExamplesUtils.java** - Uses MATSim built-in example scenarios for testing.

All three follow the same three-phase pattern: Config → Scenario → Controler customization.

### Public Transit Workflow

The project includes a complete GTFS-to-MATSim pipeline in `src/main/java/org/matsim/project/tools/`:

1. **GtfsToMatsim** - Main converter: GTFS zip → MATSim transitSchedule + transitVehicles. Uses vendored pt2matsim library (`pt2matsim/work/pt2matsim-25.8-shaded.jar`). Auto-generates sample population if needed.

2. **ConvertGtfsCoordinates** - Transforms GTFS stop coordinates between CRS systems.

3. **MergeGtfsSchedules** - Merges multiple MATSim transit schedules into one.

4. **PreRoutePt** - Pre-routes PT legs in population plans.

5. **OsmPbfToXml** - Converts OSM PBF to XML format.

6. **PrepareNetworkForPTMapping** - Cleans and prepares network for PT mapping by ensuring all subway links have 'pt' mode and running NetworkUtils.cleanNetwork().

7. **CleanSubwayNetwork** - Extracts and cleans subway-only network from multimodal network.

The pt2matsim dependency is vendored as a system-scoped JAR because it's not available in Maven Central.

#### PT Mapping with pt2matsim

The `pt2matsim-25.8-shaded.jar` includes several useful tools accessible via `-cp`:

```bash
# Create default PT mapper config
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig config.xml

# Run PT mapping (maps transit schedule to network)
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper config.xml

# Check mapped schedule plausibility
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  network.xml.gz transitSchedule.xml.gz
```

**Key PT Mapping Parameters** (in config.xml):
- `maxLinkCandidateDistance`: Max distance (m) from stop to candidate link (default: 90m, metro: 300m+)
- `nLinkThreshold`: Number of link candidates per stop (default: 6, metro: 10-12)
- `maxTravelCostFactor`: Multiplier for travel cost before creating artificial link (default: 5.0, increase to 15.0+ for difficult networks)
- `candidateDistanceMultiplier`: Expands search after N candidates found (default: 1.6, increase to 3.0+ for sparse networks)
- `networkRouter`: Router algorithm - `SpeedyALT` (fast) or `AStarLandmarks` (robust for disconnected networks)
- `modeSpecificRules`: Enable mode-specific parameters (subway, rail, tram, bus)

**Common Issues**:
- "Network is not connected" warnings → Use PrepareNetworkForPTMapping tool first
- Too many artificial links → Increase maxLinkCandidateDistance and maxTravelCostFactor
- Slow mapping → Reduce network size, increase numOfThreads, or use SpeedyALT router

### Testing Structure

Tests use JUnit 5 (Jupiter) with MATSim's `MatsimTestUtils`:
- Integration test in `RunMatsimTest` compares output plans and events against reference files
- Uses MATSim's built-in `ExamplesUtils.getTestScenarioURL("equil")` for test scenarios
- Validates both population scores and events files for regression testing

### Scenario Structure

Scenarios live in `scenarios/` with subdirectories per scenario:
- **equil/** - Example equilibrium scenario with minimal config/network/population
- **corridor/** - Custom corridor scenario (e.g., taipei_test)

Each scenario contains:
- `config.xml` or `config_min.xml` - MATSim configuration
- `network.xml` or `network_min.xml` - Road/transit network
- `population.xml` or `population_min.xml` - Agents and their plans
- `transitSchedule.xml` - PT schedules (if applicable)
- `transitVehicles.xml` - PT vehicles (if applicable)
- `output/` - Simulation results (created during runs)

## Critical Data Handling Rules

**NEVER read large scenario/output files without explicit user request.** These files can be hundreds of MB:

### High-Risk Directories
- `pt2matsim/data/` - Raw GTFS feeds, OSM data
- `pt2matsim/out/` - Converted transit schedules, networks
- `scenarios/*/` - Network, population, schedule XML files (often gzipped)
- `output/` - Simulation outputs (events, plans, statistics)
- `original-input-data/` - Raw source data

### High-Risk File Patterns
- `*.xml.gz` - Compressed MATSim data (network, population, events, plans, schedules)
- `*.xml` in scenarios/ or output/ - Uncompressed MATSim data
- `*.osm`, `*.pbf` - OpenStreetMap data
- GTFS files (stops.txt, routes.txt, etc.)
- `*events.xml*` - Event logs (extremely large)

### Safe Alternatives
Instead of reading files directly:
- Use `ls -lh` to check file sizes
- Use `zcat file.xml.gz | head -50` for compressed files
- Use `head -50 file.xml` for uncompressed files
- Ask user which specific elements to examine
- Use `grep` or `rg` with specific patterns

## Dependencies & Modules

This project uses MATSim contrib modules (all automatically included):
- **Core MATSim** - Base simulation framework
- **pt2matsim** - GTFS conversion (vendored at `pt2matsim/work/pt2matsim-25.8-shaded.jar`)
- **application** - CLI framework via MATSimApplication
- **otfvis** - Visualization (can be enabled in Controler)
- **simwrapper** - Modern web-based visualization (can be enabled in Controler)
- **minibus**, **noise**, **roadpricing**, **taxi**, **av**, **freight**, **bicycle**, **emissions**, **analysis**, **vsp** - Various transport modeling extensions

OSM processing via osmosis (0.49.2) and Apache Commons CSV (1.11.0) are also available.

## Configuration Patterns

MATSim configs use XML with module-based settings. Override via:

**Command-line:**
```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.lastIteration 100 \
  --config:controller.outputDirectory ./my-output
```

**In code (prepareConfig):**
```java
config.controller().setLastIteration(100);
config.controller().setOverwriteFileSetting(OverwriteFileSetting.deleteDirectoryIfExists);
```

Default CRS for this project: `EPSG:3826` (TWD97 / TM2 zone 121, Taiwan).

## Common Modifications

### Enable Visualization
Uncomment in `RunMatsim.java` or `RunMatsimApplication.java`:
```java
controler.addOverridingModule(new OTFVisLiveModule());  // Live visualization
controler.addOverridingModule(new SimWrapperModule());   // Web dashboard
```

### Adjust Iterations
In config.xml: `<module name="controller"><param name="lastIteration" value="10" /></module>`

Or CLI: `--config:controller.lastIteration 10`

### Change Output Directory
Always use `OverwriteFileSetting.deleteDirectoryIfExists` in code, or set via config.
