# Via Platform Export Guide

**Last Updated**: 2025-11-17
**Status**: Production Ready

---

## Overview

The Via Platform Export Pipeline generates lightweight visualization data for the Via transportation simulation platform. It filters MATSim simulation output to contain only relevant agents and vehicles, dramatically reducing file sizes while maintaining complete person-vehicle interaction data.

### Key Features

- **Dual-Filtering System**: Preserves both agent activity events AND vehicle trajectory events
- **Dramatic Size Reduction**: 99.6% compression (310K+ events → 1,200 events for 3 agents)
- **Real-Time Vehicle Movement**: Enables Via to display actual vehicle trajectories, not just agent paths
- **Isolated Output Directory**: Prevents MATSim GUI from overwriting export files
- **Time-Range Filtering**: Shows vehicles only during time windows when agents use them (advanced feature)

---

## Why Use a Separate `forVia/` Directory?

### The Problem

When MATSim GUI runs, it outputs to the default directory (e.g., `scenarios/equil/output/`):
- Generates many files (plans, events, network, etc.)
- **Overwrites** all existing files in the output directory
- Causes Via export files to be lost

### The Solution

- **Via export directory**: `scenarios/equil/forVia/` (dedicated, protected)
- **MATSim GUI output**: `scenarios/equil/output/` (frequently overwritten)
- **Complete isolation**: No interference between simulation runs and Via exports

---

## Directory Structure

```
scenarios/equil/
├── output/              ← MATSim GUI output (large, frequently overwritten)
│   ├── output_plans.xml.gz         (29 KB)   ← Agent final plans
│   ├── output_events.xml.gz        (2.9 MB)  ← Simulation events
│   ├── output_transitSchedule.xml.gz (285 KB) ← Transit schedule
│   ├── output_transitVehicles.xml.gz (7.5 KB) ← Vehicle definitions
│   ├── output_network.xml.gz       (3.5 MB)  ← Network topology
│   └── ITERS/                      (500+ MB) ← Iteration data
│
├── forVia/              ← Via export (isolated, protected)
│   ├── output_events.xml           ← Filtered events (for Via import)
│   ├── output_network.xml.gz       ← Network topology
│   ├── tracks_dt5s.csv             ← Agent trajectories (5s intervals)
│   ├── legs_table.csv              ← Trip segments
│   ├── filtered_vehicles.csv       ← Active vehicles
│   └── vehicle_usage_report.txt    ← Statistics
│
├── test_population_50.xml          ← Improved population
├── config.xml                       ← MATSim config
├── transitSchedule-mapped.xml.gz   ← PT network
└── transitVehicles.xml             ← PT vehicles
```

---

## Workflow

### Overview

```
MATSim Simulation Output
├─ output_plans.xml.gz (agents and trips)
├─ output_events.xml.gz (310K+ events)
├─ output_transitVehicles.xml.gz (2791 vehicles)
├─ output_transitSchedule.xml.gz (schedule info)
└─ output_network.xml.gz (network topology)

        ↓ build_agent_tracks.py --export-filtered-events

Via Export Package
├─ output_events.xml (1,212 filtered events)
│  ├─ 104 agent-related events (activities, boarding)
│  └─ 1,108 vehicle trajectory events (movement, stops)
├─ output_network.xml.gz (network topology)
├─ tracks_dt5s.csv (agent trajectories at 5s intervals)
├─ legs_table.csv (trip segments)
├─ filtered_vehicles.csv (vehicle summary)
└─ vehicle_usage_report.txt (statistics)
```

### Step-by-Step Process

#### Step 1: Run MATSim Simulation

```bash
# Launch MATSim GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml

# ✓ Generates output to: scenarios/equil/output/
# ✓ Includes: output_plans.xml.gz, output_events.xml.gz, output_network.xml.gz
```

See [Simulation Guide](simulation-guide.md) for detailed simulation instructions.

#### Step 2: Export to Via Platform

**Recommended: Full Export (with all features)**

```bash
cd /home/user/matsim-example-project

python src/main/python/build_agent_tracks.py \
  --plans scenarios/equil/output/output_plans.xml.gz \
  --events scenarios/equil/output/output_events.xml.gz \
  --schedule scenarios/equil/output/output_transitSchedule.xml.gz \
  --vehicles scenarios/equil/output/output_transitVehicles.xml.gz \
  --network scenarios/equil/output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia \
  --dt 5
```

**Expected Runtime**: 30 seconds ~ 2 minutes

**Progress Output**:
```
========================================================================
Starting Via Export from Simulation Output
========================================================================

Input files:
  Plans:    scenarios/equil/output/output_plans.xml.gz
  Events:   scenarios/equil/output/output_events.xml.gz
  ...

[1/4] Parsing population and plans...
  ✓ Loaded 46 agents

[2/4] Parsing events...
  ✓ Processed 1,200+ events

[3/4] Filtering events...
  ✓ Filtered to 1,200+ relevant events

[4/4] Building agent tracks...
  ✓ Created trajectory CSV

========================================================================
✓ Via Export Complete!
========================================================================
```

#### Step 3: Verify Output Files

```bash
ls -lh scenarios/equil/forVia/
```

**Expected output:**
```
-rw-r--r--  1.2M  output_events.xml         ← Via Import #1
-rw-r--r--  3.5M  output_network.xml.gz     ← Via Import #2
-rw-r--r--  100K  tracks_dt5s.csv
-rw-r--r--  50K   legs_table.csv
-rw-r--r--  15K   filtered_vehicles.csv
-rw-r--r--  10K   vehicle_usage_report.txt
```

#### Step 4: Import to Via Visualization

1. Open Via platform dashboard
2. Create new visualization project
3. Load events: `scenarios/equil/forVia/output_events.xml`
4. Load network: `scenarios/equil/forVia/output_network.xml.gz`
5. Click play button to view animation

---

## Command Reference

### Basic Via Export (All Features)

```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/output/via_tracks \
  --dt 5
```

### Minimal Via Export (Events Only)

```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/output/via_tracks
```

### Command Line Parameters

| Parameter | Type | Required | Purpose |
|-----------|------|----------|---------|
| `--plans` | path | Yes | MATSim output_plans.xml.gz |
| `--events` | path | No | output_events.xml.gz for vehicle filtering |
| `--schedule` | path | No | transitSchedule.xml.gz for PT enrichment |
| `--vehicles` | path | No | transitVehicles.xml.gz for vehicle count |
| `--network` | path | No | output_network.xml.gz to copy to output |
| `--export-filtered-events` | flag | No | Generate filtered events.xml for Via |
| `--out` | path | Yes | Output directory |
| `--dt` | int | No | Track sampling interval in seconds (default: 5s) |

---

## Output Files Explanation

### Files Generated by MATSim GUI (`scenarios/equil/output/`)

| File | Size | Purpose | Notes |
|------|------|---------|-------|
| `output_plans.xml.gz` | ~50MB | Python processing input | All agent plans |
| `output_events.xml.gz` | ~300MB | Python processing input | Complete event log |
| `output_network.xml.gz` | ~3.5MB | Via visualization background | Network topology |
| `ITERS/` | ~500MB+ | Iteration data | Per-iteration details |

### Files Generated by Python Export (`scenarios/equil/forVia/`)

| File | Size | Purpose | Notes |
|------|------|---------|-------|
| `output_events.xml` | ~15KB | **Via import** ✓ | Filtered events (agents only) |
| `output_network.xml.gz` | ~3.5MB | **Via import** ✓ | Network copy |
| `tracks_dt5s.csv` | ~50KB | Analysis | Agent trajectories, 5s sampling |
| `filtered_vehicles.csv` | ~5KB | Analysis | Used vehicle list |
| `vehicle_usage_report.txt` | ~2KB | Analysis | Compression stats |
| `legs_table.csv` | ~100KB | Analysis | Agent leg segments |

### Required for Via Visualization

**Minimum files needed:**
1. `output_events.xml` - Person-vehicle interaction events
2. `output_network.xml.gz` - Network topology for visualization

**Optional supporting files:**
- `tracks_dt5s.csv` - Agent trajectories
- `filtered_vehicles.csv` - Vehicle summary
- `vehicle_usage_report.txt` - Statistics

---

## Filtering Statistics

The pipeline dramatically reduces data size while preserving all relevant information:

```
Original MATSim Events:      310,743
Filtered for 3 agents:         1,212
Compression ratio:             99.6%

Original Vehicle Definitions: 2,791
Agent-used vehicles:              5
Vehicle compression:          99.8%
```

**For 46-agent population:**
```
Original events:    ~50,000
Filtered events:    ~1,200-1,500
Compression:        ~97%
```

**For 100-agent population:**
```
Original events:    ~150,000
Filtered events:    ~3,000-4,000
Compression:        ~97-98%
```

---

## Benefits of File Isolation

✅ **Protects Via Data**
- Running new simulations doesn't lose export data
- Can run multiple simulations, keep desired results

✅ **Clear Workflow**
- `output/` = Latest MATSim simulation results
- `forVia/` = Processed visualization data

✅ **Prevents Accidental Overwriting**
- Even if MATSim GUI generates new events, forVia contents unaffected
- Must explicitly run Python command to update

✅ **Version Control**
- Keep multiple export versions:
  ```bash
  python ... --out forVia_v1
  python ... --out forVia_v2
  python ... --out forVia_latest
  ```

---

## Advanced Features

### Time-Range Filtering

The pipeline supports fine-grained time-range filtering to show vehicles only during time windows when agents actually use them.

**Use Case**: A bus operates all day (06:00-22:00), but an agent only travels 17:20-17:35. Filter shows only vehicle events in that time window.

**How It Works**:

1. **Checkpoint 1**: Extract boarding/alighting times from `PersonEntersVehicle` and `PersonLeavesVehicle` events
2. **Checkpoint 2**: Confirm parameters before executing (prevents hang-ups on large datasets)
3. **Checkpoint 3**: Filter vehicle trajectory events to only those time windows

**Example Output**:
```
[1/3] 提取 agent-vehicle 使用時間範圍...
  ✓ 發現 42 個 agent-vehicle 組合
    car_agent_01 × car_agent_01: (07:04:42-07:14:45), (14:48:40-14:58:22)
    veh_517_subway × subway: (15:36:12-15:48:54)
    ...

[2/3] 準備事件過濾參數...
  原始事件檔案: output/output_events.xml.gz
  輸出目錄: scenarios/equil/output/via_tracks_refined
  Agent 數量: 50
  Vehicle 數量: 41
  時間範圍數: 56

[3/3] 執行精細過濾...
  ✓ 過濾完成: scenarios/equil/output/via_tracks_refined/output_events.xml
```

**Performance**: 310,743 events → 8,372 events (97.4% compression) on 50-agent dataset

### Checkpoint Mechanism

Prevents long silent processing and provides feedback:
- **[1/3]**: Displays extracted time ranges in HH:MM:SS format
- **[2/3]**: Shows parameters before major operation
- **[3/3]**: Reports completion and file location

See `working_journal/2025-11-05-Via-Export-Enhancement.md` for detailed Phase 1-4 implementation notes.

---

## Common Operations

### Update Via Export After New Simulation

```bash
# From scenarios/equil/ directory
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out forVia
```

### Keep Multiple Simulation Results

```bash
# Simulation 1 complete
python ... --out forVia_v1

# Simulation 2 complete
python ... --out forVia_v2

# Simulation 3 complete
python ... --out forVia_latest
```

### Clean Old Data (Optional)

```bash
# Remove old iteration data from output
rm -rf scenarios/equil/output/ITERS/*

# Keep output XML files for re-export
# ls scenarios/equil/output/*.xml*
```

### Analyze CSV Files Without Via

```bash
# View agent trajectories (sampled every 5 seconds)
head -50 scenarios/equil/forVia/tracks_dt5s.csv

# View active vehicles
head scenarios/equil/forVia/filtered_vehicles.csv

# View statistics
cat scenarios/equil/forVia/vehicle_usage_report.txt
```

---

## Troubleshooting

### Issue: `forVia/` Directory Doesn't Exist

**Solution**:
```bash
mkdir -p scenarios/equil/forVia
```

### Issue: Cannot Find `output_plans.xml.gz`

**Problem**: MATSim simulation hasn't generated outputs yet

**Solution**: First run MATSim GUI simulation to generate outputs
```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml
```

### Issue: `forVia/` Files Were Overwritten

**Problem**: Accidentally ran `--out output/` instead of `--out forVia/`

**Solution**: Check command line parameters, ensure using `--out scenarios/equil/forVia`

### Issue: Via Import Shows No Vehicle Trajectories

**Problem**: Missing `--export-filtered-events` flag

**Solution**: Re-run with this parameter:
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia
```

### Issue: Python Script Fails with "Module not found"

**Problem**: Missing Python dependencies

**Solution**: Install required modules
```bash
pip install lxml pandas numpy
```

### Issue: Export Takes Too Long (>5 minutes)

**Problem**: Processing very large event files

**Solutions**:
1. Check event file size: `ls -lh output/output_events.xml.gz`
2. If >100MB, consider reducing iterations or agent count
3. Use minimal export (skip `--schedule` and `--vehicles`)

### Issue: Filtered Events File is Empty

**Problem**: No agents match the filter criteria

**Solution**: Verify agent IDs in population file:
```bash
gunzip -c scenarios/equil/output/output_plans.xml.gz | \
  grep '<person id=' | head -10
```

---

## Verification Checklist

### Before Export:
- [ ] Confirm `scenarios/equil/output/` exists and contains all output files
- [ ] Confirm Python environment installed (`python --version`)
- [ ] Confirm in project root directory (`/home/user/matsim-example-project`)

### During Export:
- [ ] No error messages (warnings are OK)
- [ ] Progress messages clearly visible
- [ ] Runtime within expected range (<2 minutes)

### After Export:
- [ ] `scenarios/equil/forVia/` directory exists
- [ ] `output_events.xml` file exists (>1MB)
- [ ] `output_network.xml.gz` file exists (>3MB)
- [ ] All CSV files exist

If any check fails, review error messages or re-run command.

---

## Technical Implementation

### Core Components

- **`filter_events.py`** - Event XML filtering with dual-filter support and time-range constraints
- **`parsers.py`** - Vehicle counting, event parsing, and time-range extraction
- **`main.py`** - Pipeline orchestration with 3-checkpoint progress reporting

### Dual-Filtering System

The export tool uses a two-phase filtering approach:

1. **Agent Events**: Filters all events related to selected agents
   - `actstart`, `actend` (activities)
   - `departure`, `arrival` (trips)
   - `PersonEntersVehicle`, `PersonLeavesVehicle` (boarding/alighting)

2. **Vehicle Events**: Filters vehicle trajectory events for vehicles used by agents
   - `VehicleArrivesAtFacility`, `VehicleDepartsAtFacility` (PT stops)
   - `vehicle enters traffic`, `vehicle leaves traffic` (road network)

This ensures Via can display both agent trajectories AND vehicle movements.

---

## Data Flow Diagram

```
MATSim Simulation Output
│
├─ output_plans.xml.gz      ┐
├─ output_events.xml.gz     │
├─ output_transitSchedule   │ ── build_agent_tracks.py ──┐
├─ output_transitVehicles   │                            │
└─ output_network.xml.gz    ┘                            │
                                                          ↓
                                              Via Export Files
                                                  ┌─────────────────────────┐
                                                  │ output_events.xml       │
                                                  │ output_network.xml.gz   │
                                                  │ tracks_dt5s.csv         │
                                                  │ legs_table.csv          │
                                                  │ filtered_vehicles.csv   │
                                                  └─────────────────────────┘
                                                          ↓
                                                    Via Platform
                                                  (Visualization)
```

---

## Quick Command Reference

```bash
# Basic export (recommended)
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia \
  --dt 5

# Minimal export (agents only)
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --out scenarios/equil/forVia

# Quick analysis (skip Via export)
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --out scenarios/equil/forVia \
  --skip-activity-matching

# Re-export after simulation
cd /home/user/matsim-example-project
rm -rf scenarios/equil/forVia/*
python src/main/python/build_agent_tracks.py \
  --plans scenarios/equil/output/output_plans.xml.gz \
  --events scenarios/equil/output/output_events.xml.gz \
  --network scenarios/equil/output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia
```

---

## Related Documentation

- [Simulation Guide](simulation-guide.md) - How to run MATSim simulations
- [Output Analysis Guide](output-analysis.md) - Analyzing simulation results
- [Quick Start](1-quick-start.md) - Getting started with MATSim
- **Working Journal**: `working_journal/Via-Export-Quick-Start.md` - Quick reference
- **CLAUDE.md**: Via Platform Export Pipeline section (lines 670-809)

---

## Best Practices

✅ **Always use dedicated `forVia/` directory** to protect export data
✅ **Run full export** with all parameters for best Via visualization
✅ **Verify output file sizes** after export
✅ **Keep multiple versions** for comparison (forVia_v1, forVia_v2, etc.)
✅ **Check vehicle_usage_report.txt** to confirm filtering worked correctly

❌ **Never output to `output/` directory** (will be overwritten by MATSim)
❌ **Never skip `--export-filtered-events`** if you want Via visualization
❌ **Never delete forVia before confirming export success**

---

**Status**: ✅ Ready for Production Use
**Next Steps**: Run MATSim simulation, then use this guide to export results for Via
