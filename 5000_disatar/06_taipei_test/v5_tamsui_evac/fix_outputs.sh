#!/bin/bash
set -e

# Fix Outputs Script for v5_tamsui_evac (280k Test)
# Resolves issues with empty CSL files and SimWrapper dashboards.

# Paths
BASE_DIR="$(pwd)"
OUTPUT_DIR="$BASE_DIR/output"
CSL_DIR="$BASE_DIR/output_csl"
VIS_DIR="$BASE_DIR/output_vis"
SCRIPTS_DIR="../scripts"
TOOLS_DIR="../../../tools"

# Ensure directories exist
mkdir -p "$CSL_DIR" "$VIS_DIR"

echo "=================================================="
echo "🔧 Fixing Simulation Outputs (CSL & SimWrapper)"
echo "=================================================="

# 1. Generate Dashboard Data (Validates Events & Links)
echo "[1/4] Generating Congestion CSVs..."
python3 ../../../output/generate_advanced_dashboard.py "$OUTPUT_DIR"

# 2. Fix CSL Congestion File
echo "[2/4] Preparing CSL Congestion Data..."
# Use the peak period congestion file
CONGESTION_SRC="$OUTPUT_DIR/link_congestion_0315_0330.csv"
if [ -f "$CONGESTION_SRC" ]; then
    cp "$CONGESTION_SRC" "$CSL_DIR/congestion.csv"
    echo "  ✓ Copied $CONGESTION_SRC to $CSL_DIR/congestion.csv"
else
    echo "  ✗ Error: Congestion file not found at $CONGESTION_SRC"
    exit 1
fi

# 3. Regenerate CSL Files (GeoJSON & Parquet)
echo "[3/4] Generating CSL Visualizations..."

# 3.1 Road Service Level GeoJSON
echo "  - Generating Road Service Level GeoJSON..."
python3 "$SCRIPTS_DIR/matsim_to_road_service.py" \
    --congestion "$CSL_DIR/congestion.csv" \
    --network "$OUTPUT_DIR/output_network.xml.gz" \
    --output "$CSL_DIR/road_service_level.geojson"

# 3.3 Network GeoJSON for Congestion
echo "  - Generating Network GeoJSON for Congestion..."
python3 "$TOOLS_DIR/../5000_disatar/05_scripts/06_disaster_evacuation/network_to_geojson.py" \
    --network "$OUTPUT_DIR/output_network.xml.gz" \
    --output "$VIS_DIR/network_wgs84_congestion.geojson" \
    --whitelist "$OUTPUT_DIR/link_congestion_0300_0315.csv" "$OUTPUT_DIR/link_congestion_0315_0330.csv"

# 4. Finalize SimWrapper Dashboard
echo "[4/4] Finalizing SimWrapper..."
# Create SimWrapper config/folders manually to ensure correctness
cp "$OUTPUT_DIR"/evac_*.csv "$VIS_DIR/" 2>/dev/null || true
cp "$OUTPUT_DIR"/link_congestion_*.csv "$VIS_DIR/" 2>/dev/null || true
cp "$OUTPUT_DIR"/bottleneck_curves_*.csv "$VIS_DIR/" 2>/dev/null || true
cp "$OUTPUT_DIR"/policy_summary_transposed.csv "$VIS_DIR/" 2>/dev/null || true

# Run standard dashboard pipeline steps for final integration
# (Using the tools script but pointing to our output)
# Note: We skip the advanced dashboard generation part since we did it in step 1 manually
# Just run the YAML generation part
echo "  - Generating YAML configs..."
python3 "$TOOLS_DIR/generate_dashboard_yamls.py" --output_dir "$VIS_DIR"

echo "=================================================="
echo "✅ Fix Complete!"
echo "CSL Output: $CSL_DIR"
echo "SimWrapper: $VIS_DIR"
echo "=================================================="
