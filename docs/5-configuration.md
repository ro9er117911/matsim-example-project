# Configuration Reference

## Overview

MATSim uses XML-based configuration files. The complete reference is in `defaultConfig.xml` at project root.

## Config File Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">

<config>
    <module name="controller">
        <param name="lastIteration" value="100"/>
        <param name="outputDirectory" value="./output"/>
    </module>

    <module name="plans">
        <param name="inputPlansFile" value="population.xml"/>
    </module>

    <!-- More modules... -->
</config>
```

## Essential Modules

### Controller Module

Controls simulation execution:

```xml
<module name="controller">
    <!-- Number of iterations (line 31 in defaultConfig.xml) -->
    <param name="lastIteration" value="100"/>

    <!-- Output directory (line 42) -->
    <param name="outputDirectory" value="./output"/>

    <!-- Overwrite behavior (line 44) -->
    <param name="overwriteFiles" value="deleteDirectoryIfExists"/>

    <!-- Write output every N iterations (line 58) -->
    <param name="writeEventsInterval" value="10"/>
    <param name="writePlansInterval" value="10"/>
</module>
```

**Recommended for testing**: `lastIteration="10"`, `overwriteFiles="deleteDirectoryIfExists"`

### Global Settings

```xml
<module name="global">
    <!-- Coordinate system (line 106) -->
    <param name="coordinateSystem" value="EPSG:3826"/>

    <!-- Number of threads (line 110) -->
    <param name="numberOfThreads" value="4"/>

    <!-- Random seed for reproducibility (line 111) -->
    <param name="randomSeed" value="4711"/>
</module>
```

### Network & Plans

```xml
<module name="network">
    <param name="inputNetworkFile" value="network.xml.gz"/>
</module>

<module name="plans">
    <param name="inputPlansFile" value="population.xml"/>
</module>

<module name="facilities">
    <param name="inputFacilitiesFile" value="facilities.xml"/>
</module>
```

### Routing Configuration

```xml
<module name="routing">
    <!-- Modes routed on network (line 242) -->
    <param name="networkModes" value="car"/>

    <!-- Access/egress mode (line 243) -->
    <param name="accessEgressType" value="accessEgressModeToLink"/>

    <!-- Teleported modes (lines 247-278) -->
    <parameterset type="teleportedModeParameters">
        <param name="mode" value="walk"/>
        <param name="teleportedModeSpeed" value="1.388888888"/>
        <param name="beelineDistanceFactor" value="1.3"/>
    </parameterset>

    <!-- DO NOT add PT to teleported modes! -->
</module>
```

**Critical**: PT should **NOT** be in `networkModes` or `teleportedModeParameters`

### QSim (Queue Simulation)

```xml
<module name="qsim">
    <!-- Main congested modes (line 180) -->
    <param name="mainMode" value="car,pt"/>

    <!-- Number of threads (line 186) -->
    <param name="numberOfThreads" value="4"/>

    <!-- Start/end time -->
    <param name="startTime" value="00:00:00"/>
    <param name="endTime" value="30:00:00"/>

    <!-- Stuck agent timeout (line 203) -->
    <param name="stuckTime" value="10.0"/>

    <!-- Use transit in mobsim -->
    <param name="usingTransitInMobsim" value="true"/>
</module>
```

### Transit Module

```xml
<module name="transit">
    <!-- Enable transit (line 504) -->
    <param name="useTransit" value="true"/>

    <!-- Transit modes (line 498) -->
    <param name="transitModes" value="pt"/>

    <!-- Routing algorithm (line 494) -->
    <param name="routingAlgorithmType" value="SwissRailRaptor"/>

    <!-- Input files (lines 500-502) -->
    <param name="transitScheduleFile" value="transitSchedule.xml"/>
    <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>
```

### Transit Router

```xml
<module name="transitRouter">
    <!-- Max walk distance (line 517) -->
    <param name="maxBeelineWalkConnectionDistance" value="1000.0"/>

    <!-- Search radius (line 519) -->
    <param name="searchRadius" value="1500.0"/>

    <!-- Transfer time (line 511) -->
    <param name="additionalTransferTime" value="60.0"/>
</module>
```

### SwissRailRaptor

```xml
<module name="swissRailRaptor">
    <!-- Disable intermodal for simple scenarios -->
    <param name="useIntermodalAccessEgress" value="false"/>

    <!-- Transfer penalties (set to 0 for direct paths) -->
    <param name="transferPenaltyBaseCost" value="0.0"/>
    <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>

    <!-- Mode mapping -->
    <param name="useModeMappingForPassengers" value="false"/>
</module>
```

### Scoring Parameters

Controls agent behavior through utility functions (lines 303-460):

```xml
<module name="scoring">
    <!-- General settings -->
    <param name="fractionOfIterationsToStartScoreMSA" value="0.8"/>

    <!-- Activity types -->
    <parameterset type="activityParams">
        <param name="activityType" value="home"/>
        <param name="typicalDuration" value="12:00:00"/>
    </parameterset>

    <parameterset type="activityParams">
        <param name="activityType" value="work"/>
        <param name="typicalDuration" value="08:00:00"/>
    </parameterset>

    <!-- Mode utilities (lines 401-460) -->
    <parameterset type="modeParams">
        <param name="mode" value="car"/>
        <param name="constant" value="-0.0"/>
        <param name="dailyMonetaryConstant" value="-0.0"/>
        <param name="dailyUtilityConstant" value="0.0"/>
        <param name="marginalUtilityOfDistance_util_m" value="-0.0"/>
        <param name="marginalUtilityOfTraveling_util_hr" value="-6.0"/>
        <param name="monetaryDistanceRate" value="-0.0002"/>
    </parameterset>

    <parameterset type="modeParams">
        <param name="mode" value="pt"/>
        <param name="constant" value="0.0"/>
        <param name="marginalUtilityOfTraveling_util_hr" value="-6.0"/>
    </parameterset>

    <parameterset type="modeParams">
        <param name="mode" value="walk"/>
        <param name="marginalUtilityOfTraveling_util_hr" value="-6.0"/>
    </parameterset>
</module>
```

## Command-Line Override

Override any parameter via CLI:

```bash
java -jar matsim.jar config.xml \
  --config:controller.lastIteration 50 \
  --config:controller.outputDirectory ./my-output \
  --config:qsim.numberOfThreads 8
```

Format: `--config:moduleName.parameterName value`

## Common Configuration Patterns

### Quick Test Run

```xml
<module name="controller">
    <param name="lastIteration" value="10"/>
    <param name="overwriteFiles" value="deleteDirectoryIfExists"/>
    <param name="writeEventsInterval" value="10"/>
    <param name="writePlansInterval" value="10"/>
</module>
```

### PT-Only Scenario

```xml
<module name="routing">
    <param name="networkModes" value="car"/>
    <!-- PT NOT here -->

    <parameterset type="teleportedModeParameters">
        <param name="mode" value="walk"/>
        <!-- PT NOT here -->
    </parameterset>
</module>

<module name="transit">
    <param name="useTransit" value="true"/>
    <param name="transitModes" value="pt"/>
    <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>

<module name="qsim">
    <param name="mainMode" value="pt"/>
    <param name="usingTransitInMobsim" value="true"/>
</module>
```

### Multimodal Scenario

```xml
<module name="routing">
    <param name="networkModes" value="car"/>

    <parameterset type="teleportedModeParameters">
        <param name="mode" value="walk"/>
    </parameterset>

    <parameterset type="teleportedModeParameters">
        <param name="mode" value="bike"/>
        <param name="teleportedModeSpeed" value="4.166666667"/>
    </parameterset>
</module>

<module name="transit">
    <param name="useTransit" value="true"/>
    <param name="transitModes" value="pt"/>
</module>

<module name="qsim">
    <param name="mainMode" value="car,pt,bike"/>
</module>
```

## Configuration Validation

Check your config before running:

```bash
# Validate XML syntax
xmllint --noout config.xml

# Check required files exist
ls -lh $(grep -oP 'value="\K[^"]*\.xml[^"]*' config.xml)
```

## Critical Parameters Checklist

Before running simulations:

- [ ] `controller.lastIteration` - Set appropriately (10-50 for tests, 100+ for production)
- [ ] `controller.outputDirectory` - Unique per run
- [ ] `global.coordinateSystem` - Matches network/population CRS
- [ ] `routing.networkModes` - Includes all network-routed modes
- [ ] `transit.useTransit` - `true` for PT scenarios
- [ ] PT **NOT** in teleported modes
- [ ] `qsim.usingTransitInMobsim` - `true` for PT scenarios
- [ ] All file paths exist and are correct

## Performance Tuning

### Multi-Threading

```xml
<module name="global">
    <param name="numberOfThreads" value="8"/>
</module>

<module name="qsim">
    <param name="numberOfThreads" value="8"/>
</module>
```

### Memory Management

```bash
# Increase heap size for large scenarios
java -Xmx16g -jar matsim.jar config.xml
```

### Output Frequency

```xml
<module name="controller">
    <!-- Write less frequently to save I/O -->
    <param name="writeEventsInterval" value="50"/>
    <param name="writePlansInterval" value="50"/>
</module>
```

## Reference

- **Complete reference**: `defaultConfig.xml` in project root
- **Line numbers** in comments refer to defaultConfig.xml
- See [Public Transit Guide](3-public-transit.md) for PT-specific config
- See [Troubleshooting](6-troubleshooting.md) for config-related issues
