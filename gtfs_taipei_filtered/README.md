# gtfs_taipei_filtered - 台北市过滤版 (OLD)

**状态**: ⚠️ **OLD DATASET - Superseded**
**Type**: Intermediate/Working Data
**Created**: ~2025-11 (estimated)
**Last Updated**: 2025-11-17

---

## ⚠️ Notice: OLD DATASET

**This is an OLD intermediate dataset.**

**Use instead**:
- `tp_metro_gtfs/` - For metro-only simulations
- `merged_gtfs_extracted/` - For merged metro + TRA simulations

---

## What This Dataset Was

This was an intermediate filtered version of `gtfs_tw_v5` limited to Taipei area.

**Problems**:
1. Source dataset (`gtfs_tw_v5`) is incomplete (missing `stop_times.txt`)
2. Has been superseded by better merged datasets
3. Filtering approach was not optimal

---

## Dataset Contents

**Files**:
- agency.txt
- calendar.txt
- calendar_dates.txt
- routes.txt
- stop_times.txt (filtered)
- stops.txt
- trips.txt

**Coordinate System**: Mixed (needs verification)

---

## Why Kept

This directory is kept for reference and to understand the evolution of GTFS data processing in this project.

**Do not use for new simulations.**

---

## See Also

- `gtfs_taipei_filtered_with_tra/` - OLD merged version (also superseded)
- `merged_gtfs_extracted/` - ✅ CURRENT merged dataset
- `working_journal/2025-11-17-GTFS-Merge-Analysis.md` - Analysis of data quality issues
