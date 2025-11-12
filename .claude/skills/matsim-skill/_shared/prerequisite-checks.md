# Prerequisite Checks

Reusable prerequisite validation scripts used across MATSim skills.

## File Validation

### Check Required Files Exist

```bash
# Generic file existence check
for file in network.xml.gz transitSchedule.xml transitVehicles.xml population.xml; do
  if [ -f "$file" ]; then
    echo "✓ $file"
  else
    echo "✗ MISSING: $file"
  fi
done
```

### Check File Sizes

```bash
# Verify files are reasonable size (not empty, not suspiciously large)
ls -lh network.xml.gz transitSchedule.xml transitVehicles.xml population.xml

# Expected ranges:
#   network.xml.gz: 1-50 MB
#   transitSchedule.xml: 100 KB - 10 MB
#   transitVehicles.xml: 10 KB - 1 MB
#   population.xml: 100 KB - 100 MB
```

---

## Configuration Validation

### Validate XML Syntax

```bash
# Check config file is valid XML
xmllint --noout config.xml

# If valid: no output
# If invalid: shows error with line number
```

### Verify Referenced Files Exist

```bash
# Extract file paths from config and check they exist
for file in $(grep -oP 'value="\K[^"]*\.xml[^"]*' config.xml); do
  if [ -f "$file" ]; then
    echo "✓ $file"
  else
    echo "✗ MISSING: $file"
  fi
done
```

### Check Critical Parameters

```bash
# Verify key configuration parameters
echo "lastIteration: $(grep 'lastIteration' config.xml | grep -oP 'value="\K[^"]*')"
echo "coordinateSystem: $(grep 'coordinateSystem' config.xml | grep -oP 'value="\K[^"]*')"
echo "outputDirectory: $(grep 'outputDirectory' config.xml | grep -oP 'value="\K[^"]*')"
echo "useTransit: $(grep 'useTransit' config.xml | grep -oP 'value="\K[^"]*')"
```

---

## GTFS Validation

### Validate GTFS Zip Structure

```bash
# Check GTFS zip exists and is valid
ls -lh pt2matsim/data/gtfs.zip

# Verify required GTFS files present
unzip -l pt2matsim/data/gtfs.zip | grep -E 'stops.txt|routes.txt|trips.txt|stop_times.txt'

# Expected: All 4 required files present
```

### Test GTFS Zip Integrity

```bash
# Test zip file integrity
unzip -t pt2matsim/data/gtfs.zip

# If valid: lists files with "OK" status
# If corrupted: shows error
```

---

## Population Link Validation

### Validate Activity Links Exist in Network

```bash
# Extract link IDs from population
grep -o 'link="[^"]*"' population.xml | \
  sed 's/link="\([^"]*\)"/\1/' | \
  sort -u > /tmp/plan_links.txt

# Extract link IDs from network
gunzip -c network.xml.gz | \
  grep '<link id=' | \
  grep -o 'id="[^"]*"' | \
  sed 's/id="\([^"]*\)"/\1/' | \
  sort -u > /tmp/network_links.txt

# Find missing links (should be empty)
echo "Links in plans but not in network:"
comm -23 /tmp/plan_links.txt /tmp/network_links.txt

# If output is empty: all links valid
# If output has links: population references invalid links
```

---

## Coordinate System Validation

### Check CRS Consistency

```bash
# Extract CRS from config
CONFIG_CRS=$(grep 'coordinateSystem' config.xml | grep -oP 'value="\K[^"]*')
echo "Config CRS: $CONFIG_CRS"

# Check if network coordinates match expected range for CRS
# For EPSG:3826 (Taiwan), expect X: 120k-380k, Y: 2.4M-2.9M
echo "Network coordinate bounds:"
gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | head -1
gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | tail -1
gunzip -c network.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | head -1
gunzip -c network.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | tail -1

# Manually verify ranges match expected CRS
```

### Verify Population Coordinates Within Network Bounds

```bash
# Get network bounds
NETWORK_MIN_X=$(gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | head -1)
NETWORK_MAX_X=$(gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | tail -1)
NETWORK_MIN_Y=$(gunzip -c network.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | head -1)
NETWORK_MAX_Y=$(gunzip -c network.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | tail -1)

echo "Network bounds: X[$NETWORK_MIN_X, $NETWORK_MAX_X] Y[$NETWORK_MIN_Y, $NETWORK_MAX_Y]"

# Get population activity bounds
POP_MIN_X=$(grep -oP 'x="\K[^"]*' population.xml | sort -n | head -1)
POP_MAX_X=$(grep -oP 'x="\K[^"]*' population.xml | sort -n | tail -1)
POP_MIN_Y=$(grep -oP 'y="\K[^"]*' population.xml | sort -n | head -1)
POP_MAX_Y=$(grep -oP 'y="\K[^"]*' population.xml | sort -n | tail -1)

echo "Population bounds: X[$POP_MIN_X, $POP_MAX_X] Y[$POP_MIN_Y, $POP_MAX_Y]"

# Manually verify population is within or near network bounds
```

---

## PT Prerequisite Validation

### Check PT Files Exist and Are Valid

```bash
# Verify PT files exist
ls -lh transitSchedule.xml transitVehicles.xml

# Count PT elements
echo "Transit routes: $(grep -c '<transitRoute' transitSchedule.xml)"
echo "Stops: $(grep -c '<stopFacility' transitSchedule.xml)"
echo "Vehicles: $(grep -c '<vehicle ' transitVehicles.xml)"

# Expected: All counts > 0
```

### Verify PT Configuration in Config

```bash
# Check transit module enabled
echo "useTransit: $(grep 'useTransit' config.xml | grep -oP 'value="\K[^"]*')"
echo "transitModes: $(grep 'transitModes' config.xml | grep -oP 'value="\K[^"]*')"
echo "routingAlgorithmType: $(grep 'routingAlgorithmType' config.xml | grep -oP 'value="\K[^"]*')"

# Expected:
#   useTransit: true
#   transitModes: pt
#   routingAlgorithmType: SwissRailRaptor
```

### Check PT Not in Wrong Places

```bash
# Verify PT is NOT in teleported modes (common error)
echo "Checking if PT is in teleportedModeParameters (should be empty):"
grep -A 5 'teleportedModeParameters' config.xml | grep 'pt'

# Expected: no output (PT should NOT appear)

# Verify PT is NOT in networkModes
echo "Checking if PT is in networkModes (should be empty):"
grep 'networkModes' config.xml | grep 'pt'

# Expected: no output (PT should NOT appear in networkModes)
```

---

## Simulation Output Validation

### Check Output Directory Ready

```bash
# Verify output directory doesn't exist or is ready to overwrite
OUTPUT_DIR=$(grep 'outputDirectory' config.xml | grep -oP 'value="\K[^"]*')

if [ -d "$OUTPUT_DIR" ]; then
  echo "⚠ Output directory exists: $OUTPUT_DIR"

  # Check overwrite setting
  OVERWRITE=$(grep 'overwriteFiles' config.xml | grep -oP 'value="\K[^"]*')
  echo "Overwrite setting: $OVERWRITE"

  # Expected: deleteDirectoryIfExists for testing
else
  echo "✓ Output directory doesn't exist: $OUTPUT_DIR"
fi
```

### Check Disk Space Available

```bash
# Check available disk space for output directory
df -h .

# MATSim simulations can generate 1-10 GB of output
# Ensure at least 20 GB free space
```

---

## Memory Validation

### Estimate Memory Requirements

```bash
# Count agents in population
AGENTS=$(grep -c '<person ' population.xml)
echo "Number of agents: $AGENTS"

# Count network links
LINKS=$(gunzip -c network.xml.gz | grep -c '<link ')
echo "Number of links: $LINKS"

# Rough memory estimation:
#   Small (< 1000 agents, < 10k links): 4 GB
#   Medium (1000-10k agents, 10k-100k links): 8 GB
#   Large (> 10k agents, > 100k links): 16 GB+

echo ""
echo "Recommended memory allocation:"
if [ $AGENTS -lt 1000 ] && [ $LINKS -lt 10000 ]; then
  echo "  java -Xmx4g ..."
elif [ $AGENTS -lt 10000 ] && [ $LINKS -lt 100000 ]; then
  echo "  java -Xmx8g ..."
else
  echo "  java -Xmx16g ..."
fi
```

---

## Network Connectivity Validation

### Quick Network Connectivity Check

```bash
# Run PrepareNetworkForPTMapping in dry-run mode (just load and report)
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="network.xml.gz /tmp/network-test.xml.gz" \
  2>&1 | grep -i "network\|connected\|cleaned"

# Check for "Network is not connected" warnings
# If present: network has disconnected components
```

---

## Combined Pre-Run Checklist

### Complete Pre-Simulation Validation Script

```bash
#!/bin/bash
# Complete pre-simulation validation

echo "=== MATSim Pre-Run Validation ==="
echo ""

echo "[1/7] Checking required files..."
for file in config.xml network.xml.gz population.xml; do
  [ -f "$file" ] && echo "  ✓ $file" || echo "  ✗ MISSING: $file"
done
echo ""

echo "[2/7] Validating XML syntax..."
xmllint --noout config.xml && echo "  ✓ config.xml is valid XML" || echo "  ✗ config.xml has XML errors"
echo ""

echo "[3/7] Checking referenced files..."
for file in $(grep -oP 'value="\K[^"]*\.xml[^"]*' config.xml); do
  [ -f "$file" ] && echo "  ✓ $file" || echo "  ✗ MISSING: $file"
done
echo ""

echo "[4/7] Validating population links..."
grep -o 'link="[^"]*"' population.xml | sed 's/link="\([^"]*\)"/\1/' | sort -u > /tmp/plan_links.txt
gunzip -c network.xml.gz | grep '<link id=' | grep -o 'id="[^"]*"' | sed 's/id="\([^"]*\)"/\1/' | sort -u > /tmp/network_links.txt
MISSING=$(comm -23 /tmp/plan_links.txt /tmp/network_links.txt | wc -l)
if [ $MISSING -eq 0 ]; then
  echo "  ✓ All population links exist in network"
else
  echo "  ✗ $MISSING links in population missing from network"
fi
echo ""

echo "[5/7] Checking PT configuration..."
if grep -q 'useTransit.*true' config.xml; then
  echo "  ✓ PT enabled"

  # Check PT NOT in wrong places
  if grep -A 5 'teleportedModeParameters' config.xml | grep -q 'pt'; then
    echo "  ✗ WARNING: PT found in teleportedModeParameters (will break routing)"
  else
    echo "  ✓ PT not in teleported modes"
  fi
else
  echo "  ℹ PT not enabled (OK for car-only scenarios)"
fi
echo ""

echo "[6/7] Checking disk space..."
df -h . | tail -1
echo ""

echo "[7/7] Checking critical parameters..."
echo "  lastIteration: $(grep 'lastIteration' config.xml | grep -oP 'value="\K[^"]*')"
echo "  coordinateSystem: $(grep 'coordinateSystem' config.xml | grep -oP 'value="\K[^"]*')"
echo "  outputDirectory: $(grep 'outputDirectory' config.xml | grep -oP 'value="\K[^"]*')"
echo ""

echo "=== Validation Complete ==="
```

Save as `scripts/validate-simulation.sh` and run before each simulation.
