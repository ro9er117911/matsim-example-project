# tp_metro_gtfs_osm_filtered - OSM范围过滤的台北捷运数据

**状态**: ✅ **ACTIVE - WORKING DATA**
**Type**: Intermediate/Working Data
**Created**: ~2025-11 (estimated)
**Last Updated**: 2025-11-17

---

## Overview

This is **Taipei Metro GTFS filtered to match OSM network bounds**.

**Purpose**:
- Align metro data with available OSM road network
- Ensure all metro stations are within OSM coverage area
- Prepare for multimodal (metro + car) simulations

**Use this dataset when**:
- Running multimodal simulations with OSM-derived road network
- PT mapping requires alignment with OSM coverage
- Car agents need valid road network around metro stations

---

## Dataset Contents

**GTFS files** (filtered):
- ✅ agency.txt
- ✅ calendar.txt
- ✅ calendar_dates.txt
- ✅ routes.txt (metro lines within OSM bounds)
- ✅ stop_times.txt (schedules for filtered stations)
- ✅ stops.txt (stations within OSM bounds)
- ✅ stops_epsg3826.txt (TWD97 coordinates)
- ✅ trips.txt (trips serving filtered stations)

**Coordinate System**: EPSG:3826 (TWD97 / TM2 zone 121)

---

## OSM Bounds

This dataset was filtered to the following OSM network coverage:

```
OSM Coverage Area (EPSG:3826 / TWD97):
- Top Left:     (288137, 2783823)
- Bottom Left:  (287627, 2768820)
- Bottom Right: (314701, 2769311)
- Top Right:    (314401, 2784363)
```

**Stations outside these bounds are excluded.**

---

## Source

This dataset was created by filtering `tp_metro_gtfs/`:

```bash
python3 tools/clip_gtfs_bbox.py \
  --source tp_metro_gtfs \
  --bbox3826 "288137,2768820,314701,2784363" \
  --out tp_metro_gtfs_osm_filtered
```

**Filter tool**: `tools/clip_gtfs_bbox.py`

---

## Usage Examples

### Generate Test Population Aligned with OSM

```bash
# Population generator uses OSM bounds by default
python3 src/main/python/generate_test_population.py

# Output population will only use stations within OSM bounds
```

### Multimodal Simulation Setup

```bash
# 1. Convert filtered GTFS to MATSim
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  tp_metro_gtfs_osm_filtered \
  scenarios/corridor/taipei_test/

# 2. Map to OSM network
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  scenarios/corridor/taipei_test/config_ptmapper.xml

# 3. Run multimodal simulation (PT + car)
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config.xml
```

---

## Differences from Full Dataset

**Compared to `tp_metro_gtfs/`**:

✅ **Advantages**:
- All stations have nearby OSM road network
- Car agents can route to/from metro stations
- No "stranded" stations outside OSM coverage
- Smaller dataset size (faster processing)

❌ **Limitations**:
- Some peripheral metro stations excluded
- Incomplete metro line coverage (ends may be cut)
- Not suitable for full metro network analysis

---

## Validation

**Check filtered coverage**:

```bash
# Count stations in filtered vs full dataset
wc -l tp_metro_gtfs_osm_filtered/stops.txt
wc -l tp_metro_gtfs/stops.txt

# List excluded stations (if needed)
comm -13 \
  <(cut -d, -f1 tp_metro_gtfs_osm_filtered/stops.txt | sort) \
  <(cut -d, -f1 tp_metro_gtfs/stops.txt | sort)
```

---

## Related Datasets

**Source**:
- `tp_metro_gtfs/` - Full Taipei Metro GTFS (before filtering)

**Other filtered versions**:
- `tp_metro_gtfs_small/` - Small test subset (different filter)

**Merged datasets**:
- `merged_gtfs_extracted/` - Full merged metro + TRA (no OSM filtering)

---

## Regenerating This Dataset

If OSM network bounds change, regenerate with:

```bash
python3 tools/clip_gtfs_bbox.py \
  --source tp_metro_gtfs \
  --bbox3826 "<new_xmin>,<new_ymin>,<new_xmax>,<new_ymax>" \
  --out tp_metro_gtfs_osm_filtered_new
```

**Note**: Update OSM bounds in `src/main/python/generate_test_population.py` to match.

---

**Status**: This dataset is VALID for OSM-aligned simulations ✅
