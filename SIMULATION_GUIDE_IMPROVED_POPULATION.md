# 改進型人口模擬指南 - Improved Population Simulation Guide

**Latest Update:** 2025-11-05
**Status:** Ready for Testing
**Tested With:** MATSim 2025.0, Java 21

---

## 📋 概述 (Overview)

This guide walks you through running MATSim simulations with the **newly improved population file** (`test_population_50.xml`) that includes:

- ✅ **PT Transfer Agents** - Agents that transfer between multiple transit lines (BL↔G, G↔R, etc.)
- ✅ **Car Distance Constraints** - Car agents restricted to 1km+ trips to avoid trivial routes
- ✅ **Mode Consistency** - Agent IDs match their primary transportation mode
- ✅ **OSM Boundary Enforcement** - Car agents stay within valid road network zones
- ✅ **Trip Duration Limits** - All trips capped at 40 minutes

---

## 🚀 快速開始 (Quick Start)

### Step 1: Build the Project

```bash
cd /Users/ro9air/matsim-example-project

# Build with Maven (ensures latest code)
./mvnw clean package

# Or if mvnw not available, use system Maven
mvn clean package
```

**Expected Output:**
```
[INFO] BUILD SUCCESS
[INFO] Total time: XX seconds
[INFO] Final Memory: XXM/XXXM
```

**Build Artifacts:**
- `target/matsim-example-project-0.0.1-SNAPSHOT.jar` (executable jar)

---

### Step 2: Run Simulation with Improved Population

```bash
cd scenarios/equil/

# Option A: Launch GUI (interactive visualization)
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# Option B: Run headless (faster, for batch processing)
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml --config:controller.snapshotFormat null
```

**Config Details** (`config.xml`):
```xml
<module name="controller">
  <param name="lastIteration" value="5" />           <!-- 5 iterations for testing -->
  <param name="outputDirectory" value="./output" />  <!-- Results go here -->
</module>
```

**Expected Runtime:**
- **Headless:** ~2-5 minutes for 5 iterations
- **With GUI:** ~5-10 minutes (includes visualization overhead)

**Simulation Progress:**
```
Iteration 0 : ...
Iteration 1 : ...
Iteration 2 : ...
Iteration 3 : ...
Iteration 4 : ...
Iteration 5 : ...
```

---

### Step 3: Verify Results

After simulation completes, check the output:

```bash
cd scenarios/equil/output/

# View summary statistics
cat scorestats.csv                    # Agent scores per iteration
cat modestats.csv                     # Mode usage statistics
ls -lh ITERS/                         # Iteration folders

# Check for errors/warnings
tail -50 ../logfile.log
tail -20 ../logfileWarningsErrors.log
```

**Key Files Generated:**
```
output/
├── ITERS/
│   ├── it.0/  ← Initial (input population)
│   ├── it.1/  ← After iteration 1
│   └── ...
│   └── it.5/  ← Final iteration
├── output_events.xml.gz        ← All agent/vehicle events
├── output_plans.xml.gz         ← Final plans after replanning
├── output_network.xml.gz       ← Network (copied from input)
├── output_config.xml           ← Used configuration
├── scorestats.csv              ← Score evolution
├── modestats.csv               ← Mode choice statistics
└── logfile.log                 ← Detailed simulation log
```

---

## 📊 期望的改進 (Expected Improvements)

### Agent Behavior Improvements

#### Before (Original Population)
```
PROBLEM: Car agents walking 3+ hours
  ├─ Activity: home → 3 hour walk leg → work
  ├─ Distance: ~250km at walk speed (!!!)
  └─ Score: Extremely negative (trip takes all day)

PROBLEM: PT agents teleporting
  ├─ Activity: home → teleported 50km → work
  ├─ Mode: PT configured as teleportedModeParameters
  └─ Issue: No actual transit schedule used
```

#### After (Improved Population)
```
SOLUTION 1: Car agents with real driving
  ├─ Agent: car_agent_001
  ├─ Trip: 5km drive (13 min at 25 km/h)
  ├─ Constraint: Enforced 1km minimum distance
  └─ Score: Realistic, agents optimize behavior

SOLUTION 2: PT agents using proper routing
  ├─ Agent: pt_agent_001 (single-line)
  │  ├─ Morning: home → walk to BL02_UP → BL09_UP → work
  │  └─ Evening: work → walk from BL09_UP → BL02_UP → home
  │
  ├─ Agent: pt_transfer_001 (multi-line)
  │  ├─ Morning: BL line (home→BL14_UP) → transfer at interchange
  │  │        → G line (interchange→G13_UP) → work
  │  └─ Evening: reverse trip
  │
  └─ Score: Realistic, uses actual schedule
```

### Score Improvement Pattern

**Expected Score Evolution (scorestats.csv):**

```
Iteration | avg_executed | avg_worst | avg_average | avg_best
0         | 22.2         | 22.2      | 22.2        | 22.2      ← Input population (some negative)
1         | 35-40        | ~20       | 28-30       | 37-40     ← Agents start replanning
2         | 45-50        | ~20       | 35-40       | 50+       ← Mode adjustment, better routes
3         | 50-60        | ~5        | 40-50       | 60+       ← Convergence toward better plans
4         | 65-75        | ~2        | 50-60       | 70+       ← Few agents still improving
5         | 75-85        | ~1        | 55-65       | 75+       ← Near equilibrium
```

**What This Means:**
- ✅ `avg_executed` increasing = Agents finding better plans
- ✅ `avg_worst` decreasing = Even bad plans improve
- ✅ `avg_average` increasing = Network learning optimal behavior
- ✅ Agents should NOT have extremely negative scores (like -300)

---

### Mode Statistics (modestats.csv)

**Expected Mode Distribution:**

```
Iteration | car_legs | pt_legs | walk_legs | Total_trips
0         | 30       | 60      | 46        | 136      ← Input population
1-5       | 28-32    | 58-62   | 44-48     | 130-142  ← Minor replanning adjustments
```

**Interpretation:**
- Most agents stick with original mode (good sign - population is realistic)
- Small fluctuations = agents testing alternatives in replanning
- Car and PT roughly balanced = diverse transportation patterns

---

## 🔍 詳細驗證 (Detailed Validation)

### Check 1: Verify No "Walking 3 Hours" Agents

```bash
# Check iteration 5 events for walk legs
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep 'PersonStarts.*mode="walk"' | \
  wc -l

# Should see ~40-50 walk legs total across all agents
# NOT thousands of 3-hour walks
```

### Check 2: Verify Car Agents Using Roads

```bash
# Check for car mode trips
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep 'PersonStarts.*mode="car"' | \
  wc -l

# Should see ~30-35 car trips
# Check travel times (should be realistic, not 0 or >3 hours)
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep 'PersonStarts.*mode="car"' | head -5
```

### Check 3: Verify PT Uses Transit Schedule

```bash
# Check if PT vehicles visited stops
gunzip -c output/ITERS/it.5/5.events.xml.gz | \
  grep -c 'VehicleArrivesAtFacility'

# Should see 500-1000+ vehicle-stop interactions
# If <50, PT routing isn't working properly
```

### Check 4: Check for Simulation Errors

```bash
# Look for critical errors (should be NONE or very few)
grep -i "error\|exception\|failed" output/logfile.log | head -20

# Check for warnings about invalid plans
grep -i "ClassCastException\|invalid\|unmapped" output/logfileWarningsErrors.log
```

---

## 📤 導出到 Via 平台 (Export to Via Platform)

Once simulation completes successfully:

```bash
# From scenarios/equil/ directory
cd /Users/ro9air/matsim-example-project/scenarios/equil/

# Export simulation results to Via visualization
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out forVia \
  --dt 5

echo "✓ Export complete! Via files ready at: forVia/"
```

**Output Files:**
```
forVia/
├── output_events.xml           ← Filtered events (for Via import)
├── output_network.xml.gz       ← Network topology
├── tracks_dt5s.csv             ← Agent trajectories
├── filtered_vehicles.csv       ← Active vehicles
└── vehicle_usage_report.txt    ← Statistics
```

---

## ⚠️ 常見問題 (Common Issues)

### Issue 1: "File not found: test_population_50.xml"

**Solution:**
```bash
# Make sure you're in the right directory
cd /Users/ro9air/matsim-example-project/scenarios/equil/

# Verify file exists
ls -lh test_population_50.xml

# If missing, regenerate it
cd /Users/ro9air/matsim-example-project/
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py
```

### Issue 2: "Network is not connected" Warning

**Solution:**
- This is expected for the equil scenario with PT network
- PT agents use virtual network (pt_STATION_UP, pt_STATION_DN)
- Car agents use separate car network
- You can ignore this warning

### Issue 3: "ClassCastException: TransitPassengerRoute cannot be cast to NetworkRoute"

**Solution:**
- Indicates PT routing misconfiguration
- **Verify config.xml has:**
  ```xml
  <module name="routing">
    <param name="networkModes" value="car" />  <!-- NOT "car,pt" -->
  </module>

  <module name="transit">
    <param name="routingAlgorithmType" value="SwissRailRaptor" />
  </module>
  ```
- Rebuild and re-run simulation

### Issue 4: "Simulation is very slow"

**Solution:**
```bash
# Run headless (no visualization)
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.snapshotFormat null

# Reduce iterations in config.xml
# <param name="lastIteration" value="2" />  # Test with 2 iterations first
```

### Issue 5: "Agents aren't replanning" (scores don't change)

**Solution:**
- Check `replanning` module in config.xml
- Ensure strategy is enabled:
  ```xml
  <module name="replanning">
    <parameterset type="strategysettings">
      <param name="strategyName" value="ChangeExpBeta" />
      <param name="weight" value="1.0" />
    </parameterset>
  </module>
  ```

---

## 🎯 進階配置 (Advanced Configuration)

### Run Longer Simulation (50 iterations)

Edit `scenarios/equil/config.xml`:
```xml
<module name="controller">
  <param name="lastIteration" value="50" />
</module>
```

**Runtime Estimate:**
- Headless: ~20-30 minutes
- With GUI: ~40-60 minutes

### Adjust Agent Behavior

**Change scoring parameters** in config.xml:
```xml
<module name="scoring">
  <!-- Travel time disutility (negative score)
       Lower = agents tolerate longer trips
       Higher = agents strongly prefer shorter trips -->
  <param name="traveling" value="-6.0" />  <!-- Default: -6.0 -->

  <!-- Activity time utility (positive score)
       Higher = agents want to spend more time at activities -->
  <param name="performing" value="+1.0" />  <!-- Default: +1.0 -->
</module>
```

### Monitor Real-Time in GUI

When running with GUI (`java -jar ... config.xml`):

1. **Open Scenario** → Loads network and population
2. **Run Simulation** → Iterative optimization starts
3. **View Statistics** tab → Real-time score evolution
4. **View Agents** tab → Agent locations and movements
5. **View Events** tab → Detailed event logs

---

## 📝 人口文件規格 (Population File Specification)

**Location:** `scenarios/equil/test_population_50.xml`

**Content Structure:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">
<population>
  <!-- Car agents (single car trip) -->
  <person id="car_agent_001">
    <plan selected="yes" score="...">
      <activity type="home" link="..." x="..." y="..." end_time="07:15:00" />
      <leg mode="car" />
      <activity type="work" link="..." x="..." y="..." end_time="17:30:00" />
      <leg mode="car" />
      <activity type="home" link="..." x="..." y="..." />
    </plan>
  </person>

  <!-- PT agents (single transit line) -->
  <person id="pt_agent_001">
    <plan selected="yes" score="...">
      <activity type="home" link="..." end_time="07:15:00" />
      <leg mode="pt" route="...BL02_UP→BL09_UP..." />
      <activity type="work" link="..." end_time="17:30:00" />
      <leg mode="pt" route="...BL09_UP→BL02_UP..." />
      <activity type="home" link="..." />
    </plan>
  </person>

  <!-- PT transfer agents (multiple lines) -->
  <person id="pt_transfer_001">
    <plan selected="yes" score="...">
      <activity type="home" link="..." end_time="07:15:00" />
      <!-- Morning: BL line -->
      <leg mode="pt" route="...BL02_UP→BL14_UP..." />
      <!-- Interchange stop -->
      <activity type="visit" link="..." dur="00:05:00" />
      <!-- G line to work -->
      <leg mode="pt" route="...G01_DN→G13_UP..." />
      <activity type="work" link="..." end_time="17:30:00" />
      <!-- Evening: reverse -->
      <leg mode="pt" route="...G13_UP→G01_DN..." />
      <activity type="visit" link="..." dur="00:05:00" />
      <leg mode="pt" route="...BL14_UP→BL02_UP..." />
      <activity type="home" link="..." />
    </plan>
  </person>
</population>
```

**Agent Distribution** (46 agents):
- **Car agents:** 15 (car_agent_001 → car_agent_015)
- **PT single-line:** 20 (pt_agent_001 → pt_agent_020)
- **PT transfer:** 6 (pt_transfer_001 → pt_transfer_006)
- **Walk agents:** 5 (walk_agent_001 → walk_agent_005)

---

## ✅ 完成檢查清單 (Completion Checklist)

Before running the simulation, verify:

- [ ] Maven/Java 21 installed (`java -version` shows 21.x)
- [ ] Project built (`target/matsim-example-project-0.0.1-SNAPSHOT.jar` exists)
- [ ] Population file exists (`scenarios/equil/test_population_50.xml` 36K)
- [ ] Network file exists (`scenarios/equil/network-with-pt.xml.gz` 3.5M)
- [ ] Transit schedule exists (`scenarios/equil/transitSchedule-mapped.xml.gz` 285K)
- [ ] Transit vehicles exist (`scenarios/equil/transitVehicles.xml` 129K)
- [ ] Config is correct (`scenarios/equil/config.xml` uses test_population_50.xml)

If all ✅, proceed to "Quick Start" section above.

---

## 📚 參考 (References)

- **Population Generation:** `src/main/python/generate_test_population.py`
- **Population Validation:** `src/main/python/validate_population.py`
- **Via Export Tool:** `src/main/python/build_agent_tracks.py`
- **Quick Start:** [working_journal/Via-Export-Quick-Start.md](working_journal/Via-Export-Quick-Start.md)
- **Full Setup:** [VIA_EXPORT_SETUP.md](VIA_EXPORT_SETUP.md)

---

## 🔗 快速命令參考 (Quick Command Reference)

```bash
# Build project
./mvnw clean package

# Run simulation (GUI)
cd scenarios/equil/
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# Run simulation (headless)
cd scenarios/equil/
java -jar ../../matsim-example-project-0.0.1-SNAPSHOT.jar config.xml \
  --config:controller.snapshotFormat null

# Check results
cd scenarios/equil/output/
cat scorestats.csv
cat modestats.csv
tail -50 ../logfile.log

# Export to Via
cd scenarios/equil/
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events --out forVia --dt 5

# Regenerate population if needed
cd /Users/ro9air/matsim-example-project/
POPULATION_OUTPUT_PATH='scenarios/equil/test_population_50.xml' \
  python src/main/python/generate_test_population.py
```

---

**Created:** 2025-11-05
**Next Steps:** Follow "Quick Start" section to run your first improved population simulation!
