# Public Transit Complete Guide

## Overview

This guide covers the complete GTFS-to-MATSim workflow for public transit simulation.

## Tools & Pipeline

### Available Tools

Located in `src/main/java/org/matsim/project/tools/`:

| Tool | Function |
|------|----------|
| `GtfsToMatsim` | Convert GTFS → transitSchedule + transitVehicles |
| `ConvertGtfsCoordinates` | Transform coordinates between CRS |
| `MergeGtfsSchedules` | Merge multiple transit schedules |
| `PrepareNetworkForPTMapping` | Clean network for PT mapping |
| `CleanSubwayNetwork` | Extract subway-only network |
| `PreRoutePt` | Pre-route PT legs in population |
| `OsmPbfToXml` | Convert OSM PBF to XML |

### pt2matsim CLI Tools

The vendored JAR (`pt2matsim/work/pt2matsim-25.8-shaded.jar`) provides:

```bash
# Create default PT mapper config
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig config.xml

# Run PT mapping
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper config.xml

# Check mapped schedule plausibility
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  network.xml.gz transitSchedule.xml.gz
```

## Step-by-Step Setup

### 1. Prepare GTFS Data

Place GTFS zip files in `pt2matsim/data/`:
```
pt2matsim/data/
├── taipei_metro.zip
└── taipei_bus.zip
```

### 2. Convert GTFS to MATSim

```java
GtfsToMatsim.main(new String[] {
    "pt2matsim/data/taipei_metro.zip",
    "output/transitSchedule.xml",
    "output/transitVehicles.xml"
});
```

### 3. Prepare Network

**Critical**: Build **multimodal network** (car + walk + rail) even for PT-only scenarios:

```bash
# Use pt2matsim to create multimodal network
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  input.osm output_network.xml config.xml
```

Or clean existing network:
```java
PrepareNetworkForPTMapping.main(args);
```

### 4. Map Schedule to Network

Create mapper config:
```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig mapper_config.xml
```

Edit `mapper_config.xml` with these parameters:

```xml
<module name="ptmapper">
    <!-- Distance from stop to search for links -->
    <param name="maxLinkCandidateDistance" value="300.0"/>

    <!-- Number of link candidates per stop -->
    <param name="nLinkThreshold" value="12"/>

    <!-- Cost multiplier before creating artificial link -->
    <param name="maxTravelCostFactor" value="15.0"/>

    <!-- Router: SpeedyALT (fast) or AStarLandmarks (robust) -->
    <param name="networkRouter" value="AStarLandmarks"/>

    <!-- Number of threads -->
    <param name="numOfThreads" value="4"/>
</module>
```

Run mapping:
```bash
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper mapper_config.xml
```

### 5. Configure MATSim

Critical configuration in `config.xml`:

```xml
<!-- Enable transit -->
<module name="transit">
    <param name="useTransit" value="true"/>
    <param name="transitModes" value="pt"/>
    <param name="transitScheduleFile" value="transitSchedule.xml"/>
    <param name="vehiclesFile" value="transitVehicles.xml"/>
    <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>

<!-- PT NOT in teleported modes -->
<module name="routing">
    <param name="networkModes" value="car"/>

    <!-- Walk modes use teleportation -->
    <parameterset type="teleportedModeParameters">
        <param name="mode" value="walk"/>
        <param name="teleportedModeSpeed" value="1.388888888"/>
    </parameterset>
</module>

<!-- Enable PT in QSim -->
<module name="qsim">
    <param name="mainMode" value="car,pt"/>
    <param name="usingTransitInMobsim" value="true"/>
</module>

<!-- SwissRailRaptor config -->
<module name="swissRailRaptor">
    <param name="useIntermodalAccessEgress" value="false"/>
    <param name="transferPenaltyBaseCost" value="0.0"/>
    <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>
</module>
```

## Common Issues & Solutions

### Issue: PT Agents Use Direct Transmission

**Symptom**: PT agents teleport directly from origin to destination

**Root Cause**: PT configured as teleported mode in routing module

**Solution**: Remove PT from `teleportedModeParameters`:

```xml
<!-- ❌ WRONG -->
<parameterset type="teleportedModeParameters">
    <param name="mode" value="pt"/>
</parameterset>

<!-- ✅ CORRECT -->
<!-- PT not listed in teleported modes -->
```

### Issue: ClassCastException TransitPassengerRoute → NetworkRoute

**Root Cause**: Missing ground network for access/egress trips

**Solution**: Build multimodal network with car, walk, and PT modes:

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  taipei.osm network.xml config.xml
```

### Issue: Too Many Artificial Links

**Symptom**: Warning "creating artificial link for stop X"

**Root Cause**: PT stops too far from network links

**Solutions**:
1. Increase `maxLinkCandidateDistance` to 300-500m (metro)
2. Increase `maxTravelCostFactor` to 15.0+
3. Use `AStarLandmarks` router for disconnected networks

### Issue: Network Not Connected Warnings

**Solution**: Run `PrepareNetworkForPTMapping` to clean network:

```java
PrepareNetworkForPTMapping.main(new String[] {
    "network.xml",
    "cleaned_network.xml"
});
```

### Issue: Zero-Length Links

**Symptom**: `WARN LinkImpl:130 length=0.0`

**Solution**: Set minimum length for all links (1.0m minimum)

## Configuration Checklist

Before running PT simulation:

- [ ] `transit.useTransit = true`
- [ ] `transit.transitModes = "pt"`
- [ ] `transit.routingAlgorithmType = "SwissRailRaptor"`
- [ ] `qsim.usingTransitInMobsim = true`
- [ ] PT **NOT** in `routing.networkModes`
- [ ] PT **NOT** in `teleportedModeParameters`
- [ ] PT **NOT** in `qsim.mainMode` (for PT-only scenarios)
- [ ] Multimodal network exists (car + walk + PT)
- [ ] `transitSchedule.xml` and `transitVehicles.xml` present

## Validation

Check events for correct PT routing:

```bash
# Extract PT vehicle events
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "VehicleArrivesAtFacility\|VehicleDepartsAtFacility" | \
  head -20
```

Expected output shows **sequential stops**:
```
VehicleArrivesAtFacility at STOP_01
VehicleDepartsAtFacility from STOP_01
VehicleArrivesAtFacility at STOP_02  ← intermediate stop
VehicleDepartsAtFacility from STOP_02
...
```

## Best Practices

✅ **DO**:
- Build multimodal networks (car, walk, rail)
- Use SwissRailRaptor for PT routing
- Check link modes match routing config
- Validate link references in population
- Set realistic iterations (10-50 for testing)

❌ **DON'T**:
- Import only rail tracks without ground roads
- Configure PT as teleported mode
- Skip network mode validation
- Use zero-length links
- Forget transitVehicles.xml

## Advanced: Mode-Specific Rules

For complex networks, configure mode-specific parameters:

```xml
<module name="ptmapper">
    <param name="modeSpecificRules" value="true"/>

    <parameterset type="modeSpecific">
        <param name="mode" value="subway"/>
        <param name="maxLinkCandidateDistance" value="500.0"/>
        <param name="nLinkThreshold" value="15"/>
    </parameterset>

    <parameterset type="modeSpecific">
        <param name="mode" value="bus"/>
        <param name="maxLinkCandidateDistance" value="100.0"/>
        <param name="nLinkThreshold" value="8"/>
    </parameterset>
</module>
```

## Reference Files

- `defaultConfig.xml` - Complete config reference
- See [Configuration Guide](5-configuration.md) for all options
- See [Troubleshooting](6-troubleshooting.md) for more issues
