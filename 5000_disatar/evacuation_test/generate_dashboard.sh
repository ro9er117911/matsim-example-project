#!/bin/bash

# Configuration
EVENTS="output/output/output_events.xml.gz"
OUTDIR="analysis/simwrapper"
CELLS=20
# Taipei EPSG
EPSG="EPSG:3826" 
# Start time (optional offset, e.g. 0 for raw time)
BASE_TIME=0

# Create output directory
mkdir -p "$OUTDIR"

echo "Running SimWrapper Visualization Generator..."
echo "Input Events: $EVENTS"
echo "Output Directory: $OUTDIR"

python3 tools/make_evac_simwrapper.py "$EVENTS" \
    --outdir "$OUTDIR" \
    --cells $CELLS \
    --epsg "$EPSG" \
    --base_time $BASE_TIME

echo "Done. Open SimWrapper and navigate to $OUTDIR"
