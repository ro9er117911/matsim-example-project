#!/usr/bin/env python3
"""
GTFS Operator & Spatial Filter - Disaster Evacuation
Filters GTFS data based on:
1. Operator Priority (Requisition Likelihood)
2. Spatial Bounds (Disaster Zone: Tamsui)
"""

import argparse
import csv
import os
import shutil
from pathlib import Path
from typing import Set, Dict, List, Tuple

# --- Configuration: Operator Priority ---
# Priority 1: High Requisition Likelihood (Local/Municipal)
# Priority 2: Medium Requisition Likelihood (Major Regional)
PRIORITY_KEYWORDS = {
    '1': ['淡水客運', '指南客運', '淡水區公所'],
    '2': ['臺北客運', '首都客運', '大都會客運', '三重客運']
}

# Default Disaster Zone Bounds (Tamsui)
DEFAULT_BOUNDS = (121.35, 25.10, 121.65, 25.25)
# Default Time Window (3:00 AM to 9:00 AM)
DEFAULT_TIME_WINDOW = ("03:00:00", "09:00:00")

def read_csv(filepath: Path) -> List[Dict[str, str]]:
    if not filepath.exists(): return []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(filepath: Path, rows: List[Dict[str, str]]):
    if not rows: return
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def time_to_seconds(t_str: str) -> int:
    h, m, s = map(int, t_str.split(':'))
    return h * 3600 + m * 60 + s

def filter_gtfs(
    input_dir: Path,
    output_dir: Path,
    priority_level: int,
    bounds: Tuple[float, float, float, float],
    time_window: Tuple[str, str],
    all_agencies: bool,
):
    print(f"=== GTFS Filtering Start ===")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Priority Level: {priority_level}")
    print(f"Time Window: {time_window[0]} - {time_window[1]}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    start_sec = time_to_seconds(time_window[0])
    end_sec = time_to_seconds(time_window[1])

    # 1. Identify Target Agency IDs by Keyword
    agency_path = input_dir / 'agency.txt'
    if not agency_path.exists():
        print(f"Error: {agency_path} does not exist.")
        return
        
    agencies = read_csv(agency_path)
    print(f"Read {len(agencies)} agencies from {agency_path}")
    if all_agencies:
        target_agencies = {a['agency_id'] for a in agencies if a.get('agency_id')}
        print(f"Using all agencies: {len(target_agencies)}")
    else:
        target_agencies = set()
        keywords = []
        for p in range(1, priority_level + 1):
            keywords.extend(PRIORITY_KEYWORDS.get(str(p), []))

        for a in agencies:
            name = a.get('agency_name', '')
            if any(kw in name for kw in keywords):
                target_agencies.add(a['agency_id'])
                print(f"  Matched Operator: {name} (ID: {a['agency_id']})")
    
    if not target_agencies:
        print("Error: No operators matched the criteria.")
        return

    # 2. Filter Routes by Agency
    routes = read_csv(input_dir / 'routes.txt')
    filtered_routes = [r for r in routes if r.get('agency_id') in target_agencies]
    target_route_ids = {r['route_id'] for r in filtered_routes}
    print(f"Routes match operator: {len(filtered_routes)}")

    # 3. Filter Trips by Route
    trips = read_csv(input_dir / 'trips.txt')
    filtered_trips = [t for t in trips if t['route_id'] in target_route_ids]
    target_trip_ids = {t['trip_id'] for t in filtered_trips}
    
    # 4. Filter Stop Times by Trip AND Time
    stop_times = read_csv(input_dir / 'stop_times.txt')
    trips_in_time_window = set()
    filtered_st_temp = []
    
    for st in stop_times:
        if st['trip_id'] in target_trip_ids:
            try:
                arrival = time_to_seconds(st['arrival_time'])
                if start_sec <= arrival <= end_sec:
                    trips_in_time_window.add(st['trip_id'])
                filtered_st_temp.append(st)
            except (ValueError, KeyError): continue
            
    print(f"Trips in time window: {len(trips_in_time_window)}")
    
    # 5. Filter Stops by Spatial Bounds & Usage
    stops = read_csv(input_dir / 'stops.txt')
    lon_min, lat_min, lon_max, lat_max = bounds
    
    tamsui_stop_ids = set()
    for s in stops:
        try:
            lat = float(s['stop_lat'])
            lon = float(s['stop_lon'])
            if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
                tamsui_stop_ids.add(s['stop_id'])
        except (ValueError, KeyError): continue
    print(f"Stops in Tamsui bounds: {len(tamsui_stop_ids)}")
    
    trips_passing_tamsui = set()
    for st in filtered_st_temp:
        if st['trip_id'] in trips_in_time_window:
            if st['stop_id'] in tamsui_stop_ids:
                trips_passing_tamsui.add(st['trip_id'])
    print(f"Trips passing through Tamsui & In Time: {len(trips_passing_tamsui)}")
    
    # Final Filter
    final_trips = [t for t in filtered_trips if t['trip_id'] in trips_passing_tamsui]
    final_trip_ids = {t['trip_id'] for t in final_trips}
    final_st = [st for st in filtered_st_temp if st['trip_id'] in final_trip_ids]
    # Keep only stop_times within time range or all stop_times for these trips?
    # Usually we keep all stop_times for a valid trip to maintain continuity.
    
    final_stop_ids = {st['stop_id'] for st in final_st}
    final_route_ids = {t['route_id'] for t in final_trips}
    final_routes = [r for r in filtered_routes if r['route_id'] in final_route_ids]
    final_stops = [s for s in stops if s['stop_id'] in final_stop_ids]

    # 6. Write Data
    write_csv(output_dir / 'agency.txt', [a for a in agencies if a['agency_id'] in target_agencies])
    write_csv(output_dir / 'routes.txt', final_routes)
    write_csv(output_dir / 'trips.txt', final_trips)
    write_csv(output_dir / 'stop_times.txt', final_st)
    write_csv(output_dir / 'stops.txt', final_stops)
    
    for f in ['calendar.txt', 'calendar_dates.txt']:
        if (input_dir / f).exists(): shutil.copy(input_dir / f, output_dir / f)

    print(f"Filtering complete. Final counts:")
    print(f" - Routes: {len(final_routes)}")
    print(f" - Trips: {len(final_trips)}")
    print(f" - Stops: {len(final_stops)}")

def main():
    parser = argparse.ArgumentParser(description='GTFS Filter by Operator, Space, and Time')
    parser.add_argument('--input', '-i', required=True, help='Input GTFS directory')
    parser.add_argument('--output', '-o', required=True, help='Output GTFS directory')
    parser.add_argument('--priority', '-p', type=int, default=2, help='Priority level (1 or 2)')
    parser.add_argument('--bounds', '-b', help='lon_min,lat_min,lon_max,lat_max')
    parser.add_argument('--time', '-t', help='start_time,end_time (e.g. 03:00:00,09:00:00)')
    parser.add_argument('--all-agencies', action='store_true', help='Skip operator filtering and include all agencies')
    
    args = parser.parse_args()
    bounds = tuple(map(float, args.bounds.split(','))) if args.bounds else DEFAULT_BOUNDS
    time_window = tuple(args.time.split(',')) if args.time else DEFAULT_TIME_WINDOW
    
    filter_gtfs(Path(args.input), Path(args.output), args.priority, bounds, time_window, args.all_agencies)

if __name__ == '__main__':
    main()
