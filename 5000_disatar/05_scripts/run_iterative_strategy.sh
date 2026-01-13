#!/bin/bash
# Automates the Iterative Main-Road Priority Strategy for PT Mapping
# Usage: ./run_iterative_strategy.sh <working_directory> <config_file> <input_network>
# Example: ./run_iterative_strategy.sh ../01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes ptmapper-config.xml ../merged_network_v6/network_v6_scc.xml.gz

WORK_DIR=$1
CONFIG_FILE=$2
BASE_NETWORK=$3

if [ -z "$WORK_DIR" ] || [ -z "$CONFIG_FILE" ] || [ -z "$BASE_NETWORK" ]; then
    echo "Usage: $0 <working_directory> <config_file> <base_network_path>"
    exit 1
fi

# script paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIAGNOSE_Script="$SCRIPT_DIR/diagnose_network_gaps.py"
BRIDGE_Script="$SCRIPT_DIR/pt_bridge_generator.py"
PT_JAR="$WORK_DIR/pt2matsim-with-shapes.jar"

# Check dependencies
if [ ! -f "$DIAGNOSE_Script" ]; then echo "Error: Missing $DIAGNOSE_Script"; exit 1; fi
if [ ! -f "$BRIDGE_Script" ]; then echo "Error: Missing $BRIDGE_Script"; exit 1; fi
if [ ! -f "$PT_JAR" ]; then echo "Error: Missing pt2matsim jar in work dir $WORK_DIR"; exit 1; fi

cd "$WORK_DIR"
echo "Starting Iterative PT Mapping in $WORK_DIR"

# ==========================================
# ROUND 1: Base Run
# ==========================================
echo ">>> ROUND 1: Base Run <<<"
# 1. Update config to use BASE_NETWORK
sed -i '' "s|<param name=\"inputNetworkFile\" value=\".*\" />|<param name=\"inputNetworkFile\" value=\"$BASE_NETWORK\" />|" "$CONFIG_FILE"

# 2. Run Mapping
java -Xmx12g -cp pt2matsim-with-shapes.jar org.matsim.pt2matsim.run.PublicTransitMapperWithShapes "$CONFIG_FILE" shapes.txt EPSG:3826 > pt_mapping_round1.log 2>&1

# 3. Diagnose
echo "Diagnosing Round 1 errors..."
python3 "$DIAGNOSE_Script" pt_mapping_round1.log gaps_round1.csv

# 4. Patch
echo "Patching Network (Round 1)..."
# Create patched network named network_patched_r1.xml.gz
# We use the BASE_NETWORK as input
python3 "$BRIDGE_Script" --input_network "$BASE_NETWORK" --gap_report gaps_round1.csv --output_network "network_patched_r1.xml.gz"

# ==========================================
# ROUND 2: Patched Run (First Pass)
# ==========================================
echo ">>> ROUND 2: Patched Run <<<"
# 1. Update config to use network_patched_r1.xml.gz
# Get absolute path for reliability
NET_R1="$(pwd)/network_patched_r1.xml.gz"
sed -i '' "s|<param name=\"inputNetworkFile\" value=\".*\" />|<param name=\"inputNetworkFile\" value=\"$NET_R1\" />|" "$CONFIG_FILE"

# 2. Run Mapping
java -Xmx12g -cp pt2matsim-with-shapes.jar org.matsim.pt2matsim.run.PublicTransitMapperWithShapes "$CONFIG_FILE" shapes.txt EPSG:3826 > pt_mapping_round2.log 2>&1

# 3. Diagnose
echo "Diagnosing Round 2 errors..."
python3 "$DIAGNOSE_Script" pt_mapping_round2.log gaps_round2.csv

# 4. Patch Again (Layer 2)
echo "Patching Network (Round 2)..."
# Use network_patched_r1.xml.gz as INPUT, produce network_patched_r2.xml.gz
python3 "$BRIDGE_Script" --input_network "network_patched_r1.xml.gz" --gap_report gaps_round2.csv --output_network "network_patched_r2.xml.gz"


# ==========================================
# ROUND 3: Final Verification
# ==========================================
echo ">>> ROUND 3: Final Run <<<"
NET_R2="$(pwd)/network_patched_r2.xml.gz"
sed -i '' "s|<param name=\"inputNetworkFile\" value=\".*\" />|<param name=\"inputNetworkFile\" value=\"$NET_R2\" />|" "$CONFIG_FILE"

java -Xmx12g -cp pt2matsim-with-shapes.jar org.matsim.pt2matsim.run.PublicTransitMapperWithShapes "$CONFIG_FILE" shapes.txt EPSG:3826 > pt_mapping_final.log 2>&1

echo "Iterative Mapping Corrected. Final Output in pt_mapping_final.log"
