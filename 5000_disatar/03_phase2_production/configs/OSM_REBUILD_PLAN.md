# OSM Full Network Rebuild (v5)

Input: `5000_disatar/01_raw_data/osm/disaster_bbox.osm.pbf`  
Config: `5000_disatar/03_phase2_production/configs/osm2network-config-v5-full.xml`  
Outputs:
- Raw (no cleaner): `5000_disatar/03_phase2_production/networks/network_full_raw.xml`
- Optional cleaned: `5000_disatar/03_phase2_production/networks/network_full_clean.xml`

## 1) Build raw, uncleaned network

```bash
cd /Users/ro9air/matsim-example-project
# (legacy pt2matsim flow — kept for reference; use v7 car+walk build below instead)
# java -Xmx8g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
#   org.matsim.pt2matsim.run.Osm2MultimodalNetwork \
#   5000_disatar/01_raw_data/osm/disaster_bbox.osm.pbf \
#   5000_disatar/03_phase2_production/networks/network_full_raw.xml \
#   EPSG:3826 \
#   5000_disatar/03_phase2_production/configs/osm2network-config-v5-full.xml \
#   | tee 5000_disatar/03_phase2_production/logs/osm_conversion_v5.log

# New (v7) car+walk multimodal build using MATSim contrib-osm with custom highway defaults:
./mvnw -q -DskipTests exec:java \
  -Dexec.mainClass="org.matsim.project.tools.BuildCarWalkNetworkFromOsm" \
  -Dexec.args="5000_disatar/01_raw_data/osm/disaster_bbox_complete.pbf \
               5000_disatar/03_phase2_production/networks/network_v7_car_walk_raw.xml \
               5000_disatar/03_phase2_production/networks/network_v7_car_walk_clean.xml" \
  | tee 5000_disatar/03_phase2_production/logs/osm_conversion_v7_car_walk.log

# Outputs (v7):
# - Raw:   networks/network_v7_car_walk_raw.xml(.gz)
# - Clean: networks/network_v7_car_walk_clean.xml(.gz)
```

Notes:
- `keepPaths=true` keeps footway/path/steps/pedestrian.
- `maxLinkLength=75m` preserves local streets/turn pockets; lower to 25m if needed.
- Do **not** run NetworkCleaner here; keep the raw network for comparison.

V7 specifics:
- Input `disaster_bbox_complete.pbf` was regenerated from `taiwan_latest.osm.pbf` with bbox (top=25.245, bottom=24.585, left=121.23, right=121.71) and `completeWays=yes`.
- Custom highway defaults include residential/service/unclassified/living_street/track/path/footway/steps/cycleway/pedestrian.
- Mode rules: walk allowed on all links; car only on driveable classes (no car on footway/path/steps/pedestrian/cycleway).
- Key OSM tags stored on links: `osm:way:highway`, `osm:way:name`, `osm:way:id`.

## 2) Optional cleaning (only after checking coverage)

```bash
cd /Users/ro9air/matsim-example-project
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="5000_disatar/03_phase2_production/networks/network_full_raw.xml 5000_disatar/03_phase2_production/networks/network_full_clean.xml" \
  | tee 5000_disatar/03_phase2_production/logs/osm_clean_v5.log
```

Keep both raw and clean files; if cleaners drop neighborhoods, revert to the raw network.

## 3) Validation checklist

- Highway coverage (raw or clean):
  ```bash
  python3 5000_disatar/05_scripts/count_highway.py 5000_disatar/03_phase2_production/networks/network_full_raw.xml | head -n 30
  ```
  Expect non-zero counts for `residential,service,unclassified,living_street,track,path,footway,pedestrian`.

- Modes present:
  ```bash
  grep -o 'modes=\"[^\"]*\"' 5000_disatar/03_phase2_production/networks/network_full_raw.xml | sort | uniq -c
  ```
  Expect at least `car` and `walk` (plus `pt`/`bike`).

- Keep an eye on bbox edge cuts: if clusters are isolated, re-run with larger extract or skip cleaner.

## 4) Hand-off to PT mapping

- Use `network_full_clean.xml` if connectivity is good; otherwise feed `network_full_raw.xml` to ptmapper.
- Update `START_MAPPING_HERE.txt` checkpoints once the chosen network is ready.
