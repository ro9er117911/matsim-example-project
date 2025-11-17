# tp_metro_gtfs - 台北捷运完整数据

**状态**: ✅ **ACTIVE - PRIMARY METRO DATASET**
**Type**: Source Data
**Last Updated**: 2025-11-17

---

## Overview

This is the **primary and complete GTFS feed** for Taipei Metro (MRT) system.

**Use this dataset** for:
- Taipei Metro simulations
- PT mapping with pt2matsim
- Testing metro-only scenarios
- As source data for merged GTFS datasets

---

## Dataset Contents

**Complete GTFS specification**:
- ✅ `agency.txt` - Metro operator info
- ✅ `calendar.txt` - Service calendars
- ✅ `calendar_dates.txt` - Service exceptions
- ✅ `frequencies.txt` - Frequency-based service (optional)
- ✅ `routes.txt` - Metro lines (BL, R, G, O, BR)
- ✅ **`stop_times.txt`** - Arrival/departure times (**COMPLETE**)
- ✅ `stops.txt` - All metro stations
- ✅ `stops_epsg3826.txt` - Stations with TWD97 coordinates
- ✅ `transitions.txt` - Transfer information (optional)
- ✅ `trips.txt` - All metro trips

**Coordinate System**: EPSG:3826 (TWD97 / TM2 zone 121)

---

## Metro Lines Included

- **BL** (板南线 / Blue Line): BL01-BL23
- **R** (淡水信义线 / Red Line): R02-R28
- **G** (松山新店线 / Green Line): G01-G19
- **O** (中和新芦线 / Orange Line): O01-O54
- **BR** (文湖线 / Brown Line): BR01-BR24

---

## Usage Examples

### 1. Convert to MATSim TransitSchedule

```bash
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  tp_metro_gtfs \
  scenarios/corridor/taipei_test/
```

### 2. Filter to OSM Bounds

```bash
python3 tools/clip_gtfs_bbox.py \
  --source tp_metro_gtfs \
  --bbox3826 "288137,2768820,314701,2784363" \
  --out tp_metro_gtfs_osm_filtered
```

### 3. Create Test Subset

```bash
python3 pt2matsim/tools/filter_gtfs_bbox.py \
  --input tp_metro_gtfs \
  --output tp_metro_gtfs_small \
  --lat-min 25.02 --lat-max 25.08 \
  --lon-min 121.50 --lon-max 121.57 \
  --route-types 1
```

---

## Related Datasets

- `tp_metro_gtfs_small/` - Small test subset
- `tp_metro_gtfs_osm_filtered/` - Filtered to OSM network bounds
- `merged_gtfs_extracted/` - Merged with TRA railway data

---

## Validation

**Check completeness**:
```bash
ls tp_metro_gtfs/stop_times.txt  # Should exist
wc -l tp_metro_gtfs/stop_times.txt  # Should have many lines
```

**Verify stops**:
```bash
grep -c "^BL" tp_metro_gtfs/stops.txt  # Blue line stops
grep -c "^R" tp_metro_gtfs/stops.txt   # Red line stops
```

---

**Status**: This dataset is COMPLETE and VALIDATED ✅
