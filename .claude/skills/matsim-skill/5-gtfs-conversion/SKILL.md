# GTFS to MATSim Conversion

This skill helps convert GTFS transit data to MATSim format for public transit simulation.

## When to Activate This Skill

Activate when user mentions:
- "Convert GTFS to MATSim"
- "Import transit schedule from GTFS"
- "Set up public transit from GTFS feed"
- "Process GTFS data"
- "GtfsToMatsim"

## Workflow

### Step 1: Validate GTFS Input

```bash
# Check GTFS zip exists
ls -lh pt2matsim/data/taipei_metro.zip

# Validate GTFS structure
unzip -l pt2matsim/data/taipei_metro.zip | grep -E 'stops.txt|routes.txt|trips.txt|stop_times.txt'

# Expected: All required files present
```

### Step 2: Prepare Base Network

GTFS conversion requires a base multimodal network:

```bash
# Option 1: Use existing network
ls -lh pt2matsim/output_v1/network.xml.gz

# Option 2: Convert OSM to network (if needed)
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.OsmPbfToXml" \
  -Dexec.args="input.osm.pbf output.osm"
```

### Step 3: Convert Coordinates (if needed)

GTFS uses WGS84 (EPSG:4326), need to convert to target CRS:

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.ConvertGtfsCoordinates" \
  -Dexec.args="--input gtfs.zip --output gtfs-converted.zip --targetCRS EPSG:3826"
```

### Step 4: Run GTFS Conversion

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.GtfsToMatsim" \
  -Dexec.args="--gtfsZip pt2matsim/data/taipei_metro.zip \
               --network pt2matsim/output_v1/network.xml.gz \
               --outDir pt2matsim/output_v2 \
               --targetCRS EPSG:3826"
```

### Step 5: Validate Output

```bash
# Check generated files
ls -lh pt2matsim/output_v2/transitSchedule.xml
ls -lh pt2matsim/output_v2/transitVehicles.xml
ls -lh pt2matsim/output_v2/population.xml

# Count transit routes
grep -c '<transitRoute' pt2matsim/output_v2/transitSchedule.xml

# Count vehicles
grep -c '<vehicle ' pt2matsim/output_v2/transitVehicles.xml

# Count stops
grep -c '<stopFacility' pt2matsim/output_v2/transitSchedule.xml
```

### Step 6: Inspect Schedule Quality

```bash
# Check stop coordinates are reasonable
grep 'stopFacility' pt2matsim/output_v2/transitSchedule.xml | head -5

# Verify departure times (should be 0-86400 seconds)
grep 'departureTime' pt2matsim/output_v2/transitSchedule.xml | head -10

# Check vehicle capacities defined
grep 'capacity' pt2matsim/output_v2/transitVehicles.xml | head -5
```

## Common Issues

### Issue 1: Wrong CRS
**Symptom**: GTFS stops outside network bounds
**Fix**: Use ConvertGtfsCoordinates tool to transform coordinates

### Issue 2: Empty GTFS
**Symptom**: Invalid zip file or missing required files
**Validation**: Check zip has stops.txt, routes.txt, trips.txt, stop_times.txt

### Issue 3: Network Mismatch
**Symptom**: Network doesn't cover GTFS extent
**Fix**: Expand OSM extract or filter GTFS to network bounds

## Configuration Parameters

### sampleSelector
- **dayWithMostTrips** (default): Uses busiest service day
- **specific date**: e.g., "2024-01-15"

### targetCRS
- **EPSG:3826**: TWD97 / TM2 zone 121 (Taiwan)
- **EPSG:2056**: CH1903+ / LV95 (Switzerland)
- **EPSG:32633**: WGS 84 / UTM zone 33N (Europe)

## Full Pipeline Example

```bash
# 1. Download GTFS feed
wget https://example.com/metro-gtfs.zip -O pt2matsim/data/metro.zip

# 2. Validate GTFS
unzip -t pt2matsim/data/metro.zip

# 3. Convert coordinates if needed
./mvnw exec:java -Dexec.mainClass="org.matsim.project.tools.ConvertGtfsCoordinates" \
  -Dexec.args="--input pt2matsim/data/metro.zip --output pt2matsim/data/metro-converted.zip --targetCRS EPSG:3826"

# 4. Convert to MATSim
./mvnw exec:java -Dexec.mainClass="org.matsim.project.tools.GtfsToMatsim" \
  -Dexec.args="--gtfsZip pt2matsim/data/metro-converted.zip --network network.xml.gz --outDir pt2matsim/out --targetCRS EPSG:3826"

# 5. Validate output
grep -c '<transitRoute' pt2matsim/out/transitSchedule.xml
grep -c '<vehicle ' pt2matsim/out/transitVehicles.xml

# 6. Map to network (see PT Mapping skill)
# 7. Run simulation (see Simulation skill)
```

## Next Steps

After GTFS conversion:
1. **Map transit schedule to network** (use PT Mapping skill)
2. **Configure SwissRailRaptor** (use SwissRailRaptor skill)
3. **Run simulation** (use Simulation skill)

## File References

- Tool: `src/main/java/org/matsim/project/tools/GtfsToMatsim.java`
- Coordinate converter: `src/main/java/org/matsim/project/tools/ConvertGtfsCoordinates.java`
- CLAUDE.md: Lines 145-161
- Documentation: `docs/3-public-transit.md`
