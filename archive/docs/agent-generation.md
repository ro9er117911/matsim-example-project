# Agent Generation with OSM Boundary Constraints

## Overview

This document explains the agent generation system with spatial and temporal constraints to ensure agents are placed within the actual road network (OSM) bounds and have reasonable trip durations.

## Problem Solved

### 1. Car Agents Getting Stuck Outside Network
**Issue**: 由於捷運是虛擬網路，有些開車agent開不出去，會直接走不存在的路

**Solution**: Car agents are now constrained to only use stations within the OSM boundary box. Only 32 out of 48 stations are valid for car agents.

### 2. Ultra-Long PT Routes
**Issue**: 刪除走太遠的agent(像是 pt_agent_20，不會有正常人從市中心走到淡水，那要用天來計算)

**Solution**: All agents (PT, car, walk) are constrained to maximum 40 minutes one-way trip time, ensuring realistic commute patterns.

---

## Configuration

### OSM Boundary Specification

Edit `src/main/python/generate_test_population.py` to modify:

```python
# OSM coverage area boundary (4 corners in TWD97 / EPSG:3826)
OSM_BOUNDS = {
    'top_left': (288137, 2783823),     # 左上
    'bottom_left': (287627, 2768820),  # 左下
    'bottom_right': (314701, 2769311), # 右下
    'top_right': (314401, 2784363),    # 右上
}

# City center reference point
CITY_CENTER = (302416, 2770714)

# Maximum allowed one-way trip time
MAX_TRIP_TIME_MINUTES = 40
```

### Travel Speed Models

Speeds are configured in meters per minute (m/min):

```python
MODE_SPEEDS_M_PER_MIN = {
    'pt': 500,     # PT average speed ~30 km/h (~500 m/min, includes stops)
    'car': 417,    # Car average speed ~25 km/h in Taipei traffic (~417 m/min)
    'walk': 84,    # Walking speed 1.4 m/s = 84 m/min
}
```

---

## Usage

### Generate Population XML

```bash
# Basic usage
python src/main/python/generate_test_population.py

# Output
# ✓ Output file: scenarios/corridor/taipei_test/test_population_50.xml
# Agent Generation Summary:
#   PT agents: Created 30/30
#   Car agents: Created 15/15 (32 valid stations within OSM bounds)
#   Walk agents: Created 5/5
#   TOTAL: 50 agents
```

### Validate Population XML

```bash
# Validate generated or existing population
python src/main/python/validate_population.py scenarios/corridor/taipei_test/test_population_50.xml

# Output includes:
# ✓ All car agents within OSM bounds
# ✓ All trips within 40 minute limit
# ✓ All activity times are valid
```

---

## Agent Generation Rules

### PT Agents (30 total)

- **Station Selection**: Can use ANY of the 48 stations (including those outside OSM bounds)
  - Reason: Uses virtual PT network that extends beyond OSM roads
  - Benefit: Realistic PT coverage from peripheral stations

- **Trip Duration**: Maximum 40 minutes (35 min travel + 5 min wait)
  - Uses 500 m/min speed model (~30 km/h including stops)

- **Example Valid Routes**:
  - BL02 (永寧) → BL14 (忠孝新生): ~11.6 km, ~28 min
  - R08 (中正紀念堂) → R28 (淡水): ~16.6 km, ~39 min ✓ (just under 40min limit)

### Car Agents (15 total)

- **Station Selection**: ONLY 32 stations within OSM bounds
  - Valid stations: BL10, BL11, BL12, BL13, BL14, BL15, BL16, BL19, BL22, BR09-BR12, G10, G12, G14-G16, G19, O06-O09, R02-R03, R05, R07-R08, R10-R11, R15, R22

- **Trip Duration**: Maximum 40 minutes (38 min travel + 2 min overhead)
  - Uses 417 m/min speed model (~25 km/h realistic for Taipei traffic)
  - Car agents will NOT get stuck on virtual PT network

- **Example Valid Route**:
  - BL12 (台北車站) → BL19 (永春): ~7.5 km, ~20 min ✓

### Walk Agents (5 total)

- **Station Selection**: Short-distance pairs
  - Examples: BL11→BL12 (1km), G09→G10 (0.7km), etc.

- **Trip Duration**: Maximum 40 minutes
  - Uses 84 m/min speed model (1.4 m/s standard pace)
  - All ~1km distances = ~12 minutes ✓

---

## Validation Functions

### Core Functions in `generate_test_population.py`

| Function | Purpose | Returns |
|----------|---------|---------|
| `is_within_osm_bounds(x, y)` | Check if coordinates are inside OSM rectangle | bool |
| `euclidean_distance_m(x1, y1, x2, y2)` | Calculate distance between two points | float (meters) |
| `get_station_distance_m(station1_id, station2_id)` | Get distance between two stations | float (meters) |
| `estimate_trip_time_minutes(distance_m, mode)` | Calculate expected trip time | float (minutes) |
| `is_valid_trip(home, work, mode)` | Check all constraints for a trip | bool |
| `get_proximity_score(station_id)` | Score how close station is to city center | float (0-1) |
| `filter_valid_stations(mode)` | Get list of valid stations for a mode | list[str] |

---

## Statistics and Metrics

### Generated Population (50 agents)

```
PT agents:           30/30 ✓
Car agents:          15/15 ✓ (using 32/48 valid stations)
Walk agents:          5/5 ✓

Spatial Coverage:
  - All car agents within OSM bounds: YES
  - Car agents outside PT network: YES (can't get stuck)
  - PT agents at peripheral stations: YES (market coverage)

Temporal Coverage:
  - Max trip time: 40 minutes
  - PT longest: 39.9 min (R08→R28,淡水線)
  - Car longest: ~38 min
  - Walk longest: ~15 min
```

---

## Files Modified/Created

### Modified
- `src/main/python/generate_test_population.py`
  - Added OSM boundary configuration (70+ lines)
  - Added 6 validation functions (150+ lines)
  - Modified PT/Car/Walk agent generation loops with validation

### Created
- `src/main/python/validate_population.py` (500+ lines)
  - Comprehensive population XML validator
  - Spatial constraint checks
  - Temporal constraint checks
  - Detailed reporting

- `AGENT_GENERATION_README.md` (this file)
  - Usage documentation
  - Configuration guide
  - Agent generation rules

---

## Troubleshooting

### Too Many Agents Skipped

**Symptom**: Agent generation skips many agents, total < 50

**Causes**:
1. **OSM bounds too small**: Reduces valid stations for car agents
2. **MAX_TRIP_TIME_MINUTES too strict**: Many station pairs exceed time limit
3. **Speed models unrealistic**: Mode speeds don't match actual network conditions

**Solution**:
```python
# Increase time limit
MAX_TRIP_TIME_MINUTES = 50  # (was 40)

# Adjust speed models to allow longer routes
MODE_SPEEDS_M_PER_MIN = {
    'pt': 600,    # Faster PT (was 500)
    'car': 500,   # Faster car (was 417)
    'walk': 100,  # Faster walk (was 84)
}

# Expand OSM bounds if possible
OSM_BOUNDS = { ... }  # Use larger rectangle
```

### Car Agents Still Getting Stuck

**Symptom**: Car agents unable to route after simulation starts

**Causes**:
1. **Network preparation incomplete**: PT mapper hasn't been run
2. **Car mode not in network**: Network XML doesn't have "car" mode links

**Solution**:
```bash
# 1. Ensure network has car mode links
grep -c 'allowedModes="car' network.xml

# 2. Run PT mapper first
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
    org.matsim.pt2matsim.run.PublicTransitMapper config.xml

# 3. Verify car agents in output
python validate_population.py output/population.xml
```

### Validation Fails

**Symptom**: Validation reports errors or warnings

**Solution**:
```bash
# Re-run generation
python src/main/python/generate_test_population.py

# Validate output
python src/main/python/validate_population.py \
    scenarios/corridor/taipei_test/test_population_50.xml

# Review specific agents
grep '<person id="car_agent' scenarios/corridor/taipei_test/test_population_50.xml | head -5
```

---

## Future Enhancements

- [ ] Add proximity-based station selection (prefer city center)
- [ ] Support custom speed profiles per scenario
- [ ] Add mode-specific route constraints (e.g., PT→car transfer restrictions)
- [ ] Generate visualization of valid/invalid station zones
- [ ] Export validation report to HTML

---

## References

- **Coordinate System**: EPSG:3826 (TWD97 / TM2 zone 121, Taiwan)
- **Distance Units**: Meters (projected coordinates)
- **Time Units**: Seconds (in MATSim), minutes (in this documentation)
- **Speed Units**: m/min (400+ m/min = 24+ km/h)

---

**Last Updated**: 2025-11-05
**Status**: Production Ready
