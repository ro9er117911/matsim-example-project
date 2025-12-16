#!/usr/bin/env python3
"""
Generate Staged Network Change Events for Tsunami Evacuation.
Uses REAL OSM coastline geometry for accurate coastal link selection.

Usage:
    python generate_change_events.py \
        --network ../../scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz \
        --shoreline input/tamsui_shoreline.geojson \
        --output input/tsunami_changeEvents.xml \
        --geojson-output output/coastal_closure.geojson
"""

import argparse
import gzip
import json
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass


# Stage configuration (distance thresholds in meters)
@dataclass
class StageConfig:
    name: str
    min_dist: float
    max_dist: float
    color: str
    degrade_time_offset: int  # seconds after alert
    close_time_offset: int    # seconds after alert (0 = no closure)
    speed_factor: float       # freespeed multiplier


STAGES = [
    StageConfig("stage_1", 0, 500, "#ff0000", 0, 600, 0.5),        # Red: 0-500m
    StageConfig("stage_2", 500, 1500, "#ff6600", 300, 900, 0.5),   # Orange: 500-1500m  
    StageConfig("stage_3", 1500, 3000, "#ffcc00", 600, 1200, 0.5), # Yellow: 1500-3000m
    StageConfig("stage_4", 3000, 10000, "#99cc00", 900, 0, 0.3),   # Light: 3000-10000m (no close)
]

ALERT_TIME = 10800  # 03:00:00 in seconds


def parse_network(network_file: str) -> Dict:
    """Parse MATSim network and return nodes and links."""
    print(f"Reading network from {network_file}...")
    
    if network_file.endswith('.gz'):
        with gzip.open(network_file, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(network_file)
    
    root = tree.getroot()
    
    nodes = {}
    for node in root.findall('.//node'):
        node_id = node.get('id')
        x = float(node.get('x'))
        y = float(node.get('y'))
        nodes[node_id] = (x, y)
    
    links = {}
    for link in root.findall('.//link'):
        link_id = link.get('id')
        from_node = link.get('from')
        to_node = link.get('to')
        modes = link.get('modes', 'car')
        
        if from_node in nodes and to_node in nodes:
            from_coords = nodes[from_node]
            to_coords = nodes[to_node]
            mid_x = (from_coords[0] + to_coords[0]) / 2
            mid_y = (from_coords[1] + to_coords[1]) / 2
            links[link_id] = {
                'from': from_node,
                'to': to_node,
                'mid_x': mid_x,
                'mid_y': mid_y,
                'from_coords': from_coords,
                'to_coords': to_coords,
                'modes': modes
            }
    
    print(f"  Found {len(nodes)} nodes and {len(links)} links")
    return {'nodes': nodes, 'links': links}


def load_shoreline(shoreline_file: str) -> List[List[Tuple[float, float]]]:
    """
    Load shoreline geometry from GeoJSON and convert to EPSG:3826.
    Returns list of linestrings, each as list of (x, y) coordinates.
    """
    print(f"Loading shoreline from {shoreline_file}...")
    
    with open(shoreline_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)
    
    linestrings = []
    for feature in data.get('features', []):
        geom = feature.get('geometry', {})
        geom_type = geom.get('type', '')
        
        if geom_type == 'LineString':
            coords = geom.get('coordinates', [])
            line_3826 = [transformer.transform(lon, lat) for lon, lat in coords]
            if line_3826:
                linestrings.append(line_3826)
        elif geom_type == 'MultiLineString':
            for line in geom.get('coordinates', []):
                line_3826 = [transformer.transform(lon, lat) for lon, lat in line]
                if line_3826:
                    linestrings.append(line_3826)
    
    total_points = sum(len(ls) for ls in linestrings)
    print(f"  Loaded {len(linestrings)} linestrings with {total_points} total points")
    return linestrings


def distance_to_shoreline(x: float, y: float, linestrings: List[List[Tuple[float, float]]]) -> float:
    """Calculate minimum distance from point to any shoreline segment."""
    min_dist = float('inf')
    
    for line in linestrings:
        for i in range(len(line) - 1):
            x1, y1 = line[i]
            x2, y2 = line[i + 1]
            dist = point_to_segment_distance(x, y, x1, y1, x2, y2)
            min_dist = min(min_dist, dist)
    
    return min_dist


def point_to_segment_distance(px: float, py: float, 
                               x1: float, y1: float, 
                               x2: float, y2: float) -> float:
    """Calculate shortest distance from point to line segment."""
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)


def is_pt_link(link_id: str, modes: str) -> bool:
    """Check if link is PT-only (should be excluded)."""
    pt_prefixes = ('pt_', 'tr_', 'transit_', 'rail_', 'metro_')
    if any(link_id.lower().startswith(prefix) for prefix in pt_prefixes):
        return True
    
    # Check if subway-only (no car mode)
    link_modes = set(m.strip().lower() for m in modes.split(','))
    if 'subway' in link_modes and 'car' not in link_modes:
        return True
    
    return False


def classify_links_by_stage(network_data: Dict, linestrings: List[List[Tuple[float, float]]]) -> Dict[str, List[Tuple[str, float]]]:
    """
    Classify links into stages based on distance to shoreline.
    Returns: {stage_name: [(link_id, distance), ...]}
    """
    stage_links = {stage.name: [] for stage in STAGES}
    excluded_pt = 0
    out_of_range = 0
    
    max_distance = max(stage.max_dist for stage in STAGES)
    
    for link_id, link_data in network_data['links'].items():
        # Skip PT links
        if is_pt_link(link_id, link_data.get('modes', '')):
            excluded_pt += 1
            continue
        
        mid_x = link_data['mid_x']
        mid_y = link_data['mid_y']
        
        dist = distance_to_shoreline(mid_x, mid_y, linestrings)
        
        # Skip links outside max range
        if dist > max_distance:
            out_of_range += 1
            continue
        
        # Assign to stage
        for stage in STAGES:
            if stage.min_dist <= dist < stage.max_dist:
                stage_links[stage.name].append((link_id, dist))
                break
    
    print(f"  Excluded {excluded_pt} PT links")
    print(f"  Excluded {out_of_range} links outside 10km range")
    for stage in STAGES:
        print(f"  {stage.name} ({stage.min_dist}-{stage.max_dist}m): {len(stage_links[stage.name])} links")
    
    return stage_links


def generate_change_events(stage_links: Dict[str, List[Tuple[str, float]]]) -> ET.Element:
    """Generate network change events XML."""
    root = ET.Element('networkChangeEvents')
    root.set('xmlns', 'http://www.matsim.org/files/dtd')
    
    events = []
    
    for stage in STAGES:
        links = stage_links.get(stage.name, [])
        if not links:
            continue
        
        link_ids = [lid for lid, _ in links]
        
        # Degradation event
        if stage.speed_factor < 1.0:
            degrade_time = ALERT_TIME + stage.degrade_time_offset
            events.append({
                'time': degrade_time,
                'links': link_ids,
                'type': 'scaleFactor',
                'value': stage.speed_factor,
                'comment': f'{stage.name}: Speed reduced to {int(stage.speed_factor * 100)}%'
            })
        
        # Closure event
        if stage.close_time_offset > 0:
            close_time = ALERT_TIME + stage.close_time_offset
            events.append({
                'time': close_time,
                'links': link_ids,
                'type': 'absolute',
                'value': 0.0,
                'comment': f'{stage.name}: CLOSED (flooded)'
            })
    
    # Sort by time
    events.sort(key=lambda e: e['time'])
    
    for evt in events:
        event_elem = ET.SubElement(root, 'networkChangeEvent')
        event_elem.set('startTime', format_time(evt['time']))
        
        comment = ET.Comment(f" {evt['comment']} ")
        event_elem.insert(0, comment)
        
        for link_id in sorted(evt['links']):
            link_elem = ET.SubElement(event_elem, 'link')
            link_elem.set('refId', link_id)
        
        freespeed = ET.SubElement(event_elem, 'freespeed')
        freespeed.set('type', evt['type'])
        freespeed.set('value', str(evt['value']))
    
    print(f"  Generated {len(events)} network change events")
    return root


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


def write_xml(root: ET.Element, output_file: str):
    """Write XML with formatting."""
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='\t')
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f"  Written to {output_file}")


def generate_combined_geojson(network_data: Dict, stage_links: Dict[str, List[Tuple[str, float]]], output_file: str):
    """Generate a single combined GeoJSON with all stages."""
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    
    features = []
    
    for stage in STAGES:
        links = stage_links.get(stage.name, [])
        for link_id, dist in links:
            if link_id not in network_data['links']:
                continue
            
            link = network_data['links'][link_id]
            fx, fy = link['from_coords']
            tx, ty = link['to_coords']
            
            fx_wgs, fy_wgs = transformer.transform(fx, fy)
            tx_wgs, ty_wgs = transformer.transform(tx, ty)
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[fx_wgs, fy_wgs], [tx_wgs, ty_wgs]]
                },
                "properties": {
                    "linkId": link_id,
                    "stage": stage.name,
                    "distance_m": round(dist, 1),
                    "color": stage.color,
                    "close_time": format_time(ALERT_TIME + stage.close_time_offset) if stage.close_time_offset > 0 else "no_close"
                }
            })
    
    geojson = {
        "type": "FeatureCollection",
        "name": "coastal_closure_zones",
        "features": features
    }
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  Combined GeoJSON: {len(features)} features -> {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate staged tsunami road closure events using real coastline')
    parser.add_argument('--network', required=True, help='MATSim network file')
    parser.add_argument('--shoreline', required=True, help='Shoreline GeoJSON (coastline + riverbank)')
    parser.add_argument('--output', required=True, help='Output changeEvents.xml')
    parser.add_argument('--geojson-output', default=None, help='Output combined closure GeoJSON')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Staged Tsunami Closure - Real Coastline Version")
    print("=" * 60)
    print(f"  Alert time: {format_time(ALERT_TIME)}")
    print(f"  Stages: {len(STAGES)}")
    for stage in STAGES:
        print(f"    - {stage.name}: {stage.min_dist}-{stage.max_dist}m, color={stage.color}")
    print()
    
    # Load data
    network_data = parse_network(args.network)
    linestrings = load_shoreline(args.shoreline)
    
    if not linestrings:
        print("ERROR: No shoreline geometry found!")
        return
    
    # Classify links
    stage_links = classify_links_by_stage(network_data, linestrings)
    
    # Generate XML
    root = generate_change_events(stage_links)
    write_xml(root, args.output)
    
    # Generate GeoJSON
    geojson_output = args.geojson_output or str(Path(args.output).parent.parent / 'output' / 'coastal_closure.geojson')
    generate_combined_geojson(network_data, stage_links, geojson_output)
    
    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)


if __name__ == '__main__':
    main()
