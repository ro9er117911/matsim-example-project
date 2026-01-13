import pandas as pd
import gzip
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from pyproj import Transformer

def generate_gap_geojson(network_path, gap_csv_path, output_geojson):
    print(f"Loading network: {network_path}")
    nodes = {}
    links = {}
    
    # Initialize transformer: EPSG:3826 (TWD97 meters) to EPSG:4326 (WGS84 lon, lat)
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    
    # Use iterative parsing to save memory
    with gzip.open(network_path, 'rb') as f:
        context = ET.iterparse(f, events=('end',))
        for event, elem in context:
            if elem.tag == 'node':
                x = float(elem.get('x'))
                y = float(elem.get('y'))
                # Transform to [lon, lat]
                lon, lat = transformer.transform(x, y)
                nodes[elem.get('id')] = (lon, lat)
                elem.clear() # Free memory
            elif elem.tag == 'link':
                links[elem.get('id')] = {
                    'from': elem.get('from'),
                    'to': elem.get('to')
                }
                elem.clear()

    print(f"Loading gaps: {gap_csv_path}")
    if not Path(gap_csv_path).exists():
        print(f"Error: {gap_csv_path} not found. Please run diagnose_network_gaps.py first.")
        return

    gaps_df = pd.read_csv(gap_csv_path)
    
    features = []
    
    for _, row in gaps_df.iterrows():
        from_link_id = str(row['from_link'])
        to_link_id = str(row['to_link'])
        
        if from_link_id in links and to_link_id in links:
            node_out_id = links[from_link_id]['to']
            node_in_id = links[to_link_id]['from']
            
            if node_out_id in nodes and node_in_id in nodes:
                coord_out = nodes[node_out_id]
                coord_in = nodes[node_in_id]
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [coord_out, coord_in]
                    },
                    "properties": {
                        "from_link": from_link_id,
                        "to_link": to_link_id,
                        "gap_count": int(row['count']) if 'count' in row else 1,
                        "route_num": str(row['route_num']) if 'route_num' in row else "unknown"
                    }
                })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_geojson, 'w') as f:
        json.dump(geojson, f)
    
    print(f"Success! Exported {len(features)} transformed gaps to {output_geojson}")

if __name__ == "__main__":
    net = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/merged_network_v6/network_v6_scc.xml.gz"
    gaps = "/Users/ro9air/matsim-example-project/5000_disatar/05_scripts/network_gaps_detailed.csv"
    out = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/network_gaps_visualization.geojson"
    
    generate_gap_geojson(net, gaps, out)
