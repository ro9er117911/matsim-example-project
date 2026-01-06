#!/usr/bin/env python3
"""
Create Phase 2 GTFS for NeatNet testing.
Routes: 5 TPE (with shapes) + 3 NWT (without shapes).
"""

import csv
import gzip
import shutil
from pathlib import Path

# Configuration
BASE_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v5/gtfs_filtered")
SHAPES_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v6/v6_GTFS")
OUTPUT_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v6/test_phase2_neatnet")
OUTPUT_DIR.mkdir(exist_ok=True)

# TPE Candidates from shapefile
TPE_CANDIDATES = ['652', '0南', '641', '616', '680', '202', '72', '承德幹線']
NWT_COUNT = 3

def get_target_routes():
    tpe_routes = {}
    nwt_routes = []
    
    with open(BASE_DIR / "routes.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        rows = list(reader)
        
    for row in rows:
        name = row['route_short_name']
        rid = row['route_id']
        
        # Check TPE
        if name in TPE_CANDIDATES and name not in tpe_routes:
            tpe_routes[name] = rid
            
        # Check NWT
        if rid.startswith("BUS_NWT") and len(nwt_routes) < NWT_COUNT:
            nwt_routes.append(rid)
            
    print(f"Found TPE Routes ({len(tpe_routes)}): {tpe_routes}")
    print(f"Found NWT Routes ({len(nwt_routes)}): {nwt_routes}")
    
    return list(tpe_routes.values()) + nwt_routes

def filter_gtfs(target_route_ids):
    # 1. Filter routes.txt
    filtered_routes = []
    with open(BASE_DIR / "routes.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        for row in reader:
            if row['route_id'] in target_route_ids:
                filtered_routes.append(row)
                
    with open(OUTPUT_DIR / "routes.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_routes)

    # 2. Filter trips.txt (max 2 trips per route to keep it small)
    filtered_trips = []
    trip_ids = set()
    shape_ids = set()
    
    with open(BASE_DIR / "trips.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        trip_fieldnames = reader.fieldnames
        
        trips_per_route = {}
        for row in reader:
            rid = row['route_id']
            if rid in target_route_ids:
                count = trips_per_route.get(rid, 0)
                if count < 2:
                    filtered_trips.append(row)
                    trip_ids.add(row['trip_id'])
                    if row['shape_id']:
                        shape_ids.add(row['shape_id'])
                    trips_per_route[rid] = count + 1
                    
    with open(OUTPUT_DIR / "trips.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=trip_fieldnames)
        writer.writeheader()
        writer.writerows(filtered_trips)
        
    # 3. Filter stop_times.txt
    stop_ids = set()
    with open(BASE_DIR / "stop_times.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        st_fieldnames = reader.fieldnames
        rows = [r for r in reader if r['trip_id'] in trip_ids]
        for r in rows:
            stop_ids.add(r['stop_id'])
            
    with open(OUTPUT_DIR / "stop_times.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=st_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # 4. Filter stops.txt
    with open(BASE_DIR / "stops.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        stops_fieldnames = reader.fieldnames
        rows = [r for r in reader if r['stop_id'] in stop_ids]
        
    with open(OUTPUT_DIR / "stops.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=stops_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # 5. Filter shapes.txt (FROM V6 SHAPES DIR!)
    # Only keep shapes for TPE (which should exist in V6)
    # NWT shapes won't exist there, and that's fine (will be filtered out)
    found_shapes = 0
    with open(SHAPES_DIR / "shapes.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        shapes_fieldnames = reader.fieldnames
        rows = []
        for r in reader:
            if r['shape_id'] in shape_ids:
                rows.append(r)
                found_shapes += 1
                
    with open(OUTPUT_DIR / "shapes.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=shapes_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"shapes.txt: {found_shapes} points found for {len(shape_ids)} potential shapes")

    # 6. Copy other files
    for fname in ["agency.txt", "calendar.txt"]:
        if (BASE_DIR / fname).exists():
            shutil.copy(BASE_DIR / fname, OUTPUT_DIR / fname)

def main():
    print("Generating Phase 2 GTFS...")
    target_ids = get_target_routes()
    filter_gtfs(target_ids)
    print("Done.")

if __name__ == "__main__":
    main()
