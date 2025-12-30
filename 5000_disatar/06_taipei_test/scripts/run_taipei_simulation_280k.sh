#!/usr/bin/env bash
# =============================================================================
# Taipei 280k Evacuation Simulation Runner (car + pt teleported)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG="${SCRIPT_DIR}/config_taipei_280k.xml"

# Java memory settings
JAVA_MEM="${JAVA_MEM:--Xms8g -Xmx12g}"

echo "=============================================="
echo "Taipei 280k Evacuation Simulation"
echo "=============================================="
echo "Config: ${CONFIG}"
echo "Project: ${PROJECT_ROOT}"
echo ""

# Verify input files exist
NETWORK="${SCRIPT_DIR}/input/network.xml.gz"
POPULATION="${SCRIPT_DIR}/input/population_280k.xml.gz"

if [[ ! -f "${NETWORK}" ]]; then
    echo "ERROR: Network file not found: ${NETWORK}"
    exit 1
fi

if [[ ! -f "${POPULATION}" ]]; then
    echo "ERROR: Population file not found: ${POPULATION}"
    exit 1
fi

echo "OK: Network: ${NETWORK}"
echo "OK: Population: ${POPULATION}"
echo ""

# Run simulation
echo "Starting MATSim simulation..."
cd "${PROJECT_ROOT}"

./mvnw exec:java \
    -Dexec.mainClass="org.matsim.project.RunMatsim" \
    -Dexec.args="${CONFIG}" \
    -Dexec.cleanupDaemonThreads=false \
    ${JAVA_MEM:+-Dexec.vmargs="$JAVA_MEM"}

echo ""
echo "=============================================="
echo "Simulation Complete!"
echo "=============================================="
echo "Results: ${SCRIPT_DIR}/output_taipei_280k/"
