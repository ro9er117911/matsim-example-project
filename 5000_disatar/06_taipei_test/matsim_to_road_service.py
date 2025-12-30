import argparse
import gzip
import json
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from pyproj import Transformer
import sys
import os

def calculate_los(vc):
    if vc < 0.3: return 'A'
    if vc < 0.5: return 'B'
    if vc < 0.7: return 'C'
    if vc < 0.8: return 'D'
    if vc < 1.0: return 'E'
    return 'F'

def is_major_road(road_class, freespeed):
    # Hierarchy definition
    major_types = {
        'motorway', 'motorway_link',
        'trunk', 'trunk_link',
        'primary', 'primary_link',
        'secondary', 'secondary_link'
    }
    if str(road_class).lower() in major_types:
        return True
    
    # Fallback for SHP classification
    if freespeed >= 11.0:
        return True
        
    return False

def load_shp_attributes(shp_path):
    try:
        import geopandas as gpd
        print(f"Loading SHP attributes from {shp_path}...")
        gdf = gpd.read_file(shp_path)
        
        # Mapping: LinkID -> {attr: value}
        attr_map = {}
        for _, row in gdf.iterrows():
            link_id = str(row.get('ROADSEGID', ''))
            if link_id:
                attr_map[link_id] = {
                    'RoadName': str(row.get('ROADNAME', 'Unknown')),
                    'RoadClassName': str(row.get('ROADCLASS1', 'Unknown')),
                    'RoadID': link_id
                }
        print(f"  Loaded attributes for {len(attr_map)} records.")
        return attr_map
    except Exception as e:
        print(f"Warning: Could not load SHP attributes: {e}")
        return {}

def convert_hierarchical(congestion_file, network_file, output_base_dir, shp_path=None):
    # Load SHP attributes if provided
    shp_attrs = load_shp_attributes(shp_path) if shp_path else {}

    print(f"Loading congestion data: {congestion_file}")
    df_cong = pd.read_csv(congestion_file)
    id_col = next((c for c in ['id', 'link_id', 'linkId'] if c in df_cong.columns), None)
    if not id_col:
        print(f"Error: No link ID column found in {congestion_file}")
        return
    
    cong_data = dict(zip(df_cong[id_col].astype(str), df_cong['volume']))
    del df_cong
    
    os.makedirs(output_base_dir, exist_ok=True)
    out_all_path = os.path.join(output_base_dir, "road_service_all.geojson")
    out_major_path = os.path.join(output_base_dir, "road_service_major.geojson")
    out_minor_path = os.path.join(output_base_dir, "road_service_minor.geojson")

    print(f"Parsing network and streaming hierarchical GeoJSONs to {output_base_dir}")
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    nodes = {}
    
    if network_file.endswith('.gz'):
        f_net = gzip.open(network_file, 'rt', encoding='utf-8')
    else:
        f_net = open(network_file, 'r', encoding='utf-8')
    
    # Open three file handles
    f_all = open(out_all_path, 'w', encoding='utf-8')
    f_major = open(out_major_path, 'w', encoding='utf-8')
    f_minor = open(out_minor_path, 'w', encoding='utf-8')
    
    for f in [f_all, f_major, f_minor]:
        f.write('{"type": "FeatureCollection", "features": [\n')
    
    counts = {"all": 0, "major": 0, "minor": 0}
    node_count = 0
    link_count = 0
    
    context = ET.iterparse(f_net, events=('end',))
    for event, elem in context:
        if elem.tag == 'node':
            nid = elem.get('id')
            nodes[nid] = transformer.transform(float(elem.get('x')), float(elem.get('y')))
            node_count += 1
            if node_count % 100000 == 0:
                print(f"  Processed {node_count} nodes...")
            elem.clear()
            
        elif elem.tag == 'link':
            lid = elem.get('id')
            link_count += 1
            if link_count % 50000 == 0:
                print(f"  Processed {link_count} links...")
            
            # lid might have _r or _reverse suffix
            base_lid = lid
            for suffix in ['_r', '_reverse']:
                if lid.endswith(suffix):
                    base_lid = lid[:-len(suffix)]
                    break
            
            if lid in cong_data:
                from_node = elem.get('from')
                to_node = elem.get('to')
                
                if from_node in nodes and to_node in nodes:
                    flow = cong_data[lid]
                    capacity = float(elem.get('capacity', 0))
                    length = float(elem.get('length'))
                    lanes = float(elem.get('permlanes', 1))
                    freespeed = float(elem.get('freespeed', 0))
                    
                    # 1. Try SHP attributes first
                    shp_info = shp_attrs.get(base_lid, {})
                    road_name = shp_info.get('RoadName', "Unknown")
                    road_class = shp_info.get('RoadClassName', "Unknown")
                    road_id = shp_info.get('RoadID', "Unknown")
                    
                    # 2. Then try network attributes if SHP didn't have it
                    if road_name == "Unknown":
                        attrs_elem = elem.find('attributes')
                        if attrs_elem is not None:
                            for attr in attrs_elem.findall('attribute'):
                                name = attr.get('name')
                                if name == 'osm:way:name':
                                    road_name = attr.text if attr.text else "Unknown"
                                elif name == 'osm:way:highway':
                                    road_class = attr.text if attr.text else "Unknown"
                                elif name == 'osm:way:id':
                                    road_id = attr.text if attr.text else "Unknown"
                    
                    vc = round(flow / capacity, 2) if capacity > 0 else 0
                    length_km = round(length / 1000, 4)
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [nodes[from_node], nodes[to_node]]
                        },
                        "properties": {
                            'RoadID': road_id,
                            'LinkID': lid,
                            'RoadName': road_name,
                            'RoadClassName': road_class,
                            'Length': length_km,
                            'lane': lanes,
                            'factor': 1.0,
                            'PCU_hr_km': round(flow * length_km, 2),
                            'count': int(flow),
                            'flow': flow,
                            'V/C': vc,
                            'log_V/C': round(np.log10(vc + 1), 4),
                            'LOS': calculate_los(vc)
                        }
                    }
                    
                    feat_json = json.dumps(feature, ensure_ascii=False)
                    
                    # Write to ALL
                    if counts["all"] > 0: f_all.write(',\n')
                    f_all.write(feat_json)
                    counts["all"] += 1
                    
                    # Write to Major or Minor
                    if is_major_road(road_class, freespeed):
                        if counts["major"] > 0: f_major.write(',\n')
                        f_major.write(feat_json)
                        counts["major"] += 1
                    else:
                        if counts["minor"] > 0: f_minor.write(',\n')
                        f_minor.write(feat_json)
                        counts["minor"] += 1
                
            elem.clear()
    
    for f in [f_all, f_major, f_minor]:
        f.write('\n]}')
        f.close()
    f_net.close()
    
    print(f"Done. Processed: {node_count} nodes, {link_count} links.")
    print(f"Saved All: {counts['all']} features to {out_all_path}")
    print(f"Saved Major: {counts['major']} features to {out_major_path}")
    print(f"Saved Minor: {counts['minor']} features to {out_minor_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--congestion', required=True)
    parser.add_argument('--network', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--shp', help='Optional original SHP file to join road names')
    args = parser.parse_args()
    
    convert_hierarchical(args.congestion, args.network, args.output_dir, args.shp)

if __name__ == "__main__":
    main()
