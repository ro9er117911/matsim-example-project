#!/usr/bin/env bash
# =============================================================================
# 台北純私家車 5000 人撤離模擬執行腳本
# Taipei Car-only 5000 Agent Evacuation Simulation Runner
#
# Usage: ./run_taipei_simulation.sh [iterations]
# Default: 10 iterations
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG="${SCRIPT_DIR}/config_taipei_car_5000.xml"

# Java memory settings
JAVA_MEM="${JAVA_MEM:--Xms8g -Xmx12g}"

echo "=============================================="
echo "台北純私家車 5000 人撤離模擬"
echo "=============================================="
echo "Config: ${CONFIG}"
echo "Project: ${PROJECT_ROOT}"
echo ""

# Verify input files exist
NETWORK="${SCRIPT_DIR}/input/network.xml.gz"
POPULATION="${SCRIPT_DIR}/input/population_5000.xml.gz"

if [[ ! -f "${NETWORK}" ]]; then
    echo "ERROR: Network file not found: ${NETWORK}"
    exit 1
fi

if [[ ! -f "${POPULATION}" ]]; then
    echo "ERROR: Population file not found: ${POPULATION}"
    exit 1
fi

echo "✓ Network: ${NETWORK}"
echo "✓ Population: ${POPULATION}"
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
echo "Results: ${SCRIPT_DIR}/output_taipei_car_5000/"
