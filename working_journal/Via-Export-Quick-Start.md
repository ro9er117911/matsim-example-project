# Via Export - Quick Start Guide

**Time to complete**: 5 minutes
**Updated**: 2025-11-05

---

## One-Line Summary

Generate lightweight Via-compatible visualization data from MATSim simulation output with automatic person-vehicle interaction filtering.

---

## 30-Second Quick Start

```bash
# After MATSim simulation completes, run:
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/output/via_tracks

# Then import to Via:
# 1. Open Via platform
# 2. Load: scenarios/equil/output/via_tracks/output_events.xml
# 3. Load: scenarios/equil/output/via_tracks/output_network.xml.gz
```

---

## What You Get

✅ **output_events.xml** (13 KB)
- 1,212 filtered person-vehicle events
- All agent activities and vehicle movements
- Ready for Via import

✅ **output_network.xml.gz** (3.5 MB)
- Network topology
- Transit lines + road network
- Via visualization background

✅ **Bonus files** (for analysis)
- `tracks_dt5s.csv` - Agent trajectories
- `filtered_vehicles.csv` - Vehicle list
- `vehicle_usage_report.txt` - Statistics

---

## Data Compression

```
Before:
  310,743 events in output_events.xml.gz
  2,791 vehicle definitions

After:
  1,212 events in output_events.xml
  5 used vehicles

Result: 99.6% event compression, 99.8% vehicle compression
```

---

## Parameters Reference

| Must Have | Optional But Recommended |
|-----------|--------------------------|
| `--plans` | `--events` |
| `--out` | `--vehicles` |
| | `--schedule` |
| | `--network` |
| | `--export-filtered-events` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Files not found | Check paths are absolute or relative from project root |
| No vehicle display in Via | Make sure `--export-filtered-events` flag is set |
| Large output file | Normal if scenario has many events (use with Via limits: 500 agents, 500 vehicles) |
| Slow processing | Large events files are compressed; decompress takes time |

---

## What's Happening

1. **Load plans** - Read agent definitions and trips
2. **Count vehicles** - From transitVehicles.xml (2,791 total)
3. **Extract used vehicles** - From events.xml (5 used by agents)
4. **Filter events** - Keep agent + vehicle events (1,212 total)
5. **Generate outputs** - CSV/XML files for Via

---

## Output File Structure

```
scenarios/equil/output/via_tracks/
├── output_events.xml          ← Import to Via
├── output_network.xml.gz      ← Import to Via
├── tracks_dt5s.csv
├── legs_table.csv
├── filtered_vehicles.csv
└── vehicle_usage_report.txt
```

---

## Key Statistics (Example)

```
Agents Found:        3
  - car_commuter_01
  - metro_up_01
  - metro_down_01

Vehicles Used:       5
  - car_commuter_01 (car)
  - veh_465_subway (subway)
  - veh_604_subway (subway)
  - veh_663_subway (subway)
  - veh_756_subway (subway)

Events Kept:         1,212
  - Agent events: 104
  - Vehicle events: 1,108

Compression:         99.6%
```

---

## Advanced Usage

### Event Filtering Only
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --export-filtered-events \
  --out output/via_filtered
```

### With Custom Sampling
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out output/via_export \
  --dt 10  # 10-second intervals instead of 5
```

### Full Data Enrichment
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/output/via_tracks
```

---

## Via Platform Import Steps

1. **Open Via Dashboard**
2. **New Project** → Select Output Directory
3. **Select Files**:
   - Events: `output_events.xml`
   - Network: `output_network.xml.gz`
4. **Configure Display**:
   - Agent color: by mode (car/pt)
   - Vehicle color: by type
   - Time range: full day or custom
5. **Play** - Watch agents and vehicles move

---

## Common Questions

**Q: Can I skip event filtering?**
A: Yes, use build_agent_tracks.py without `--export-filtered-events`

**Q: What's the maximum agents/vehicles?**
A: Via supports up to 500 agents and 500 vehicles

**Q: Can I filter to specific agents?**
A: Not yet - currently filters all agents and their used vehicles

**Q: How often should I run this?**
A: After each MATSim simulation run if you want updated visualization

---

## Related Documentation

- **Full Documentation**: `CLAUDE.md` - "Via Platform Export Pipeline" section
- **Implementation Details**: `working_journal/2025-11-05-Via-Export-Enhancement.md`
- **Vehicle Filtering Details**: `working_journal/2025-11-04-Vehicle-Filtering-Implementation.md`

---

**Last Updated**: 2025-11-05
**Stable**: Yes - Production Ready
