# gtfs_taipei_tra - 台铁台北区域数据

**状态**: ✅ **ACTIVE - SOURCE DATA**
**Type**: Source Data
**Last Updated**: 2025-11-17

---

## Overview

This is the **TRA (Taiwan Railways Administration) GTFS data** for Taipei area.

**Use this dataset**:
- As source data for merged GTFS datasets
- For railway-only simulations (if needed)
- For analyzing TRA service patterns

---

## Dataset Contents

**GTFS files**:
- ✅ `agency.txt` - TRA operator info
- ✅ `calendar.txt` - Service calendars
- ✅ `calendar_dates.txt` - Service exceptions (if any)
- ✅ `routes.txt` - TRA routes in Taipei area
- ✅ **`stop_times.txt`** - Arrival/departure times (**COMPLETE**)
- ✅ `stops.txt` - Railway stations
- ✅ `trips.txt` - Railway trips

**Coordinate System**: EPSG:3826 (TWD97 / TM2 zone 121)

---

## Scope

**Geographic coverage**:
- Taipei Main Station (台北車站)
- Songshan Station (松山)
- Wanhua Station (萬華)
- Other Taipei area railway stations

**Route types**: Type 2 (Railway)

---

## Usage

### Standalone Railway Simulation

```bash
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  org.matsim.project.tools.GtfsToMatsim \
  gtfs_taipei_tra \
  scenarios/corridor/railway_test/
```

### Merge with Metro Data

```bash
python3 src/main/python/merge_gtfs.py \
  tp_metro_gtfs \
  gtfs_taipei_tra \
  output_merged \
  --prefix1 METRO_ \
  --prefix2 TRA_
```

---

## Data Quality

**Validation**:
- ✅ Contains stop_times.txt (complete)
- ✅ Coordinates in EPSG:3826
- ✅ No missing required files

**Status**: This dataset is COMPLETE and USABLE ✅

---

## Related Datasets

**Merged with**:
- `merged_gtfs_extracted/` - Combined metro + TRA dataset (✅ CURRENT)

**Used in**:
- `gtfs_taipei_filtered_with_tra/` - OLD merged version (superseded)

---

## Source

TRA GTFS data was obtained from [Taiwan open data sources or TRA official feeds].

**Data freshness**: Verify service dates in `calendar.txt` and `calendar_dates.txt`

---

**Status**: This dataset is VALIDATED and READY FOR USE ✅
