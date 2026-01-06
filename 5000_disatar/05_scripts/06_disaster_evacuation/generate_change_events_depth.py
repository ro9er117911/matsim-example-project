#!/usr/bin/env python3
"""
Generate Staged Network Change Events for Tsunami Evacuation.
Uses 2025 Tsunami Inundation Map (Max_depth) for accurate flood zone selection.

Usage:
    python generate_change_events_depth.py \
        --network ../../scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz \
        --inundation ../evacuation_shp/2025年海嘯溢淹潛勢圖資/2025年海嘯溢淹潛勢更新模擬.shp \
        --output input/tsunami_changeEvents_2025.xml \
        --geojson-output output/inundation_closure.geojson
"""

import argparse
import gzip
import json
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    from pyproj import Transformer
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install geopandas shapely pyproj")
    exit(1)


# Stage configuration based on inundation depth (meters)
# Reference: 新北市淡水區海嘯疏散避難地圖
@dataclass
class DepthStageConfig:
    name: str
    min_depth: float
    max_depth: float
    color: str
    degrade_time_offset: int  # seconds after alert
    close_time_offset: int    # seconds after alert (0 = no closure)
    speed_factor: float       # freespeed multiplier


DEPTH_STAGES = [
    # 按照深度分階段：深度越深，封閉越早
    DepthStageConfig("depth_gt3", 3.0, 999.0, "#8B0000", 0, 300, 0.0),       # 深紅: >3m - 最早封閉
    DepthStageConfig("depth_2_3", 2.0, 3.0, "#FF4500", 60, 360, 0.3),        # 橘紅: 2-3m
    DepthStageConfig("depth_1_2", 1.0, 2.0, "#FF8C00", 120, 420, 0.4),       # 深橘: 1-2m
    DepthStageConfig("depth_05_1", 0.5, 1.0, "#FFA500", 180, 480, 0.5),      # 淺橘: 0.5-1m
    DepthStageConfig("depth_03_05", 0.3, 0.5, "#FFD700", 240, 540, 0.6),     # 淺黃: 0.3-0.5m
    DepthStageConfig("depth_0_03", 0.0, 0.3, "#FFFF00", 300, 0, 0.7),        # 黃: <0.3m - 只減速不封閉
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


def load_inundation_map(shp_file: str, roi_bounds: Optional[Tuple[float, float, float, float]] = None) -> gpd.GeoDataFrame:
    """
    Load 2025 Tsunami Inundation Map shapefile.
    
    Args:
        shp_file: Path to shapefile
        roi_bounds: Optional (minx, miny, maxx, maxy) in EPSG:4326 to filter
    
    Returns:
        GeoDataFrame with Max_depth and geometry (converted to EPSG:3826)
    """
    print(f"Loading inundation map from {shp_file}...")
    
    gdf = gpd.read_file(shp_file)
    print(f"  Total records: {len(gdf)}")
    
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    # Filter to ROI if provided (淡水區域)
    if roi_bounds:
        minx, miny, maxx, maxy = roi_bounds
        gdf = gdf.cx[minx:maxx, miny:maxy]
        print(f"  After ROI filter: {len(gdf)} records")
    
    # Convert to EPSG:3826 (Taiwan TM2 zone 121)
    if gdf.crs.to_epsg() != 3826:
        gdf = gdf.to_crs("EPSG:3826")
        print(f"  Converted to EPSG:3826")
    
    print(f"  Max_depth range: {gdf['Max_depth'].min():.2f} - {gdf['Max_depth'].max():.2f} m")
    return gdf


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


def classify_links_by_depth(network_data: Dict, inundation_gdf: gpd.GeoDataFrame) -> Dict[str, List[Tuple[str, float]]]:
    """
    Classify links into stages based on inundation depth.
    Uses spatial index for efficient lookup.
    
    Returns: {stage_name: [(link_id, max_depth), ...]}
    """
    print("Classifying links by inundation depth...")
    
    stage_links = {stage.name: [] for stage in DEPTH_STAGES}
    excluded_pt = 0
    no_inundation = 0
    
    # Build spatial index for inundation polygons
    print("  Building spatial index...")
    geometries = list(inundation_gdf.geometry.values)
    tree = STRtree(geometries)
    
    print("  Processing links...")
    processed = 0
    total = len(network_data['links'])
    
    for link_id, link_data in network_data['links'].items():
        processed += 1
        if processed % 5000 == 0:
            print(f"    Processed {processed}/{total} links...")
        
        # Skip PT links
        if is_pt_link(link_id, link_data.get('modes', '')):
            excluded_pt += 1
            continue
        
        # Create point at link midpoint
        mid_point = Point(link_data['mid_x'], link_data['mid_y'])
        
        # Query spatial index - Shapely 2.x returns indices
        candidate_indices = tree.query(mid_point)
        
        max_depth = 0.0
        for idx in candidate_indices:
            geom = geometries[idx]
            if geom.contains(mid_point):
                depth = inundation_gdf.iloc[idx]['Max_depth']
                max_depth = max(max_depth, depth)
        
        if max_depth <= 0:
            no_inundation += 1
            continue
        
        # Assign to appropriate stage
        for stage in DEPTH_STAGES:
            if stage.min_depth <= max_depth < stage.max_depth:
                stage_links[stage.name].append((link_id, max_depth))
                break
    
    print(f"  Excluded {excluded_pt} PT links")
    print(f"  {no_inundation} links outside inundation zone")
    
    total_affected = 0
    for stage in DEPTH_STAGES:
        count = len(stage_links[stage.name])
        total_affected += count
        print(f"  {stage.name} ({stage.min_depth}-{stage.max_depth}m): {count} links")
    
    print(f"  Total affected links: {total_affected}")
    return stage_links


def generate_change_events(stage_links: Dict[str, List[Tuple[str, float]]]) -> ET.Element:
    """Generate network change events XML."""
    root = ET.Element('networkChangeEvents')
    root.set('xmlns', 'http://www.matsim.org/files/dtd')
    
    events = []
    
    for stage in DEPTH_STAGES:
        links = stage_links.get(stage.name, [])
        if not links:
            continue
        
        link_ids = [lid for lid, _ in links]
        
        # Degradation event (speed reduction)
        if 0 < stage.speed_factor < 1.0:
            degrade_time = ALERT_TIME + stage.degrade_time_offset
            events.append({
                'time': degrade_time,
                'links': link_ids,
                'type': 'scaleFactor',
                'value': stage.speed_factor,
                'comment': f'{stage.name}: Speed reduced to {int(stage.speed_factor * 100)}% (depth {stage.min_depth}-{stage.max_depth}m)'
            })
        
        # Closure event
        if stage.close_time_offset > 0:
            close_time = ALERT_TIME + stage.close_time_offset
            events.append({
                'time': close_time,
                'links': link_ids,
                'type': 'absolute',
                'value': 0.0,
                'comment': f'{stage.name}: CLOSED - Flooded (depth {stage.min_depth}-{stage.max_depth}m)'
            })
        elif stage.speed_factor == 0.0:
            # Immediate closure for very deep areas
            close_time = ALERT_TIME + stage.degrade_time_offset
            events.append({
                'time': close_time,
                'links': link_ids,
                'type': 'absolute',
                'value': 0.0,
                'comment': f'{stage.name}: IMMEDIATE CLOSURE - Severe flooding (depth >{stage.min_depth}m)'
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
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    
    features = []
    
    for stage in DEPTH_STAGES:
        links = stage_links.get(stage.name, [])
        for link_id, depth in links:
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
                    "depth_m": round(depth, 2),
                    "color": stage.color,
                    "close_time": format_time(ALERT_TIME + stage.close_time_offset) if stage.close_time_offset > 0 else (
                        format_time(ALERT_TIME + stage.degrade_time_offset) if stage.speed_factor == 0.0 else "no_close"
                    )
                }
            })
    
    geojson = {
        "type": "FeatureCollection",
        "name": "inundation_closure_zones_2025",
        "features": features
    }
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  Combined GeoJSON: {len(features)} features -> {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate staged tsunami road closure events using 2025 inundation depth map')
    parser.add_argument('--network', required=True, help='MATSim network file')
    parser.add_argument('--inundation', required=True, help='2025 Tsunami inundation shapefile')
    parser.add_argument('--output', required=True, help='Output changeEvents.xml')
    parser.add_argument('--geojson-output', default=None, help='Output combined closure GeoJSON')
    parser.add_argument('--roi', default='121.35,25.10,121.52,25.22', 
                       help='ROI bounds as minlon,minlat,maxlon,maxlat (default: Tamsui area)')
    
    args = parser.parse_args()
    
    # Parse ROI
    roi_parts = [float(x) for x in args.roi.split(',')]
    roi_bounds = tuple(roi_parts) if len(roi_parts) == 4 else None
    
    print("=" * 60)
    print("Staged Tsunami Closure - 2025 Inundation Depth Version")
    print("=" * 60)
    print(f"  Alert time: {format_time(ALERT_TIME)}")
    print(f"  Stages: {len(DEPTH_STAGES)} (based on inundation depth)")
    for stage in DEPTH_STAGES:
        close_info = f"close@+{stage.close_time_offset}s" if stage.close_time_offset > 0 else (
            "immediate close" if stage.speed_factor == 0.0 else "no close"
        )
        print(f"    - {stage.name}: {stage.min_depth}-{stage.max_depth}m, {close_info}, color={stage.color}")
    print(f"  ROI: {roi_bounds}")
    print()
    
    # Load data
    network_data = parse_network(args.network)
    inundation_gdf = load_inundation_map(args.inundation, roi_bounds)
    
    if len(inundation_gdf) == 0:
        print("ERROR: No inundation data found in ROI!")
        return
    
    # Classify links by depth
    stage_links = classify_links_by_depth(network_data, inundation_gdf)
    
    # Check if any links affected
    total_affected = sum(len(links) for links in stage_links.values())
    if total_affected == 0:
        print("WARNING: No links found in inundation zone!")
        print("  Check if network and inundation map overlap spatially.")
        return
    
    # Generate XML
    root = generate_change_events(stage_links)
    write_xml(root, args.output)
    
    # Generate GeoJSON
    geojson_output = args.geojson_output or str(Path(args.output).parent.parent / 'output' / 'inundation_closure.geojson')
    generate_combined_geojson(network_data, stage_links, geojson_output)
    
    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"  1. Review generated events: {args.output}")
    print(f"  2. Visualize closure zones: {geojson_output}")
    print("  3. Update config.xml to use new changeEvents file")


if __name__ == '__main__':
    main()
