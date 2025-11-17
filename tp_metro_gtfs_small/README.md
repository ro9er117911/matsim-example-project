# tp_metro_gtfs_small - 台北捷运小型测试数据集

**状态**: ✅ **ACTIVE - TEST DATASET**
**Type**: Test/Development Data
**Created**: ~2025-11 (estimated)
**Last Updated**: 2025-11-17

---

## Overview

This is a **small subset of Taipei Metro GTFS** for testing and development.

**Use this dataset for**:
- Quick testing of PT workflows
- Development and debugging
- Small-scale simulations
- CI/CD test scenarios

**Do NOT use for**:
- Production simulations
- Full network analysis
- Complete metro coverage

---

## Dataset Contents

**GTFS files** (subset):
- ✅ agency.txt
- ✅ calendar.txt
- ✅ calendar_dates.txt
- ✅ routes.txt (limited lines)
- ✅ stop_times.txt (limited schedules)
- ✅ stops.txt (limited stations)
- ✅ trips.txt (limited trips)

**Coverage**: Small corridor or specific metro lines (verify with routes.txt)

**Coordinate System**: EPSG:3826 (TWD97 / TM2 zone 121)

---

## Source

This dataset was created by filtering `tp_metro_gtfs/`:

```bash
# Example filter command (approximate)
python3 pt2matsim/tools/filter_gtfs_bbox.py \
  --input tp_metro_gtfs \
  --output tp_metro_gtfs_small \
  --lat-min 25.02 --lat-max 25.08 \
  --lon-min 121.50 --lon-max 121.57 \
  --route-types 1
```

---

## Usage Examples

### Quick Test Simulation

```bash
# Convert small GTFS to MATSim
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  tp_metro_gtfs_small \
  scenarios/corridor/test_small/

# Run quick simulation (10 iterations)
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/test_small/config_min.xml \
  --config:controller.lastIteration 10
```

### Validate PT Mapping

```bash
# Test PT mapping on small dataset
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  scenarios/corridor/test_small/config_ptmapper.xml
```

---

## Statistics

**Approximate counts** (verify with actual data):
- Routes: ~5-10 (subset of metro lines)
- Stops: ~20-50 (limited stations)
- Trips: ~100-500 (limited schedules)

**File sizes**: Much smaller than full `tp_metro_gtfs/` dataset

---

## Advantages

✅ Fast processing (seconds instead of minutes)
✅ Easy to debug (fewer entities)
✅ Good for CI/CD tests
✅ Lightweight for development

---

## Limitations

❌ Incomplete metro network
❌ May not have all transfer stations
❌ Limited time coverage (may have fewer service periods)
❌ Not suitable for realistic simulations

---

## Related Datasets

**Full version**:
- `tp_metro_gtfs/` - Complete Taipei Metro GTFS (✅ USE FOR PRODUCTION)

**Other subsets**:
- `tp_metro_gtfs_osm_filtered/` - Filtered to OSM network bounds

**Merged datasets**:
- `merged_gtfs_extracted/` - Full merged metro + TRA

---

## Regenerating This Dataset

If you need to recreate or update this test subset:

```bash
python3 pt2matsim/tools/filter_gtfs_bbox.py \
  --input tp_metro_gtfs \
  --output tp_metro_gtfs_small_new \
  --lat-min <your_lat_min> \
  --lat-max <your_lat_max> \
  --lon-min <your_lon_min> \
  --lon-max <your_lon_max> \
  --route-types 1
```

---

**Status**: This dataset is VALID for testing purposes ✅
