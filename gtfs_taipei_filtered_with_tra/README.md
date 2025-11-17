# gtfs_taipei_filtered_with_tra - 台北市+台铁合并版 (OLD)

**状态**: ⚠️ **OLD DATASET - Superseded**
**Type**: Intermediate/Merged Data
**Created**: ~2025-11 (estimated)
**Last Updated**: 2025-11-17

---

## ⚠️ Notice: OLD MERGED DATASET

**This is an OLD merged dataset that has been superseded.**

**Use instead**:
- `merged_gtfs_extracted/` - ✅ CURRENT merged GTFS (metro + TRA)

---

## What This Dataset Was

This was an early attempt to merge:
- Filtered Taipei GTFS (`gtfs_taipei_filtered/`)
- TRA Railway GTFS (`gtfs_taipei_tra/`)

**Problems**:
1. Source dataset quality issues (inherited from `gtfs_taipei_filtered/`)
2. Merging approach has been improved
3. Better merged dataset now available

---

## Dataset Contents

**Files** (merged GTFS):
- agency.txt (combined agencies)
- calendar.txt
- calendar_dates.txt
- routes.txt (metro + TRA routes)
- stop_times.txt
- stops.txt (metro + railway stations)
- trips.txt (combined trips)

**Coordinate System**: Mixed (likely EPSG:3826)

---

## Why Kept

This directory is kept for:
- Reference to understand GTFS merging evolution
- Debugging historical issues
- Comparison with current merged dataset

**Do not use for new simulations.**

---

## Migration Path

If you were using this dataset, migrate to:

```bash
# Old (don't use)
cp gtfs_taipei_filtered_with_tra/* scenarios/my_scenario/

# New (use this instead)
cp merged_gtfs_extracted/* scenarios/my_scenario/
```

---

## See Also

- `merged_gtfs_extracted/` - ✅ CURRENT merged dataset
- `gtfs_taipei_filtered/` - OLD filtered source (also superseded)
- `gtfs_taipei_tra/` - TRA source data (still valid)
- `working_journal/2025-11-17-GTFS-Merge-Analysis.md` - Merge analysis
