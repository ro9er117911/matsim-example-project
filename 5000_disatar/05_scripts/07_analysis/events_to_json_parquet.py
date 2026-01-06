#!/usr/bin/env python3
"""
MATSim Events to JSON/Parquet Converter

Converts MATSim output_events.xml to Via platform-compatible JSON and Parquet formats.
Includes network-based trajectory reconstruction with precise routing.

Usage:
    python events_to_json_parquet.py \
        --events scenarios/equil/forVia/output_events.xml \
        --network scenarios/equil/network-with-pt.xml \
        --json-out output/5000_abm_format_outcome.json \
        --parquet-out output/5000_abm_format_outcome.parquet
"""

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import Transformer
import networkx as nx


# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

# Coordinate reference systems
TWD97_EPSG = "EPSG:3826"  # Taiwan TWD97/TM2 Zone 121 (projected)
WGS84_EPSG = "EPSG:4326"  # WGS84 Geographic (lat/lon)

# Sampling interval
SAMPLING_INTERVAL = 3.0  # seconds

# Mode encoding for Parquet output (4 modes: BUS, CAR, RAIL, WALK)
MODE_ENCODING = {
    "car": (1, "CAR"),
    "walk": (2, "WALK"),
    "pt": (3, "RAIL"),           # Generic PT → RAIL
    "bus": (4, "BUS"),
    "subway": (3, "RAIL"),       # Subway → RAIL
    "metro": (3, "RAIL"),        # Metro → RAIL
    "tram": (3, "RAIL"),         # Tram → RAIL
    "train": (3, "RAIL"),        # Train → RAIL
    "rail": (3, "RAIL"),         # Rail → RAIL
    "transit_walk": (2, "WALK"), # Transit walk → WALK
    "access_walk": (2, "WALK"),  # Access walk → WALK
    "egress_walk": (2, "WALK"),  # Egress walk → WALK
}


# ==============================================================================
# 2. XML PARSER MODULE
# ==============================================================================

def parse_events_xml(filepath: str) -> List[Dict]:
    """
    Parse MATSim events XML file.

    Args:
        filepath: Path to events.xml or events.xml.gz

    Returns:
        List of event dictionaries, sorted by time
    """
    print(f"  [1/2] Loading events file: {filepath}")

    # Auto-detect compression
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(filepath)

    events = []
    for event_elem in tree.getroot().findall('event'):
        event = dict(event_elem.attrib)

        # Convert time to float
        event['time'] = float(event['time'])

        # Convert coordinates to float if present
        if 'x' in event:
            event['x'] = float(event['x'])
        if 'y' in event:
            event['y'] = float(event['y'])

        events.append(event)

    # Sort by time
    events.sort(key=lambda e: e['time'])

    print(f"  [2/2] Loaded {len(events):,} events")
    return events


def parse_network_xml(filepath: str) -> Tuple[Dict[str, Dict], nx.DiGraph]:
    """
    Parse MATSim network XML file.

    Args:
        filepath: Path to network.xml or network.xml.gz

    Returns:
        Tuple of (link_info_dict, network_graph)
        - link_info_dict: {link_id: {'from': node_id, 'to': node_id, 'x': x, 'y': y, 'length': m}}
        - network_graph: NetworkX directed graph for routing
    """
    print(f"  [1/3] Loading network file: {filepath}")

    # Auto-detect compression
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(filepath)

    root = tree.getroot()

    # Parse nodes
    print("  [2/3] Parsing nodes...")
    nodes = {}
    for node_elem in root.find('nodes').findall('node'):
        node_id = node_elem.get('id')
        nodes[node_id] = {
            'x': float(node_elem.get('x')),
            'y': float(node_elem.get('y'))
        }

    # Parse links
    print("  [3/3] Parsing links and building graph...")
    links = {}
    graph = nx.DiGraph()

    for link_elem in root.find('links').findall('link'):
        link_id = link_elem.get('id')
        from_node = link_elem.get('from')
        to_node = link_elem.get('to')
        length = float(link_elem.get('length'))

        # Calculate midpoint coordinate for link
        from_x, from_y = nodes[from_node]['x'], nodes[from_node]['y']
        to_x, to_y = nodes[to_node]['x'], nodes[to_node]['y']
        mid_x = (from_x + to_x) / 2.0
        mid_y = (from_y + to_y) / 2.0

        links[link_id] = {
            'from': from_node,
            'to': to_node,
            'from_x': from_x,
            'from_y': from_y,
            'to_x': to_x,
            'to_y': to_y,
            'x': mid_x,
            'y': mid_y,
            'length': length
        }

        # Add edge to graph
        graph.add_edge(from_node, to_node, link_id=link_id, length=length)

    print(f"    Loaded {len(nodes):,} nodes, {len(links):,} links")
    return links, graph


# ==============================================================================
# 3. COORDINATE TRANSFORMER MODULE
# ==============================================================================

def create_coordinate_transformer() -> Transformer:
    """
    Create coordinate transformer from TWD97 to WGS84.

    Returns:
        Transformer object for coordinate conversion
    """
    return Transformer.from_crs(TWD97_EPSG, WGS84_EPSG, always_xy=True)


def transform_coordinates(x_twd97: float, y_twd97: float,
                         transformer: Transformer) -> Tuple[float, float]:
    """
    Transform single coordinate from TWD97 to WGS84 (lat, lon).

    Args:
        x_twd97: X coordinate in TWD97
        y_twd97: Y coordinate in TWD97
        transformer: Transformer object

    Returns:
        Tuple of (latitude, longitude) in WGS84
    """
    lon, lat = transformer.transform(x_twd97, y_twd97)
    return lat, lon


# ==============================================================================
# 4. NETWORK GRAPH MODULE
# ==============================================================================

def find_network_path(from_link_id: str, to_link_id: str,
                      links: Dict[str, Dict], graph: nx.DiGraph) -> List[str]:
    """
    Find shortest path between two links using network graph.

    Args:
        from_link_id: Starting link ID
        to_link_id: Ending link ID
        links: Link information dictionary
        graph: NetworkX directed graph

    Returns:
        List of link IDs along the path (including start and end links)
    """
    try:
        from_node = links[from_link_id]['to']  # Start from end of first link
        to_node = links[to_link_id]['from']    # End at start of last link

        # Find shortest path between nodes
        node_path = nx.shortest_path(graph, from_node, to_node, weight='length')

        # Convert node path to link path
        link_path = [from_link_id]
        for i in range(len(node_path) - 1):
            from_n = node_path[i]
            to_n = node_path[i + 1]
            # Get link between these nodes
            edge_data = graph.get_edge_data(from_n, to_n)
            if edge_data:
                link_path.append(edge_data['link_id'])

        # Ensure destination link is included
        if link_path[-1] != to_link_id:
            link_path.append(to_link_id)

        return link_path

    except (KeyError, nx.NetworkXNoPath):
        # If path not found, return direct connection
        return [from_link_id, to_link_id]


def interpolate_along_links(link_ids: List[str], links: Dict[str, Dict],
                            num_samples: int) -> List[Tuple[float, float]]:
    """
    Interpolate positions along a sequence of links.

    Args:
        link_ids: List of link IDs forming the path
        links: Link information dictionary
        num_samples: Number of position samples to generate

    Returns:
        List of (x, y) coordinate tuples in TWD97
    """
    if not link_ids or num_samples <= 0:
        return []

    # Collect all coordinates along the path
    path_coords = []
    for link_id in link_ids:
        if link_id in links:
            link = links[link_id]
            # Add from node coordinate
            path_coords.append((link['from_x'], link['from_y']))

    # Add final to node coordinate
    if link_ids[-1] in links:
        last_link = links[link_ids[-1]]
        path_coords.append((last_link['to_x'], last_link['to_y']))

    if len(path_coords) < 2:
        # Fallback: use link midpoint
        if link_ids[0] in links:
            link = links[link_ids[0]]
            return [(link['x'], link['y'])] * num_samples
        return []

    # Interpolate positions uniformly along the path
    positions = []
    num_segments = len(path_coords) - 1
    samples_per_segment = max(1, num_samples // num_segments)

    for i in range(num_segments):
        x1, y1 = path_coords[i]
        x2, y2 = path_coords[i + 1]

        for j in range(samples_per_segment):
            t = j / samples_per_segment if samples_per_segment > 1 else 0.5
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            positions.append((x, y))

    # Ensure we have exactly num_samples
    while len(positions) < num_samples:
        positions.append(path_coords[-1])
    positions = positions[:num_samples]

    return positions


# ==============================================================================
# 5. TRAJECTORY RECONSTRUCTOR MODULE
# ==============================================================================

def group_events_by_person(events: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group events by person ID.

    Args:
        events: List of all events

    Returns:
        Dictionary mapping person_id to list of their events
    """
    person_events = defaultdict(list)
    for event in events:
        if 'person' in event:
            person_events[event['person']].append(event)
    return dict(person_events)


def extract_agent_id(person_id: str) -> int:
    """
    Extract integer agent ID from person string ID.

    Args:
        person_id: String like "pt_agent_01" or "4441"

    Returns:
        Integer agent ID
    """
    # Try to extract numeric suffix after underscore
    if '_' in person_id:
        suffix = person_id.split('_')[-1]
        try:
            return int(suffix)
        except ValueError:
            pass

    # Try direct integer conversion
    try:
        return int(person_id)
    except ValueError:
        # Fallback: hash the string
        return abs(hash(person_id)) % 100000


def extract_mode_from_vehicle(vehicle_id: str) -> str:
    """
    Extract PT mode from vehicle ID.

    Maps to 4 standard modes: BUS, CAR, RAIL, WALK

    Args:
        vehicle_id: String like "metro_veh_6843_subway" or "bus_veh_22_bus"

    Returns:
        Uppercase mode string (BUS or RAIL)
    """
    vehicle_lower = vehicle_id.lower()

    # Check for specific PT modes in vehicle ID
    if 'bus' in vehicle_lower:
        return "BUS"
    else:
        # All other PT modes (subway, metro, tram, train, rail) → RAIL
        return "RAIL"


def reconstruct_person_trajectory(person_events: List[Dict],
                                  links: Dict[str, Dict],
                                  graph: nx.DiGraph,
                                  transformer: Transformer) -> Tuple[List, List, List]:
    """
    Reconstruct continuous trajectory for a single person.

    Args:
        person_events: List of events for one person, sorted by time
        links: Link information dictionary
        graph: Network graph
        transformer: Coordinate transformer

    Returns:
        Tuple of (positions, modes, timestamps)
        - positions: List of [lat, lon] pairs
        - modes: List of mode strings (uppercase)
        - timestamps: List of integer timestamps (seconds)
    """
    positions = []
    modes = []
    timestamps = []

    i = 0
    while i < len(person_events):
        event = person_events[i]
        event_type = event.get('type')

        # Handle activity start events (add position snapshot)
        if event_type == 'actstart':
            if 'x' in event and 'y' in event:
                lat, lon = transform_coordinates(event['x'], event['y'], transformer)
                positions.append([lat, lon])
                modes.append("WALK")  # Activity/停留時標記為 WALK
                timestamps.append(int(event['time']))
            i += 1
            continue

        # Handle activity end followed by leg
        if event_type == 'actend':
            # Get activity end position
            act_x = event.get('x')
            act_y = event.get('y')
            act_time = event['time']

            # Look for next departure event
            if i + 1 < len(person_events) and person_events[i + 1].get('type') == 'departure':
                dep_event = person_events[i + 1]
                leg_mode = dep_event.get('legMode', 'walk')
                dep_time = dep_event['time']
                dep_link = dep_event.get('link')

                # Find arrival event
                arrival_event = None
                arrival_idx = i + 2
                while arrival_idx < len(person_events):
                    if person_events[arrival_idx].get('type') == 'arrival':
                        arrival_event = person_events[arrival_idx]
                        break
                    arrival_idx += 1

                if arrival_event:
                    arr_time = arrival_event['time']
                    arr_link = arrival_event.get('link')

                    # Calculate trajectory for this leg
                    leg_duration = arr_time - dep_time
                    num_samples = max(1, int(leg_duration / SAMPLING_INTERVAL))

                    # Get link path
                    if dep_link and arr_link and dep_link in links and arr_link in links:
                        # Use network routing
                        link_path = find_network_path(dep_link, arr_link, links, graph)
                        leg_positions_twd = interpolate_along_links(link_path, links, num_samples)
                    elif act_x and act_y and 'x' in arrival_event and 'y' in arrival_event:
                        # Use linear interpolation between activity locations
                        arr_x = arrival_event['x']
                        arr_y = arrival_event['y']
                        leg_positions_twd = []
                        for s in range(num_samples):
                            t = s / (num_samples - 1) if num_samples > 1 else 0.5
                            x = act_x + t * (arr_x - act_x)
                            y = act_y + t * (arr_y - act_y)
                            leg_positions_twd.append((x, y))
                    else:
                        leg_positions_twd = []

                    # Determine mode string
                    # For PT legs, try to extract specific mode from vehicle ID
                    mode_str = MODE_ENCODING.get(leg_mode, (3, "PT"))[1]
                    if leg_mode == 'pt':
                        # Look for PersonEntersVehicle event to get vehicle type
                        for j in range(i + 1, min(arrival_idx, len(person_events))):
                            evt = person_events[j]
                            if evt.get('type') == 'PersonEntersVehicle' and 'vehicle' in evt:
                                mode_str = extract_mode_from_vehicle(evt['vehicle'])
                                break

                    # Transform to WGS84 and add to trajectory
                    for idx, (x, y) in enumerate(leg_positions_twd):
                        lat, lon = transform_coordinates(x, y, transformer)
                        positions.append([lat, lon])
                        modes.append(mode_str)
                        sample_time = dep_time + idx * SAMPLING_INTERVAL
                        timestamps.append(int(sample_time))

                    # Jump to after arrival event
                    i = arrival_idx + 1
                    continue

            i += 1
            continue

        i += 1

    return positions, modes, timestamps


# ==============================================================================
# 6. JSON EXPORTER MODULE
# ==============================================================================

def export_to_json(agent_data: List[Dict], output_path: str):
    """
    Export agent trajectories to JSON format.

    Args:
        agent_data: List of agent trajectory dictionaries
        output_path: Output JSON file path
    """
    print(f"  Writing JSON to: {output_path}")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(agent_data, f, indent=2)

    # Report file size
    file_size = Path(output_path).stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"  ✓ JSON export complete: {size_mb:.1f} MB")


# ==============================================================================
# 7. PARQUET EXPORTER MODULE
# ==============================================================================

def export_to_parquet(agent_data: List[Dict], output_path: str):
    """
    Export agent trajectories to Parquet format with GeoArrow metadata.

    Args:
        agent_data: List of agent trajectory dictionaries
        output_path: Output Parquet file path
    """
    print(f"  Writing Parquet to: {output_path}")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Prepare arrays
    agent_ids = []
    modes_list = []
    timestamps_list = []
    geometry_list = []

    for agent in agent_data:
        agent_ids.append(agent['agent_id'])

        # Modes
        m_codes = [
            MODE_ENCODING.get(p['mode'].lower(), (3, "PT"))[0]
            for p in agent['weekday_path']
        ]
        modes_list.append(m_codes)

        # Timestamps
        t_stamps = agent['weekday_timestamp']
        timestamps_list.append(t_stamps)

        # Geometry: list of structs
        geo_points = []
        for p in agent['weekday_path']:
            geo_points.append({'x': p['position'][0], 'y': p['position'][1]})
        geometry_list.append(geo_points)

    # Build PyArrow Arrays
    agent_id_array = pa.array(agent_ids, type=pa.int64())
    modes_array = pa.array(modes_list, type=pa.list_(pa.int8()))
    timestamps_array = pa.array(timestamps_list, type=pa.list_(pa.int32()))

    # Geometry Array construction with specific non-null fields for GeoArrow
    # Inner struct: x, y (both non-null)
    point_struct_type = pa.struct([
        pa.field("x", pa.float64(), nullable=False),
        pa.field("y", pa.float64(), nullable=False)
    ])
    
    # List of points (elements non-null)
    geometry_array = pa.array(geometry_list, type=pa.list_(pa.field("element", point_struct_type, nullable=False)))

    # Define Metadata for GeoArrow
    # WGS84 PROJJSON
    crs_metadata = '{"crs": {"$schema": "https://proj.org/schemas/v0.7/projjson.schema.json", "type": "GeographicCRS", "name": "WGS 84", "datum_ensemble": {"name": "World Geodetic System 1984 ensemble", "members": [{"name": "World Geodetic System 1984 (Transit)", "id": {"authority": "EPSG", "code": 1166}}, {"name": "World Geodetic System 1984 (G730)", "id": {"authority": "EPSG", "code": 1152}}, {"name": "World Geodetic System 1984 (G873)", "id": {"authority": "EPSG", "code": 1153}}, {"name": "World Geodetic System 1984 (G1150)", "id": {"authority": "EPSG", "code": 1154}}, {"name": "World Geodetic System 1984 (G1674)", "id": {"authority": "EPSG", "code": 1155}}, {"name": "World Geodetic System 1984 (G1762)", "id": {"authority": "EPSG", "code": 1156}}, {"name": "World Geodetic System 1984 (G2139)", "id": {"authority": "EPSG", "code": 1309}}, {"name": "World Geodetic System 1984 (G2296)", "id": {"authority": "EPSG", "code": 1383}}], "ellipsoid": {"name": "WGS 84", "semi_major_axis": 6378137, "inverse_flattening": 298.257223563}, "accuracy": "2.0", "id": {"authority": "EPSG", "code": 6326}}, "coordinate_system": {"subtype": "ellipsoidal", "axis": [{"name": "Geodetic latitude", "abbreviation": "Lat", "direction": "north", "unit": "degree"}, {"name": "Geodetic longitude", "abbreviation": "Lon", "direction": "east", "unit": "degree"}]}, "scope": "Horizontal component of 3D system.", "area": "World.", "bbox": {"south_latitude": -90, "west_longitude": -180, "north_latitude": 90, "east_longitude": 180}, "id": {"authority": "EPSG", "code": 4326}}, "crs_type": "projjson"}'

    geometry_field = pa.field(
        "geometry", 
        geometry_array.type,
        metadata={
            b'ARROW:extension:name': b'geoarrow.linestring',
            b'ARROW:extension:metadata': crs_metadata.encode('utf-8')
        }
    )

    # Construct Schema
    schema = pa.schema([
        pa.field("agent_id", pa.int64()),
        pa.field("modes", pa.list_(pa.int8())),
        pa.field("timestamps", pa.list_(pa.int32())),
        geometry_field
    ])

    # Create Table
    table = pa.Table.from_arrays(
        [agent_id_array, modes_array, timestamps_array, geometry_array],
        schema=schema
    )

    # Write Parquet
    pq.write_table(table, output_path, compression='snappy')

    # Report file size
    file_size = Path(output_path).stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"  ✓ Parquet export complete: {size_mb:.1f} MB")


# ==============================================================================
# 8. MAIN EXECUTION
# ==============================================================================

def main():
    """Main conversion pipeline."""
    parser = argparse.ArgumentParser(
        description='Convert MATSim events to JSON/Parquet format for Via platform'
    )
    parser.add_argument('--events', required=True,
                       help='Path to MATSim output_events.xml[.gz]')
    parser.add_argument('--network', required=True,
                       help='Path to MATSim network.xml[.gz]')
    parser.add_argument('--json-out', required=True,
                       help='Output path for JSON file')
    parser.add_argument('--parquet-out', required=True,
                       help='Output path for Parquet file')

    args = parser.parse_args()

    print("=" * 70)
    print("MATSim Events → JSON/Parquet Converter")
    print("=" * 70)

    # Step 1: Parse events
    print("\n[Step 1/5] Parsing events XML...")
    events = parse_events_xml(args.events)

    # Step 2: Parse network
    print("\n[Step 2/5] Parsing network XML...")
    links, graph = parse_network_xml(args.network)

    # Step 3: Create coordinate transformer
    print("\n[Step 3/5] Creating coordinate transformer (TWD97 → WGS84)...")
    transformer = create_coordinate_transformer()
    print("  ✓ Transformer ready")

    # Step 4: Reconstruct trajectories
    print("\n[Step 4/5] Reconstructing agent trajectories...")
    person_events = group_events_by_person(events)
    print(f"  Found {len(person_events)} agents")

    agent_data = []
    for person_id, events_list in person_events.items():
        positions, modes_list, timestamps_list = reconstruct_person_trajectory(
            events_list, links, graph, transformer
        )

        if not positions:
            print(f"  Warning: No trajectory for agent {person_id}")
            continue

        agent_id = extract_agent_id(person_id)
        agent_data.append({
            'agent_id': agent_id,
            'weekday_path': [
                {'position': pos, 'mode': mode}
                for pos, mode in zip(positions, modes_list)
            ],
            'weekday_timestamp': timestamps_list
        })

    print(f"  ✓ Reconstructed {len(agent_data)} agent trajectories")

    # Step 5: Export data
    print("\n[Step 5/5] Exporting data...")
    export_to_json(agent_data, args.json_out)
    export_to_parquet(agent_data, args.parquet_out)

    print("\n" + "=" * 70)
    print("✓ Conversion complete!")
    print(f"  JSON output:    {args.json_out}")
    print(f"  Parquet output: {args.parquet_out}")
    print("=" * 70)


if __name__ == '__main__':
    main()
