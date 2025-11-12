# Via Platform Export Generation

This skill helps export MATSim simulation results for Via platform visualization with filtered, lightweight data.

## When to Activate This Skill

Activate when user mentions:
- "Export for Via"
- "Generate Via visualization files"
- "Create filtered events for Via"
- "Prepare data for Via platform"
- "Build agent tracks"

## Workflow

### Step 1: Validate Simulation Output

```bash
# Check output directory exists
ls -lh scenarios/equil/output/

# Verify required files
ls -lh scenarios/equil/output/output_plans.xml.gz
ls -lh scenarios/equil/output/output_events.xml.gz
ls -lh scenarios/equil/output/output_network.xml.gz
```

### Step 2: Run Via Export Pipeline

**Full export with all features**:
```bash
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

**Minimal export** (events only):
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --export-filtered-events \
  --out forVia
```

### Step 3: Monitor Progress

Expected output with 3-checkpoint mechanism:
```
[1/3] Extracting agent-vehicle time ranges...
  ✓ Found 42 agent-vehicle combinations
    car_agent_01 × car_agent_01: (07:04:42-07:14:45), (14:48:40-14:58:22)
    veh_517_subway × subway: (15:36:12-15:48:54)

[2/3] Preparing event filter parameters...
  Original events: 310,743
  Agents: 50
  Vehicles: 41

[3/3] Executing fine-grained filtering...
  ✓ Filtering complete: forVia/output_events.xml
```

### Step 4: Validate Output

```bash
# Check generated files
ls -lh forVia/

# Expected files:
# - output_events.xml (1-10 MB, filtered)
# - output_network.xml.gz (copied)
# - tracks_dt5s.csv (agent trajectories)
# - legs_table.csv (trip segments)
# - filtered_vehicles.csv (vehicle summary)
# - vehicle_usage_report.txt (statistics)

# Verify compression
wc -l forVia/output_events.xml
# Should be <<< original event count
```

### Step 5: Check Statistics

```bash
cat forVia/vehicle_usage_report.txt

# Expected output:
# Original events: 310,743
# Filtered events: 1,212
# Compression: 99.6%
# Vehicles used: 5/2,791
```

## Command Line Parameters

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `--plans` | Yes | MATSim output_plans.xml.gz |
| `--events` | No | For vehicle filtering |
| `--schedule` | No | PT enrichment |
| `--vehicles` | No | Vehicle count |
| `--network` | No | Copy to output |
| `--export-filtered-events` | No | Generate filtered XML |
| `--out` | Yes | Output directory |
| `--dt` | No | Track sampling (default: 5s) |

## Output Files for Via

**Required for Via**:
1. `output_events.xml` - Filtered person-vehicle events
2. `output_network.xml.gz` - Network topology

**Optional supporting files**:
- `tracks_dt5s.csv` - Agent trajectories at 5s intervals
- `filtered_vehicles.csv` - Vehicle summary
- `vehicle_usage_report.txt` - Statistics

## Common Issues

### Issue 1: Missing Python Dependencies
**Error**: ImportError: No module named 'lxml'
**Fix**: `pip install lxml`

### Issue 2: Large Unfiltered Events
**Symptom**: output_events.xml is same size as input
**Cause**: Missing `--export-filtered-events` flag
**Fix**: Re-run with flag

### Issue 3: Empty Tracks CSV
**Cause**: Agent IDs mismatch or wrong time range
**Fix**: Check agent IDs in plans vs events

## Performance Benchmarks

**50-agent simulation**:
- Original: 310,743 events
- Filtered: 8,372 events (97.4% compression)
- Vehicles: 41 used (from 2,791 total)

**3-agent simulation**:
- Original: 310,743 events
- Filtered: 1,212 events (99.6% compression)
- Vehicles: 5 used

## Validation Steps

1. Check file sizes are reasonable (events <10MB for 50 agents)
2. Verify compression ratio >90%
3. Spot-check events contain only relevant agents
4. Ensure network file is copied correctly

## File References

- Workflow: `VIA_EXPORT_WORKFLOW.md`
- Python tool: `src/main/python/build_agent_tracks/`
- CLAUDE.md: Lines 578-641
- Working journal: Phase 1-4 implementation notes
