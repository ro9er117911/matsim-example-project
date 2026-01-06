#!/usr/bin/env python3
"""
Strict GTFS Filter for pt2matsim Mapping

Ensures ALL stops of a route are within the network bounds to prevent:
1. Artificial links being created to external stops
2. Long virtual connections crossing the network

Strategy:
- Filter routes where 100% of stops are within network bounds + buffer
- Buffer accounts for maxLinkCandidateDistance (600m in ptmapper config)
"""

import csv
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from pyproj import Transformer
from typing import Set, Dict, List, Tuple
import shutil

def get_network_bounds(network_path: Path, buffer_m: float = 600) -> Tuple[float, float, float, float]:
    """Get network bounds in WGS84 with buffer for ptmapper."""
    print(f"Loading network bounds from {network_path}...")
    
    if str(network_path).endswith('.gz'):
        with gzip.open(network_path, 'rt') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(network_path)
    
    root = tree.getroot()
    x_coords, y_coords = [], []
    
    for node in root.iterfind('.//node'):
        x_coords.append(float(node.attrib['x']))
        y_coords.append(float(node.attrib['y']))
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    # Apply buffer
    x_min -= buffer_m
    x_max += buffer_m
    y_min -= buffer_m
    y_max += buffer_m
    
    # Transform to WGS84
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    lon_min, lat_min = transformer.transform(x_min, y_min)
    lon_max, lat_max = transformer.transform(x_max, y_max)
    
    print(f"  Network nodes: {len(x_coords)}")
    print(f"  Bounds (WGS84 + {buffer_m}m buffer): [{lon_min:.4f}, {lat_min:.4f}] to [{lon_max:.4f}, {lat_max:.4f}]")
    
    return (lon_min, lat_min, lon_max, lat_max)


def read_csv(filepath: Path) -> List[Dict[str, str]]:
    if not filepath.exists():
        return []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(filepath: Path, rows: List[Dict[str, str]]):
    if not rows:
        return
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def is_in_bounds(lat: float, lon: float, bounds: Tuple[float, float, float, float]) -> bool:
    lon_min, lat_min, lon_max, lat_max = bounds
    return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max


def filter_gtfs_strict(
    input_dir: Path,
    output_dir: Path,
    network_path: Path,
    buffer_m: float = 600
):
    """
    Strict GTFS filtering: only keep routes where ALL stops are within network bounds.
    """
    print("\n=== Strict GTFS Filter for pt2matsim ===")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Get network bounds
    bounds = get_network_bounds(network_path, buffer_m)
    
    # 2. Load and classify stops (inside vs outside)
    print("\n[1/6] Classifying stops by location...")
    stops = read_csv(input_dir / 'stops.txt')
    
    stops_inside: Set[str] = set()
    stops_outside: Set[str] = set()
    
    for s in stops:
        try:
            lat = float(s['stop_lat'])
            lon = float(s['stop_lon'])
            if is_in_bounds(lat, lon, bounds):
                stops_inside.add(s['stop_id'])
            else:
                stops_outside.add(s['stop_id'])
        except (ValueError, KeyError):
            stops_outside.add(s.get('stop_id', ''))
    
    print(f"  Stops inside bounds: {len(stops_inside)}")
    print(f"  Stops outside bounds: {len(stops_outside)}")
    
    # 3. Analyze stop_times to find which trips use which stops
    print("\n[2/6] Analyzing trip-stop relationships...")
    stop_times = read_csv(input_dir / 'stop_times.txt')
    
    trip_stops: Dict[str, Set[str]] = {}  # trip_id -> set of stop_ids
    for st in stop_times:
        trip_id = st['trip_id']
        stop_id = st['stop_id']
        if trip_id not in trip_stops:
            trip_stops[trip_id] = set()
        trip_stops[trip_id].add(stop_id)
    
    print(f"  Total trips: {len(trip_stops)}")
    
    # 4. Find trips where ALL stops are inside bounds
    print("\n[3/6] Filtering trips with 100% internal stops...")
    valid_trip_ids: Set[str] = set()
    partial_trip_ids: Set[str] = set()  # Trips with some external stops
    
    for trip_id, trip_stop_ids in trip_stops.items():
        outside_count = len(trip_stop_ids & stops_outside)
        if outside_count == 0:
            valid_trip_ids.add(trip_id)
        else:
            partial_trip_ids.add(trip_id)
    
    print(f"  Trips with 100% internal stops: {len(valid_trip_ids)}")
    print(f"  Trips with external stops (removed): {len(partial_trip_ids)}")
    
    # 5. Get routes for valid trips
    print("\n[4/6] Filtering routes and related data...")
    trips = read_csv(input_dir / 'trips.txt')
    
    valid_trips = [t for t in trips if t['trip_id'] in valid_trip_ids]
    valid_route_ids = {t['route_id'] for t in valid_trips}
    valid_service_ids = {t['service_id'] for t in valid_trips}
    
    routes = read_csv(input_dir / 'routes.txt')
    valid_routes = [r for r in routes if r['route_id'] in valid_route_ids]
    
    print(f"  Valid routes: {len(valid_routes)}")
    print(f"  Valid trips: {len(valid_trips)}")
    
    # 6. Filter stop_times and stops
    print("\n[5/6] Filtering stop_times and stops...")
    valid_stop_times = [st for st in stop_times if st['trip_id'] in valid_trip_ids]
    used_stop_ids = {st['stop_id'] for st in valid_stop_times}
    valid_stops = [s for s in stops if s['stop_id'] in used_stop_ids]
    
    print(f"  Valid stop_times: {len(valid_stop_times)}")
    print(f"  Valid stops: {len(valid_stops)}")
    
    # 7. Filter agency
    agency = read_csv(input_dir / 'agency.txt')
    used_agency_ids = {r.get('agency_id') for r in valid_routes}
    valid_agency = [a for a in agency if a.get('agency_id') in used_agency_ids]
    
    # 8. Write output
    print("\n[6/6] Writing filtered GTFS...")
    write_csv(output_dir / 'stops.txt', valid_stops)
    write_csv(output_dir / 'routes.txt', valid_routes)
    write_csv(output_dir / 'trips.txt', valid_trips)
    write_csv(output_dir / 'stop_times.txt', valid_stop_times)
    write_csv(output_dir / 'agency.txt', valid_agency)
    
    # Copy calendar files
    for f in ['calendar.txt', 'calendar_dates.txt', 'shapes.txt', 'frequencies.txt']:
        src = input_dir / f
        if src.exists():
            if f == 'calendar.txt':
                calendar = read_csv(src)
                valid_calendar = [c for c in calendar if c['service_id'] in valid_service_ids]
                write_csv(output_dir / f, valid_calendar)
            else:
                shutil.copy(src, output_dir / f)
    
    print("\n=== Strict Filtering Complete ===")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"\nSummary:")
    print(f"  Routes: {len(routes)} → {len(valid_routes)} ({100*len(valid_routes)/len(routes):.1f}%)")
    print(f"  Trips:  {len(trips)} → {len(valid_trips)} ({100*len(valid_trips)/len(trips):.1f}%)")
    print(f"  Stops:  {len(stops)} → {len(valid_stops)} ({100*len(valid_stops)/len(stops):.1f}%)")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Strict GTFS filter for pt2matsim')
    parser.add_argument('--input', '-i', required=True, help='Input GTFS directory')
    parser.add_argument('--output', '-o', required=True, help='Output GTFS directory')
    parser.add_argument('--network', '-n', required=True, help='MATSim network file (.xml or .xml.gz)')
    parser.add_argument('--buffer', '-b', type=float, default=600, help='Buffer in meters (default: 600)')
    
    args = parser.parse_args()
    filter_gtfs_strict(
        Path(args.input),
        Path(args.output),
        Path(args.network),
        args.buffer
    )
