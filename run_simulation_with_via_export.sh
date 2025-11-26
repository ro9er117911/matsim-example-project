#!/usr/bin/env bash
# Run MATSim simulation and Via export for a given config.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <config.xml>" >&2
  exit 1
fi

CONFIG="$1"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT}/logs"
mkdir -p "${LOG_DIR}"

JAVA_OPTS=${JAVA_OPTS:-"-Xms12g -Xmx12g -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"}

ts() { date +"%Y-%m-%d_%H-%M-%S"; }

echo "=== Pre-flight ==="
echo "Config: ${CONFIG}"

# Basic free-memory check (approx, macOS vm_stat)
if command -v vm_stat >/dev/null 2>&1; then
  FREE_PAGES=$(vm_stat | awk '/(Pages free|Pages inactive)/{gsub(\".\",\"\",$3);free+=$3} END{print free+0}')
  PAGE_SIZE=$(vm_stat | awk '/page size of/{print $8}')
  FREE_GB=$(( FREE_PAGES * PAGE_SIZE / 1024 / 1024 / 1024 ))
  if [[ ${FREE_GB} -lt 14 ]]; then
    echo "Warning: Available memory ~${FREE_GB} GB (<14GB). Consider closing apps." >&2
  fi
fi

if [[ ! -f "${CONFIG}" ]]; then
  echo "Config not found: ${CONFIG}" >&2
  exit 1
fi

# Derive output directory from config
OUTPUT_DIR=$(python3 - <<'PY'
import sys, xml.etree.ElementTree as ET
cfg = sys.argv[1]
tree = ET.parse(cfg)
root = tree.getroot()
out = None
for mod in root.findall("module"):
    if mod.get("name") == "controller":
        for p in mod.findall("param"):
            if p.get("name") == "outputDirectory":
                out = p.get("value")
                break
if not out:
    raise SystemExit("outputDirectory not found in config")
print(out)
PY
 "${CONFIG}")

echo "Output directory: ${OUTPUT_DIR}"

JAR="${ROOT}/target/matsim-example-project-0.0.1-SNAPSHOT.jar"
if [[ ! -f "${JAR}" ]]; then
  echo "JAR not found at ${JAR}. Build with ./mvnw package" >&2
  exit 1
fi

SIM_LOG="${LOG_DIR}/sim_$(ts).log"
EXPORT_LOG="${LOG_DIR}/via_export_$(ts).log"

echo "=== Running simulation ==="
set +e
java ${JAVA_OPTS} -jar "${JAR}" "${CONFIG}" > "${SIM_LOG}" 2>&1
SIM_EXIT=$?
set -e
if [[ ${SIM_EXIT} -ne 0 ]]; then
  echo "Simulation failed, see log: ${SIM_LOG}" >&2
  exit ${SIM_EXIT}
fi
echo "Simulation complete. Log: ${SIM_LOG}"

PLANS="${OUTPUT_DIR}/output_plans.xml.gz"
EVENTS="${OUTPUT_DIR}/output_events.xml.gz"
NETWORK="${OUTPUT_DIR}/output_network.xml.gz"
SCHEDULE="${ROOT}/scenarios/equil/transitSchedule-0300-0618.xml.gz"
VEHICLES="${ROOT}/scenarios/equil/transitVehicles-0300-0618.xml.gz"
OUT_DIR="${OUTPUT_DIR}/via_export"

echo "=== Running Via export ==="
python3 "${ROOT}/src/main/python/build_agent_tracks.py" \
  --plans "${PLANS}" \
  --events "${EVENTS}" \
  --network "${NETWORK}" \
  --schedule "${SCHEDULE}" \
  --vehicles "${VEHICLES}" \
  --export-filtered-events \
  --out "${OUT_DIR}" \
  --dt 5 \
  > "${EXPORT_LOG}" 2>&1
echo "Via export complete. Log: ${EXPORT_LOG}"

echo "All done. Outputs in ${OUTPUT_DIR}"
