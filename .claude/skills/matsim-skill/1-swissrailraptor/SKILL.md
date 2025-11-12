# SwissRailRaptor PT Configuration & Troubleshooting

This skill helps configure SwissRailRaptor routing algorithm for MATSim public transit simulations and troubleshoot common PT routing issues.

## When to Activate This Skill

Activate this skill when user mentions:
- "PT agents not boarding vehicles"
- "No transfers happening"
- "Configure SwissRailRaptor"
- "Agents using direct transmission instead of PT"
- "PersonEntersVehicle events missing"
- "PT routing not working"
- "useIntermodalAccessEgress"

## Workflow

### Step 1: Diagnose Current State

First, check if agents are actually boarding PT vehicles:

```bash
# Check for boarding events
gunzip -c output/ITERS/it.0/0.events.xml.gz | grep "PersonEntersVehicle" | wc -l
```

**Expected**: >0 boarding events
**If 0**: PT routing is broken

If boarding events exist, check for transfers:

```bash
# Count boardings per agent
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10
```

**Expected**: Multiple agents with 2+ boardings (indicating transfers)
**If all agents have exactly 1 boarding**: Transfers not working

### Step 2: Identify Root Cause

Run these diagnostic checks:

**Check 1: PT configured as teleported mode?**
```bash
grep -A 5 'teleportedModeParameters' config.xml | grep 'pt'
```

If PT appears here, this is the problem. PT must NOT be in teleported modes.

**Check 2: Population plan structure**
```bash
grep -A 3 '<leg mode=' population.xml | head -20
```

Determine if plans have:
- **Simple structure**: Only `<leg mode="pt">` between activities
- **Intermodal structure**: Explicit `access_walk`, `transit_walk`, `egress_walk` legs

**Check 3: SwissRailRaptor configuration**
```bash
grep -A 10 'swissRailRaptor' config.xml
```

### Step 3: Fix Configuration

Based on diagnosis, apply fixes:

#### Fix 1: Remove PT from Teleported Modes

If PT appears in teleportedModeParameters, remove it:

```xml
<module name="routing">
  <!-- PT NOT in networkModes -->
  <param name="networkModes" value="car" />

  <!-- Only walk modes use teleportation -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk" />
    <param name="teleportedModeSpeed" value="1.388888888" />
    <param name="beelineDistanceFactor" value="1.3" />
  </parameterset>
</module>
```

#### Fix 2: Configure useIntermodalAccessEgress

**If population plans are simple** (only `<leg mode="pt">`):
```xml
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>
  <param name="transferPenaltyBaseCost" value="0.0"/>
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>
  <param name="useModeMappingForPassengers" value="false"/>
</module>
```

**If population plans have explicit access/egress legs**:
```xml
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="true"/>
  <parameterset type="accessEgressSettings">
    <param name="mode" value="walk"/>
    <param name="radius" value="1000.0"/>
  </parameterset>
</module>
```

#### Fix 3: Ensure Transit Modules Enabled

```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="qsim">
  <param name="mainMode" value="car,pt"/>
  <param name="usingTransitInMobsim" value="true"/>
</module>
```

### Step 4: Validate Transfer Stations

For transfers to work, transfer stations must share the same `stopAreaId`:

```bash
gunzip -c transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | \
  grep 'stopAreaId' | \
  head -20
```

**Expected output**:
```xml
<stopFacility id="BL11_UP" stopAreaId="086" ... />
<stopFacility id="G12_UP" stopAreaId="086" ... />
```

If transfer stations lack stopAreaId or have different IDs, transfers won't work.

### Step 5: Run Test Simulation

```bash
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="config.xml \
    --config:controller.lastIteration 5 \
    --config:controller.outputDirectory ./test_output"
```

### Step 6: Verify Results

```bash
# Check boarding events exist
gunzip -c test_output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  wc -l

# Check transfers working (multiple vehicles per agent)
gunzip -c test_output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*vehicle="\([^"]*\)".*/\1 \2/' | \
  sort
```

**Success Criteria**:
- Multiple `PersonEntersVehicle` events
- Agents board different vehicle IDs (indicating transfers)
- Sequential stop visits in events log

### Step 7: Debug Transfer Issues

If transfers still not working:

```bash
# Check if agents are stuck at transfer stations
gunzip -c test_output/ITERS/it.5/5.events.xml.gz | \
  grep "actend\|PersonEntersVehicle" | \
  grep -A 5 "pt_agent_01"
```

Common issues:
- **stopAreaId missing**: Transfer stations don't have matching stopAreaId
- **Transfer time too short**: Arrival/departure times don't align
- **Wrong transfer penalty**: Router avoids transfers due to high penalty

## Configuration Checklist

Before running PT simulation, verify:

- [ ] `transit.useTransit = true`
- [ ] `transit.routingAlgorithmType = "SwissRailRaptor"`
- [ ] `qsim.usingTransitInMobsim = true`
- [ ] PT NOT in `routing.networkModes`
- [ ] PT NOT in `teleportedModeParameters`
- [ ] `useIntermodalAccessEgress` matches population plan structure
- [ ] Transfer stations have consistent stopAreaId
- [ ] transitSchedule.xml and transitVehicles.xml exist

## Quick Diagnostic Commands

```bash
# 1. Check if PT routing is working at all
gunzip -c output/ITERS/it.0/0.events.xml.gz | grep "PersonEntersVehicle" | wc -l
# Expected: >0

# 2. Check for transfers
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10
# Expected: agents with 2+ boardings

# 3. Verify transfer station configuration
gunzip -c transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | grep 'stopAreaId' | head -20
# Expected: matching stopAreaId for transfer stations

# 4. Check config for PT teleportation (SHOULD BE EMPTY)
grep -A 5 'teleportedModeParameters' config.xml | grep 'pt'
# Expected: no output
```

## Common Error Scenarios

### Scenario 1: Zero PersonEntersVehicle Events

**Cause**: PT configured as teleported mode
**Fix**: Remove PT from `teleportedModeParameters`

### Scenario 2: Agents Board Once But No Transfers

**Cause**: Transfer stations lack matching stopAreaId
**Fix**: Regenerate schedule with stopAreaId or manually add

### Scenario 3: useIntermodalAccessEgress Mismatch

**Symptom**: 0 PersonEntersVehicle events despite correct teleportation config
**Cause**: `useIntermodalAccessEgress=true` but population plans lack access_walk legs
**Fix**: Change to `useIntermodalAccessEgress=false`

## File References

- Configuration guide: `working_journal/2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md`
- Transfer analysis: `working_journal/2025-11-11-PT-Transfer-Validation.md`
- CLAUDE.md: Lines 377-485
- Example config: `scenarios/equil/config_pt_only.xml`

## Success Indicators

When correctly configured, you should see:

1. **Events log shows sequential stop visits**:
```
VehicleArrivesAtFacility at BL02_UP
VehicleDepartsAtFacility from BL02_UP
VehicleArrivesAtFacility at BL03_UP (intermediate)
VehicleDepartsAtFacility from BL03_UP
...
VehicleArrivesAtFacility at BL14_UP
```

2. **Multiple boarding events per agent** (for transfer trips)

3. **No "direct transmission" warnings** in log

4. **Realistic travel times** in output_trips.csv
