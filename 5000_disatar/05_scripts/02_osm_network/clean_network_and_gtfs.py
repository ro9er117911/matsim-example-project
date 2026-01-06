#!/usr/bin/env python3
"""
Clean Network and Ultra-Strict GTFS Filter

1. Remove anomalously long links from network (likely data errors)
2. Filter GTFS to stricter Taipei/New Taipei bounds (exclude Taoyuan)
"""

import csv
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from pyproj import Transformer
from typing import Set, Dict, List, Tuple
import shutil
import math

# ============ CONFIGURATION ============
# Strict bounds for Taipei + New Taipei ONLY (exclude Taoyuan/Keelung edges)
# Roughly: Tamsui to Xizhi, Beitou to Xindian
TAIPEI_STRICT_BOUNDS = {
    'lon_min': 121.43,  # West boundary (before Linkou)
    'lon_max': 121.95,  # East boundary (Xizhi area)
    'lat_min': 24.95,   # South boundary (Xindian area)
    'lat_max': 25.30    # North boundary (Tamsui)
}

# Maximum link length (links longer than this are removed)
MAX_LINK_LENGTH_M = 1500

# Buffer for GTFS stops (within this distance from network links)
STOP_BUFFER_M = 400


def clean_network(
    input_network: Path,
    output_network: Path,
    max_link_length_m: float = MAX_LINK_LENGTH_M
) -> Tuple[Dict[str, Tuple[float, float]], Set[str]]:
    """Remove anomalously long links and return cleaned nodes/links."""
    print(f"\n=== Cleaning Network ===")
    print(f"Max link length: {max_link_length_m}m")
    
    if str(input_network).endswith('.gz'):
        with gzip.open(input_network, 'rt') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(input_network)
    
    root = tree.getroot()
    
    # Load nodes
    nodes = {}
    nodes_elem = root.find('.//nodes')
    for node in root.iterfind('.//node'):
        nid = node.attrib['id']
        x = float(node.attrib['x'])
        y = float(node.attrib['y'])
        nodes[nid] = (x, y)
    
    # Find and remove long links
    links_elem = root.find('.//links')
    links_to_remove = []
    removed_count = 0
    
    for link in root.iterfind('.//link'):
        from_id = link.attrib['from']
        to_id = link.attrib['to']
        
        if from_id in nodes and to_id in nodes:
            x1, y1 = nodes[from_id]
            x2, y2 = nodes[to_id]
            length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            
            if length > max_link_length_m:
                links_to_remove.append(link)
                removed_count += 1
    
    # Remove from XML
    for link in links_to_remove:
        links_elem.remove(link)
    
    print(f"  Removed {removed_count} links > {max_link_length_m}m")
    
    # Get remaining link IDs
    remaining_links = set()
    for link in root.iterfind('.//link'):
        remaining_links.add(link.attrib['id'])
    
    # Write cleaned network
    if str(output_network).endswith('.gz'):
        with gzip.open(output_network, 'wt', encoding='utf-8') as f:
            tree.write(f, encoding='unicode', xml_declaration=True)
    else:
        tree.write(output_network, encoding='utf-8', xml_declaration=True)
    
    print(f"  Cleaned network written to: {output_network}")
    return nodes, remaining_links


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


def is_in_taipei_bounds(lat: float, lon: float) -> bool:
    """Check if point is within strict Taipei/New Taipei bounds."""
    return (TAIPEI_STRICT_BOUNDS['lon_min'] <= lon <= TAIPEI_STRICT_BOUNDS['lon_max'] and
            TAIPEI_STRICT_BOUNDS['lat_min'] <= lat <= TAIPEI_STRICT_BOUNDS['lat_max'])


def filter_gtfs_ultra_strict(
    input_dir: Path,
    output_dir: Path
):
    """Ultra-strict GTFS filtering: Taipei/New Taipei only."""
    print(f"\n=== Ultra-Strict GTFS Filter ===")
    print(f"Bounds: lon=[{TAIPEI_STRICT_BOUNDS['lon_min']}, {TAIPEI_STRICT_BOUNDS['lon_max']}]")
    print(f"        lat=[{TAIPEI_STRICT_BOUNDS['lat_min']}, {TAIPEI_STRICT_BOUNDS['lat_max']}]")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Classify stops
    print("\n[1/6] Classifying stops...")
    stops = read_csv(input_dir / 'stops.txt')
    
    stops_inside: Set[str] = set()
    stops_outside: Set[str] = set()
    
    for s in stops:
        try:
            lat = float(s['stop_lat'])
            lon = float(s['stop_lon'])
            if is_in_taipei_bounds(lat, lon):
                stops_inside.add(s['stop_id'])
            else:
                stops_outside.add(s['stop_id'])
        except (ValueError, KeyError):
            stops_outside.add(s.get('stop_id', ''))
    
    print(f"  Stops inside Taipei bounds: {len(stops_inside)}")
    print(f"  Stops outside: {len(stops_outside)}")
    
    # 2. Analyze trips
    print("\n[2/6] Analyzing trips...")
    stop_times = read_csv(input_dir / 'stop_times.txt')
    
    trip_stops: Dict[str, Set[str]] = {}
    for st in stop_times:
        trip_id = st['trip_id']
        stop_id = st['stop_id']
        if trip_id not in trip_stops:
            trip_stops[trip_id] = set()
        trip_stops[trip_id].add(stop_id)
    
    # 3. Filter trips with 100% internal stops
    print("\n[3/6] Filtering trips...")
    valid_trip_ids: Set[str] = set()
    
    for trip_id, trip_stop_ids in trip_stops.items():
        outside_count = len(trip_stop_ids & stops_outside)
        if outside_count == 0 and len(trip_stop_ids) >= 2:
            valid_trip_ids.add(trip_id)
    
    print(f"  Valid trips: {len(valid_trip_ids)}")
    
    # 4. Get routes
    print("\n[4/6] Filtering routes...")
    trips = read_csv(input_dir / 'trips.txt')
    
    valid_trips = [t for t in trips if t['trip_id'] in valid_trip_ids]
    valid_route_ids = {t['route_id'] for t in valid_trips}
    valid_service_ids = {t['service_id'] for t in valid_trips}
    
    routes = read_csv(input_dir / 'routes.txt')
    valid_routes = [r for r in routes if r['route_id'] in valid_route_ids]
    
    print(f"  Valid routes: {len(valid_routes)}")
    
    # 5. Filter stop_times and stops
    print("\n[5/6] Filtering stop_times and stops...")
    valid_stop_times = [st for st in stop_times if st['trip_id'] in valid_trip_ids]
    used_stop_ids = {st['stop_id'] for st in valid_stop_times}
    valid_stops = [s for s in stops if s['stop_id'] in used_stop_ids]
    
    print(f"  Valid stops: {len(valid_stops)}")
    
    # 6. Filter agency
    agency = read_csv(input_dir / 'agency.txt')
    used_agency_ids = {r.get('agency_id') for r in valid_routes}
    valid_agency = [a for a in agency if a.get('agency_id') in used_agency_ids]
    
    # Write output
    print("\n[6/6] Writing filtered GTFS...")
    write_csv(output_dir / 'stops.txt', valid_stops)
    write_csv(output_dir / 'routes.txt', valid_routes)
    write_csv(output_dir / 'trips.txt', valid_trips)
    write_csv(output_dir / 'stop_times.txt', valid_stop_times)
    write_csv(output_dir / 'agency.txt', valid_agency)
    
    # Calendar
    calendar_src = input_dir / 'calendar.txt'
    if calendar_src.exists():
        calendar = read_csv(calendar_src)
        valid_calendar = [c for c in calendar if c['service_id'] in valid_service_ids]
        write_csv(output_dir / 'calendar.txt', valid_calendar)
    
    # Copy other files
    for f in ['calendar_dates.txt', 'shapes.txt', 'frequencies.txt']:
        src = input_dir / f
        if src.exists():
            shutil.copy(src, output_dir / f)
    
    print(f"\n=== Ultra-Strict Filter Complete ===")
    print(f"  Routes: {len(routes)} → {len(valid_routes)}")
    print(f"  Trips:  {len(trips)} → {len(valid_trips)}")
    print(f"  Stops:  {len(stops)} → {len(valid_stops)}")
    
    return len(valid_routes), len(valid_trips), len(valid_stops)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Clean network and ultra-strict GTFS filter')
    parser.add_argument('--input-network', '-n', required=True, help='Input network file')
    parser.add_argument('--output-network', '-on', required=True, help='Output cleaned network')
    parser.add_argument('--input-gtfs', '-g', required=True, help='Input GTFS directory')
    parser.add_argument('--output-gtfs', '-og', required=True, help='Output GTFS directory')
    parser.add_argument('--max-link', type=float, default=MAX_LINK_LENGTH_M, help='Max link length in meters')
    
    args = parser.parse_args()
    
    # Clean network
    clean_network(
        Path(args.input_network),
        Path(args.output_network),
        args.max_link
    )
    
    # Filter GTFS
    filter_gtfs_ultra_strict(
        Path(args.input_gtfs),
        Path(args.output_gtfs)
    )
