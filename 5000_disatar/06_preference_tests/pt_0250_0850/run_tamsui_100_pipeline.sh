#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CONFIG="${ROOT}/5000_disatar/06_preference_tests/pt_0250_0850/config_tamsui_100.xml"
POP_GEN="${ROOT}/5000_disatar/06_preference_tests/generate_tamsui_population_100.py"
NETWORK_RAW="${ROOT}/5000_disatar/06_preference_tests/pt_0250_0850/network-with-pt.xml.gz"
NETWORK="${ROOT}/5000_disatar/06_preference_tests/pt_0250_0850/network-with-pt-car-connected.xml.gz"

if [[ ! -f "${CONFIG}" ]]; then
  echo "Config not found: ${CONFIG}" >&2
  exit 1
fi

echo "=== [1/4] Generate population (Tamsui 50 PT + 50 car) ==="
python3 "${POP_GEN}"

echo "=== [2/4] Ensure car network is connected ==="
if [[ ! -f "${NETWORK}" ]]; then
  MAVEN_OPTS="${JAVA_OPTS:--Xms2g -Xmx2g}" \
    "${ROOT}/mvnw" -q \
    -Dexec.mainClass=org.matsim.project.tools.TrimCarModeToLargestComponent \
    -Dexec.args="${NETWORK_RAW} ${NETWORK}" \
    exec:java
fi

OUTPUT_DIR=$(python3 - "${CONFIG}" <<'PY'
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
)

mkdir -p "${OUTPUT_DIR}"
ln -sf "${NETWORK}" "${OUTPUT_DIR}/network.xml.gz"
ln -sf "${NETWORK}" "${OUTPUT_DIR}/network.xml"

echo "=== [3/4] Run MATSim (1 iteration) ==="
LOG_DIR="${ROOT}/logs"
mkdir -p "${LOG_DIR}"
SIM_LOG="${LOG_DIR}/tamsui_100_$(date +%Y-%m-%d_%H-%M-%S).log"
DISABLE_SIMWRAPPER=1 MAVEN_OPTS="${JAVA_OPTS:--Xms4g -Xmx4g}" \
  "${ROOT}/mvnw" -q \
  -Dexec.mainClass=org.matsim.project.RunMatsimApplication \
  -Dexec.args="run --config ${CONFIG}" \
  exec:java > "${SIM_LOG}" 2>&1
echo "Simulation log: ${SIM_LOG}"

echo "=== [4/4] Build SimWrapper dashboard assets ==="
INPUT_NETWORK="${NETWORK}" bash "${ROOT}/5000_disatar/05_scripts/07_analysis/run_dashboard_pipeline.sh" "${OUTPUT_DIR}"

echo "=== Pipeline complete ==="
echo "Output: ${OUTPUT_DIR}"
