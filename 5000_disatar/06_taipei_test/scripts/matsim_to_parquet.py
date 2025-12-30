import argparse
import gzip
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from pyproj import Transformer
from collections import defaultdict
import pyarrow as pa
import pyarrow.parquet as pq

# Coordinate transformer: EPSG:3826 -> EPSG:4326
transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)

def parse_network(network_file):
    print(f"Parsing network: {network_file}")
    nodes = {}
    links = {}
    if network_file.endswith('.gz'):
        f = gzip.open(network_file, 'rt', encoding='utf-8')
    else:
        f = open(network_file, 'r', encoding='utf-8')
    
    context = ET.iterparse(f, events=('end',))
    for event, elem in context:
        if elem.tag == 'node':
            nid = elem.get('id')
            x, y = float(elem.get('x')), float(elem.get('y'))
            lon, lat = transformer.transform(x, y)
            nodes[nid] = (lon, lat)
        elif elem.tag == 'link':
            lid = elem.get('id')
            from_node = elem.get('from')
            to_node = elem.get('to')
            if from_node in nodes and to_node in nodes:
                links[lid] = (nodes[from_node], nodes[to_node])
        elem.clear()
    f.close()
    return links

def parse_events(events_file, links):
    print(f"Parsing events: {events_file}")
    agent_paths = defaultdict(list)
    agent_times = defaultdict(list)
    agent_modes = defaultdict(list)
    
    # Mode mapping: 1=car, 2=walk/pt
    mode_map = {'car': 1, 'walk': 2, 'pt': 2, 'bus': 2, 'subway': 2}
    
    if events_file.endswith('.gz'):
        f = gzip.open(events_file, 'rt', encoding='utf-8')
    else:
        f = open(events_file, 'r', encoding='utf-8')
    
    # Track current position of agents
    agent_current_link = {}
    
    context = ET.iterparse(f, events=('end',))
    for event, elem in context:
        if elem.tag == 'event':
            etype = elem.get('type')
            time = float(elem.get('time'))
            person = elem.get('person')
            
            if etype == 'leftLink':
                lid = elem.get('link')
                if lid in links and person:
                    from_coord, to_coord = links[lid]
                    # Add point at start of link
                    agent_paths[person].extend([from_coord[0], from_coord[1]])
                    agent_times[person].append(int(time))
                    agent_modes[person].append(1) # Default to car for now, can be improved
            
            elif etype == 'arrival':
                lid = elem.get('link')
                if lid in links and person:
                    from_coord, to_coord = links[lid]
                    # Add point at end of link
                    agent_paths[person].extend([to_coord[0], to_coord[1]])
                    agent_times[person].append(int(time))
                    agent_modes[person].append(1)

        elem.clear()
    f.close()
    return agent_paths, agent_times, agent_modes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', required=True)
    parser.add_argument('--network', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    links = parse_network(args.network)
    paths, times, modes = parse_events(args.events, links)
    
    data = []
    for person in paths:
        if len(times[person]) < 2: continue
        data.append({
            'paths': paths[person],
            'timestamps': times[person],
            'modes': modes[person][:len(times[person])]
        })
    
    df = pd.DataFrame(data)
    # Ensure modes match timestamp length
    table = pa.Table.from_pandas(df)
    pq.write_table(table, args.output)
    print(f"Successfully wrote {len(df)} trajectories to {args.output}")

if __name__ == "__main__":
    main()
