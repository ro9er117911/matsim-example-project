#!/usr/bin/env python3
"""
Create Test GTFS with 5 routes for PT Mapping verification.
Select routes with matching shapes (TPE + NWT).
"""

import csv
import shutil
from pathlib import Path

# Config
BASE_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v5/gtfs_filtered")
SHAPES_FILE = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/shapes_v6_combined.txt")
OUTPUT_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes")
OUTPUT_DIR.mkdir(exist_ok=True)

# Target routes - these are route_ids from routes.txt that have shapes
# Note: route_id IS the full string like BUS_NWT10424_0
TARGET_ROUTE_IDS = [
    'BUS_NWT10424_0',   # NWT 520
    'BUS_NWT10424_1',   # NWT 520 reverse
    'BUS_NWT158513_0',  # NWT 640
    'BUS_TPE108440_0',  # TPE (to be verified)
    'BUS_TPE118110_0',  # TPE (to be verified)
]

def get_route_ids_from_shapes():
    """Return target route IDs directly"""
    print(f"Target route_ids: {TARGET_ROUTE_IDS}")
    return set(TARGET_ROUTE_IDS)

def filter_gtfs():
    route_ids = get_route_ids_from_shapes()
    
    # 1. Filter routes.txt
    print("Filtering routes.txt...")
    routes = []
    with open(BASE_DIR / "routes.txt") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row['route_id'] in route_ids:
                routes.append(row)
    
    with open(OUTPUT_DIR / "routes.txt", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(routes)
    print(f"  Routes: {len(routes)}")
    
    # 2. Filter trips.txt (get trip_ids and shape_ids)
    print("Filtering trips.txt...")
    trips = []
    trip_ids = set()
    shape_ids = set()
    with open(BASE_DIR / "trips.txt") as f:
        reader = csv.DictReader(f)
        trip_fieldnames = reader.fieldnames
        for row in reader:
            if row['route_id'] in route_ids:
                # Take max 2 trips per route to keep small
                route_trip_count = sum(1 for t in trips if t['route_id'] == row['route_id'])
                if route_trip_count < 2:
                    trips.append(row)
                    trip_ids.add(row['trip_id'])
                    if row.get('shape_id'):
                        shape_ids.add(row['shape_id'])
    
    with open(OUTPUT_DIR / "trips.txt", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=trip_fieldnames)
        writer.writeheader()
        writer.writerows(trips)
    print(f"  Trips: {len(trips)}, Shape IDs: {shape_ids}")
    
    # 3. Filter stop_times.txt
    print("Filtering stop_times.txt...")
    stop_ids = set()
    st_rows = []
    with open(BASE_DIR / "stop_times.txt") as f:
        reader = csv.DictReader(f)
        st_fieldnames = reader.fieldnames
        for row in reader:
            if row['trip_id'] in trip_ids:
                st_rows.append(row)
                stop_ids.add(row['stop_id'])
    
    with open(OUTPUT_DIR / "stop_times.txt", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=st_fieldnames)
        writer.writeheader()
        writer.writerows(st_rows)
    print(f"  Stop times: {len(st_rows)}, Stop IDs: {len(stop_ids)}")
    
    # 4. Filter stops.txt
    print("Filtering stops.txt...")
    stops = []
    with open(BASE_DIR / "stops.txt") as f:
        reader = csv.DictReader(f)
        stops_fieldnames = reader.fieldnames
        for row in reader:
            if row['stop_id'] in stop_ids:
                stops.append(row)
    
    with open(OUTPUT_DIR / "stops.txt", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=stops_fieldnames)
        writer.writeheader()
        writer.writerows(stops)
    print(f"  Stops: {len(stops)}")
    
    # 5. Filter shapes.txt from combined shapes
    print("Filtering shapes.txt...")
    shape_rows = []
    with open(SHAPES_FILE) as f:
        reader = csv.DictReader(f)
        shapes_fieldnames = reader.fieldnames
        for row in reader:
            if row['shape_id'] in shape_ids:
                shape_rows.append(row)
    
    with open(OUTPUT_DIR / "shapes.txt", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=shapes_fieldnames)
        writer.writeheader()
        writer.writerows(shape_rows)
    print(f"  Shape points: {len(shape_rows)}")
    
    # 6. Copy other files
    for fname in ["agency.txt", "calendar.txt"]:
        if (BASE_DIR / fname).exists():
            shutil.copy(BASE_DIR / fname, OUTPUT_DIR / fname)
    
    print(f"\n✓ Test GTFS created at: {OUTPUT_DIR}")

if __name__ == "__main__":
    filter_gtfs()
