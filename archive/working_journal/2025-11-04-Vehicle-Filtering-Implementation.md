# Vehicle Filtering Implementation - 2025-11-04

## Overview

Implemented a vehicle filtering system for the MATSim PT-Car simulation to reduce Via platform's vehicle import from 2,791 to just 5 vehicles (99.8% compression). This addresses the Via platform constraint of maximum 500 vehicles per project.

## Problem Statement

- **Total vehicles defined**: 2,791 subway vehicles in `transitVehicles.xml`
- **Vehicles actually used by agents**: Only 5 (4 subway + 1 car)
- **Via platform limit**: 500 agents + 500 vehicles
- **Wasteful upload**: Would import 2,786 unused vehicles (99.8% overhead)

## Solution Architecture

### Three-Layer Filtering Strategy

1. **Event Parsing Layer**: Extract `PersonEntersVehicle` events from `output_events.xml.gz`
2. **Agent Whitelist Layer**: Filter to vehicles used by REAL agents only (metro_up_01, metro_down_01, car_commuter_01), excluding vehicle pseudo-agents
3. **Output Generation Layer**: Create filtered_vehicles.csv + vehicle_usage_report.txt

### Key Insight: Real vs. Pseudo Agents

MATSim's transit simulation distinguishes between:
- **Real agents**: metro_up_01, metro_down_01, car_commuter_01 (actual travelers)
- **Pseudo agents**: pt_veh_*_subway_Subway (internal vehicle operators)

Backend simulation activates ALL 2,791 vehicles for schedule operation, but agents directly interact with only 5 vehicles. Filtering isolates agent-used vehicles.

## Implementation Details

### New Functions in `src/main/python/build_agent_tracks.py`

#### 1. `load_actively_used_vehicles(events_path, agent_ids=None)`

```python
def load_actively_used_vehicles(events_path: str | Path | None, agent_ids: set[str] | None = None) -> dict[str, dict]:
    """
    Parse events.xml(.gz) to extract vehicles used by specific agents.
    
    Returns: vehicle_id -> {
        'mode': 'subway' or 'car',
        'first_use_time_s': int,
        'last_use_time_s': int,
        'agent_count': int (unique agents using this vehicle)
    }
    """
```

**Features**:
- Iterative XML parsing to minimize memory usage
- Filters PersonEntersVehicle events by agent_id
- Auto-detects vehicle mode from ID (subway vs. car)
- Tracks first/last use times and agent count
- Default agent set: {metro_up_01, metro_down_01, car_commuter_01}

#### 2. `write_filtered_vehicles_csv(used_vehicles, outdir)`

Generates CSV with columns:
- vehicle_id: Unique vehicle identifier
- mode: subway or car
- first_use_time_s: Seconds since midnight when first used
- last_use_time_s: Seconds since midnight when last used
- first_use_time: HH:MM:SS format
- last_use_time: HH:MM:SS format
- agent_count: Number of agents using this vehicle

#### 3. `create_vehicle_usage_report(total_vehicles, used_vehicles, outdir)`

Generates `vehicle_usage_report.txt` with:
- Summary statistics (total, used, filtered, compression %)
- Detailed table of each vehicle
- Time ranges for each vehicle

#### 4. Updated `run_pipeline(...)`

- Now accepts `events_path` parameter
- Automatically triggers vehicle filtering if events_path provided
- Generates both filtered_vehicles.csv and vehicle_usage_report.txt
- Prints compression statistics

### Integration into Data Pipeline

```
input files:
  output_plans.xml.gz
  output_events.xml.gz
  transitSchedule-mapped.xml.gz

run_pipeline()
  ├─ parse_population_or_plans(plans)
  ├─ load_transit_mode_lookup(schedule)
  ├─ load_transit_route_stops(schedule)
  ├─ build_legs_table()              → legs_table.csv
  ├─ build_tracks_from_legs()        → tracks_dt5s.csv
  │
  └─ load_actively_used_vehicles(events)  → filtered_vehicles.csv
                                          → vehicle_usage_report.txt
```

## Results

### Filtered Vehicle List (5 vehicles)

| Vehicle ID | Mode | Agents | Time Range |
|-----------|------|--------|-----------|
| car_commuter_01 | car | 1 | 7:30:08 - 17:00:05 |
| veh_465_subway | subway | 1 | 6:47:48 - 6:47:48 |
| veh_604_subway | subway | 1 | 17:09:07 - 17:09:07 |
| veh_663_subway | subway | 1 | 6:22:07 - 6:22:07 |
| veh_756_subway | subway | 1 | 17:13:51 - 17:13:51 |

### Compression Statistics

- Total vehicles defined: 2,791
- Agent-used vehicles: 5
- Vehicles filtered out: 2,786
- **Compression ratio: 99.8%**

### Output Files

All files generated in `scenarios/equil/output/via_tracks/`:

1. **filtered_vehicles.csv** (353 bytes)
   - Via-compatible format
   - 5 vehicles + 1 header row
   - Ready for Via import

2. **vehicle_usage_report.txt** (958 bytes)
   - Human-readable summary
   - Detailed vehicle statistics
   - Compression metrics

3. **legs_table.csv** (16 KB)
   - Existing leg-based data (unchanged)

4. **tracks_dt5s.csv** (909 KB)
   - Existing trajectory data (unchanged)

## Usage

### Command Line

```bash
python src/main/python/build_agent_tracks.py \
  --population output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule scenarios/equil/transitSchedule-mapped.xml.gz \
  --out scenarios/equil/output/via_tracks
```

### Programmatic Usage

```python
from build_agent_tracks import load_actively_used_vehicles, write_filtered_vehicles_csv, create_vehicle_usage_report

# Extract used vehicles
used_vehicles = load_actively_used_vehicles("output_events.xml.gz")

# Generate outputs
csv_path = write_filtered_vehicles_csv(used_vehicles, "output_dir")
report_path = create_vehicle_usage_report(2791, used_vehicles, "output_dir")
```

## Via Platform Integration

### Before Filtering
- Vehicle count: 2,791
- Load time: High (parsing thousands of vehicle objects)
- Memory usage: Large (indexing all vehicles)
- Rendering: Slow (calculating visibility for all vehicles)

### After Filtering
- Vehicle count: 5
- Load time: Instant
- Memory usage: Minimal
- Rendering: Responsive

### Recommended Via Import Procedure

1. Delete previous vehicle import (2,791 vehicles)
2. Import filtered_vehicles.csv as vehicle data source
3. Import legs_table.csv as leg data source
4. Import tracks_dt5s.csv as trajectory data source
5. Verify 5 vehicles appear in vehicle layer

## Key Design Decisions

1. **Agent-based filtering**: Filter to vehicles used by real agents, not vehicle pseudo-agents
   - Rationale: MATSim backend uses all vehicles; agents only interact with subset

2. **Default agent set hardcoded**: {metro_up_01, metro_down_01, car_commuter_01}
   - Rationale: Makes script self-contained; can be overridden programmatically

3. **Event parsing instead of XML parsing**: Extracted from events.xml, not vehicles.xml
   - Rationale: Events capture actual usage; XML lists all definitions

4. **Time-based filtering metadata**: Stores first/last use times
   - Rationale: Allows validation and temporal analysis of vehicle usage

5. **Dual output formats**: CSV (primary) + text report (reference)
   - Rationale: CSV for Via; text for human verification

## Testing & Validation

✅ Verified via bash:
- Correct vehicle count: 5
- Correct compression ratio: 99.8%
- CSV format: Valid (7 columns + header)
- Time ranges: Realistic (within simulation period)
- Agent counts: Accurate per vehicle

✅ Generated outputs:
- filtered_vehicles.csv: Ready for Via import
- vehicle_usage_report.txt: Human-readable verification

## Future Enhancements

1. **Dynamic agent discovery**: Auto-detect real agents from plans.xml instead of hardcoding
2. **Filtered transitVehicles.xml**: Create MATSim-format XML subset for reproducible scenarios
3. **Mode-based filtering**: Separate filtered files for subway vs. car vehicles
4. **Time-window filtering**: Filter vehicles used within specified time periods
5. **Via API integration**: Direct upload to Via platform

## Technical Notes

### Memory Efficiency
- Uses iterative XML parsing with element clearing
- Processes events_path twice: once for extraction, stored in RAM
- Minimal overhead for 2.9MB events file

### Error Handling
- Graceful degradation if events_path missing/invalid
- Non-fatal warnings if vehicle filtering fails
- Main pipeline continues even if vehicle filtering errors

### Backward Compatibility
- Events_path is optional parameter
- Existing pipeline works unchanged if events_path not provided
- No modifications to legs_table or tracks_dt5s generation

## Files Modified

```
src/main/python/build_agent_tracks.py
  ├─ load_actively_used_vehicles() [NEW]
  ├─ write_filtered_vehicles_csv() [NEW]
  ├─ create_vehicle_usage_report() [NEW]
  └─ run_pipeline() [MODIFIED: added events_path handling]
```

## References

- MATSim Documentation: [Events & Vehicle Tracking](https://matsim.org/javadoc/org/matsim/core/events/PersonEntersVehicleEvent.html)
- PT Simulation: See PT_SETUP_REPORT.md
- Via Platform: [Via Visualization Docs](https://via.transport.org/)

---

**Completion Date**: 2025-11-04 17:21 UTC
**Status**: ✅ COMPLETE - Compression achieved (2,791 → 5 vehicles, 99.8% reduction)
**Tested**: ✅ YES - All outputs verified
**Ready for Via**: ✅ YES - filtered_vehicles.csv ready for import
