# PT Mapping Parameter Reference

## Core Parameters

### maxLinkCandidateDistance

**Type**: Double (meters)
**Default**: 90.0
**Range**: 0.0 (artificial only) to 2000.0+

**Purpose**: Maximum distance from stop to candidate link on network.

**How it works**:
1. For each transit stop, pt2matsim finds all network links within this radius
2. If distance > 0: Attempts to map stop to real network links
3. If distance = 0: Creates artificial loop link immediately (bypass real mapping)

**Impact**:
- **Too low**: Many artificial links created (stop can't find nearby links)
- **Too high**: Slower processing, may map to inappropriate links
- **0.0**: Special mode - pure artificial links (fastest, 1-2 min)

**Tuning guide**:

| Mode | Typical Spacing | Recommended Value |
|------|----------------|-------------------|
| Dense urban bus | 200-500m | 100.0 |
| Light rail / Tram | 500-1000m | 200.0 |
| Metro / Subway | 1000-2000m | 300.0 - 500.0 |
| Rural bus | 2000m+ | 500.0 - 1000.0 |
| Disconnected network | N/A | 0.0 (artificial) |

**Example**:
```xml
<!-- Metro: Stations are far apart, need wide search -->
<param name="maxLinkCandidateDistance" value="500.0"/>

<!-- Bus: Stops are close, narrow search sufficient -->
<param name="maxLinkCandidateDistance" value="100.0"/>

<!-- Artificial mode: Bypass network entirely -->
<param name="maxLinkCandidateDistance" value="0.0"/>
```

---

### nLinkThreshold

**Type**: Integer
**Default**: 6
**Range**: 1 to 50+

**Purpose**: Number of candidate links to evaluate per stop before expanding search.

**How it works**:
1. pt2matsim searches for links within maxLinkCandidateDistance
2. If fewer than nLinkThreshold found, expands search by candidateDistanceMultiplier
3. Higher threshold = more candidates evaluated = better mapping but slower

**Impact**:
- **Too low**: May miss best candidate link
- **Too high**: Slower processing, diminishing returns

**Tuning guide**:

| Network Density | Recommended Value |
|----------------|-------------------|
| Dense urban (many links) | 6-8 |
| Suburban | 8-12 |
| Metro (sparse but important) | 10-15 |
| Rural (very sparse) | 15-20 |

**Example**:
```xml
<!-- Metro: Few links, but need to find the right one -->
<param name="nLinkThreshold" value="15"/>

<!-- Urban bus: Many links available -->
<param name="nLinkThreshold" value="8"/>
```

---

### maxTravelCostFactor

**Type**: Double
**Default**: 5.0
**Range**: 1.0 to 50.0+

**Purpose**: Multiplier for acceptable travel cost before creating artificial link.

**How it works**:
1. pt2matsim calculates "cost" to route from one stop to the next on network
2. If actual_cost > (beeline_cost × maxTravelCostFactor), gives up and creates artificial link
3. Higher factor = more tolerance for circuitous routes on network

**Impact**:
- **Too low (e.g., 2.0)**: Creates many artificial links (network routing seen as "too expensive")
- **Too high (e.g., 50.0)**: Accepts unrealistic circuitous routes
- **Goldilocks zone**: 10.0-20.0 for most scenarios

**Tuning guide**:

| Scenario | Recommended Value | Rationale |
|----------|-------------------|-----------|
| Grid network (Manhattan) | 5.0-10.0 | Direct routes available |
| Complex topology (hills, rivers) | 15.0-20.0 | Routes may be circuitous |
| Metro with barriers | 20.0-30.0 | Few crossing points |
| Disconnected clusters | 30.0+ or artificial | No direct paths |

**Example**:
```xml
<!-- Metro crossing river with few bridges -->
<param name="maxTravelCostFactor" value="20.0"/>

<!-- Bus on grid network -->
<param name="maxTravelCostFactor" value="10.0"/>
```

---

### candidateDistanceMultiplier

**Type**: Double
**Default**: 1.6
**Range**: 1.1 to 5.0

**Purpose**: Factor to expand search radius if nLinkThreshold not met.

**How it works**:
1. Initial search radius = maxLinkCandidateDistance
2. If fewer than nLinkThreshold candidates found:
   - New radius = old radius × candidateDistanceMultiplier
3. Repeats until enough candidates found or max iterations reached

**Impact**:
- **Too low (e.g., 1.1)**: Slow incremental expansion
- **Too high (e.g., 5.0)**: Jumps too far, may skip good candidates
- **Sweet spot**: 1.6-3.0

**Tuning guide**:

| Network Type | Recommended Value |
|--------------|-------------------|
| Dense (links everywhere) | 1.6 (default) |
| Moderate density | 2.0 |
| Sparse network | 3.0-4.0 |

**Example**:
```xml
<!-- Sparse metro network: Expand search aggressively -->
<param name="candidateDistanceMultiplier" value="3.0"/>
```

---

### networkRouter

**Type**: String
**Default**: SpeedyALT
**Options**: SpeedyALT, AStarLandmarks

**Purpose**: Routing algorithm for mapping stops to network.

#### SpeedyALT (Speedy Approximate Landmarks and Triangles)

**Characteristics**:
- Fast preprocessing
- Good performance on well-connected networks
- May struggle with disconnected components

**Use when**:
- Network is fully connected
- Speed is priority
- Bus networks with good coverage

#### AStarLandmarks

**Characteristics**:
- More robust routing algorithm
- Better handles disconnected network components
- Slightly slower than SpeedyALT
- Recommended for complex topologies

**Use when**:
- Network has disconnected clusters
- Metro networks with barriers (rivers, mountains)
- Getting "Network is not connected" warnings
- Process gets stuck with SpeedyALT

**Example**:
```xml
<!-- Metro with complex topology -->
<param name="networkRouter" value="AStarLandmarks"/>

<!-- Well-connected bus network -->
<param name="networkRouter" value="SpeedyALT"/>
```

---

### numOfThreads

**Type**: Integer
**Default**: 1
**Range**: 1 to system CPU count

**Purpose**: Number of parallel threads for mapping.

**Impact**:
- **More threads**: Faster mapping, higher memory usage
- **Fewer threads**: Slower but less memory

**Recommendations**:

| System | Recommended Threads | Memory Allocation |
|--------|-------------------|-------------------|
| 4 cores | 2-4 | -Xmx8g |
| 8 cores | 4-8 | -Xmx10g |
| 16+ cores | 8 | -Xmx12g |

**Example**:
```xml
<param name="numOfThreads" value="4"/>
```

```bash
# Corresponding Java command
java -Xmx10g -cp pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper config.xml
```

---

## Mode-Specific Parameters

### modeSpecificRules

**Type**: Boolean
**Default**: true

**Purpose**: Enable mode-specific mapping rules (subway, rail, tram, bus).

**When to disable**:
- Artificial link mode (maxLinkCandidateDistance=0.0)
- Simple scenarios with single PT mode
- Troubleshooting mapping failures

**Example**:
```xml
<!-- Standard mapping: Enable mode-specific rules -->
<param name="modeSpecificRules" value="true"/>

<!-- Artificial mode: Disable for simplicity -->
<param name="modeSpecificRules" value="false"/>
```

---

### routingWithCandidateDistance

**Type**: Boolean
**Default**: true

**Purpose**: Use candidate distance heuristic during routing.

**When to disable**:
- Artificial link mode
- Routing behaves unexpectedly

**Example**:
```xml
<!-- Artificial mode -->
<param name="routingWithCandidateDistance" value="false"/>
```

---

## Configuration Presets

### Preset 1: Artificial Link Mode (Fastest)

**Use when**: Testing, disconnected network, or PT-only scenario

```xml
<module name="ptmapper">
  <param name="networkFile" value="network.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <param name="maxLinkCandidateDistance" value="0.0"/>
  <param name="modeSpecificRules" value="false"/>
  <param name="routingWithCandidateDistance" value="false"/>
  <param name="numOfThreads" value="4"/>
</module>
```

**Expected time**: 1-2 minutes
**Result**: 100% artificial links (pt_STATION_UP/DN)

---

### Preset 2: Metro Network (Real Mapping)

**Use when**: Metro/subway with reasonable network coverage

```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Wide search for metro stations -->
  <param name="maxLinkCandidateDistance" value="500.0"/>
  <param name="nLinkThreshold" value="15"/>
  <param name="maxTravelCostFactor" value="20.0"/>
  <param name="candidateDistanceMultiplier" value="3.0"/>

  <!-- Robust router for potential disconnections -->
  <param name="networkRouter" value="AStarLandmarks"/>

  <param name="modeSpecificRules" value="true"/>
  <param name="numOfThreads" value="4"/>
</module>
```

**Expected time**: 10-30 minutes
**Result**: <20% artificial links (ideal)

---

### Preset 3: Urban Bus Network

**Use when**: Dense bus network with good coverage

```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Tighter search for bus stops -->
  <param name="maxLinkCandidateDistance" value="100.0"/>
  <param name="nLinkThreshold" value="8"/>
  <param name="maxTravelCostFactor" value="10.0"/>
  <param name="candidateDistanceMultiplier" value="1.6"/>

  <!-- Fast router for well-connected network -->
  <param name="networkRouter" value="SpeedyALT"/>

  <param name="modeSpecificRules" value="true"/>
  <param name="numOfThreads" value="4"/>
</module>
```

**Expected time**: 15-45 minutes
**Result**: <5% artificial links (ideal)

---

### Preset 4: Challenging Metro (Desperate Measures)

**Use when**: Metro mapping keeps failing or getting stuck

```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Very wide search -->
  <param name="maxLinkCandidateDistance" value="1000.0"/>
  <param name="nLinkThreshold" value="20"/>
  <param name="maxTravelCostFactor" value="30.0"/>
  <param name="candidateDistanceMultiplier" value="4.0"/>

  <!-- Most robust router -->
  <param name="networkRouter" value="AStarLandmarks"/>

  <param name="modeSpecificRules" value="true"/>
  <param name="numOfThreads" value="4"/>
</module>
```

**Expected time**: 30-60 minutes
**Result**: 20-40% artificial links (acceptable compromise)

---

## Troubleshooting Decision Tree

```
Is mapping stuck (>10 min no progress)?
├─ YES
│  ├─ Try 1: Switch to AStarLandmarks
│  ├─ Try 2: Increase maxTravelCostFactor to 30.0
│  └─ Try 3: Use artificial mode (maxLinkCandidateDistance=0.0)
└─ NO: Continue to next question

Are there too many artificial links (>30%)?
├─ YES
│  ├─ Increase maxLinkCandidateDistance (×2)
│  ├─ Increase maxTravelCostFactor (+10.0)
│  └─ Increase candidateDistanceMultiplier to 3.0
└─ NO: Continue to next question

Are there route failures?
├─ YES
│  ├─ Check log for specific errors
│  ├─ Ensure network covers all stop coordinates
│  └─ Increase maxTravelCostFactor
└─ NO: Mapping successful!
```

---

## Validation Commands

### Check Mapping Progress

```bash
# Watch log file
tail -f pt2matsim/work/ptmapper.log

# Look for completion message
grep -i "routes with failures" pt2matsim/work/ptmapper.log
```

### Calculate Artificial Link Percentage

```bash
# Count artificial links
ARTIFICIAL=$(gunzip -c network-with-pt.xml.gz | grep -c 'pt_.*_UP')

# Count total stops
TOTAL=$(grep -c '<stopFacility' transitSchedule.xml)

# Calculate percentage
echo "scale=2; $ARTIFICIAL * 100 / $TOTAL" | bc
# Output: e.g., 8.50 (8.5% artificial - good for real mapping)
```

### Check Network Mode Coverage

```bash
# Count PT-enabled links
gunzip -c network-with-pt.xml.gz | grep 'modes=' | grep 'pt' | wc -l

# Count artificial links specifically
gunzip -c network-with-pt.xml.gz | grep 'id="pt_' | wc -l
```

---

## Performance Benchmarks

Based on Taipei Metro mapping experience:

| Configuration | Network Size | Stops | Time | Artificial % | Outcome |
|--------------|-------------|-------|------|-------------|---------|
| Artificial mode | Any | 120 | 1 min | 100% | Success (testing) |
| Metro preset | 50K links | 120 | 25 min | 15% | Success (production) |
| Challenging preset | 50K links | 120 | 45 min | 25% | Success (difficult) |
| Default params | 50K links | 120 | STUCK | N/A | Failure (hung) |

---

## File References

- Tool: `pt2matsim/work/pt2matsim-25.8-shaded.jar`
- Preparation: `src/main/java/org/matsim/project/tools/PrepareNetworkForPTMapping.java`
- Working journal: `working_journal/2025-11-06-PT-Mapper-Fix.md`
- Example configs: `pt2matsim/work/ptmapper-config-*.xml`
- CLAUDE.md: Lines 163-212
