# Troubleshooting Matrix

Quick reference for common MATSim issues across all skills.

## SwissRailRaptor Issues

| Symptom | Likely Cause | Quick Fix | Detailed Reference |
|---------|--------------|-----------|-------------------|
| 0 PersonEntersVehicle events | PT in teleportedModeParameters | Remove PT from teleported modes | [SwissRailRaptor SKILL](../1-swissrailraptor/SKILL.md#fix-1-remove-pt-from-teleported-modes) |
| Agents board once, no transfers | Missing/mismatched stopAreaId | Check transfer stations share stopAreaId | [SwissRailRaptor SKILL](../1-swissrailraptor/SKILL.md#step-4-validate-transfer-stations) |
| 0 events with useIntermodalAccessEgress=true | Plans lack access_walk legs | Change to useIntermodalAccessEgress=false | [SwissRailRaptor reference](../1-swissrailraptor/reference.md#useintermodalaccessegress) |
| Transfers exist but unrealistic | Transfer penalty too low/high | Adjust transferPenaltyBaseCost | [SwissRailRaptor reference](../1-swissrailraptor/reference.md#transferpenaltybasecost) |
| Agents prefer walking over PT | PT not attractive enough | Check scoring parameters | [SwissRailRaptor examples](../1-swissrailraptor/examples.md#example-2-multimodal-scenario-with-car--pt) |

---

## PT Mapping Issues

| Symptom | Likely Cause | Quick Fix | Detailed Reference |
|---------|--------------|-----------|-------------------|
| Process stuck >10 min | Network disconnected / SpeedyALT fails | Switch to AStarLandmarks or artificial mode | [PT Mapping SKILL](../2-pt-mapping/SKILL.md#issue-1-process-stuck-10-min-with-no-progress) |
| Too many artificial links (>30%) | Search radius too small | Increase maxLinkCandidateDistance to 500m+ | [PT Mapping SKILL](../2-pt-mapping/SKILL.md#issue-2-too-many-artificial-links-30) |
| Routes with failures >0 | Stops outside network bounds | Increase maxTravelCostFactor or expand network | [PT Mapping SKILL](../2-pt-mapping/SKILL.md#issue-3-routes-with-failures) |
| Mapping extremely slow (>1 hour) | numOfThreads=1 or complex network | Increase threads to 4-8, or use artificial mode | [PT Mapping reference](../2-pt-mapping/reference.md#numofthreads) |
| "Network is not connected" warnings | Disconnected components | Run PrepareNetworkForPTMapping first | [PT Mapping SKILL](../2-pt-mapping/SKILL.md#step-2-prepare-network-for-pt-mapping) |

---

## Network Validation Issues

| Symptom | Likely Cause | Quick Fix | Detailed Reference |
|---------|--------------|-----------|-------------------|
| Network is not connected | Isolated clusters | Run PrepareNetworkForPTMapping | [Network Validation SKILL](../3-network-validation/SKILL.md#step-3-run-automated-network-cleaning) |
| Zero-length links | Coordinate rounding / OSM import | Set minimum length 1.0m in generation | [Network Validation SKILL](../3-network-validation/SKILL.md#issue-2-zero-length-links) |
| Mode mismatch error | Config references modes not in network | Add modes to network or remove from config | [Network Validation SKILL](../3-network-validation/SKILL.md#issue-3-mode-mismatch) |
| Subway links missing 'pt' mode | Network not prepared for PT | Run PrepareNetworkForPTMapping | [Network Validation SKILL](../3-network-validation/SKILL.md#issue-4-missing-pt-modes) |
| Link not found in network | Population references invalid links | Validate population link references | [Validation Commands](validation-commands.md#validate-activity-link-references) |

---

## Simulation Execution Issues

| Symptom | Likely Cause | Quick Fix | Detailed Reference |
|---------|--------------|-----------|-------------------|
| Simulation doesn't converge | Too few iterations or bad scoring | Increase iterations to 50-100 | [Simulation SKILL](../4-simulation/SKILL.md#issue-1-simulation-doesnt-converge) |
| OutOfMemoryError | Heap too small | Increase: java -Xmx16g | [Simulation SKILL](../4-simulation/SKILL.md#issue-2-out-of-memory) |
| Wrong coordinate system error | CRS mismatch across files | Ensure consistent CRS (EPSG:3826 for Taiwan) | [Simulation SKILL](../4-simulation/SKILL.md#issue-3-wrong-coordinate-system) |
| Agent XXX is stuck | stuckTime too short or bad network | Increase stuckTime to 30s, check activity links | [Simulation SKILL](../4-simulation/SKILL.md#issue-4-stuck-agents) |
| No PT usage in results | Transit modules not enabled | Set useTransit=true, usingTransitInMobsim=true | [Simulation SKILL](../4-simulation/SKILL.md#pt-only-scenario) |

---

## GTFS Conversion Issues

| Symptom | Likely Cause | Quick Fix | Detailed Reference |
|---------|--------------|-----------|-------------------|
| Stops outside network bounds | Wrong CRS | Use ConvertGtfsCoordinates tool | [GTFS Conversion SKILL](../5-gtfs-conversion/SKILL.md#issue-1-wrong-crs) |
| Empty GTFS output | Invalid zip or missing files | Validate zip has stops.txt, routes.txt, trips.txt | [GTFS Conversion SKILL](../5-gtfs-conversion/SKILL.md#issue-2-empty-gtfs) |
| Network doesn't cover GTFS | OSM extract too small | Expand OSM extract or filter GTFS | [GTFS Conversion SKILL](../5-gtfs-conversion/SKILL.md#issue-3-network-mismatch) |

---

## Via Export Issues

| Symptom | Likely Cause | Quick Fix | Detailed Reference |
|---------|--------------|-----------|-------------------|
| ImportError: No module 'lxml' | Missing Python dependency | pip install lxml | [Via Export SKILL](../6-via-export/SKILL.md#issue-1-missing-python-dependencies) |
| Events file not filtered (same size) | Missing --export-filtered-events flag | Re-run with flag | [Via Export SKILL](../6-via-export/SKILL.md#issue-2-large-unfiltered-events) |
| Empty tracks CSV | Agent ID mismatch | Check agent IDs in plans vs events | [Via Export SKILL](../6-via-export/SKILL.md#issue-3-empty-tracks-csv) |

---

## Decision Trees

### PT Routing Not Working

```
Are agents boarding at all?
├─ NO (0 PersonEntersVehicle events)
│  ├─ Check: Is PT in teleportedModeParameters?
│  │  └─ YES → Remove PT from teleported modes
│  ├─ Check: useIntermodalAccessEgress=true but plans lack access_walk?
│  │  └─ YES → Change to useIntermodalAccessEgress=false
│  └─ Check: transitScheduleFile and vehiclesFile exist?
│     └─ NO → Verify file paths
└─ YES (some boarding events)
   └─ Are transfers working?
      ├─ NO (all agents board exactly once)
      │  └─ Check stopAreaId on transfer stations
      └─ YES → PT routing working correctly!
```

### PT Mapping Stuck

```
Is process stuck (>10 min no progress)?
├─ YES
│  ├─ Try 1: Switch to AStarLandmarks router
│  ├─ Try 2: Increase maxTravelCostFactor to 30.0
│  └─ Try 3: Use artificial mode (maxLinkCandidateDistance=0.0)
└─ NO
   └─ Are there too many artificial links (>30%)?
      ├─ YES
      │  ├─ Increase maxLinkCandidateDistance (×2)
      │  ├─ Increase maxTravelCostFactor (+10.0)
      │  └─ Increase candidateDistanceMultiplier to 3.0
      └─ NO → Mapping successful!
```

---

## Common Root Causes

### Root Cause 1: Missing Ground Network

**Affects**: SwissRailRaptor routing, ClassCastException errors

**Symptoms**:
- ClassCastException: TransitPassengerRoute cannot be cast to NetworkRoute
- Agents can't reach PT stations

**Why**: MATSim requires multimodal network (car+walk+rail) even for PT-only scenarios for access/egress routing.

**Solution**: Build complete multimodal network with Osm2MultimodalNetwork

---

### Root Cause 2: PT Configured as Teleported Mode

**Affects**: SwissRailRaptor routing completely bypassed

**Symptoms**:
- 0 PersonEntersVehicle events
- Direct transmission instead of sequential stops

**Why**: When PT is in teleportedModeParameters, MATSim uses beeline routing instead of SwissRailRaptor.

**Solution**: Remove PT from teleportedModeParameters, keep only in transit module

---

### Root Cause 3: Network Not Connected

**Affects**: PT mapping hangs, simulation routing fails

**Symptoms**:
- PT mapper stuck with "Network is not connected" warnings
- Agents stuck at activities

**Why**: Network has isolated clusters unreachable from each other.

**Solution**: Run PrepareNetworkForPTMapping to clean network

---

### Root Cause 4: CRS Mismatch

**Affects**: All workflows, agents in wrong locations

**Symptoms**:
- Coordinates don't align
- Routing fails inexplicably

**Why**: GTFS (EPSG:4326), network (EPSG:3826), and population use different coordinate systems.

**Solution**: Ensure consistent CRS across all files, use ConvertGtfsCoordinates for GTFS

---

## Cross-Skill Validation Sequence

When troubleshooting complex issues, validate in this order:

1. **Network Structure** (Network Validation skill)
   - [ ] Network loads without errors
   - [ ] No "network is not connected" warnings
   - [ ] Modes in config match network

2. **PT Schedule** (GTFS Conversion / PT Mapping skills)
   - [ ] transitSchedule.xml and transitVehicles.xml exist
   - [ ] Stops have valid coordinates
   - [ ] Artificial link percentage acceptable

3. **SwissRailRaptor Config** (SwissRailRaptor skill)
   - [ ] PT NOT in teleportedModeParameters
   - [ ] useIntermodalAccessEgress matches population structure
   - [ ] Transfer stations have matching stopAreaId

4. **Simulation** (Simulation skill)
   - [ ] Run with 10 iterations first
   - [ ] Check for boarding events
   - [ ] Validate convergence

5. **Export** (Via Export skill)
   - [ ] Only after simulation succeeds
   - [ ] Verify compression ratio
