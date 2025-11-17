# Cleanup Plan: Duplicates Organization

**Date**: 2025-11-17
**Purpose**: Identify and organize duplicate Python scripts, markdown documentation, and GTFS data

---

## 1. Python Files - Duplicates Found

### 1.1 Population Generation Scripts

**✅ KEEP (Current Version)**:
- `src/main/python/generate_test_population.py` (427 lines)
  - Advanced version with OSM boundary validation
  - PT transfer support (multi-line routes)
  - Trip validation (distance and time constraints)
  - Detailed reporting and statistics

**⚠️ OLD/DUPLICATE (Should be marked or removed)**:
- `./generate_test_population.py` (200 lines)
  - Basic version without validation
  - No PT transfer support
  - Minimal reporting
  - **Action**: Move to `archive/old_scripts/` with clear naming

**Also found**:
- `./src/main/python/generate_test_population_100.py` (variation for 100 agents)
  - **Action**: Keep if actively used, otherwise archive

### 1.2 Test Files (Different but similar)

**Both versions valid but have different purposes**:
- `./pt2matsim/combine/middle/tests/test_network_modes.py` (49 lines)
  - Basic mode collection test
- `./pt2matsim/tests/test_network_modes.py` (61 lines)
  - More robust test with PT link validation
  - **Recommendation**: Consolidate to single test in `pt2matsim/tests/`

### 1.3 GTFS Merge Scripts (Different tools, not duplicates)

**All are different and serve different purposes**:
- `./merge_taipei_gtfs.py` - Taipei-specific TRA + Metro merge
- `./src/main/python/merge_gtfs.py` - Generic CLI merge tool (most complete)
- `./pt2matsim/combine/middle/merge_gtfs.py` - Specific tw_v5 + tp_metro merge

**Action**: Keep all, but add clear documentation to each explaining their purpose

### 1.4 GTFS Filter/Clip Tools (Different approaches)

**Both are different**:
- `./pt2matsim/tools/filter_gtfs_bbox.py` (314 lines) - Uses lat/lon + route types
- `./tools/clip_gtfs_bbox.py` (208 lines) - Uses EPSG:3826 coordinates

**Action**: Keep both, document their different use cases

### 1.5 Other Root-Level Python Scripts

**Likely old/duplicate scripts in root**:
- `./clean_non_taipei_metro.py`
- `./filter_gtfs_taipei.py`
- `./filter_gtfs_taipei_tra.py`
- `./filter_gtfs_taipei_tra_full.py`
- `./fix_stop_times_issue.py`
- `./rebuild_gtfs_with_stop_times.py`

**Action**: Review each and move to `archive/old_scripts/` if not actively used

---

## 2. Markdown Documentation - Duplicates Found

### 2.1 GTFS Merge Analysis

**✅ KEEP (Most detailed version)**:
- `./working_journal/2025-11-17-GTFS-Merge-Analysis.md` (287 lines)
  - Most recent and detailed
  - Includes analysis findings and recommendations

**⚠️ DUPLICATE (Shorter summary)**:
- `./GTFS_MERGE_ANALYSIS.md` (239 lines)
  - Similar content but less detail
  - **Action**: Add note at top: "See working_journal/2025-11-17-GTFS-Merge-Analysis.md for detailed version" or remove

### 2.2 Multiple README files

**Various README.md files found**:
- `./README.md` (main project README - ✅ KEEP)
- `./archive/README.md` (archive explanation - ✅ KEEP)
- `./.claude/skills/matsim-skill/README.md` (skill documentation - ✅ KEEP)
- `./docs/README.md` (docs index - ✅ KEEP)
- `./src/main/python/README.md` (Python tools - ✅ KEEP)
- `./src/main/python/build_agent_tracks/README.md` (Via export - ✅ KEEP)
- `./original-input-data/README.md` (data source info - ✅ KEEP)
- `./scenarios/corridor/all_pt_test/README.md` (scenario info - ✅ KEEP)
- `./pt2matsim/combine/input/gtfs_tw_v5_taipei_station/README.md` (GTFS subset - ✅ KEEP)

**Assessment**: All README files serve different purposes - all should be kept

### 2.3 Archived Journal Entries

**Potential duplicates in archive/working_journal**:
- `./archive/working_journal/WEEKLY_EXECUTION_SUMMARY.md`
- `./archive/summaries/WEEKLY_EXECUTION_SUMMARY.md`

**Action**: Check if these are true duplicates and consolidate

---

## 3. GTFS Data - Organization Needed

### 3.1 Current GTFS Datasets (Root Level)

**Primary datasets**:

1. **`gtfs_tw_v5/`** (全台湾交通数据)
   - ⚠️ **Missing stop_times.txt - UNUSABLE**
   - Contains: agency, calendar, routes, stops, trips
   - **Status**: INCOMPLETE - Cannot be used for simulation
   - **Action**: Add README.md with warning

2. **`tp_metro_gtfs/`** (台北捷运完整数据)
   - ✅ Complete GTFS with stop_times.txt
   - **Status**: PRIMARY METRO DATASET - KEEP
   - **Action**: Add README.md explaining it's the primary metro feed

3. **`tp_metro_gtfs_small/`** (测试用小型数据集)
   - ✅ Small subset for testing
   - **Status**: TEST DATASET - KEEP
   - **Action**: Add README.md explaining it's for testing

4. **`tp_metro_gtfs_osm_filtered/`** (OSM范围过滤版)
   - Filtered to OSM network bounds
   - **Status**: INTERMEDIATE - Created by filter scripts
   - **Action**: Add README.md with creation date and purpose

**Derived/merged datasets**:

5. **`gtfs_taipei_filtered/`** (台北市过滤版)
   - Filtered version of gtfs_tw_v5 for Taipei
   - **Status**: OLD/INTERMEDIATE
   - **Action**: Add README.md marking as "OLD - See merged_gtfs_extracted"

6. **`gtfs_taipei_tra/`** (台铁数据)
   - TRA railway data
   - **Status**: SOURCE DATA - KEEP
   - **Action**: Add README.md explaining source

7. **`gtfs_taipei_filtered_with_tra/`** (台北市+台铁)
   - Merged version
   - **Status**: OLD/INTERMEDIATE
   - **Action**: Mark as "OLD - Superseded by merged_gtfs_extracted"

8. **`merged_gtfs_extracted/`** (最新合并版本)
   - Latest merged dataset
   - **Status**: CURRENT MERGED DATASET - KEEP
   - **Action**: Add README.md explaining it's the current merged version

### 3.2 Recommended GTFS Directory Structure

**Proposed reorganization**:

```
gtfs_data/
├── source/                          # Original source datasets
│   ├── tp_metro_gtfs/               # Primary metro feed (KEEP)
│   ├── gtfs_taipei_tra/             # TRA railway (KEEP)
│   └── gtfs_tw_v5/                  # Taiwan-wide (UNUSABLE - missing stop_times)
│       └── README.md                # ⚠️ Warning: Incomplete dataset
├── working/                         # Intermediate/filtered versions
│   ├── tp_metro_gtfs_small/         # Test subset
│   ├── tp_metro_gtfs_osm_filtered/  # OSM-filtered metro
│   ├── gtfs_taipei_filtered/        # OLD filtered version
│   └── gtfs_taipei_filtered_with_tra/ # OLD merged version
└── output/                          # Final merged datasets
    └── merged_gtfs_extracted/       # Current merged GTFS (ACTIVE)
        └── README.md                # Explains merge components
```

---

## 4. Action Items Summary

### 4.1 Python Scripts

- [ ] Move old `generate_test_population.py` to `archive/old_scripts/generate_test_population_basic.py`
- [ ] Consolidate test files: Keep only `pt2matsim/tests/test_network_modes.py`
- [ ] Add documentation headers to merge_gtfs scripts explaining their purposes
- [ ] Review and archive root-level GTFS processing scripts if not actively used

### 4.2 Markdown Documentation

- [ ] Add redirect note in `GTFS_MERGE_ANALYSIS.md` pointing to working_journal version
- [ ] Check for duplicate WEEKLY_EXECUTION_SUMMARY.md and consolidate
- [ ] All README.md files are valid - no action needed

### 4.3 GTFS Data

- [ ] Add README.md to each GTFS directory explaining:
  - **Purpose** (source/working/output)
  - **Status** (active/old/intermediate/unusable)
  - **Creation date** and **last modified**
  - **Dependencies** (if merged, what sources were used)

- [ ] Create clear markers for old/superseded datasets:
  ```
  gtfs_taipei_filtered/
  └── OLD_DATASET_README.md
      ⚠️ OLD DATASET - Superseded by merged_gtfs_extracted
      Keep for reference only
  ```

- [ ] Optional: Reorganize GTFS into source/working/output structure

### 4.4 Documentation

- [ ] Create `GTFS_DATA_INVENTORY.md` documenting all GTFS datasets
- [ ] Update `CLAUDE.md` with GTFS data organization guidelines
- [ ] Update `.gitignore` to ensure old datasets are not accidentally modified

---

## 5. Priority Cleanup Tasks

**High Priority** (do first):
1. Add README.md to all GTFS directories explaining their status
2. Mark old/superseded GTFS datasets clearly
3. Move old generate_test_population.py to archive

**Medium Priority**:
4. Consolidate test files
5. Add documentation to merge_gtfs scripts
6. Review root-level Python scripts for archival

**Low Priority**:
7. Reorganize GTFS into source/working/output structure (optional)
8. Create comprehensive GTFS data inventory document

---

## 6. Files to Keep vs Archive

### Keep in Root/Active Locations
- `src/main/python/generate_test_population.py` (advanced version)
- `src/main/python/merge_gtfs.py` (generic tool)
- All current GTFS in `gtfs_data/source/` and `gtfs_data/output/`
- `working_journal/2025-11-17-GTFS-Merge-Analysis.md`

### Move to Archive
- `./generate_test_population.py` → `archive/old_scripts/`
- Root-level GTFS scripts → `archive/old_scripts/gtfs/`
- Old GTFS intermediate datasets → Mark with README, keep for reference

### Mark as Deprecated (but keep)
- `gtfs_taipei_filtered/` - Add "OLD" marker
- `gtfs_taipei_filtered_with_tra/` - Add "OLD" marker
- `GTFS_MERGE_ANALYSIS.md` - Add redirect note

---

**Next Step**: Execute cleanup according to priority list above
