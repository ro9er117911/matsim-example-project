#!/usr/bin/env python3
"""
Convert MATSim Network to WGS84 GeoJSON.
"""

import xml.etree.ElementTree as ET
import gzip
import json
import argparse
from pyproj import Transformer
from shapely.geometry import LineString, mapping

def load_whitelist(csv_files):
    ids = set()
    for fpath in csv_files:
        if not fpath: continue
        try:
            import pandas as pd
            df = pd.read_csv(fpath)
            if 'linkId' in df.columns:
                ids.update(df['linkId'].astype(str))
            elif 'link_id' in df.columns:
                ids.update(df['link_id'].astype(str))
            elif 'id' in df.columns:
                ids.update(df['id'].astype(str))
            print(f"Loaded {len(df)} links from {fpath}")
        except Exception as e:
            print(f"Warning: Could not read whitelist file {fpath}: {e}")
    return ids

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network', required=True, help='Input network.xml.gz')
    parser.add_argument('--output', required=True, help='Output network.geojson')
    parser.add_argument('--whitelist', nargs='*', help='CSV files containing active linkIds')
    args = parser.parse_args()
    
    active_links = set()
    if args.whitelist:
        print("Loading active link whitelist...")
        active_links = load_whitelist(args.whitelist)
        print(f"Total unique active links: {len(active_links)}")
    
    print(f"Reading {args.network}...")
    
    if args.network.endswith('.gz'):
        f = gzip.open(args.network, 'rt', encoding='utf-8')
    else:
        f = open(args.network, 'r', encoding='utf-8')
        
    nodes = {}
    features = []
    
    # Transformer EPSG:3826 -> EPSG:4326
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    
    context = ET.iterparse(f, events=('end',))
    for event, elem in context:
        if elem.tag == 'node':
            nid = elem.get('id')
            x = float(elem.get('x'))
            y = float(elem.get('y'))
            # Transform to WGS84
            lon, lat = transformer.transform(x, y)
            nodes[nid] = (lon, lat)
            
        elif elem.tag == 'link':
            lid = elem.get('id')
            
            # Filter if whitelist exists
            if active_links and lid not in active_links:
                elem.clear()
                continue
                
            from_node = elem.get('from')
            to_node = elem.get('to')
            
            if from_node in nodes and to_node in nodes:
                coords = [nodes[from_node], nodes[to_node]]
                geom = LineString(coords)
                
                features.append({
                    "type": "Feature",
                    "geometry": mapping(geom),
                    "properties": {
                        "id": lid,
                    }
                })
            
        elem.clear()
        
    f.close()
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    print(f"Writing {len(features)} links to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
        
    print("Done.")

if __name__ == "__main__":
    main()
