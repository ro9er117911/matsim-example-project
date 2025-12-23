# OSM Network Rebuild (v7)

Input: `5000_disatar/01_raw_data/osm/disaster_bbox_complete.pbf`  
Builder: `org.matsim.project.tools.BuildCarWalkNetworkFromOsm` (no XML config)  
Outputs:
- Raw: `5000_disatar/03_phase2_production/networks/network_v7_car_walk_raw.xml(.gz)`
- Clean: `5000_disatar/03_phase2_production/networks/network_v7_car_walk_clean.xml(.gz)`

Legacy (pt2matsim `Osm2MultimodalNetwork`) configs are archived at:
`archive/5000_disatar/03_phase2_production/configs/osm2network/`

## 1) Build v7 car+walk network

```bash
cd /Users/ro9air/matsim-example-project
# v7 car+walk multimodal build using MATSim contrib-osm with custom highway defaults:
./mvnw -q -DskipTests exec:java \
  -Dexec.mainClass="org.matsim.project.tools.BuildCarWalkNetworkFromOsm" \
  -Dexec.args="5000_disatar/01_raw_data/osm/disaster_bbox_complete.pbf \
               5000_disatar/03_phase2_production/networks/network_v7_car_walk_raw.xml \
               5000_disatar/03_phase2_production/networks/network_v7_car_walk_clean.xml" \
  | tee 5000_disatar/03_phase2_production/logs/osm_conversion_v7_car_walk.log
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
  -Dexec.args="5000_disatar/03_phase2_production/networks/network_v7_car_walk_raw.xml 5000_disatar/03_phase2_production/networks/network_v7_car_walk_clean.xml" \
  | tee 5000_disatar/03_phase2_production/logs/osm_clean_v7_car_walk.log
```

Keep both raw and clean files; if cleaners drop neighborhoods, revert to the raw network.

## 3) Validation checklist

- Highway coverage (raw or clean):
  ```bash
  python3 5000_disatar/05_scripts/count_highway.py 5000_disatar/03_phase2_production/networks/network_v7_car_walk_raw.xml | head -n 30
  ```
  Expect non-zero counts for `residential,service,unclassified,living_street,track,path,footway,pedestrian`.

- Modes present:
  ```bash
  grep -o 'modes=\"[^\"]*\"' 5000_disatar/03_phase2_production/networks/network_v7_car_walk_raw.xml | sort | uniq -c
  ```
  Expect at least `car` and `walk` (plus `pt`/`bike`).

- Keep an eye on bbox edge cuts: if clusters are isolated, re-run with larger extract or skip cleaner.

## 4) Hand-off to PT mapping

- Use `network_v7_car_walk_clean.xml(.gz)` if connectivity is good; otherwise feed the raw network to ptmapper.
