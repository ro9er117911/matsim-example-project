# SwissRailRaptor Configuration Reference

## Parameter Documentation

### useIntermodalAccessEgress

**Critical Setting**: Controls how SwissRailRaptor interprets population plans.

#### When useIntermodalAccessEgress = true

SwissRailRaptor **expects** population plans with **explicit leg segments**:

```xml
<activity type="home" x="..." y="..."/>
<leg mode="access_walk">...</leg>      <!-- Walk to nearest PT station -->
<leg mode="pt">...</leg>               <!-- First PT segment -->
<leg mode="transit_walk">...</leg>     <!-- Walk between transfer stations -->
<leg mode="pt">...</leg>               <!-- Second PT segment -->
<leg mode="egress_walk">...</leg>      <!-- Walk from station to destination -->
<activity type="work" x="..." y="..."/>
```

**Requirements**:
- Population plans must have access_walk/egress_walk/transit_walk legs
- Must configure accessEgressSettings in swissRailRaptor module

**Configuration**:
```xml
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="true"/>
  <parameterset type="accessEgressSettings">
    <param name="mode" value="walk"/>
    <param name="radius" value="1000.0"/>  <!-- Max walk distance to station (m) -->
  </parameterset>
</module>
```

#### When useIntermodalAccessEgress = false (RECOMMENDED for simple scenarios)

SwissRailRaptor works directly with **activity coordinates**:

```xml
<activity type="home" x="296356.46" y="2766793.71"/>
<leg mode="pt">...</leg>                <!-- SwissRailRaptor fills in details -->
<activity type="work" x="302503.61" y="2771706.94"/>
```

**How it works**:
1. Router finds nearest PT station to home activity (access point)
2. Computes shortest PT path with transfers if needed
3. Finds nearest PT station to work activity (egress point)
4. Expands single `<leg mode="pt">` into actual vehicle boardings

**Configuration**:
```xml
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>
</module>
```

**Result**: Transfers work correctly; agents produce multiple `PersonEntersVehicle` events.

### Rule of Thumb

| Population Plan Structure | useIntermodalAccessEgress |
|---------------------------|---------------------------|
| Only `<leg mode="pt">` | `false` |
| Has access_walk/egress_walk legs | `true` |
| Unsure | Start with `false` |

---

## Transfer Configuration

### transferPenaltyBaseCost

**Type**: Double (seconds equivalent cost)
**Default**: 0.0
**Purpose**: Fixed penalty added for each transfer

**When to adjust**:
- **Set to 0.0**: For testing, to ensure agents use PT at all
- **Set to 120.0-300.0**: Realistic modeling of transfer inconvenience
- **Set higher**: Discourage transfers (agents prefer longer direct routes)

```xml
<param name="transferPenaltyBaseCost" value="0.0"/>
```

### transferPenaltyCostPerTravelTimeHour

**Type**: Double (per hour)
**Default**: 0.0
**Purpose**: Penalty proportional to transfer waiting time

**Formula**: `total_penalty = baseCost + (waitTime_hours × costPerHour)`

```xml
<param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>
```

### Transfer Station Requirements

For transfers to work, both conditions must be met:

1. **Stops must share stopAreaId**:
```xml
<!-- Transfer between Blue Line and Green Line at Station 11/12 -->
<stopFacility id="BL11_UP" stopAreaId="086" x="..." y="..."/>
<stopFacility id="G12_UP" stopAreaId="086" x="..." y="..."/>
```

2. **Departure times must align** (arrival time + transfer time ≤ next departure)

---

## Mode Configuration

### useModeMappingForPassengers

**Type**: Boolean
**Default**: false
**Purpose**: Maps PT submodes (bus, subway, tram) to generic "pt" mode

**When to use**:
- **false**: Simple scenarios with single PT mode
- **true**: Complex scenarios with mode-specific routing

```xml
<param name="useModeMappingForPassengers" value="false"/>
```

---

## Integration with Other Modules

### Required Transit Module Configuration

```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>
```

### Required QSim Configuration

```xml
<module name="qsim">
  <!-- PT must be in mainMode -->
  <param name="mainMode" value="car,pt"/>

  <!-- Enable transit in mobility simulation -->
  <param name="usingTransitInMobsim" value="true"/>
</module>
```

### Critical Routing Configuration

```xml
<module name="routing">
  <!-- PT must NOT be in networkModes -->
  <!-- networkModes are routed on network graph -->
  <param name="networkModes" value="car"/>

  <!-- PT must NOT be in teleportedModeParameters -->
  <!-- Teleported modes skip routing entirely -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
  </parameterset>
</module>
```

**Why PT is excluded**:
- Not in `networkModes`: PT uses SwissRailRaptor, not network router
- Not in `teleportedModeParameters`: PT needs actual routing, not beeline

---

## Troubleshooting Matrix

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 0 PersonEntersVehicle events | PT in teleportedModeParameters | Remove PT from teleported modes |
| Agents board once, no transfers | Missing/mismatched stopAreaId | Check transfer stations share stopAreaId |
| 0 events with useIntermodalAccessEgress=true | Plans lack access_walk legs | Change to useIntermodalAccessEgress=false |
| Transfers exist but unrealistic | Transfer penalty too low/high | Adjust transferPenaltyBaseCost |
| Agents prefer walking over PT | PT not attractive enough | Check scoring parameters (see scoring module) |

---

## Validation Commands

### Check SwissRailRaptor is Active

```bash
# Should see "SwissRailRaptor" in log
grep -i "swissrailraptor\|transit.*router" output/logfile.log
```

### Verify PT Routing Results

```bash
# Count distinct vehicles per agent (transfers = >1 vehicle)
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*vehicle="\([^"]*\)".*/\1 \2/' | \
  awk '{agents[$1]++; vehicles[$1]=vehicles[$1] " " $2} END {for (a in agents) print a, agents[a], vehicles[a]}' | \
  sort -k2 -rn | head -10
```

Expected output:
```
pt_agent_01 3 veh_BL01 veh_G05 veh_R10
pt_agent_02 2 veh_BL03 veh_G07
pt_agent_03 1 veh_BL01
```

### Check Transfer Station Configuration

```bash
# Extract stopAreaId for potential transfer stations
gunzip -c transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | \
  grep 'stopAreaId' | \
  sed 's/.*id="\([^"]*\)".*stopAreaId="\([^"]*\)".*/\2 \1/' | \
  sort | uniq -c | \
  awk '$1 > 1'  # Only show stops with multiple facilities (transfer candidates)
```

Expected output:
```
2 086 BL11_UP
2 086 G12_UP
```

---

## Performance Tuning

### Speed vs. Accuracy

SwissRailRaptor is fast by design, but can be tuned:

**Fast routing** (testing):
```xml
<param name="transferPenaltyBaseCost" value="0.0"/>
<param name="useModeMappingForPassengers" value="false"/>
```

**Realistic routing** (production):
```xml
<param name="transferPenaltyBaseCost" value="180.0"/>  <!-- 3 minutes -->
<param name="transferPenaltyCostPerTravelTimeHour" value="600.0"/>
```

### Memory Considerations

SwissRailRaptor builds routing data structures in memory. For large networks:
- Increase JVM heap: `java -Xmx10g`
- Monitor log for "OutOfMemoryError"

---

## File References

- Working journal: `working_journal/2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md`
- Transfer analysis: `working_journal/2025-11-11-PT-Transfer-Validation.md`
- CLAUDE.md: Lines 377-485
- Example configs:
  - `scenarios/equil/config_pt_only.xml`
  - `defaultConfig.xml` (lines 494-519)
