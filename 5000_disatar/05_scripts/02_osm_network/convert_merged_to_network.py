#!/usr/bin/env python3
"""
Convert Merged GPKG to MATSim Network.
Generates nodes from geometry (end points) since topology is fixed.
"""

import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from pathlib import Path
import gzip
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Config
INPUT_GPKG = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v6/merged_network_v6/merged_fixed_roads.gpkg")
OUTPUT_XML = INPUT_GPKG.parent / "network_v5_scc_bus.xml.gz" # Using user requested filename

# Road Mapping (Reuse existing logic)
ROAD_CLASS_PARAMS = {
    '1': (33.3, 2000, 3, 'National Highway'),
    '2': (25.0, 1500, 2, 'Provincial Road'),
    '3': (16.7, 1000, 2, 'County Road'),
    '4': (13.9, 800, 1, 'Township Road'),
    '5': (11.1, 600, 1, 'Urban Street'),
    '6': (8.3, 400, 1, 'Other'),
    'default': (11.1, 600, 1, 'Default')
}

def get_road_params(road_class):
    r_str = str(road_class).strip()
    return ROAD_CLASS_PARAMS.get(r_str, ROAD_CLASS_PARAMS['default'])

def main():
    print(f"Loading {INPUT_GPKG}...")
    try:
        gdf = gpd.read_file(INPUT_GPKG)
    except Exception as e:
        print(f"Error reading GPKG: {e}")
        return

    print(f"Processing {len(gdf)} links...")
    
    # 1. Identify Nodes
    nodes = {}  # (x, y) -> node_id
    next_node_id = 1
    
    def get_node_id(point):
        nonlocal next_node_id
        coord = (round(point.x, 2), round(point.y, 2))
        if coord not in nodes:
            nodes[coord] = next_node_id
            next_node_id += 1
        return nodes[coord]

    # MATSim XML
    network = Element('network')
    nodes_elem = SubElement(network, 'nodes')
    links_elem = SubElement(network, 'links')
    
    links_count = 0
    
    # Iteration
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom.is_empty: continue
        
        # Handle MultiLineString (take biggest part or iterate? simpler: assume simple lines from neatnet)
        parts = [geom] if geom.geom_type == 'LineString' else list(geom.geoms)
        
        road_class = row.get('ROADCLASS1', 'default')
        freespeed, cap_lane, lanes, _ = get_road_params(road_class)
        oneway = str(row.get('ONEWAY', '0')) # Assuming field exists? Or DIR?
        # Check DIR field if ONEWAY missing
        if 'ONEWAY' not in row and 'DIR' in row:
             oneway = str(row['DIR']) # 0=bi, 1=one? need check. Assuming 0 is bi for now.

        
        for part in parts:
            start_pt = Point(part.coords[0])
            end_pt = Point(part.coords[-1])
            
            from_id = get_node_id(start_pt)
            to_id = get_node_id(end_pt)
            
            length = part.length
            link_id = f"link_{idx}"
            if len(parts) > 1: link_id += f"_{parts.index(part)}"
            
            # Create Link
            # Forward
            SubElement(links_elem, 'link', {
                'id': str(link_id),
                'from': str(from_id),
                'to': str(to_id),
                'length': f"{length:.2f}",
                'freespeed': f"{freespeed:.2f}",
                'capacity': f"{cap_lane * lanes}",
                'permlanes': f"{lanes}",
                'modes': "car,bus"  # User mentioned "bus" in filename, ensuring bus mode
            })
            links_count += 1
            
            # Reverse (if not oneway - simplistic check)
            # Standard: if Oneway/Dir = 0, bidirectional.
            if oneway == '0' or oneway is None:
                SubElement(links_elem, 'link', {
                    'id': str(link_id) + "_r",
                    'from': str(to_id),
                    'to': str(from_id),
                    'length': f"{length:.2f}",
                    'freespeed': f"{freespeed:.2f}",
                    'capacity': f"{cap_lane * lanes}",
                    'permlanes': f"{lanes}",
                    'modes': "car,bus"
                })
                links_count += 1

    # Add Nodes to XML
    print(f"Generating {len(nodes)} nodes...")
    for (x, y), nid in nodes.items():
        SubElement(nodes_elem, 'node', {
            'id': str(nid),
            'x': f"{x:.2f}",
            'y': f"{y:.2f}"
        })

    print(f"Total Links: {links_count}")
    print(f"Writing to {OUTPUT_XML}...")
    
    # Prettify and write
    rough_string = tostring(network, encoding='unicode')
    # reparsed = minidom.parseString(rough_string) # Large files crash minidom, ship direct string or manual format?
    # Skipping prettify for speed on large network, or just write directly.
    # But user might want readable. Let's try direct write.
    
    with gzip.open(OUTPUT_XML, 'wt', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n')
        f.write(rough_string)
        
    print("Done.")

if __name__ == "__main__":
    main()
