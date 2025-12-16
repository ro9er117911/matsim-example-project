#!/bin/bash
# Setup script to copy large simulation files for the demo

SOURCE_DIR="../../../output/phase3_withinday"
TARGET_DIR="."

echo "Copying large simulation files from Phase 3 output..."

if [ -f "$SOURCE_DIR/output_network.xml.gz" ]; then
    cp "$SOURCE_DIR/output_network.xml.gz" "$TARGET_DIR/"
    echo "Copied network file."
else
    echo "Warning: output_network.xml.gz not found in source."
fi

if [ -f "$SOURCE_DIR/output_events.xml.gz" ]; then
    cp "$SOURCE_DIR/output_events.xml.gz" "$TARGET_DIR/"
    echo "Copied events file."
else
    echo "Warning: output_events.xml.gz not found in source."
fi

echo "Demo setup complete. You can now use Simwrapper on this folder."
