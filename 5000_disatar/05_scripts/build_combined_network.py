#!/usr/bin/env python3
"""
Build a combined MATSim network from multiple Taiwan GIS Shapefile directories.
Supports Taipei (A_*) and New Taipei (F_*) data formats.
"""
import argparse
import gzip
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Mapping from ROADCLASS1 codes to MATSim parameters
# (freespeed_m_s, capacity_veh_h_lane, lanes, description)
ROAD_CODE_PARAMS = {
    'HW': (33.3, 2000, 3, '國道 National Highway'),
    '1U': (25.0, 1500, 2, '省道 Provincial Road'),
    '1W': (25.0, 1500, 2, '省道 Provincial Road'),
    '1E': (25.0, 1500, 2, '省道 Provincial Road'),
    '2U': (20.0, 1200, 2, '快速道路/省道支線'),
    '2W': (20.0, 1200, 2, '快速道路/省道支線'),
    '3U': (16.7, 1000, 2, '縣道 County Road'),
    '3W': (16.7, 1000, 2, '縣道 County Road'),
    '4W': (13.9, 800, 1, '鄉道 Township Road'),
    'RD': (11.1, 600, 1, '市區道路 Urban Street'),
    'AL': (8.3, 400, 1, '巷弄 Alley'),
    'default': (11.1, 600, 1, '預設 Default')
}

def get_road_params(road_class: str) -> Tuple[float, int, int]:
    params = ROAD_CODE_PARAMS.get(road_class, ROAD_CODE_PARAMS['default'])
    return params[0], params[1], params[2]

def prettify_xml(elem):
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def build_combined_network(
    input_dirs: List[Path],
    output_file: Path,
    modes: str = "car,walk",
    encoding: str = "cp950"
):
    all_nodes_gdf = []
    all_roads_gdf = []
    
    for input_dir in input_dirs:
        print(f"Searching for shapefiles in {input_dir}...")
        road_files = list(input_dir.glob("*_ROAD.shp"))
        node_files = list(input_dir.glob("*_RDNODE.shp"))
        
        if not road_files or not node_files:
            print(f"WARNING: No ROAD or RDNODE found in {input_dir}")
            continue
            
        print(f"Loading nodes: {node_files[0]}")
        all_nodes_gdf.append(gpd.read_file(node_files[0], encoding=encoding))
        
        print(f"Loading roads: {road_files[0]}")
        all_roads_gdf.append(gpd.read_file(road_files[0], encoding=encoding))
        
    if not all_nodes_gdf:
        print("ERROR: No data loaded.")
        return
        
    # Merge and drop duplicates
    nodes_gdf = pd.concat(all_nodes_gdf).drop_duplicates(subset=['NODEID'])
    roads_gdf = pd.concat(all_roads_gdf).drop_duplicates(subset=['ROADSEGID'])
    
    print(f"Total Unique Nodes: {len(nodes_gdf)}")
    print(f"Total Unique Roads: {len(roads_gdf)}")
    
    # Use a set for fast O(1) node lookup
    nodes_set = set(nodes_gdf['NODEID'].astype(str))
    
    print(f"Writing to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write gzipped XML manually for performance and to include DTD
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n')
        f.write('<network>\n')
        
        f.write('  <nodes>\n')
        for _, row in nodes_gdf.iterrows():
            f.write(f'    <node id="{row["NODEID"]}" x="{row.geometry.x:.2f}" y="{row.geometry.y:.2f}" />\n')
        f.write('  </nodes>\n')
        
        f.write('  <links>\n')
        links_created = 0
        for _, row in roads_gdf.iterrows():
            link_id = str(row['ROADSEGID'])
            from_node = str(row['FNODE'])
            to_node = str(row['TNODE'])
            
            if from_node not in nodes_set or to_node not in nodes_set:
                continue
                
            road_class = row['ROADCLASS1'] if 'ROADCLASS1' in row else 'default'
            freespeed, cap_per_lane, lanes = get_road_params(road_class)
            length = row.geometry.length
            capacity = int(cap_per_lane * lanes)
            lanes_int = int(lanes)
            
            # Forward Link
            f.write(f'    <link id="{link_id}" from="{from_node}" to="{to_node}" length="{length:.2f}" '
                    f'freespeed="{freespeed:.2f}" capacity="{capacity}" permlanes="{lanes_int}" modes="{modes}" />\n')
            links_created += 1
            
            # Reverse Link
            if str(row['DIR']) == '0':
                f.write(f'    <link id="{link_id}_r" from="{to_node}" to="{from_node}" length="{length:.2f}" '
                        f'freespeed="{freespeed:.2f}" capacity="{capacity}" permlanes="{lanes_int}" modes="{modes}" />\n')
                links_created += 1
        
        f.write('  </links>\n')
        f.write('</network>\n')
    
    print(f"Total Links Created: {links_created}")
    print("Done!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", nargs='+', required=True, help="Input directories")
    parser.add_argument("-o", "--output", required=True, help="Output XML file")
    parser.add_argument("--encoding", default="cp950")
    args = parser.parse_args()
    
    build_combined_network(
        [Path(d) for d in args.input],
        Path(args.output),
        encoding=args.encoding
    )

if __name__ == "__main__":
    main()
