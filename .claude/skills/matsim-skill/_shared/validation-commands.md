# Common Validation Commands

Shared validation commands used across MATSim skills.

## Network Inspection

### Count Nodes and Links
```bash
gunzip -c network.xml.gz | grep -c '<node '
gunzip -c network.xml.gz | grep -c '<link '
```

### Check Coordinate Bounds
```bash
# Min/Max X coordinates
gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | head -1  # Min X
gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | tail -1  # Max X

# Min/Max Y coordinates
gunzip -c network.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | head -1  # Min Y
gunzip -c network.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | tail -1  # Max Y
```

### Check Network Modes
```bash
# Extract all modes present in network
gunzip -c network.xml.gz | grep -o 'modes="[^"]*"' | sort | uniq -c
```

---

## PT Boarding Validation

### Check for Boarding Events
```bash
# Count PersonEntersVehicle events
gunzip -c output/ITERS/it.0/0.events.xml.gz | grep "PersonEntersVehicle" | wc -l
# Expected: >0 if PT routing works
```

### Check for Transfers
```bash
# Count boardings per agent
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10

# Expected: Agents with 2+ boardings indicate transfers
```

### Verify Vehicle Usage
```bash
# Show agent-vehicle pairs
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*vehicle="\([^"]*\)".*/\1 \2/' | \
  sort
```

---

## Transfer Station Validation

### Check stopAreaId Configuration
```bash
gunzip -c transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | \
  grep 'stopAreaId' | \
  head -20

# Expected: Transfer stations share same stopAreaId
# Example:
#   <stopFacility id="BL11_UP" stopAreaId="086" ... />
#   <stopFacility id="G12_UP" stopAreaId="086" ... />
```

### Find Transfer Candidates
```bash
# Extract stopAreaId for potential transfer stations
gunzip -c transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | \
  grep 'stopAreaId' | \
  sed 's/.*id="\([^"]*\)".*stopAreaId="\([^"]*\)".*/\2 \1/' | \
  sort | uniq -c | \
  awk '$1 > 1'  # Only show stops with multiple facilities

# Expected output:
#   2 086 BL11_UP
#   2 086 G12_UP
```

---

## PT Mapping Validation

### Calculate Artificial Link Percentage
```bash
# Count artificial links
ARTIFICIAL=$(gunzip -c network-with-pt.xml.gz | grep -c 'pt_.*_UP')

# Count total stops
TOTAL=$(grep -c '<stopFacility' transitSchedule.xml)

# Calculate percentage
echo "scale=2; $ARTIFICIAL * 100 / $TOTAL" | bc

# Acceptable ranges:
#   <10% = Excellent real network mapping
#   10-30% = Good mixed mapping
#   >30% = Consider improving parameters
#   100% = Artificial mode (intentional for testing)
```

### Check Mapping Completion
```bash
# Check for route failures in log
grep -i "routes with failures" pt2matsim/work/ptmapper.log

# Expected: "Routes with failures: 0"
```

### Verify PT Modes on Links
```bash
# Count PT-enabled links
gunzip -c network-with-pt.xml.gz | grep 'modes=' | grep 'pt' | wc -l

# Count artificial links specifically
gunzip -c network-with-pt.xml.gz | grep 'id="pt_' | wc -l
```

### Run Plausibility Check
```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  network-with-pt.xml.gz transitSchedule-mapped.xml.gz

# Expected:
#   INFO  PlausibilityCheck: All routes are plausible
#   INFO  PlausibilityCheck: No unrealistic travel times detected
```

---

## Transit Schedule Validation

### Count Transit Elements
```bash
# Count transit routes
grep -c '<transitRoute' transitSchedule.xml

# Count vehicles
grep -c '<vehicle ' transitVehicles.xml

# Count stops
grep -c '<stopFacility' transitSchedule.xml
```

### Check Departure Times
```bash
# Verify departure times are reasonable (0-86400 seconds)
grep 'departureTime' transitSchedule.xml | head -10
```

### Verify Vehicle Capacities
```bash
# Check vehicle capacities defined
grep 'capacity' transitVehicles.xml | head -5
```

---

## Population Validation

### Validate Activity Link References
```bash
# Extract link IDs from population
grep -o 'link="[^"]*"' population.xml | sort -u > plan_links.txt

# Extract link IDs from network
gunzip -c network.xml.gz | grep '<link id=' | grep -o 'id="[^"]*"' | sort -u > network_links.txt

# Find missing links (should be empty)
comm -23 plan_links.txt network_links.txt
```

### Check Population Bounds
```bash
# Extract activity coordinates
grep -oP '[xy]="\K[^"]*' population.xml | sort -n | head -1  # Min
grep -oP '[xy]="\K[^"]*' population.xml | sort -n | tail -1  # Max

# Compare with network bounds to ensure overlap
```

---

## Simulation Output Validation

### Check Convergence
```bash
# View score statistics
open output/scorestats.png

# Or check CSV
tail -10 output/scorestats.csv
```

### Check Mode Distribution
```bash
# View mode statistics
cat output/modestats.csv

# Count completed iterations
ls output/ITERS/ | grep -c 'it\.'
```

### Count Event Types
```bash
# Analyze event distribution
gunzip -c output/output_events.xml.gz | \
  grep -oP 'type="\K[^"]*' | \
  sort | uniq -c | sort -rn
```

---

## GTFS Output Validation

### Validate GTFS Conversion Output
```bash
# Check generated files exist
ls -lh transitSchedule.xml
ls -lh transitVehicles.xml
ls -lh population.xml

# Count transit routes
grep -c '<transitRoute' transitSchedule.xml

# Count vehicles
grep -c '<vehicle ' transitVehicles.xml

# Count stops
grep -c '<stopFacility' transitSchedule.xml
```

### Check Stop Coordinates
```bash
# Verify stop coordinates are reasonable
grep 'stopFacility' transitSchedule.xml | head -5
```

---

## Via Export Validation

### Check Via Export Output
```bash
# Verify files generated
ls -lh forVia/output_events.xml
ls -lh forVia/output_network.xml.gz
ls -lh forVia/tracks_dt5s.csv

# Check event count reduction
wc -l forVia/output_events.xml
# Should be <<< original event count
```

### Verify Compression Ratio
```bash
# Check statistics
cat forVia/vehicle_usage_report.txt

# Expected output shows:
#   Original events: XXX,XXX
#   Filtered events: X,XXX
#   Compression: XX.X%
```
