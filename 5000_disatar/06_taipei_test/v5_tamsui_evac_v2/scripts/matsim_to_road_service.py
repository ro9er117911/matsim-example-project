import argparse
import gzip
import json
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from pyproj import Transformer
import sys

def calculate_los(vc):
    if vc < 0.3: return 'A'
    if vc < 0.5: return 'B'
    if vc < 0.7: return 'C'
    if vc < 0.8: return 'D'
    if vc < 1.0: return 'E'
    return 'F'

def convert_streaming(congestion_file, network_file, output_file):
    print(f"Loading congestion data: {congestion_file}")
    df_cong = pd.read_csv(congestion_file)
    id_col = next((c for c in ['id', 'link_id', 'linkId'] if c in df_cong.columns), None)
    if not id_col:
        print(f"Error: No link ID column found in {congestion_file}")
        return
    
    cong_data = dict(zip(df_cong[id_col].astype(str), df_cong['volume']))
    del df_cong
    
    print(f"Parsing network and streaming GeoJSON output: {network_file}")
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    nodes = {}
    
    if network_file.endswith('.gz'):
        f = gzip.open(network_file, 'rt', encoding='utf-8')
    else:
        f = open(network_file, 'r', encoding='utf-8')
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        f_out.write('{"type": "FeatureCollection", "features": [\n')
        
        node_count = 0
        link_count = 0
        saved_count = 0
        
        context = ET.iterparse(f, events=('end',))
        for event, elem in context:
            if elem.tag == 'node':
                nid = elem.get('id')
                # Save as tuple for memory efficiency
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
                
                if lid in cong_data:
                    from_node = elem.get('from')
                    to_node = elem.get('to')
                    
                    if from_node in nodes and to_node in nodes:
                        flow = cong_data[lid]
                        capacity = float(elem.get('capacity', 0))
                        length = float(elem.get('length'))
                        lanes = float(elem.get('permlanes', 1))
                        
                        road_name = "Unknown"
                        road_class = "Unknown"
                        road_id = "Unknown"
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
                        
                        if saved_count > 0:
                            f_out.write(',\n')
                        json.dump(feature, f_out)
                        saved_count += 1
                
                elem.clear()
        
        f_out.write('\n]}')
    
    f.close()
    print(f"Done. Processed: {node_count} nodes, {link_count} links. Saved {saved_count} features to {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--congestion', required=True)
    parser.add_argument('--network', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    convert_streaming(args.congestion, args.network, args.output)

if __name__ == "__main__":
    main()
