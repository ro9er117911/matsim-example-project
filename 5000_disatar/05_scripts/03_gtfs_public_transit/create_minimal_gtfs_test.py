#!/usr/bin/env python3
"""
Create a minimal GTFS for testing pt2matsim shapes.txt support.
Selects 5 routes: 2 TPE bus (with shapes), 2 MRT (with shapes), 1 NWT bus (no shape)
"""

import csv
import gzip
from pathlib import Path

# Configuration
BASE_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v5/gtfs_filtered")
SHAPES_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v6/v6_GTFS")
OUTPUT_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v6/test_minimal")
OUTPUT_DIR.mkdir(exist_ok=True)

# Select specific routes: 2 TPE bus + 2 MRT + 1 NWT (no shape)
KEEP_ROUTES = {
    "BUS_TPE10221_0",  # TPE bus with shape
    "BUS_TPE10221_1",  # TPE bus with shape (return)
    "MRT_Red",         # MRT with shape
    "MRT_Blue",        # MRT with shape
    "BUS_NWT10424_0",  # NWT bus (NO shape - for comparison)
}

def filter_routes():
    """Filter routes.txt"""
    with open(BASE_DIR / "routes.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        rows = [r for r in reader if r["route_id"] in KEEP_ROUTES or r["route_id"] in ["MRT_Red", "MRT_Blue"]]
    
    with open(OUTPUT_DIR / "routes.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"routes.txt: {len(rows)} routes")
    return set(r["route_id"] for r in rows)

def filter_trips(route_ids):
    """Filter trips.txt and collect trip_ids and shape_ids"""
    with open(BASE_DIR / "trips.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        rows = [r for r in reader if r["route_id"] in route_ids]
    
    # Limit to first 3 trips per route
    route_trip_count = {}
    filtered_rows = []
    for r in rows:
        rid = r["route_id"]
        count = route_trip_count.get(rid, 0)
        if count < 3:
            filtered_rows.append(r)
            route_trip_count[rid] = count + 1
    
    with open(OUTPUT_DIR / "trips.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)
    
    trip_ids = set(r["trip_id"] for r in filtered_rows)
    shape_ids = set(r["shape_id"] for r in filtered_rows if r.get("shape_id"))
    print(f"trips.txt: {len(filtered_rows)} trips, {len(shape_ids)} unique shapes")
    return trip_ids, shape_ids

def filter_stop_times(trip_ids):
    """Filter stop_times.txt and collect stop_ids"""
    with open(BASE_DIR / "stop_times.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        rows = [r for r in reader if r["trip_id"] in trip_ids]
    
    with open(OUTPUT_DIR / "stop_times.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    stop_ids = set(r["stop_id"] for r in rows)
    print(f"stop_times.txt: {len(rows)} stop_times, {len(stop_ids)} unique stops")
    return stop_ids

def filter_stops(stop_ids):
    """Filter stops.txt"""
    with open(BASE_DIR / "stops.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        rows = [r for r in reader if r["stop_id"] in stop_ids]
    
    with open(OUTPUT_DIR / "stops.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"stops.txt: {len(rows)} stops")

def filter_shapes(shape_ids):
    """Filter shapes.txt from v6 shapes directory"""
    with open(SHAPES_DIR / "shapes.txt", "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        rows = [r for r in reader if r["shape_id"] in shape_ids]
    
    with open(OUTPUT_DIR / "shapes.txt", "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"shapes.txt: {len(rows)} shape points for {len(shape_ids)} shapes")
    if shape_ids:
        print(f"  Shape IDs: {sorted(shape_ids)}")

def copy_other_files():
    """Copy agency.txt, calendar.txt"""
    for fname in ["agency.txt", "calendar.txt"]:
        src = BASE_DIR / fname
        dst = OUTPUT_DIR / fname
        if src.exists():
            dst.write_text(src.read_text())
            print(f"{fname}: copied")

def main():
    print("=" * 50)
    print("Creating Minimal GTFS for shapes.txt Test")
    print("=" * 50)
    
    route_ids = filter_routes()
    trip_ids, shape_ids = filter_trips(route_ids)
    stop_ids = filter_stop_times(trip_ids)
    filter_stops(stop_ids)
    filter_shapes(shape_ids)
    copy_other_files()
    
    print()
    print(f"✓ Minimal GTFS created in: {OUTPUT_DIR}")
    print()
    print("Expected shapes coverage:")
    print("  - TPE buses: should have shapes")
    print("  - MRT: should have shapes")
    print("  - NWT bus: NO shape (will use artificial links)")

if __name__ == "__main__":
    main()
