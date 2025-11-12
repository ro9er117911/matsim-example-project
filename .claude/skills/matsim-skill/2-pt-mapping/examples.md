# PT Mapping Examples

## Example 1: Quick Artificial Mode Test (1-2 minutes)

**Scenario**: You want to test PT simulation quickly without waiting for real network mapping.

**Prerequisites**:
```bash
# Have these files ready
ls -lh transitSchedule.xml
ls -lh network.xml.gz
```

**Step 1: Create minimal config**

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim/work/ptmapper-config-artificial.xml
```

**Step 2: Edit config** (`pt2matsim/work/ptmapper-config-artificial.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
<config>
  <module name="ptmapper">
    <param name="networkFile" value="../../scenarios/equil/network.xml.gz"/>
    <param name="transitScheduleFile" value="../../scenarios/equil/transitSchedule.xml"/>
    <param name="outputNetworkFile" value="../../scenarios/equil/network-with-pt.xml.gz"/>
    <param name="outputScheduleFile" value="../../scenarios/equil/transitSchedule-mapped.xml.gz"/>

    <!-- ARTIFICIAL MODE: maxLinkCandidateDistance = 0.0 -->
    <param name="maxLinkCandidateDistance" value="0.0"/>

    <!-- Disable mode-specific rules for simplicity -->
    <param name="modeSpecificRules" value="false"/>
    <param name="routingWithCandidateDistance" value="false"/>

    <param name="numOfThreads" value="4"/>
  </module>
</config>
```

**Step 3: Run mapping**:

```bash
cd pt2matsim/work
java -Xmx6g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config-artificial.xml
```

**Expected output**:
```
INFO  PublicTransitMapper: Creating artificial links for all stops...
INFO  PublicTransitMapper: Created 120 artificial links
INFO  PublicTransitMapper: Mapping complete
INFO  PublicTransitMapper: Routes with failures: 0
```

**Expected time**: 1-2 minutes

**Step 4: Validate results**:

```bash
# Check output files created
ls -lh ../../scenarios/equil/network-with-pt.xml.gz
ls -lh ../../scenarios/equil/transitSchedule-mapped.xml.gz

# Count artificial links (should be 100%)
gunzip -c ../../scenarios/equil/network-with-pt.xml.gz | grep -c 'pt_.*_UP'
# Output: 120 (all stops have artificial links)

# Check network link structure
gunzip -c ../../scenarios/equil/network-with-pt.xml.gz | \
  grep 'id="pt_' | head -5

# Expected output:
#   <link id="pt_BL01_UP" from="..." to="..." ...>
#   <link id="pt_BL01_DN" from="..." to="..." ...>
#   <link id="pt_BL02_UP" from="..." to="..." ...>
```

**Result**: Pure artificial PT network, ready for testing in <2 minutes.

---

## Example 2: Taipei Metro Real Network Mapping

**Scenario**: Map Taipei Metro Blue Line onto actual road network with good coverage.

**Network characteristics**:
- 120 metro stops
- 50,000 network links
- Stations 1-2 km apart
- Some disconnected components (river crossings)

**Step 1: Prepare network**:

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="pt2matsim/output_v1/network.xml.gz pt2matsim/output_v1/network-cleaned.xml.gz"
```

Expected output:
```
INFO  PrepareNetworkForPTMapping: Loading network...
INFO  PrepareNetworkForPTMapping: Adding 'pt' mode to 1234 subway links
INFO  PrepareNetworkForPTMapping: Running NetworkCleaner...
INFO  PrepareNetworkForPTMapping: Removed 45 unreachable nodes
INFO  PrepareNetworkForPTMapping: Network cleaning complete
```

**Step 2: Create config**:

```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim/work/ptmapper-config-metro.xml
```

**Step 3: Edit config** for metro parameters:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
<config>
  <module name="ptmapper">
    <param name="networkFile" value="../output_v1/network-cleaned.xml.gz"/>
    <param name="transitScheduleFile" value="../output_v1/transitSchedule.xml"/>
    <param name="outputNetworkFile" value="../output_v2/network-with-pt.xml.gz"/>
    <param name="outputScheduleFile" value="../output_v2/transitSchedule-mapped.xml.gz"/>

    <!-- METRO PARAMETERS: Wide search radius -->
    <param name="maxLinkCandidateDistance" value="500.0"/>
    <param name="nLinkThreshold" value="15"/>
    <param name="maxTravelCostFactor" value="20.0"/>
    <param name="candidateDistanceMultiplier" value="3.0"/>

    <!-- Robust router for river crossings -->
    <param name="networkRouter" value="AStarLandmarks"/>

    <!-- Enable mode-specific rules -->
    <param name="modeSpecificRules" value="true"/>

    <!-- Performance -->
    <param name="numOfThreads" value="4"/>
  </module>
</config>
```

**Step 4: Run mapping**:

```bash
cd pt2matsim/work
java -Xmx10g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config-metro.xml 2>&1 | tee ptmapper.log
```

**Monitor progress**:
```bash
# In another terminal, watch progress
tail -f pt2matsim/work/ptmapper.log

# Expected log sequence:
# INFO  PublicTransitMapper: Initializing network router...
# INFO  PublicTransitMapper: Mapping 120 stops to network...
# INFO  PublicTransitMapper: Processing Blue Line...
# INFO  PublicTransitMapper: Stop BL01: Mapped to link 12345 (distance: 234m)
# INFO  PublicTransitMapper: Stop BL02: Mapped to link 12389 (distance: 187m)
# ...
# INFO  PublicTransitMapper: Created 18 artificial links
# INFO  PublicTransitMapper: Mapping complete (25 minutes)
# INFO  PublicTransitMapper: Routes with failures: 0
```

**Expected time**: 20-30 minutes

**Step 5: Validate results**:

```bash
# Check completion
grep -i "routes with failures" pt2matsim/work/ptmapper.log
# Output: Routes with failures: 0

# Count artificial links
ARTIFICIAL=$(gunzip -c ../output_v2/network-with-pt.xml.gz | grep -c 'pt_.*_UP')
echo "Artificial links: $ARTIFICIAL"
# Output: Artificial links: 18 (15% of 120 stops - acceptable)

# Run plausibility check
java -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  ../output_v2/network-with-pt.xml.gz \
  ../output_v2/transitSchedule-mapped.xml.gz

# Expected output:
# INFO  PlausibilityCheck: All routes are plausible
# INFO  PlausibilityCheck: Average link speed: 45 km/h
# INFO  PlausibilityCheck: No unrealistic travel times detected
```

**Result**: 85% real network mapping, 15% artificial (production-ready).

---

## Example 3: Stuck Process Recovery

**Scenario**: PT mapping process gets stuck after 15 minutes with no progress.

**Symptoms**:
```bash
# Log shows repeated warnings
tail -50 pt2matsim/work/ptmapper.log

# Output:
# WARN  NetworkRouter: Network is not connected from node 12345 to node 67890
# WARN  NetworkRouter: Network is not connected from node 12346 to node 67891
# (repeating for 10+ minutes)
```

**Step 1: Kill stuck process**:

```bash
# Find Java process
ps aux | grep PublicTransitMapper

# Output:
# user  12345  98.2  2.3  10240000  ...  java -Xmx10g ... PublicTransitMapper

# Kill it
kill 12345
```

**Step 2: Analyze root cause**:

```bash
# Check which stops were being processed
grep -i "mapping stop\|processing" pt2matsim/work/ptmapper.log | tail -10

# Output:
# INFO  Mapping stop BL23 to network...
# WARN  Could not find path from BL23 to BL24
# (stuck here)

# Check coordinates of problematic stops
grep 'id="BL23"' pt2matsim/output_v1/transitSchedule.xml
grep 'id="BL24"' pt2matsim/output_v1/transitSchedule.xml

# Compare with network bounds
gunzip -c pt2matsim/output_v1/network-cleaned.xml.gz | \
  grep -oP 'x="\K[^"]*' | sort -n | tail -1  # Max X

# Diagnosis: Stop BL24 is outside network bounds
```

**Step 3: Choose recovery strategy**:

**Option A: Quick fix - Use artificial mode**

```xml
<!-- ptmapper-config-artificial.xml -->
<param name="maxLinkCandidateDistance" value="0.0"/>
<param name="modeSpecificRules" value="false"/>
```

```bash
java -Xmx10g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config-artificial.xml
```

**Time**: 1-2 minutes
**Result**: 100% artificial links, but simulation can proceed

**Option B: Expand network coverage**

```bash
# Download larger OSM extract covering all stops
# Rerun network preparation
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.OsmPbfToXml" \
  -Dexec.args="larger-area.osm.pbf larger-area.osm"

# Regenerate network and retry mapping
```

**Time**: 1-2 hours total
**Result**: Better real network mapping

**Option C: Desperate measures - Extreme parameters**

```xml
<!-- ptmapper-config-desperate.xml -->
<param name="maxLinkCandidateDistance" value="2000.0"/>
<param name="nLinkThreshold" value="30"/>
<param name="maxTravelCostFactor" value="50.0"/>
<param name="candidateDistanceMultiplier" value="5.0"/>
<param name="networkRouter" value="AStarLandmarks"/>
```

```bash
java -Xmx12g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config-desperate.xml
```

**Time**: 45-60 minutes
**Result**: 30-50% artificial links, acceptable compromise

**Recommendation for this scenario**: Option A (artificial mode) for immediate testing, then Option B (expand network) for production.

---

## Example 4: Dense Urban Bus Network

**Scenario**: Map 500 bus stops across a dense urban grid network.

**Network characteristics**:
- 500 bus stops (average 200m spacing)
- 100,000 network links
- Well-connected grid
- Full coverage

**Configuration**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
<config>
  <module name="ptmapper">
    <param name="networkFile" value="urban-network-cleaned.xml.gz"/>
    <param name="transitScheduleFile" value="bus-schedule.xml"/>
    <param name="outputNetworkFile" value="urban-network-with-pt.xml.gz"/>
    <param name="outputScheduleFile" value="bus-schedule-mapped.xml.gz"/>

    <!-- BUS PARAMETERS: Tight search for dense stops -->
    <param name="maxLinkCandidateDistance" value="100.0"/>
    <param name="nLinkThreshold" value="8"/>
    <param name="maxTravelCostFactor" value="10.0"/>
    <param name="candidateDistanceMultiplier" value="1.6"/>

    <!-- Fast router for well-connected network -->
    <param name="networkRouter" value="SpeedyALT"/>

    <param name="modeSpecificRules" value="true"/>

    <!-- More threads for larger dataset -->
    <param name="numOfThreads" value="8"/>
  </module>
</config>
```

**Execution**:

```bash
java -Xmx12g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config-bus.xml
```

**Expected results**:

```bash
# Check artificial link percentage
ARTIFICIAL=$(gunzip -c urban-network-with-pt.xml.gz | grep -c 'pt_.*_UP')
TOTAL=500

echo "scale=2; $ARTIFICIAL * 100 / $TOTAL" | bc
# Output: 2.40 (2.4% artificial - excellent for bus network)

# Validate plausibility
java -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  urban-network-with-pt.xml.gz \
  bus-schedule-mapped.xml.gz

# Output:
# INFO  All routes plausible
# INFO  Average link speed: 25 km/h (realistic for urban bus)
```

**Expected time**: 30-45 minutes
**Result**: <5% artificial links (excellent real network mapping)

---

## Example 5: Hybrid Metro + Bus Mapping

**Scenario**: Map both metro (sparse, 120 stops) and bus (dense, 300 stops) in same network.

**Strategy**: Use mode-specific parameters.

**Configuration**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
<config>
  <module name="ptmapper">
    <param name="networkFile" value="multimodal-network-cleaned.xml.gz"/>
    <param name="transitScheduleFile" value="combined-schedule.xml"/>
    <param name="outputNetworkFile" value="combined-network-with-pt.xml.gz"/>
    <param name="outputScheduleFile" value="combined-schedule-mapped.xml.gz"/>

    <!-- Balanced parameters for mixed modes -->
    <param name="maxLinkCandidateDistance" value="300.0"/>
    <param name="nLinkThreshold" value="12"/>
    <param name="maxTravelCostFactor" value="15.0"/>
    <param name="candidateDistanceMultiplier" value="2.5"/>

    <param name="networkRouter" value="AStarLandmarks"/>

    <!-- Enable mode-specific rules for different treatment -->
    <param name="modeSpecificRules" value="true"/>

    <param name="numOfThreads" value="8"/>
  </module>

  <!-- Mode-specific overrides (if supported by pt2matsim version) -->
  <module name="ptmapper:subway">
    <param name="maxLinkCandidateDistance" value="500.0"/>
    <param name="nLinkThreshold" value="15"/>
  </module>

  <module name="ptmapper:bus">
    <param name="maxLinkCandidateDistance" value="100.0"/>
    <param name="nLinkThreshold" value="8"/>
  </module>
</config>
```

**Execution**:

```bash
java -Xmx14g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  ptmapper-config-hybrid.xml
```

**Expected time**: 45-60 minutes
**Expected result**:
- Metro: 10-15% artificial links
- Bus: 2-5% artificial links
- Overall: ~8% artificial links

---

## Parameter Tuning Flow Chart

```
START: Initial mapping attempt with default parameters

Did process complete within 30 minutes?
├─ NO (stuck/too slow)
│  ├─ Switch to artificial mode (maxLinkCandidateDistance=0.0)
│  └─ OR use AStarLandmarks router
└─ YES: Continue

Are artificial links >30%?
├─ YES
│  ├─ Increase maxLinkCandidateDistance (+200m)
│  ├─ Increase maxTravelCostFactor (+10.0)
│  └─ Increase candidateDistanceMultiplier (+1.0)
│  └─ RETRY mapping
└─ NO: Continue

Routes with failures >0?
├─ YES
│  ├─ Check log for specific stop failures
│  ├─ Increase maxTravelCostFactor
│  └─ RETRY mapping
└─ NO: SUCCESS!

Plausibility check passes?
├─ YES: Mapping complete, proceed to simulation
└─ NO
   ├─ Check for unrealistic travel times
   ├─ Adjust maxTravelCostFactor down
   └─ RETRY mapping
```

---

## File References

- Tool: `pt2matsim/work/pt2matsim-25.8-shaded.jar`
- Preparation: `src/main/java/org/matsim/project/tools/PrepareNetworkForPTMapping.java`
- Working journal: `working_journal/2025-11-06-PT-Mapper-Fix.md`
- Example configs:
  - `pt2matsim/work/ptmapper-config-artificial.xml`
  - `pt2matsim/work/ptmapper-config-merged.xml`
  - `pt2matsim/work/ptmapper-config-v2.xml`
