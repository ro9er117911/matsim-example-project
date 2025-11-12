# SwissRailRaptor Configuration Examples

## Example 1: PT-Only Scenario with Simple Plans

**Use Case**: Testing PT network with minimal complexity, no car mode, simple population plans.

**Population Plan Structure**:
```xml
<person id="pt_agent_01">
  <plan selected="yes">
    <activity type="home" link="81226" x="296356.46" y="2766793.71" end_time="07:15:00"/>
    <leg mode="pt"/>
    <activity type="work" link="81226" x="302503.61" y="2771706.94" end_time="17:30:00"/>
    <leg mode="pt"/>
    <activity type="home" link="81226" x="296356.46" y="2766793.71"/>
  </plan>
</person>
```

**Configuration**:
```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="routing">
  <!-- No network modes (PT-only) -->
  <param name="networkModes" value=""/>
  <param name="accessEgressType" value="accessEgressModeToLink"/>
  <param name="clearDefaultTeleportedModeParams" value="true"/>

  <!-- Walk for access/egress (auto-calculated) -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
    <param name="beelineDistanceFactor" value="1.3"/>
  </parameterset>
</module>

<module name="qsim">
  <!-- Only PT in mainMode (no car) -->
  <param name="mainMode" value="pt"/>
  <param name="usingTransitInMobsim" value="true"/>
  <param name="numberOfThreads" value="4"/>
</module>

<module name="swissRailRaptor">
  <!-- Simple plans: useIntermodalAccessEgress = false -->
  <param name="useIntermodalAccessEgress" value="false"/>

  <!-- Zero penalties for testing -->
  <param name="transferPenaltyBaseCost" value="0.0"/>
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>

  <!-- Simple passenger routing -->
  <param name="useModeMappingForPassengers" value="false"/>
</module>

<module name="controller">
  <param name="lastIteration" value="10"/>
  <param name="outputDirectory" value="./output_pt_only"/>
</module>
```

**Expected Results**:
- Agents board PT vehicles at stops nearest to home/work
- Multiple `PersonEntersVehicle` events if transfers needed
- Routes follow actual transit schedule

**Validation**:
```bash
gunzip -c output_pt_only/ITERS/it.10/10.events.xml.gz | \
  grep "PersonEntersVehicle" | wc -l
# Should be > 0
```

---

## Example 2: Multimodal Scenario with Car + PT

**Use Case**: Agents can choose between car and PT, realistic transfer penalties.

**Population Plan Structure**:
```xml
<person id="agent_01">
  <plan selected="yes">
    <activity type="home" link="1001" x="..." y="..." end_time="08:00:00"/>
    <leg mode="car"/>
    <activity type="work" link="2001" x="..." y="..." end_time="18:00:00"/>
    <leg mode="pt"/>
    <activity type="home" link="1001" x="..." y="..."/>
  </plan>
</person>
```

**Configuration**:
```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="routing">
  <!-- Car uses network routing -->
  <param name="networkModes" value="car"/>
  <param name="accessEgressType" value="accessEgressModeToLink"/>

  <!-- Walk for PT access/egress -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
  </parameterset>
</module>

<module name="qsim">
  <!-- Both car and PT simulated -->
  <param name="mainMode" value="car,pt"/>
  <param name="usingTransitInMobsim" value="true"/>
  <param name="numberOfThreads" value="4"/>
</module>

<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>

  <!-- Realistic transfer penalties -->
  <param name="transferPenaltyBaseCost" value="180.0"/>  <!-- 3 minutes fixed cost -->
  <param name="transferPenaltyCostPerTravelTimeHour" value="600.0"/>  <!-- 10 min per hour wait -->

  <param name="useModeMappingForPassengers" value="false"/>
</module>

<module name="scoring">
  <!-- Make PT competitive with car -->
  <parameterset type="modeParams">
    <param name="mode" value="car"/>
    <param name="constant" value="-2.0"/>
    <param name="marginalUtilityOfTraveling_util_hr" value="-6.0"/>
  </parameterset>
  <parameterset type="modeParams">
    <param name="mode" value="pt"/>
    <param name="constant" value="0.0"/>
    <param name="marginalUtilityOfTraveling_util_hr" value="-4.0"/>
  </parameterset>
</module>

<module name="controller">
  <param name="lastIteration" value="50"/>
  <param name="outputDirectory" value="./output_multimodal"/>
</module>
```

**Expected Results**:
- Agents choose between car and PT based on scoring
- Mode distribution converges over iterations
- Transfer penalties affect route choices

**Validation**:
```bash
# Check mode distribution
tail -5 output_multimodal/modestats.csv

# Expected output:
# ITERATION    car    pt    walk
# 46          120    80     15
# 47          118    82     15
# ...
```

---

## Example 3: Intermodal Access/Egress (Advanced)

**Use Case**: Population plans have explicit access_walk, transit_walk, egress_walk legs.

**Population Plan Structure**:
```xml
<person id="intermodal_agent_01">
  <plan selected="yes">
    <activity type="home" x="..." y="..." end_time="07:30:00"/>
    <leg mode="access_walk">
      <route type="generic" distance="450.0" traveltime="324.0"/>
    </leg>
    <leg mode="pt">
      <route type="experimentalPt1"/>
    </leg>
    <leg mode="transit_walk">
      <route type="generic" distance="120.0" traveltime="86.4"/>
    </leg>
    <leg mode="pt">
      <route type="experimentalPt1"/>
    </leg>
    <leg mode="egress_walk">
      <route type="generic" distance="280.0" traveltime="201.6"/>
    </leg>
    <activity type="work" x="..." y="..." end_time="17:00:00"/>
  </plan>
</person>
```

**Configuration**:
```xml
<module name="swissRailRaptor">
  <!-- Enable intermodal for explicit access/egress legs -->
  <param name="useIntermodalAccessEgress" value="true"/>

  <!-- Configure access/egress settings -->
  <parameterset type="accessEgressSettings">
    <param name="mode" value="walk"/>
    <param name="radius" value="1000.0"/>
    <param name="initialSearchRadius" value="500.0"/>
    <param name="searchExtensionRadius" value="250.0"/>
  </parameterset>

  <!-- Configure transfer walk -->
  <parameterset type="accessEgressSettings">
    <param name="mode" value="transit_walk"/>
    <param name="radius" value="200.0"/>
  </parameterset>

  <param name="transferPenaltyBaseCost" value="120.0"/>
  <param name="useModeMappingForPassengers" value="false"/>
</module>

<module name="routing">
  <param name="networkModes" value="car"/>

  <!-- All walk modes teleported -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
  </parameterset>
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="access_walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
  </parameterset>
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="egress_walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
  </parameterset>
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="transit_walk"/>
    <param name="teleportedModeSpeed" value="1.0"/>  <!-- Slower for station transfers -->
  </parameterset>
</module>

<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>

<module name="qsim">
  <param name="mainMode" value="car,pt"/>
  <param name="usingTransitInMobsim" value="true"/>
</module>
```

**Expected Results**:
- SwissRailRaptor respects explicit access/egress legs
- Transfer walks use specified radius constraints
- More precise control over access/egress routing

---

## Example 4: Transfer Station Configuration

**Use Case**: Enabling transfers between two transit lines at shared station.

**Transit Schedule Setup**:
```xml
<transitSchedule>
  <!-- Blue Line stops -->
  <stopFacility id="BL11_UP" x="300123.45" y="2770456.78"
                linkRefId="pt_BL11_UP"
                name="City Center - Blue Line"
                stopAreaId="086"/>

  <!-- Green Line stops at same location -->
  <stopFacility id="G12_UP" x="300123.45" y="2770456.78"
                linkRefId="pt_G12_UP"
                name="City Center - Green Line"
                stopAreaId="086"/>

  <!-- Blue Line route -->
  <transitLine id="BlueLine">
    <transitRoute id="BL_Route_01">
      <transportMode>pt</transportMode>
      <routeProfile>
        <stop refId="BL10_UP" arrivalOffset="00:00:00" departureOffset="00:00:00"/>
        <stop refId="BL11_UP" arrivalOffset="00:05:00" departureOffset="00:05:30"/>
        <stop refId="BL12_UP" arrivalOffset="00:10:00" departureOffset="00:10:30"/>
      </routeProfile>
      <route>
        <link refId="pt_BL10_UP"/>
        <link refId="pt_BL11_UP"/>
        <link refId="pt_BL12_UP"/>
      </route>
      <departures>
        <departure id="BL_01_07:00" departureTime="07:00:00" vehicleRefId="veh_BL_01"/>
        <departure id="BL_01_07:10" departureTime="07:10:00" vehicleRefId="veh_BL_02"/>
      </departures>
    </transitRoute>
  </transitLine>

  <!-- Green Line route -->
  <transitLine id="GreenLine">
    <transitRoute id="G_Route_01">
      <transportMode>pt</transportMode>
      <routeProfile>
        <stop refId="G11_UP" arrivalOffset="00:00:00" departureOffset="00:00:00"/>
        <stop refId="G12_UP" arrivalOffset="00:03:00" departureOffset="00:03:30"/>
        <stop refId="G13_UP" arrivalOffset="00:08:00" departureOffset="00:08:30"/>
      </routeProfile>
      <route>
        <link refId="pt_G11_UP"/>
        <link refId="pt_G12_UP"/>
        <link refId="pt_G13_UP"/>
      </route>
      <departures>
        <departure id="G_01_07:06" departureTime="07:06:00" vehicleRefId="veh_G_01"/>
        <departure id="G_01_07:16" departureTime="07:16:00" vehicleRefId="veh_G_02"/>
      </departures>
    </transitRoute>
  </transitLine>
</transitSchedule>
```

**Key Points**:
1. Both `BL11_UP` and `G12_UP` have **same stopAreaId="086"**
2. Coordinates are identical (or very close)
3. Departure times align: BL arrives 07:05:30, G departs 07:06:00 (30s transfer)

**SwissRailRaptor Configuration**:
```xml
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>

  <!-- Low transfer penalty for testing -->
  <param name="transferPenaltyBaseCost" value="30.0"/>  <!-- 30 seconds penalty -->
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>

  <param name="useModeMappingForPassengers" value="false"/>
</module>
```

**Validation**:
```bash
# Check agent transfers from BL to G
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "pt_agent_01" | \
  grep "PersonEntersVehicle\|PersonLeavesVehicle\|VehicleArrivesAtFacility" | \
  head -20

# Expected sequence:
# PersonEntersVehicle vehicle="veh_BL_01"
# VehicleArrivesAtFacility facility="BL11_UP"
# PersonLeavesVehicle vehicle="veh_BL_01"
# PersonEntersVehicle vehicle="veh_G_01"  ← TRANSFER HAPPENED
# VehicleArrivesAtFacility facility="G13_UP"
```

---

## Example 5: Debugging No-Transfer Issue

**Scenario**: Agents board PT but never transfer, even though routes require it.

**Diagnostic Steps**:

```bash
# Step 1: Check if agents are boarding at all
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle" | wc -l
# Output: 50 (agents ARE boarding)

# Step 2: Check boardings per agent
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10
# Output:
#   1 pt_agent_01
#   1 pt_agent_02
#   1 pt_agent_03
# Problem: All agents board exactly once (no transfers)

# Step 3: Check transfer station stopAreaId
gunzip -c transitSchedule.xml.gz | \
  grep 'stopFacility' | \
  grep -E 'BL11|G12' | \
  grep 'stopAreaId'
# Output:
#   <stopFacility id="BL11_UP" ... (no stopAreaId)
#   <stopFacility id="G12_UP" ... (no stopAreaId)
# FOUND THE ISSUE: Missing stopAreaId
```

**Fix**: Add stopAreaId to transfer stations

```xml
<!-- Before (broken) -->
<stopFacility id="BL11_UP" x="..." y="..." linkRefId="pt_BL11_UP"/>
<stopFacility id="G12_UP" x="..." y="..." linkRefId="pt_G12_UP"/>

<!-- After (fixed) -->
<stopFacility id="BL11_UP" x="..." y="..." linkRefId="pt_BL11_UP" stopAreaId="086"/>
<stopFacility id="G12_UP" x="..." y="..." linkRefId="pt_G12_UP" stopAreaId="086"/>
```

**Re-run and verify**:
```bash
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="config.xml --config:controller.lastIteration 5"

gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep "PersonEntersVehicle" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10
# Output:
#   3 pt_agent_01  ← Now has 3 boardings (transfers working!)
#   2 pt_agent_02
#   1 pt_agent_03
```

---

## Decision Tree: Which Configuration to Use?

```
START: What does your population plan look like?
│
├─ Only <leg mode="pt"> between activities
│  └─ useIntermodalAccessEgress = false
│     └─ Simple PT-only or multimodal scenario
│        └─ Use Example 1 or Example 2
│
└─ Has <leg mode="access_walk">, <leg mode="egress_walk">
   └─ useIntermodalAccessEgress = true
      └─ Advanced intermodal scenario
         └─ Use Example 3

Are transfers needed?
│
├─ Yes
│  └─ Ensure transfer stations have matching stopAreaId
│     └─ Use Example 4
│     └─ If not working: Use Example 5 debugging
│
└─ No
   └─ Standard configuration
      └─ Use Example 1 or Example 2
```
