# Common Configuration Templates

Reusable configuration templates used across MATSim skills.

## SwissRailRaptor Configurations

### Simple PT-Only Configuration

For testing PT network with simple population plans (only `<leg mode="pt">`):

```xml
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="transitModes" value="pt"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="vehiclesFile" value="transitVehicles.xml"/>
</module>

<module name="routing">
  <!-- PT NOT in networkModes -->
  <param name="networkModes" value=""/>
  <param name="accessEgressType" value="accessEgressModeToLink"/>
  <param name="clearDefaultTeleportedModeParams" value="true"/>

  <!-- Walk for access/egress -->
  <parameterset type="teleportedModeParameters">
    <param name="mode" value="walk"/>
    <param name="teleportedModeSpeed" value="1.388888888"/>
    <param name="beelineDistanceFactor" value="1.3"/>
  </parameterset>
</module>

<module name="qsim">
  <!-- Only PT in mainMode -->
  <param name="mainMode" value="pt"/>
  <param name="usingTransitInMobsim" value="true"/>
</module>

<module name="swissRailRaptor">
  <!-- Simple plans: useIntermodalAccessEgress = false -->
  <param name="useIntermodalAccessEgress" value="false"/>

  <!-- Zero penalties for testing -->
  <param name="transferPenaltyBaseCost" value="0.0"/>
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0"/>

  <param name="useModeMappingForPassengers" value="false"/>
</module>
```

**Use when**: Testing PT-only scenarios with simple population plans

---

### Multimodal Configuration (Car + PT)

For scenarios where agents can choose between car and PT:

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
</module>

<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>

  <!-- Realistic transfer penalties -->
  <param name="transferPenaltyBaseCost" value="180.0"/>  <!-- 3 minutes -->
  <param name="transferPenaltyCostPerTravelTimeHour" value="600.0"/>

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
```

**Use when**: Multimodal scenarios with car and PT

---

## PT Mapping Configurations

### Artificial Mode (Fast Testing)

Creates pure artificial PT network, bypasses real network mapping:

```xml
<module name="ptmapper">
  <param name="networkFile" value="network.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- ARTIFICIAL MODE: distance = 0.0 -->
  <param name="maxLinkCandidateDistance" value="0.0"/>

  <!-- Disable mode-specific rules -->
  <param name="modeSpecificRules" value="false"/>
  <param name="routingWithCandidateDistance" value="false"/>

  <param name="numOfThreads" value="4"/>
</module>
```

**Use when**:
- Quick testing (1-2 minutes)
- Disconnected network
- PT-only scenarios

**Result**: 100% artificial links (pt_STATION_UP/DN)

---

### Metro Network Mapping

For metro/subway with reasonable network coverage:

```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Metro parameters: Wide search -->
  <param name="maxLinkCandidateDistance" value="500.0"/>
  <param name="nLinkThreshold" value="15"/>
  <param name="maxTravelCostFactor" value="20.0"/>
  <param name="candidateDistanceMultiplier" value="3.0"/>

  <!-- Robust router for disconnected components -->
  <param name="networkRouter" value="AStarLandmarks"/>

  <param name="modeSpecificRules" value="true"/>
  <param name="numOfThreads" value="4"/>
</module>
```

**Use when**: Metro with stations 1-2 km apart, potential river crossings

**Expected time**: 20-30 minutes

**Expected result**: <20% artificial links

---

### Urban Bus Network Mapping

For dense bus network with good coverage:

```xml
<module name="ptmapper">
  <param name="networkFile" value="network-cleaned.xml.gz"/>
  <param name="transitScheduleFile" value="transitSchedule.xml"/>
  <param name="outputNetworkFile" value="network-with-pt.xml.gz"/>
  <param name="outputScheduleFile" value="transitSchedule-mapped.xml.gz"/>

  <!-- Bus parameters: Tighter search -->
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

**Use when**: Bus network with stops 200-500m apart, grid network

**Expected time**: 15-45 minutes

**Expected result**: <5% artificial links

---

### Desperate Measures (Challenging Network)

When mapping keeps failing or getting stuck:

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

**Use when**: Standard parameters fail, process gets stuck, complex topology

**Expected time**: 30-60 minutes

**Expected result**: 20-40% artificial links (acceptable compromise)

---

## Testing Configuration Template

Quick simulation run for testing:

```xml
<module name="controller">
  <param name="lastIteration" value="10"/>  <!-- Not 1000! -->
  <param name="outputDirectory" value="./test_output"/>
  <param name="overwriteFiles" value="deleteDirectoryIfExists"/>
  <param name="writeEventsInterval" value="10"/>
  <param name="writePlansInterval" value="10"/>
</module>

<module name="global">
  <param name="coordinateSystem" value="EPSG:3826"/>  <!-- Taiwan -->
  <param name="numberOfThreads" value="4"/>
</module>
```

**Use when**: Testing new scenarios, validating configurations

**Benefits**: Fast iteration, automatic output cleanup
