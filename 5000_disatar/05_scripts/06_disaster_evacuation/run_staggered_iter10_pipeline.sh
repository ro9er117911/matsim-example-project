#!/usr/bin/env bash
# Run the staggered tsunami scenario and build SimWrapper dashboard assets with visual filters.
# Default config = iter10; override with CONFIG_FILE=/path/to/config_combined_5000_staggered_iter100.xml for 100 iters.
# Usage: ./5000_disatar/05_scripts/06_disaster_evacuation/run_staggered_iter10_pipeline.sh
# Env knobs:
#   CONFIG_FILE=...             # Optional override config (defaults to iter10)
#   JAVA_MEM="-Xms12g -Xmx12g"  # JVM memory (default 12g)
#   SKIP_SIM=1                  # Skip the simulation and only regenerate dashboard assets
#   MIN_VOLUME=20               # Flow threshold for map filter (veh/15min)
#   MIN_TT_RATIO=2              # Travel-time ratio threshold for map filter

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CONFIG="${CONFIG_FILE:-${ROOT}/5000_disatar/05_combined_evac/config_combined_5000_staggered_iter10.xml}"
# [DEPRECATED] VIA export - now using SimWrapper for visualization
# RUNNER="${ROOT}/run_simulation_with_via_export.sh"
RUNNER="${ROOT}/5000_disatar/05_scripts/05_simulation/run_simulation.sh"
DASH_PIPELINE="${ROOT}/5000_disatar/05_scripts/07_analysis/run_dashboard_pipeline.sh"
# Hazard polygons (buffered zones) and line closures (moderate 0-3km)
HAZARD_POLY_SRC="${ROOT}/output/inundation_zones_buffered.geojson"
HAZARD_LINE_SRC="${ROOT}/output/moderate_closure.geojson"

# Original Network with Attributes (for Road Names)
export INPUT_NETWORK="${ROOT}/scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz"

# Derive outputDirectory from config
OUTPUT_DIR="$(
  python3 - "$CONFIG" <<'PY'
import sys, xml.etree.ElementTree as ET
cfg = sys.argv[1]
root = ET.parse(cfg).getroot()
for mod in root.findall("module"):
    if mod.get("name") == "controller":
        for p in mod.findall("param"):
            if p.get("name") == "outputDirectory":
                print(p.get("value"))
                raise SystemExit
raise SystemExit("outputDirectory not found")
PY
)"

echo "Config: $CONFIG"
echo "Output dir: $OUTPUT_DIR"

JAVA_MEM_DEFAULT="-Xms12g -Xmx12g -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"
export JAVA_OPTS="${JAVA_OPTS:-${JAVA_MEM_DEFAULT}}"
export MAVEN_OPTS="${MAVEN_OPTS:-${JAVA_OPTS}}"

if [[ "${SKIP_SIM:-0}" != "1" ]]; then
  echo "=== Running simulation (staggered) ==="
  "${RUNNER}" "${CONFIG}"
else
  echo "=== SKIP_SIM=1 set; reusing existing output at ${OUTPUT_DIR} ==="
fi

echo "=== Building dashboard assets with visual filters ==="
# Default to no filtering so all used links appear (override with MIN_VOLUME/MIN_TT_RATIO if desired)
MIN_VOLUME="${MIN_VOLUME:-0}" MIN_TT_RATIO="${MIN_TT_RATIO:-0}" "${DASH_PIPELINE}" "${OUTPUT_DIR}"

# Copy hazard polygons (buffered zones) and line closures to output
if [[ -f "$HAZARD_POLY_SRC" ]]; then
  cp "$HAZARD_POLY_SRC" "${OUTPUT_DIR}/hazard_zone.geojson"
else
  echo "Warning: Hazard polygon GeoJSON not found at $HAZARD_POLY_SRC"
fi
if [[ -f "$HAZARD_LINE_SRC" ]]; then
  cp "$HAZARD_LINE_SRC" "${OUTPUT_DIR}/moderate_closure.geojson"
fi

echo "=== Generating Stuck Agents Analysis ==="
python3 "${ROOT}/5000_disatar/05_scripts/07_analysis/generate_stuck_agents_csv.py" "${OUTPUT_DIR}" "${INPUT_NETWORK}"

echo "=== Copying Dashboard Templates ==="
DASH5_TEMPLATE="${ROOT}/tools/dashboard-5-stuck.yaml"
if [[ -f "$DASH5_TEMPLATE" ]]; then
  cp "$DASH5_TEMPLATE" "${OUTPUT_DIR}/dashboard-5.yaml"
fi

echo "Done. Load SimWrapper with ${OUTPUT_DIR}."
