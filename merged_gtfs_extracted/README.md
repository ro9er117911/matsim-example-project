# merged_gtfs_extracted - 台北市多模式公共运输 GTFS (CURRENT)

**状态**: ✅ **ACTIVE - CURRENT MERGED DATASET**
**Type**: Output/Production Data
**Created**: 2025-11-17
**Last Updated**: 2025-11-17

---

## Overview

This is the **current, active merged GTFS dataset** for Taipei multi-modal public transport.

**Includes**:
- 🚇 Taipei Metro (MRT) - All 5 lines (BL, R, G, O, BR)
- 🚆 TRA Railway - Selected Taipei area stations

**Use this dataset** for:
- Multi-modal Taipei simulations (metro + rail)
- Production MATSim scenarios
- PT mapping with pt2matsim
- Via visualization exports

---

## Dataset Contents

**Complete GTFS specification**:
- ✅ `agency.txt` - Metro + TRA agencies
- ✅ `calendar.txt` - Combined service calendars
- ✅ `calendar_dates.txt` - Service exceptions
- ✅ `routes.txt` - Metro lines + TRA routes
- ✅ **`stop_times.txt`** - All arrival/departure times (**COMPLETE**)
- ✅ `stops.txt` - Metro stations + railway stations
- ✅ `trips.txt` - Combined trips

**Coordinate System**: EPSG:3826 (TWD97 / TM2 zone 121)

---

## Source Datasets

This merged GTFS was created from:

1. **`tp_metro_gtfs/`** (primary source)
   - Complete Taipei Metro GTFS
   - All 5 metro lines
   - Validated and complete

2. **`gtfs_taipei_tra/`** (secondary source)
   - TRA Railway data for Taipei area
   - Selected stations and routes

**Merge Tool**: `src/main/python/merge_gtfs.py`

**Merge Date**: 2025-11-17

---

## Statistics

**Approximate counts** (verify with actual data):
- Agencies: ~10+ (metro + TRA operators)
- Routes: ~50+ (metro lines + TRA routes)
- Stops: ~200+ (metro stations + railway stations)
- Trips: Variable (depends on service calendars)

---

## Usage Examples

### 1. Convert to MATSim TransitSchedule

```bash
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  merged_gtfs_extracted \
  scenarios/corridor/taipei_test/
```

### 2. Map to OSM Network

```bash
# 1. Create PT mapper config
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  scenarios/corridor/taipei_test/config_ptmapper.xml

# 2. Run mapping
java -Xmx10g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  scenarios/corridor/taipei_test/config_ptmapper.xml
```

### 3. Validate GTFS

```bash
python3 src/main/python/validate_gtfs.py merged_gtfs_extracted
```

---

## Quality Checks

**Validation performed**:
- ✅ All required GTFS files present
- ✅ stop_times.txt complete with schedules
- ✅ Coordinate system consistent (EPSG:3826)
- ✅ No duplicate IDs between metro and TRA
- ✅ Transfer stations properly defined

**Known Issues**: None (as of 2025-11-17)

---

## Updating This Dataset

If you need to regenerate or update this merged GTFS:

```bash
python3 src/main/python/merge_gtfs.py \
  tp_metro_gtfs \
  gtfs_taipei_tra \
  merged_gtfs_extracted_new \
  --prefix1 METRO_ \
  --prefix2 TRA_
```

---

## Related Datasets

**Source data**:
- `tp_metro_gtfs/` - Taipei Metro source
- `gtfs_taipei_tra/` - TRA Railway source

**Old/superseded datasets** (don't use):
- `gtfs_taipei_filtered/` - OLD filtered version
- `gtfs_taipei_filtered_with_tra/` - OLD merged version

**Subsets/variants**:
- `tp_metro_gtfs_small/` - Small metro-only test subset
- `tp_metro_gtfs_osm_filtered/` - Metro filtered to OSM bounds

---

## Documentation

See also:
- `working_journal/2025-11-17-GTFS-Merge-Analysis.md` - Merge analysis and methodology
- `GTFS_TOOLS_GUIDE.md` - GTFS processing tools guide
- `docs/3-public-transit.md` - PT workflow documentation

---

**Status**: This dataset is VALIDATED and READY FOR USE ✅
