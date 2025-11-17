# gtfs_tw_v5 - 全台湾交通数据

**状态**: ⚠️ **UNUSABLE - INCOMPLETE DATASET**
**Last Updated**: 2025-11-17

---

## ⚠️ Critical Issue

**This dataset is MISSING `stop_times.txt` - a required GTFS file.**

Without `stop_times.txt`:
- Cannot generate MATSim transitSchedule.xml
- Cannot be used for any schedule-based simulation
- Missing arrival/departure times for all trips

**DO NOT USE this dataset for MATSim simulations.**

---

## Dataset Contents

**Files present**:
- ✅ `agency.txt` (393 agencies)
- ✅ `calendar.txt` (261,385 service calendars)
- ✅ `calendar_dates.txt` (56,884 exceptions)
- ✅ `routes.txt` (9,663 routes)
- ✅ `stops.txt` (154,477 stops)
- ✅ `stops_epsg3826.txt` (154,477 stops with TWD97 coordinates)
- ✅ `trips.txt` (326,645 trips)
- ❌ **`stop_times.txt` - MISSING**

**Route types**:
- Type 1 (Metro): 47 routes
- Type 2 (Rail): 1,234 routes
- Type 3 (Bus): 8,329 routes
- Type 4 (Ferry): 49 routes
- Type 6 (Cable car/Aviation): 4 routes

---

## Usage

**This dataset should NOT be used directly.**

If you need Taiwan-wide GTFS data:
1. Request complete GTFS feed from source (including stop_times.txt)
2. Or use specific regional datasets like `tp_metro_gtfs/` for Taipei metro

---

## See Also

- `tp_metro_gtfs/` - Complete Taipei Metro GTFS (✅ USABLE)
- `merged_gtfs_extracted/` - Merged GTFS with metro + TRA
- `working_journal/2025-11-17-GTFS-Merge-Analysis.md` - Analysis of this dataset's issues
