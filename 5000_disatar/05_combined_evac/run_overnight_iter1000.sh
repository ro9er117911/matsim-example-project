#!/usr/bin/env bash
# run_overnight_iter1000.sh - Overnight 1000-iteration simulation with automatic ITERS cleanup
# Keeps: iter.0 (baseline) + latest 3 iterations to save disk space
# Usage: ./5000_disatar/05_combined_evac/run_overnight_iter1000.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG="${ROOT}/5000_disatar/05_combined_evac/config_optimized_iter1000.xml"
OUTPUT_DIR="output_ideal_iter1000"
ITERS_DIR="${ROOT}/${OUTPUT_DIR}/ITERS"
KEEP_LATEST=3
CLEANUP_INTERVAL=60  # Check every 60 seconds

echo "========================================"
echo "  Overnight 1000-Iteration Simulation"
echo "========================================"
echo "Config: $CONFIG"
echo "Output: $OUTPUT_DIR"
echo "ITERS Cleanup: Keep it.0 + latest $KEEP_LATEST iterations"
echo "Start time: $(date)"
echo ""

# Memory settings
JAVA_MEM="-Xmx8g -Djava.awt.headless=true"

# Cleanup function - keeps it.0 + latest N iterations
cleanup_iters() {
    if [ ! -d "$ITERS_DIR" ]; then
        return
    fi
    
    # Get all iteration folders except it.0, sorted by number
    ITERS=$(ls -1 "$ITERS_DIR" 2>/dev/null | grep "^it\." | grep -v "^it\.0$" | sort -t. -k2 -n)
    COUNT=$(echo "$ITERS" | grep -c . 2>/dev/null || echo 0)
    
    if [ "$COUNT" -le "$KEEP_LATEST" ]; then
        return
    fi
    
    # Calculate how many to delete
    TO_DELETE_COUNT=$((COUNT - KEEP_LATEST))
    
    # Get iterations to delete (oldest ones)
    TO_DELETE=$(echo "$ITERS" | head -n "$TO_DELETE_COUNT")
    
    for iter in $TO_DELETE; do
        if [ -d "$ITERS_DIR/$iter" ]; then
            echo "[$(date +%H:%M:%S)] Cleanup: Removing $iter"
            rm -rf "$ITERS_DIR/$iter"
        fi
    done
}

# Background cleanup loop
start_cleanup_loop() {
    echo "[Cleanup] Starting background cleanup loop (interval: ${CLEANUP_INTERVAL}s)"
    while true; do
        sleep "$CLEANUP_INTERVAL"
        cleanup_iters
    done
}

# Cleanup old output directory
if [ -d "${ROOT}/${OUTPUT_DIR}" ]; then
    echo "Removing old output directory..."
    rm -rf "${ROOT}/${OUTPUT_DIR}"
fi

# Start background cleanup loop
start_cleanup_loop &
CLEANUP_PID=$!
echo "[Cleanup] Background cleanup PID: $CLEANUP_PID"

# Trap to kill cleanup on script exit
trap "kill $CLEANUP_PID 2>/dev/null; echo 'Cleanup loop stopped.'" EXIT

# Run MATSim simulation
echo ""
echo "=== Starting MATSim Simulation ==="
cd "$ROOT"
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.RunMatsimApplication" \
  -Dexec.args="run --config $CONFIG" \
  -Dexec.vmArgs="$JAVA_MEM"

echo ""
echo "=== Simulation Complete ==="
echo "End time: $(date)"

# Final cleanup to ensure only baseline + last 3
echo ""
echo "=== Final ITERS Cleanup ==="
cleanup_iters
echo "Remaining iterations:"
ls "$ITERS_DIR" 2>/dev/null | sort -t. -k2 -n || echo "(none)"

# Run dashboard pipeline
echo ""
echo "=== Building Dashboard ==="
export INPUT_NETWORK="${ROOT}/scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz"
bash "${ROOT}/tools/run_dashboard_pipeline.sh" "$OUTPUT_DIR"

echo ""
echo "========================================"
echo "  Overnight Simulation Complete!"
echo "========================================"
echo "Output: ${ROOT}/${OUTPUT_DIR}"
echo "View with: cd $OUTPUT_DIR && python3 -m http.server 8080"
