import pandas as pd
import os
from pathlib import Path
import shutil

# Paths
V6_GTFS_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/v6_GTFS")
TRIPS_FILE = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/trips.txt")
OUTPUT_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/production_mapping_v6_400routes/GTFS")

def create_production_gtfs(target_bus_count=400):
    print("Loading GTFS files...")
    routes = pd.read_csv(V6_GTFS_DIR / "routes.txt")
    trips = pd.read_csv(TRIPS_FILE)
    stop_times = pd.read_csv(V6_GTFS_DIR / "stop_times.txt")
    stops = pd.read_csv(V6_GTFS_DIR / "stops.txt")
    calendar = pd.read_csv(V6_GTFS_DIR / "calendar.txt")
    agency = pd.read_csv(V6_GTFS_DIR / "agency.txt")
    shapes = pd.read_csv(V6_GTFS_DIR / "shapes.txt")

    # 1. Identify all MRT routes
    # MRT routes have agency_id 'MRT_TRTC' or route_id starting with 'MRT_'
    mrt_routes = routes[routes['route_id'].str.startswith('MRT_')]
    mrt_route_ids = set(mrt_routes['route_id'])
    print(f"Found {len(mrt_route_ids)} MRT routes.")

    # 2. Identify bus routes with shapes
    # Filter out MRT from trips to get bus trips
    bus_trips = trips[~trips['route_id'].isin(mrt_route_ids)]
    # Keep only those with shapes
    bus_trips_with_shapes = bus_trips[bus_trips['shape_id'].notna()]
    
    # Selection logic: prioritize routes with more entries (proxy for importance/frequency)
    # but also ensure a mix. 
    bus_route_stats = bus_trips_with_shapes.groupby('route_id').size().reset_index(name='trip_count')
    # Merge with routes to get names if needed
    bus_routes_with_shapes = routes[routes['route_id'].isin(bus_route_stats['route_id'])]
    
    selected_bus_route_ids = set(bus_route_stats.sort_values('trip_count', ascending=False).head(target_bus_count)['route_id'])
    print(f"Selected {len(selected_bus_route_ids)} bus routes with shapes.")

    # All target routes
    target_route_ids = mrt_route_ids.union(selected_bus_route_ids)
    print(f"Total target routes: {len(target_route_ids)}")

    # 3. Filter all tables
    filtered_routes = routes[routes['route_id'].isin(target_route_ids)]
    filtered_trips = trips[trips['route_id'].isin(target_route_ids)]
    
    # Important: keep only one trip per shape if we want to minimize redundant mapping,
    # but PTMapper usually handles it. Let's keep one representative trip per route/direction
    # to keep the test manageable while covering all physical paths.
    # Actually, the user asked for 400 routes, which usually implies the whole schedule for those routes.
    
    target_trip_ids = set(filtered_trips['trip_id'])
    filtered_stop_times = stop_times[stop_times['trip_id'].isin(target_trip_ids)]
    
    target_stop_ids = set(filtered_stop_times['stop_id'])
    filtered_stops = stops[stops['stop_id'].isin(target_stop_ids)]
    
    target_shape_ids = set(filtered_trips['shape_id'])
    filtered_shapes = shapes[shapes['shape_id'].isin(target_shape_ids)]
    
    target_service_ids = set(filtered_trips['service_id'])
    filtered_calendar = calendar[calendar['service_id'].isin(target_service_ids)]
    
    # 4. Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filtered_routes.to_csv(OUTPUT_DIR / "routes.txt", index=False)
    filtered_trips.to_csv(OUTPUT_DIR / "trips.txt", index=False)
    filtered_stop_times.to_csv(OUTPUT_DIR / "stop_times.txt", index=False)
    filtered_stops.to_csv(OUTPUT_DIR / "stops.txt", index=False)
    filtered_calendar.to_csv(OUTPUT_DIR / "calendar.txt", index=False)
    filtered_shapes.to_csv(OUTPUT_DIR / "shapes.txt", index=False)
    agency.to_csv(OUTPUT_DIR / "agency.txt", index=False)
    
    print(f"Filtered GTFS saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    create_production_gtfs(450) # Buffer to ensure >400
