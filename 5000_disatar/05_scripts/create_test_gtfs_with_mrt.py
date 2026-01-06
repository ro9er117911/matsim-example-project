#!/usr/bin/env python3
"""
Create Test GTFS with 4 Bus lines + 2 MRT lines for PT Mapping test.
Merges existing bus GTFS with MRT data from disaster GTFS.
"""

import pandas as pd
from pathlib import Path
import shutil

# Paths
TEST_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes")
MRT_GTFS_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS/disaster/merged_disaster_gtfs")
OUTPUT_DIR = TEST_DIR  # Overwrite in-place

# MRT lines to include
MRT_ROUTES = ["MRT_Red", "MRT_Blue"]  # 淡水信義線, 板南線

def load_and_filter_mrt():
    """Load MRT GTFS and filter to selected routes."""
    print("Loading MRT GTFS data...")
    
    # Load routes
    routes = pd.read_csv(MRT_GTFS_DIR / "routes.txt")
    mrt_routes = routes[routes['route_id'].isin(MRT_ROUTES)]
    print(f"Selected MRT routes: {list(mrt_routes['route_id'])}")
    
    # Load trips for selected routes
    trips = pd.read_csv(MRT_GTFS_DIR / "trips.txt")
    mrt_trips = trips[trips['route_id'].isin(MRT_ROUTES)]
    print(f"MRT trips: {len(mrt_trips)}")
    
    # Load stop_times for selected trips
    trip_ids = set(mrt_trips['trip_id'])
    stop_times = pd.read_csv(MRT_GTFS_DIR / "stop_times.txt")
    mrt_stop_times = stop_times[stop_times['trip_id'].isin(trip_ids)]
    print(f"MRT stop_times: {len(mrt_stop_times)}")
    
    # Load stops that are referenced
    stop_ids = set(mrt_stop_times['stop_id'])
    stops = pd.read_csv(MRT_GTFS_DIR / "stops.txt")
    mrt_stops = stops[stops['stop_id'].isin(stop_ids)]
    print(f"MRT stops: {len(mrt_stops)}")
    
    # Load agency
    agency = pd.read_csv(MRT_GTFS_DIR / "agency.txt")
    mrt_agency = agency[agency['agency_id'] == 'MRT_TRTC']
    
    # Load calendar
    calendar = pd.read_csv(MRT_GTFS_DIR / "calendar.txt")
    service_ids = set(mrt_trips['service_id'])
    mrt_calendar = calendar[calendar['service_id'].isin(service_ids)]
    
    return {
        'routes': mrt_routes,
        'trips': mrt_trips,
        'stop_times': mrt_stop_times,
        'stops': mrt_stops,
        'agency': mrt_agency,
        'calendar': mrt_calendar
    }

def merge_gtfs():
    """Merge bus GTFS with MRT GTFS."""
    print("\n=== Loading existing bus GTFS ===")
    bus_routes = pd.read_csv(TEST_DIR / "routes.txt")
    bus_trips = pd.read_csv(TEST_DIR / "trips.txt")
    bus_stop_times = pd.read_csv(TEST_DIR / "stop_times.txt")
    bus_stops = pd.read_csv(TEST_DIR / "stops.txt")
    bus_agency = pd.read_csv(TEST_DIR / "agency.txt")
    bus_calendar = pd.read_csv(TEST_DIR / "calendar.txt")
    
    print(f"Bus routes: {len(bus_routes)}")
    print(f"Bus trips: {len(bus_trips)}")
    
    print("\n=== Loading MRT GTFS ===")
    mrt = load_and_filter_mrt()
    
    print("\n=== Merging GTFS ===")
    
    # Merge each file
    merged_routes = pd.concat([bus_routes, mrt['routes']], ignore_index=True)
    merged_trips = pd.concat([bus_trips, mrt['trips']], ignore_index=True)
    merged_stop_times = pd.concat([bus_stop_times, mrt['stop_times']], ignore_index=True)
    merged_stops = pd.concat([bus_stops, mrt['stops']], ignore_index=True).drop_duplicates(subset=['stop_id'])
    merged_agency = pd.concat([bus_agency, mrt['agency']], ignore_index=True).drop_duplicates(subset=['agency_id'])
    merged_calendar = pd.concat([bus_calendar, mrt['calendar']], ignore_index=True).drop_duplicates(subset=['service_id'])
    
    print(f"Merged routes: {len(merged_routes)}")
    print(f"Merged trips: {len(merged_trips)}")
    print(f"Merged stops: {len(merged_stops)}")
    
    # Backup original files
    backup_dir = TEST_DIR / "backup_bus_only"
    backup_dir.mkdir(exist_ok=True)
    for f in ['routes.txt', 'trips.txt', 'stop_times.txt', 'stops.txt', 'agency.txt', 'calendar.txt']:
        src = TEST_DIR / f
        if src.exists():
            shutil.copy(src, backup_dir / f)
    print(f"\nBackup created: {backup_dir}")
    
    # Save merged files
    print("\n=== Saving merged GTFS ===")
    merged_routes.to_csv(OUTPUT_DIR / "routes.txt", index=False)
    merged_trips.to_csv(OUTPUT_DIR / "trips.txt", index=False)
    merged_stop_times.to_csv(OUTPUT_DIR / "stop_times.txt", index=False)
    merged_stops.to_csv(OUTPUT_DIR / "stops.txt", index=False)
    merged_agency.to_csv(OUTPUT_DIR / "agency.txt", index=False)
    merged_calendar.to_csv(OUTPUT_DIR / "calendar.txt", index=False)
    
    print("Done! Merged GTFS saved.")
    print(f"\nFinal counts:")
    print(f"  Routes: {len(merged_routes)} (4 bus + 2 MRT)")
    print(f"  Trips: {len(merged_trips)}")
    print(f"  Stops: {len(merged_stops)}")

if __name__ == "__main__":
    merge_gtfs()
