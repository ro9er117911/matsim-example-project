#!/usr/bin/env python3
"""
Generate GeoJSON for closed links visualization in SimWrapper.

This script:
1. Reads the networkChangeEvents.xml to get closed link IDs
2. Reads the MATSim network to get link geometries
3. Outputs a GeoJSON file for SimWrapper visualization

Usage:
    python generate_closed_links_geojson.py \
        --network ../../scenarios/equil/network-with-pt-metro-v7-carscc.xml.gz \
        --events input/changeEvents_extended.xml \
        --output output/closed_links.geojson
"""

import argparse
import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from pyproj import Transformer


def parse_change_events(events_file: str) -> dict:
    """Parse networkChangeEvents.xml and return closure info."""
    print(f"Reading change events from {events_file}...")
    
    tree = ET.parse(events_file)
    root = tree.getroot()
    
    closures = {}
    
    # Handle namespace
    ns = {'matsim': 'http://www.matsim.org/files/dtd'}
    
    # Try with namespace first
    events = root.findall('.//matsim:networkChangeEvent', ns)
    if not events:
        # Try without namespace
        events = root.findall('.//networkChangeEvent')
    if not events:
        # Try direct children
        events = [child for child in root if 'networkChangeEvent' in child.tag]
    
    for event in events:
        start_time = event.get('startTime')
        
        # Handle namespace for link elements
        links = event.findall('matsim:link', ns)
        if not links:
            links = event.findall('link')
        if not links:
            links = [child for child in event if 'link' in child.tag]
        
        link_ids = [link.get('refId') for link in links]
        
        for link_id in link_ids:
            if link_id:
                closures[link_id] = {
                    'closedAt': start_time,
                    'type': 'tsunami_closure'
                }
    
    print(f"  Found {len(closures)} closed links")
    return closures


def parse_network(network_file: str, closed_link_ids: set) -> dict:
    """Parse MATSim network and return geometries for closed links."""
    print(f"Reading network from {network_file}...")
    
    if network_file.endswith('.gz'):
        with gzip.open(network_file, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(network_file)
    
    root = tree.getroot()
    
    # Parse nodes
    nodes = {}
    for node in root.findall('.//node'):
        node_id = node.get('id')
        x = float(node.get('x'))
        y = float(node.get('y'))
        nodes[node_id] = (x, y)
    
    # Parse links (only closed ones)
    links = {}
    for link in root.findall('.//link'):
        link_id = link.get('id')
        
        if link_id not in closed_link_ids:
            continue
            
        from_node = link.get('from')
        to_node = link.get('to')
        
        if from_node in nodes and to_node in nodes:
            links[link_id] = {
                'from_coords': nodes[from_node],
                'to_coords': nodes[to_node]
            }
    
    print(f"  Found geometries for {len(links)} closed links")
    return links


def create_geojson(closures: dict, link_geometries: dict, output_file: str):
    """Create GeoJSON file for closed links."""
    
    # Transformer from EPSG:3826 (TWD97) to EPSG:4326 (WGS84)
    try:
        transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
        has_transformer = True
    except Exception as e:
        print(f"  Warning: Could not create coordinate transformer: {e}")
        print("  Using raw coordinates (will need manual transformation)")
        has_transformer = False
    
    features = []
    
    for link_id, closure_info in closures.items():
        if link_id not in link_geometries:
            continue
        
        geom = link_geometries[link_id]
        from_x, from_y = geom['from_coords']
        to_x, to_y = geom['to_coords']
        
        if has_transformer:
            # Transform to WGS84
            from_lon, from_lat = transformer.transform(from_x, from_y)
            to_lon, to_lat = transformer.transform(to_x, to_y)
        else:
            from_lon, from_lat = from_x, from_y
            to_lon, to_lat = to_x, to_y
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [from_lon, from_lat],
                    [to_lon, to_lat]
                ]
            },
            "properties": {
                "linkId": link_id,
                "closedAt": closure_info['closedAt'],
                "type": closure_info['type'],
                "status": "closed"
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "name": "closed_links",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features
    }
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  Written GeoJSON with {len(features)} features to {output_file}")
    return len(features)


def main():
    parser = argparse.ArgumentParser(description='Generate closed links GeoJSON')
    parser.add_argument('--network', required=True, help='Path to MATSim network file')
    parser.add_argument('--events', required=True, help='Path to changeEvents.xml')
    parser.add_argument('--output', required=True, help='Output GeoJSON path')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Generating Closed Links GeoJSON for SimWrapper")
    print("=" * 60)
    
    # Parse change events
    closures = parse_change_events(args.events)
    
    # Parse network for closed links only
    link_geometries = parse_network(args.network, set(closures.keys()))
    
    # Create GeoJSON
    num_features = create_geojson(closures, link_geometries, args.output)
    
    print("=" * 60)
    print(f"SUCCESS: Generated GeoJSON with {num_features} closed link features")
    print("=" * 60)


if __name__ == '__main__':
    main()
