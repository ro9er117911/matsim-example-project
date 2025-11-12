# PT Network Mapping with pt2matsim

This skill helps map transit schedules onto road networks using the pt2matsim library, troubleshoot mapping issues, and optimize parameters for different network scenarios.

## When to Activate This Skill

Activate this skill when user mentions:
- "Map transit schedule to network"
- "Run PT mapper"
- "PT mapping is stuck/slow"
- "Too many artificial links"
- "Network is not connected"
- "PublicTransitMapper"
- "pt2matsim mapping"

## Workflow

### Step 1: Validate Prerequisites

Before running PT mapper, ensure you have:

```bash
# Check required files exist
ls -lh transitSchedule.xml
ls -lh network.xml.gz
ls -lh pt2matsim/work/pt2matsim-25.8-shaded.jar

# Count stops and routes
grep -c '<stopFacility' transitSchedule.xml
grep -c '<transitRoute' transitSchedule.xml

# Check network size
gunzip -c network.xml.gz | grep -c '<link '
```

**Critical**: Network must be **multimodal** (car + walk + rail) for best results, even for PT-only scenarios.

### Step 2: Prepare Network for PT Mapping

Run network cleaning tool to ensure connectivity:

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="network.xml.gz network-cleaned.xml.gz"
```

This tool:
1. Ensures all subway/rail links have 'pt' mode
2. Runs NetworkUtils.cleanNetwork() to remove disconnected components
3. Reports mode statistics

**Validation**:
```bash
# Check for "Network is not connected" warnings
# Should see: "Network cleaning complete"
```

### Step 3: Assess Network Coverage

Determine which mapping strategy to use:

```bash
# Extract stop coordinates
grep -oP 'x="\K[^"]*' transitSchedule.xml | head -20
grep -oP 'y="\K[^"]*' transitSchedule.xml | head -20

# Extract network bounds
gunzip -c network-cleaned.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | head -1  # Min X
gunzip -c network-cleaned.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | tail -1  # Max X
gunzip -c network-cleaned.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | head -1  # Min Y
gunzip -c network-cleaned.xml.gz | grep -oP 'y="\K[^"]*' | sort -n | tail -1  # Max Y
```

**Decision Tree**:
- **Stops within network bounds**: Use real network mapping (Step 4A)
- **Stops outside network bounds**: Use artificial link mode (Step 4B)
- **Unsure or mixed**: Start with artificial mode (fastest, 1-2 minutes)

### Step 4A: Real Network Mapping (Recommended if network covers stops)

**Create PT mapper config**:
```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim/work/ptmapper-config.xml
```

**Edit configuration** for your scenario type:

**For Metro/Subway** (large station spacing):
```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Metro parameters: wider search radius -->
  <param name="maxLinkCandidateDistance" value="500.0"/>
  <param name="nLinkThreshold" value="15"/>
  <param name="maxTravelCostFactor" value="20.0"/>
  <param name="candidateDistanceMultiplier" value="3.0"/>

  <!-- Robust router for potentially disconnected network -->
  <param name="networkRouter" value="AStarLandmarks"/>

  <!-- Performance -->
  <param name="numOfThreads" value="4"/>
</module>
```

**For Bus** (dense station spacing):
```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Bus parameters: tighter search -->
  <param name="maxLinkCandidateDistance" value="100.0"/>
  <param name="nLinkThreshold" value="8"/>
  <param name="maxTravelCostFactor" value="10.0"/>
  <param name="candidateDistanceMultiplier" value="1.6"/>

  <!-- Fast router for connected network -->
  <param name="networkRouter" value="SpeedyALT"/>

  <param name="numOfThreads" value="4"/>
</module>
```

**Run mapping**:
```bash
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config.xml
```

**Monitor progress**:
- Watch for "Routes with failures: 0" (success)
- If stuck >10 minutes: Process may be hung (see troubleshooting)

### Step 4B: Artificial Link Mode (Fast, Independent PT Network)

**For PT-only or disconnected networks**:

```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Artificial mode: distance = 0 -->
  <param name="maxLinkCandidateDistance" value="0.0"/>

  <!-- Disable mode-specific rules for pure artificial -->
  <param name="modeSpecificRules" value="false"/>
  <param name="routingWithCandidateDistance" value="false"/>

  <param name="numOfThreads" value="4"/>
</module>
```

**Advantages**:
- Extremely fast (1-2 minutes for large networks)
- No network connectivity issues
- Works for any scenario

**Disadvantages**:
- Creates artificial loop links (pt_STATION_UP, pt_STATION_DN)
- No integration with ground transportation

**Run mapping**:
```bash
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config.xml
```

Expected completion: <2 minutes

### Step 5: Validate Mapping Results

```bash
# Check completion message
tail -20 pt2matsim/work/ptmapper.log

# Expected: "Routes with failures: 0"
# Warning: "Routes with failures: 15" means incomplete mapping

# Count artificial links created
gunzip -c network-with-pt.xml.gz | grep -c 'pt_.*_UP'

# Check total stops
grep -c '<stopFacility' transitSchedule.xml

# Calculate artificial link percentage
# Acceptable: <10% for real network mapping, 100% for artificial mode
```

**Plausibility check**:
```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  network-with-pt.xml.gz transitSchedule-mapped.xml.gz
```

Expected output:
```
Checking plausibility of mapped transit schedule...
✓ All routes are plausible
✓ No unrealistic travel times detected
```

### Step 6: Troubleshoot Issues

**Issue 1: Process Stuck (>10 min with no progress)**

**Symptoms**:
- Log shows "Network is not connected" warnings repeatedly
- CPU usage drops to near zero
- No progress for >10 minutes

**Immediate fix**:
1. Kill the process (Ctrl+C)
2. Switch to artificial link mode (maxLinkCandidateDistance=0.0)
3. Re-run mapping

**Long-term fix**:
1. Expand OSM extract to cover all PT stops
2. Ensure network is connected via PrepareNetworkForPTMapping
3. Use robust router: networkRouter=AStarLandmarks

**Issue 2: Too Many Artificial Links (>30%)**

**Symptom**:
```bash
# Artificial link percentage high
gunzip -c network-with-pt.xml.gz | grep -c 'pt_.*_UP'  # e.g., 450
grep -c '<stopFacility' transitSchedule.xml  # e.g., 500
# 450/500 = 90% artificial (too high for real mapping)
```

**Fixes**:
- Increase maxLinkCandidateDistance to 500m or 1000m
- Increase maxTravelCostFactor to 20.0 or 30.0
- Increase candidateDistanceMultiplier to 3.0
- Switch to AStarLandmarks router

**Issue 3: Routes With Failures**

**Symptom**:
```
Routes with failures: 15
```

**Diagnosis**:
```bash
# Check log for specific route failures
grep -i "failure\|error\|could not map" pt2matsim/work/ptmapper.log
```

**Common causes**:
- Stop coordinates outside network bounds
- Network not connected between stops
- maxTravelCostFactor too low

**Fixes**:
- Increase maxTravelCostFactor
- Expand network coverage
- Use artificial mode for failed routes

### Step 7: Integrate Mapped Network

After successful mapping:

```bash
# Copy mapped files to scenario directory
cp network-with-pt.xml.gz scenarios/equil/network-with-pt.xml.gz
cp transitSchedule-mapped.xml.gz scenarios/equil/transitSchedule.xml.gz

# Update config.xml to use mapped schedule
# <param name="transitScheduleFile" value="transitSchedule.xml.gz"/>
# <param name="networkFile" value="network-with-pt.xml.gz"/>
```

## Parameter Tuning Guide

### maxLinkCandidateDistance

**Purpose**: Maximum distance (meters) from stop to candidate network link

**Values**:
- **0.0**: Artificial mode (no real network mapping)
- **50-100m**: Dense urban bus networks
- **100-200m**: Light rail, tram
- **300-500m**: Metro, subway
- **1000m+**: Rural bus, desperate measures

**When to increase**: Too many artificial links created

### nLinkThreshold

**Purpose**: Number of link candidates to consider per stop

**Values**:
- **6-8**: Bus (default)
- **10-15**: Metro
- **20+**: Sparse networks with long distances

**When to increase**: Mapping fails for sparse networks

### maxTravelCostFactor

**Purpose**: Multiplier for travel cost before creating artificial link

**Values**:
- **5.0**: Default (strict)
- **10.0**: Relaxed
- **15.0-20.0**: Metro with challenging topology
- **30.0+**: Desperate measures to avoid artificial links

**When to increase**: Too many artificial links, or process stuck

### networkRouter

**Purpose**: Routing algorithm for mapping

**Options**:
- **SpeedyALT**: Fast, works for well-connected networks
- **AStarLandmarks**: Robust, handles disconnected components better

**When to use AStarLandmarks**:
- Process gets stuck
- "Network is not connected" warnings
- Metro networks with complex topology

### numOfThreads

**Purpose**: Parallel processing

**Values**: 1, 2, 4, 8

**Trade-off**: More threads = faster, but uses more memory

## Decision Matrix

| Network Type | Coverage | Recommended Config |
|--------------|----------|-------------------|
| Metro, good network | Stops within bounds | maxLinkCandidateDistance=500, maxTravelCostFactor=20, AStarLandmarks |
| Metro, sparse network | Some stops outside | maxLinkCandidateDistance=1000, maxTravelCostFactor=30, AStarLandmarks |
| Bus, urban | Full coverage | maxLinkCandidateDistance=100, maxTravelCostFactor=10, SpeedyALT |
| Any, disconnected | Any | maxLinkCandidateDistance=0 (artificial mode) |
| Testing | Any | maxLinkCandidateDistance=0 (fastest) |

## File References

- Tool: `pt2matsim/work/pt2matsim-25.8-shaded.jar`
- Working journal: `working_journal/2025-11-06-PT-Mapper-Fix.md`
- Preparation tool: `src/main/java/org/matsim/project/tools/PrepareNetworkForPTMapping.java`
- CLAUDE.md: Lines 163-212
- Example configs: `pt2matsim/work/ptmapper-config-*.xml`

## Success Criteria

After successful mapping:
- [ ] "Routes with failures: 0" in log
- [ ] network-with-pt.xml.gz created
- [ ] transitSchedule-mapped.xml.gz created
- [ ] Artificial link percentage is acceptable (<10% for real mapping, 100% for artificial)
- [ ] Plausibility check passes
- [ ] Mapping completed in reasonable time (<10 min for artificial, <30 min for real)
