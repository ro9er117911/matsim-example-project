#!/bin/bash
# ============================================================================
# [DEPRECATED] Via Export Script - Filtered Events for Visualization
# ============================================================================
# This script is DEPRECATED. SimWrapper is now the primary visualization
# platform. Use `npx simwrapper serve --port 8000` instead.
#
# Original description:
# This script exports MATSim simulation results to Via platform format
# Generated: 2025-11-05
# ============================================================================

echo "============================================================================"
echo "[DEPRECATED] Via Export is no longer used."
echo "============================================================================"
echo ""
echo "SimWrapper is now the primary visualization framework."
echo "Run: npx simwrapper serve --port 8000"
echo ""
echo "To still run the Via export (for legacy purposes), uncomment the code below."
echo "============================================================================"
exit 0

# [DEPRECATED] Navigate to project root (in case script is run from elsewhere)
# cd "$(dirname "${BASH_SOURCE[0]}")/.."

# echo "=========================================================================="
# echo "Starting Via Export from Simulation Output"
# echo "=========================================================================="
# echo ""
# echo "Input files:"
# echo "  Plans:    scenarios/equil/output/output_plans.xml.gz"
# echo "  Events:   scenarios/equil/output/output_events.xml.gz"
# echo "  Network:  scenarios/equil/output/output_network.xml.gz"
# echo "  Schedule: scenarios/equil/output/output_transitSchedule.xml.gz"
# echo "  Vehicles: scenarios/equil/output/output_transitVehicles.xml.gz"
# echo ""
# echo "Output: scenarios/equil/forVia/"
# echo "=========================================================================="
# echo ""

# # Run the Via export with filtered events
# python src/main/python/build_agent_tracks.py \
#   --plans scenarios/equil/output/output_plans.xml.gz \
#   --events scenarios/equil/output/output_events.xml.gz \
#   --schedule scenarios/equil/output/output_transitSchedule.xml.gz \
#   --vehicles scenarios/equil/output/output_transitVehicles.xml.gz \
#   --network scenarios/equil/output/output_network.xml.gz \
#   --export-filtered-events \
#   --out scenarios/equil/forVia \
#   --dt 5

# echo ""
# echo "=========================================================================="
# echo "✓ Via Export Complete!"
# echo "=========================================================================="
# echo ""
# echo "Output files ready in: scenarios/equil/forVia/"
# echo ""
# echo "Files created:"
# ls -lh scenarios/equil/forVia/
# echo ""
# echo "Next steps:"
# echo "  1. Open Via platform dashboard"
# echo "  2. Create new visualization"
# echo "  3. Load: scenarios/equil/forVia/output_events.xml"
# echo "  4. Load: scenarios/equil/forVia/output_network.xml.gz"
# echo "  5. Play visualization!"
# echo ""
# echo "=========================================================================="

