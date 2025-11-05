# Troubleshooting Guide

## Common Errors & Solutions

### PT Agents Using Direct Transmission

**Symptom**: PT agents teleport directly from origin to destination, ignoring intermediate stops.

**Check Events**:
```bash
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "VehicleArrivesAtFacility" | head -5
```

**Root Cause**: PT configured as teleported mode

**Solution**: Remove PT from teleportedModeParameters in config.xml

```xml
<!-- ❌ WRONG -->
<module name="routing">
    <parameterset type="teleportedModeParameters">
        <param name="mode" value="pt"/>
    </parameterset>
</module>

<!-- ✅ CORRECT -->
<module name="routing">
    <!-- PT not listed in teleported modes -->
    <parameterset type="teleportedModeParameters">
        <param name="mode" value="walk"/>
    </parameterset>
</module>
```

---

### ClassCastException: TransitPassengerRoute → NetworkRoute

**Full Error**:
```
java.lang.ClassCastException: class org.matsim.pt.routes.TransitPassengerRoute
cannot be cast to class org.matsim.core.population.routes.NetworkRoute
```

**Root Cause**: Missing ground network for access/egress trips

**Solution**: Build multimodal network with car, walk, and PT modes:

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
  input.osm output_network.xml config.xml
```

Even PT-only scenarios need ground network for walking to/from stations.

---

### Network Not Connected Warnings

**Symptom**:
```
WARN NetworkImpl:428 Network is not connected. There are X clusters.
```

**Solution**: Clean network with PrepareNetworkForPTMapping:

```java
PrepareNetworkForPTMapping.main(new String[] {
    "network.xml",
    "cleaned_network.xml"
});
```

Or use NetworkCleaner:
```java
Network network = NetworkUtils.readNetwork("network.xml");
new NetworkCleaner().run(network);
NetworkWriter networkWriter = new NetworkWriter(network);
networkWriter.write("cleaned_network.xml");
```

---

### Too Many Artificial Links

**Symptom**:
```
WARN PublicTransitMapper:xxx creating artificial link for stop XXXX
```

**Root Cause**: PT stops too far from network links

**Solutions**:

1. Increase search distance in PT mapper config:
```xml
<module name="ptmapper">
    <param name="maxLinkCandidateDistance" value="500.0"/>
    <param name="nLinkThreshold" value="15"/>
    <param name="maxTravelCostFactor" value="20.0"/>
</module>
```

2. Use more robust router:
```xml
<module name="ptmapper">
    <param name="networkRouter" value="AStarLandmarks"/>
</module>
```

3. Expand candidate search:
```xml
<module name="ptmapper">
    <param name="candidateDistanceMultiplier" value="3.0"/>
</module>
```

---

### Zero-Length Links

**Symptom**:
```
WARN LinkImpl:130 length=0.0 of link id pt_STATION_UP
```

**Solution**: Set minimum length (1.0m) for all links in network

---

### Link Not Found in Network

**Symptom**:
```
ERROR ActivityImpl:xxx Link id=XXXXX not found in network
```

**Root Cause**: Activity references link that doesn't exist

**Validation**:
```bash
# Extract link IDs from population
grep -o 'link="[^"]*"' population.xml | sort -u > plan_links.txt

# Extract link IDs from network
grep '<link id=' network.xml | grep -o 'id="[^"]*"' | sort -u > network_links.txt

# Find missing links
comm -23 plan_links.txt network_links.txt
```

**Solution**:
- Use coordinate-based activities instead of link-based
- Or ensure all referenced links exist in network

---

### Stuck Agents

**Symptom**:
```
WARN QSim:xxx Agent XXX is stuck and removed from simulation
```

**Root Causes**:
1. No route found between locations
2. Network congestion
3. Invalid activity locations

**Solutions**:

1. Increase stuck time threshold:
```xml
<module name="qsim">
    <param name="stuckTime" value="30.0"/>
</module>
```

2. Check agent activities are reachable:
```bash
# Verify coordinates are within network bounds
grep -oP 'x="\K[^"]*' population.xml | sort -n | head -1
grep -oP 'x="\K[^"]*' population.xml | sort -n | tail -1
```

3. Enable teleportation for stuck agents:
```xml
<module name="qsim">
    <param name="removeStuckVehicles" value="true"/>
</module>
```

---

### Insufficient Storage Capacity

**Symptom**:
```
WARN QueueWithBuffer:504 Link too small: enlarge storage capacity
```

**Solutions**:

1. Increase storage capacity factor:
```xml
<module name="qsim">
    <param name="storageCapFactor" value="2.0"/>
    <param name="flowCapacityFactor" value="1.0"/>
</module>
```

2. Or increase link capacity in network.xml

---

### Transit Vehicle Not Found

**Symptom**:
```
ERROR TransitQSimEngine:xxx Transit vehicle XXXX not found
```

**Root Cause**: transitVehicles.xml missing or incomplete

**Solution**: Ensure transitVehicles.xml contains all vehicles referenced in transitSchedule.xml

```bash
# Check vehicle references
grep -oP 'vehicleId="[^"]*"' transitSchedule.xml | sort -u > schedule_vehicles.txt
grep -oP 'id="[^"]*"' transitVehicles.xml | sort -u > available_vehicles.txt
comm -23 schedule_vehicles.txt available_vehicles.txt
```

---

### Out of Memory

**Symptom**:
```
java.lang.OutOfMemoryError: Java heap space
```

**Solutions**:

1. Increase heap size:
```bash
java -Xmx16g -jar matsim.jar config.xml
```

2. Reduce output frequency:
```xml
<module name="controller">
    <param name="writeEventsInterval" value="50"/>
    <param name="writePlansInterval" value="50"/>
</module>
```

3. Use sampling for large populations:
```xml
<module name="plans">
    <param name="inputPlansFile" value="population.xml"/>
    <param name="removingUnusedPlans" value="true"/>
</module>
```

---

### Simulation Doesn't Converge

**Symptom**: Score stats show no stabilization after many iterations

**Check**:
```bash
# View score convergence
open output/scorestats.png
```

**Solutions**:

1. Increase iterations:
```xml
<module name="controller">
    <param name="lastIteration" value="200"/>
</module>
```

2. Adjust MSA (Method of Successive Averages):
```xml
<module name="replanning">
    <param name="fractionOfIterationsToDisableInnovation" value="0.8"/>
</module>
```

3. Check scoring parameters are realistic

---

### Wrong Coordinate System

**Symptom**: Agents appear in wrong locations, routing fails

**Solution**: Ensure consistent CRS across all files:

```xml
<module name="global">
    <param name="coordinateSystem" value="EPSG:3826"/>
</module>
```

Transform coordinates if needed:
```java
ConvertGtfsCoordinates.main(new String[] {
    "input_gtfs.zip",
    "output_gtfs.zip",
    "EPSG:4326",  // From WGS84
    "EPSG:3826"   // To TWD97
});
```

---

## Debugging Strategies

### 1. Check Logs

```bash
# View warnings and errors only
cat output/logfileWarningsErrors.log

# Search for specific error
grep -i "error\|exception" output/logfile.log
```

### 2. Validate Configuration

```bash
# Check config syntax
xmllint --noout config.xml

# Verify file paths
for file in $(grep -oP 'value="\K[^"]*\.xml[^"]*' config.xml); do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ MISSING: $file"
    fi
done
```

### 3. Inspect Events

```bash
# Count event types
gunzip -c output/output_events.xml.gz | \
  grep -oP 'type="\K[^"]*' | \
  sort | uniq -c | sort -rn

# Check PT events
gunzip -c output/output_events.xml.gz | \
  grep "PersonEntersVehicle\|PersonLeavesVehicle" | \
  head -20
```

### 4. Visualize Output

```bash
# Use MATSim VIA (built-in visualizer)
java -cp matsim.jar org.matsim.contrib.otfvis.OTFVis \
  output/output_network.xml.gz \
  output/output_events.xml.gz
```

### 5. Analyze Statistics

```bash
# Check mode shares
cat output/modestats.csv

# Check convergence
cat output/scorestats.csv
```

---

## Performance Issues

### Slow Simulation

**Causes**:
- Too many threads (overhead)
- Large events file writing
- Complex network

**Solutions**:

1. Optimize threading:
```xml
<module name="qsim">
    <!-- Try 1, 2, 4, or 8 threads -->
    <param name="numberOfThreads" value="4"/>
</module>
```

2. Reduce I/O:
```xml
<module name="controller">
    <param name="writeEventsInterval" value="100"/>
</module>
```

3. Simplify network:
- Remove unnecessary links
- Use higher link capacities
- Reduce simulation end time

### High Memory Usage

**Solutions**:

1. Use events streaming instead of loading all:
```java
EventsManager events = EventsUtils.createEventsManager();
events.addHandler(new MyEventHandler());
EventsUtils.readEvents(events, "events.xml.gz");
```

2. Process iterations incrementally

3. Use sampling (run with 10% of population first)

---

## Getting Help

1. **Check logs**: `output/logfileWarningsErrors.log`
2. **Read errors carefully**: Stack traces show exact problem
3. **Validate inputs**: Config, network, population
4. **Search MATSim docs**: https://matsim.org/docs
5. **MATSim mailing list**: matsim@googlegroups.com

## Best Practices for Prevention

✅ **DO**:
- Start with small test populations
- Validate all XML files before running
- Use deleteDirectoryIfExists for testing
- Check convergence with scorestats.png
- Keep backups of working configurations

❌ **DON'T**:
- Run 1000 iterations without testing
- Ignore warnings in logs
- Use production data for testing
- Skip validation steps
- Modify multiple things at once

---

## Quick Fixes Checklist

When simulation fails:

- [ ] Check `logfileWarningsErrors.log`
- [ ] Verify all input files exist
- [ ] Validate coordinate system is consistent
- [ ] Ensure PT not in teleported modes (if using transit)
- [ ] Check network is connected
- [ ] Verify all links referenced in population exist
- [ ] Confirm transitVehicles.xml matches schedule
- [ ] Try with smaller population/fewer iterations
- [ ] Check available memory (`-Xmx` setting)

---

## See Also

- [Configuration Reference](5-configuration.md) - Config troubleshooting
- [Public Transit Guide](3-public-transit.md) - PT-specific issues
- [Agent Development](4-agent-development.md) - Population issues
