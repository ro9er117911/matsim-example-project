#!/bin/bash
# cleanup_iters.sh - Sliding window cleanup for MATSim ITERS folder
# Keeps: iter.0 (baseline) + latest 3 iterations
# Usage: ./cleanup_iters.sh <output_dir> [interval_seconds]
# macOS compatible version

OUTPUT_DIR="${1:-output_ideal_iter1000}"
INTERVAL="${2:-30}"
ITERS_DIR="$OUTPUT_DIR/ITERS"
KEEP_BASELINE="it.0"
KEEP_LATEST=3

echo "=== ITERS Cleanup Script (macOS compatible) ==="
echo "Directory: $ITERS_DIR"
echo "Keep: $KEEP_BASELINE + latest $KEEP_LATEST iterations"
echo "Check interval: ${INTERVAL}s"
echo "Press Ctrl+C to stop"
echo ""

cleanup() {
    if [ ! -d "$ITERS_DIR" ]; then
        return
    fi
    
    # Get all iteration folders sorted by number (excluding it.0)
    # Format: it.1, it.2, it.3, ...
    ITERS=$(ls -1 "$ITERS_DIR" 2>/dev/null | grep "^it\." | grep -v "^it\.0$" | sort -t. -k2 -n)
    COUNT=$(echo "$ITERS" | grep -c . 2>/dev/null || echo 0)
    
    if [ "$COUNT" -le "$KEEP_LATEST" ]; then
        # Not enough iterations yet, nothing to clean
        return
    fi
    
    # Calculate how many to delete
    TO_DELETE_COUNT=$((COUNT - KEEP_LATEST))
    
    # Get iterations to delete (oldest ones, excluding baseline)
    TO_DELETE=$(echo "$ITERS" | head -n "$TO_DELETE_COUNT")
    
    for iter in $TO_DELETE; do
        if [ -d "$ITERS_DIR/$iter" ]; then
            echo "[$(date +%H:%M:%S)] Removing $iter ..."
            rm -rf "$ITERS_DIR/$iter"
        fi
    done
}

# Main loop
while true; do
    cleanup
    sleep "$INTERVAL"
done
