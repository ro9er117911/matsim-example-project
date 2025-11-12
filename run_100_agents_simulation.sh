#!/bin/bash
#
# 100 Agents Simulation Runner
# This script runs the complete workflow for 100 agents simulation
#

set -e  # Exit on error

PROJECT_DIR="/home/user/matsim-example-project"
CONFIG_FILE="scenarios/corridor/taipei_test/config.xml"
POPULATION_FILE="test_population_100.xml"
OUTPUT_DIR="output_100agents"
VIA_OUTPUT_DIR="forVia_100test"

echo "========================================================================"
echo "100 AGENTS SIMULATION WORKFLOW"
echo "========================================================================"
echo ""
echo "Population:"
echo "  - 20 single-line PT agents (PT-ONLY)"
echo "  - 30 transfer PT agents (PT-ONLY) ✓"
echo "  - 40 car agents"
echo "  - 10 walk agents"
echo "  Total: 100 agents"
echo ""

cd "$PROJECT_DIR"

# Step 1: Build project (if needed)
echo "[1/4] Checking if project needs to be built..."
if [ ! -f "matsim-example-project-0.0.1-SNAPSHOT.jar" ]; then
    echo "  Building project..."
    mvn clean package -DskipTests
    echo "  ✓ Build complete"
else
    echo "  ✓ JAR file already exists"
fi

# Step 2: Run simulation
echo ""
echo "[2/4] Running MATSim simulation (5 iterations)..."
echo "  Output directory: $OUTPUT_DIR"

java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
    "$CONFIG_FILE" \
    --config:plans.inputPlansFile "$POPULATION_FILE" \
    --config:controller.lastIteration 5 \
    --config:controller.outputDirectory "./$OUTPUT_DIR"

echo "  ✓ Simulation complete"

# Step 3: Verify transfers
echo ""
echo "[3/4] Verifying PT transfers..."

TRANSFER_COUNT=$(gunzip -c "$OUTPUT_DIR/output_events.xml.gz" | \
    grep "PersonEntersVehicle" | \
    grep "pt_transfer_agent" | \
    awk -F'"' '{print $4}' | \
    sort | uniq -c | \
    awk '$1 >= 2 {count++} END {print count}')

echo "  Agents with successful transfers: $TRANSFER_COUNT / 30"

if [ "$TRANSFER_COUNT" -ge 20 ]; then
    echo "  ✓ Transfer validation PASSED (≥ 20 agents)"
else
    echo "  ⚠ Transfer validation WARNING (< 20 agents)"
fi

# Extract sample transfer sequence
echo ""
echo "  Sample transfer agent (pt_transfer_agent_21):"
gunzip -c "$OUTPUT_DIR/output_events.xml.gz" | \
    grep "person=\"pt_transfer_agent_21\"" | \
    grep "PersonEntersVehicle" | \
    head -4 | \
    awk -F'"' '{print "    - Boarding:", $8, "at time", $2}'

# Step 4: Generate Via output
echo ""
echo "[4/4] Generating Via visualization output..."
echo "  Output directory: $VIA_OUTPUT_DIR"

mkdir -p "$VIA_OUTPUT_DIR"

python src/main/python/build_agent_tracks.py \
    --plans "$OUTPUT_DIR/output_plans.xml.gz" \
    --events "$OUTPUT_DIR/output_events.xml.gz" \
    --network "scenarios/corridor/taipei_test/network-with-pt.xml.gz" \
    --schedule "scenarios/corridor/taipei_test/transitSchedule-mapped.xml.gz" \
    --vehicles "scenarios/corridor/taipei_test/transitVehicles.xml" \
    --export-filtered-events \
    --out "$VIA_OUTPUT_DIR" \
    --dt 5

echo "  ✓ Via output generated"

# Summary
echo ""
echo "========================================================================"
echo "SIMULATION COMPLETE"
echo "========================================================================"
echo ""
echo "Output files:"
echo "  - Simulation output:   $OUTPUT_DIR/"
echo "  - Via visualization:   $VIA_OUTPUT_DIR/"
echo ""
echo "Key files for Via platform:"
echo "  - $VIA_OUTPUT_DIR/output_events.xml"
echo "  - $VIA_OUTPUT_DIR/output_network.xml.gz"
echo "  - $VIA_OUTPUT_DIR/tracks_dt5s.csv"
echo ""
echo "Verification:"
echo "  - PT agents with transfers: $TRANSFER_COUNT / 30"
echo "  - Total agents simulated: 100"
echo ""
echo "Next: Import '$VIA_OUTPUT_DIR/' to Via platform for visualization"
echo "========================================================================"
