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

## Configuration Reference

**IMPORTANT: Before modifying any scenario config files, always consult `defaultConfig.xml` first.**

The `defaultConfig.xml` file at the project root is the **complete reference** for all MATSim configuration options. It contains:
- All available configuration modules with their parameters
- Default values for each parameter
- Possible values and options (documented in comments)
- Parameter descriptions and usage notes

### Key Configuration Modules in defaultConfig.xml

1. **changeMode** - Mode choice behavior (car/pt switching)
2. **controller** - Simulation control (iterations: line 31, output settings: line 42-58, routing algorithm: line 46)
3. **global** - Global settings (coordinate system: line 106, threads: line 110, random seed: line 111)
4. **qsim** - Queue-based simulation engine (main congested modes: line 180, threads: line 186, stuck time: line 203)
5. **routing** - Routing configuration (network modes: line 242, teleported modes: lines 247-278)
6. **scoring** - Agent scoring parameters (travel time utilities: lines 401-460, activity types: lines 303-400)
7. **transit** - Public transport (routing algorithm: line 494, transit modes: line 498, schedule file: line 500)
8. **transitRouter** - PT routing (transfer time: line 511, max walk distance: line 517, search radius: line 519)

### Critical Parameters to Check Before Runs

When creating or modifying scenarios, verify these settings:
- **controller.lastIteration** (line 31) - Default: 1000 (very long for testing)
- **controller.outputDirectory** (line 42) - Avoid overwriting results
- **controller.overwriteFiles** (line 44) - Set to `deleteDirectoryIfExists` for iterative testing
- **global.coordinateSystem** (line 106) - Must match network/population CRS
- **routing.networkModes** (line 242) - Must include all simulated modes (car, pt, subway, etc.)
- **transit.useTransit** (line 504) - Must be `true` for PT scenarios
- **transit.transitModes** (line 498) - Define which modes are treated as transit

### Usage Pattern

```bash
# 1. Check defaultConfig.xml for available options
cat defaultConfig.xml | grep -A 5 "module name=\"controller\""

# 2. Create minimal scenario config with only required overrides
# 3. Reference defaultConfig.xml when troubleshooting parameters
```

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

## Common Issues & Best Practices

### Public Transit Simulation Errors

#### ClassCastException: TransitPassengerRoute cannot be cast to NetworkRoute

**Root Cause**: Code attempts to cast transit passenger routes to network routes (incompatible types).

**Why This Happens**:
- MATSim was originally designed for car-only simulations
- Activities (home, work) must be linked to network links
- PT agents still need access/egress trips (walking/driving to/from stations)
- **Missing ground network** causes routing failures even for PT-only scenarios

**Solutions**:

1. **Build Complete Multimodal Network** (Recommended)
   ```bash
   # Use Osm2MultimodalNetwork to create network with car, walk, rail modes
   java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
     org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
     input.osm output_network.xml config.xml
   ```

2. **Use Artificial Links** (PT-only network)
   ```xml
   <!-- In PT mapper config -->
   <module name="ptmapper">
     <param name="maxLinkCandidateDistance" value="0.0"/>
   </module>
   ```
   Creates independent PT network with dummy loop links (pt_ prefix).

3. **Configure Car as Teleported Mode** (if agents have car legs but network lacks car links)
   ```xml
   <module name="routing">
     <parameterset type="teleportedModeParameters">
       <param name="mode" value="car"/>
       <param name="teleportedModeSpeed" value="10.0"/>
       <param name="beelineDistanceFactor" value="1.3"/>
     </parameterset>
   </module>
   ```

### Network Mode Configuration

**Critical**: Ensure `routing.networkModes` matches actual network link modes:

```xml
<module name="routing">
  <!-- Must include ALL simulated network modes -->
  <param name="networkModes" value="car,bus,subway,pt"/>
</module>
```

Verify network contains these modes:
```bash
grep -o 'modes="[^"]*"' network.xml | sort | uniq -c
```

### Transit Configuration Checklist

Before running PT simulations, verify:

```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>

<module name="qsim">
  <param name="mainMode" value="car,pt"/>
  <param name="usingTransitInMobsim" value="true"/>
</module>
```

### Link Validation

Common warnings to fix:

1. **Zero-length links**:
   ```
   WARN LinkImpl:130 length=0.0 of link id pt_BL01_DN
   ```
   Fix: Set minimum length (e.g., 1.0m) for all links

2. **Insufficient capacity**:
   ```
   WARN QueueWithBuffer:504 Link too small: enlarge storage capacity
   ```
   Fix: Increase `capacity` attribute in network.xml or use `storageCapacityFactor` in config

### Population Plans Validation

Ensure all activity locations reference valid network links:

```xml
<person id="agent_01">
  <plan selected="yes">
    <!-- Link must exist in network.xml -->
    <activity type="home" link="81226" x="..." y="..." end_time="07:15:00"/>
    <leg mode="pt"/>
    <!-- Link must exist in network.xml -->
    <activity type="work" link="81226" x="..." y="..." end_time="17:30:00"/>
  </plan>
</person>
```

Validate with:
```bash
# Extract all link IDs from plans
grep -o 'link="[^"]*"' population.xml | sort -u > plan_links.txt
# Extract all link IDs from network
grep '<link id=' network.xml | grep -o 'id="[^"]*"' | sort -u > network_links.txt
# Compare
comm -23 plan_links.txt network_links.txt  # Links in plans but not in network
```

### Best Practices Summary

✅ **Always build multimodal networks** (car, walk, rail) even for PT-only scenarios
✅ **Check link modes** match routing configuration
✅ **Enable transit modules** (useTransit=true, usingTransitInMobsim=true)
✅ **Use teleportation** for non-critical modes to avoid routing failures
✅ **Validate link references** in population plans
✅ **Set realistic iterations** for testing (10-50, not 1000)
✅ **Use deleteDirectoryIfExists** to avoid output conflicts

❌ **Never import only rail tracks** without ground roads
❌ **Never force-cast route types** without type checking
❌ **Never forget transitVehicles.xml** when using PT
❌ **Never skip network mode validation**
❌ **Never use zero-length links**

## SwissRailRaptor Configuration for Sequential PT Routing

### Problem: PT Agents Using Straight-Line Transmission

**Symptom**: PT agents teleport directly from origin to destination, ignoring intermediate stops on the virtual PT network.

**Root Cause**: PT mode configured with `teleportedModeParameters` in routing module instead of using SwissRailRaptor algorithm.

### Solution: Remove PT from Teleported Modes

**❌ WRONG** - PT configured as teleported mode:
```xml
<module name="routing">
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="pt"/>
    <param name="teleportedModeSpeed" value="20.0"/>
  </parameterset>
</module>
```
Result: Direct transmission, no intermediate stops visited.

**✅ CORRECT** - PT routed through SwissRailRaptor:
```xml
<module name="routing">
  <!-- networkModes must NOT include "pt" -->
  <param name="networkModes" value="car" />
  <param name="accessEgressType" value="accessEgressModeToLink" />
  <param name="clearDefaultTeleportedModeParams" value="true" />

  <!-- Only walk modes use teleportation -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk" />
    <param name="teleportedModeSpeed" value="1.388888888" />
    <param name="beelineDistanceFactor" value="1.3" />
  </parameterset>
  <!-- access_walk, egress_walk, transit_walk follow -->
</module>

<!-- SwissRailRaptor handles PT routing -->
<module name="swissRailRaptor">
  <!-- Disable intermodal unless population plans support it -->
  <param name="useIntermodalAccessEgress" value="false" />

  <!-- Zero transfer penalties for direct path selection -->
  <param name="transferPenaltyBaseCost" value="0.0" />
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0" />

  <!-- No mode mapping for simple passenger routing -->
  <param name="useModeMappingForPassengers" value="false" />
</module>
```

### SwissRailRaptor Configuration Checklist

Before running simulations with PT:

- [ ] **PT NOT in routing.networkModes** → routing will use SwissRailRaptor
- [ ] **PT NOT in qsim.mainMode** → allows PT-only scenarios without network congestion
- [ ] **PT NOT in teleportedModeParameters** → critical to enable routing
- [ ] **transit.useTransit = true** → enables transit simulation
- [ ] **transit.usingTransitInMobsim = true** → PT vehicles operate in simulation
- [ ] **transit.routingAlgorithmType = "SwissRailRaptor"** → correct routing algorithm
- [ ] **Virtual network exists** → pt2matsim-generated network with links like `pt_STATION_UP`
- [ ] **Transit schedule complete** → all stops and departures defined
- [ ] **transitVehicles.xml** → capacity and vehicle definitions

### How SwissRailRaptor Works

1. **Input**: Agent wants to travel from stop A to stop B at time T
2. **Algorithm**: Finds shortest path considering:
   - Real departure/arrival times from schedule
   - Transfer penalties (configurable)
   - Multiple route options
3. **Output**: Agent uses actual transit route links, visiting every intermediate stop
4. **Validation**: Events show `PersonEntersVehicle` and `PersonLeavesVehicle` with stop facility IDs

### Verification

**Check event logs for correct PT routing**:
```bash
# Should see stops being visited in sequence
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "VehicleArrivesAtFacility\|VehicleDepartsAtFacility" | \
  grep "BL0[2-9]\|BL1[0-4]" | head -50

# Expected output (sequential):
# VehicleArrivesAtFacility at BL02_UP
# VehicleDepartsAtFacility from BL02_UP
# VehicleArrivesAtFacility at BL03_UP  ← intermediate stop
# VehicleDepartsAtFacility from BL03_UP
# VehicleArrivesAtFacility at BL04_UP  ← intermediate stop
# ...
# VehicleArrivesAtFacility at BL14_UP
# VehicleDepartsAtFacility from BL14_UP
```

✅ **Success**: All intermediate stops appear in sequence
❌ **Failure**: Only origin and destination appear, no intermediate stops
