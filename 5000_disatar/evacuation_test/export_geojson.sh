#!/bin/bash

INPUT_FILE="input/tamsui_to_wenshan.osm"
FILTERED_FILE="input/filtered_car.osm.pbf"
OUTPUT_FILE="output/car_network.geojson"

echo "1. Filtering Car Network (Highways)..."
osmium tags-filter $INPUT_FILE \
    w/highway=motorway,trunk,primary,secondary,tertiary,unclassified,residential,service \
    w/highway=motorway_link,trunk_link,primary_link,secondary_link,tertiary_link \
    -o $FILTERED_FILE --overwrite

echo "2. Exporting to GeoJSON..."
# -f geojson for specific format, though extension handles it usually
osmium export $FILTERED_FILE -o $OUTPUT_FILE --overwrite -f geojson

echo "Done. File saved to $OUTPUT_FILE"
