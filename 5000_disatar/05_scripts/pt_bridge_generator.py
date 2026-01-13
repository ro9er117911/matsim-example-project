import pandas as pd
import gzip
import xml.etree.ElementTree as ET
import math
import sys
from scipy.spatial import KDTree
import numpy as np

# Configuration
INPUT_NETWORK = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/merged_network_v6/network_v6_scc.xml.gz"
GAP_REPORT = "/Users/ro9air/matsim-example-project/5000_disatar/05_scripts/network_gaps_detailed.csv"
OUTPUT_NETWORK = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/merged_network_v6/network_v6_patched.xml.gz"
SEARCH_RADIUS_M = 200.0

# Proxy for "Main Road": Freespeed >= 36km/h (10.0 m/s) OR Capacity >= 600
MIN_MAIN_ROAD_SPEED = 10.0  
MIN_MAIN_ROAD_CAPACITY = 600.0

class NetworkPatcher:
    def __init__(self):
        self.nodes = {}  # id -> (x, y)
        self.links = {}  # id -> {from, to, freespeed, capacity}
        self.main_road_links = [] # list of link_ids
        self.new_links = []
        
        # KDTree Components
        self.main_road_coords = [] # list of [x, y]
        self.main_road_link_ids = [] # corresponding IDs
        self.tree = None
        
    def load_network(self, path):
        print(f"Loading network from {path}...")
        try:
            with gzip.open(path, 'rb') as f:
                context = ET.iterparse(f, events=('end',))
                for event, elem in context:
                    if elem.tag == 'node':
                        self.nodes[elem.get('id')] = (float(elem.get('x')), float(elem.get('y')))
                        elem.clear()
                    elif elem.tag == 'link':
                        lid = elem.get('id')
                        fs = float(elem.get('freespeed'))
                        cap = float(elem.get('capacity'))
                        
                        link_data = {
                            'id': lid,
                            'from': elem.get('from'),
                            'to': elem.get('to'),
                            'freespeed': fs,
                            'capacity': cap
                        }
                        self.links[lid] = link_data
                        
                        # Identify Main Roads
                        if fs >= MIN_MAIN_ROAD_SPEED or cap >= MIN_MAIN_ROAD_CAPACITY:
                            self.main_road_links.append(lid)
                            # Store coord for KDTree (using FROM node)
                            from_node = link_data['from']
                            if from_node in self.nodes:
                                self.main_road_coords.append(self.nodes[from_node])
                                self.main_road_link_ids.append(lid)
                        
                        elem.clear()
                        
            print(f"Network loaded. Nodes: {len(self.nodes)}, Links: {len(self.links)}")
            print(f"Identified {len(self.main_road_links)} potential main road links.")
            
            # Build KDTree
            if self.main_road_coords:
                print("Building KDTree for fast spatial search...")
                self.tree = KDTree(self.main_road_coords)
                
        except Exception as e:
            print(f"Error loading network: {e}")
            sys.exit(1)

    def find_nearest_main_roads(self, x, y, k=5):
        if not self.tree: return [], []
        
        # Query nearest k neighbors
        dists, idxs = self.tree.query([x, y], k=k, distance_upper_bound=SEARCH_RADIUS_M)
        
        candidates = []
        for d, i in zip(dists, idxs):
            if d == float('inf'): continue
            if i >= len(self.main_road_link_ids): continue # KDTree padding
            candidates.append((self.main_road_link_ids[i], d))
            
        return candidates

    def create_bridges(self, gaps_file):
        print(f"Reading gaps from {gaps_file}...")
        df = pd.read_csv(gaps_file)
        unique_handles = df['from_link'].unique()
        print(f"Found {len(unique_handles)} unique umbrella handles (problematic links).")
        
        count = 0
        for handle_id in unique_handles:
            handle_id = str(handle_id)
            if handle_id not in self.links:
                continue
                
            # Get the END node of the handle (where the bus is stuck)
            stuck_node_id = self.links[handle_id]['to']
            if stuck_node_id not in self.nodes: continue
            
            sx, sy = self.nodes[stuck_node_id]
            
            # Find nearest main road entry point candidates
            candidates = self.find_nearest_main_roads(sx, sy, k=10)
            
            best_target = None
            for target_link_id, dist in candidates:
                target_node_id = self.links[target_link_id]['from']
                
                # Validation Logic:
                # 1. Start Node != End Node (No self loop)
                if stuck_node_id == target_node_id:
                    continue
                
                # 2. Target Link != Handle Link (No connecting to self)
                if target_link_id == handle_id:
                    continue
                    
                # 3. Target Link != Reverse of Handle (No trivial U-turn if it's the same segment)
                # Assumes reverse link is named {id}_r or something, or check geometry.
                # Just checking connectivity is enough. If we add a link, does it help?
                # If we connect to the reverse link, it might be a valid U-turn.
                # However, usually we want to go *forward*.
                # Let's trust the spatial proximity.
                
                best_target = (target_link_id, target_node_id, dist)
                break
            
            if best_target:
                target_link_id, target_node_id, dist = best_target
                
                new_link = {
                    'id': f"pt_bridge_{handle_id}_to_{target_link_id}",
                    'from': stuck_node_id,
                    'to': target_node_id,
                    'length': max(dist, 1.0), 
                    'freespeed': 11.11, # 40km/h
                    'capacity': 9999,
                    'permlanes': 1,
                    'modes': "bus"
                }
                self.new_links.append(new_link)
                count += 1
                
        print(f"Generated {count} bridge links.")

    def save_patched_network(self):
        print(f"Saving patched network to {OUTPUT_NETWORK} (using ET)...")
        
        try:
            # We need to reload the tree to edit it, or keep it from load_network.
            # load_network used iterparse to save memory, so we don't have the full tree.
            # We will parse strictly for writing now.
            with gzip.open(INPUT_NETWORK, 'rb') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
            # Find the links element
            links_elem = root.find('links')
            if links_elem is None:
                # Some network files have links directly under root? No, usually <network><links>...
                # Or namespaced? MATSim defaults usually no namespace or simple one.
                print("Error: Could not find <links> element in network.")
                return

            print(f"Injecting {len(self.new_links)} new links...")
            for l in self.new_links:
                # <link id="1" from="1" to="2" length="10.0" freespeed="10.0" capacity="10.0" permlanes="1.0" oneway="1" modes="car" />
                attribs = {
                    'id': l['id'],
                    'from': l['from'],
                    'to': l['to'],
                    'length': f"{l['length']:.2f}",
                    'freespeed': str(l['freespeed']),
                    'capacity': str(l['capacity']),
                    'permlanes': str(l['permlanes']),
                    'oneway': "1",
                    'modes': l['modes']
                }
                ET.SubElement(links_elem, 'link', attribs)
                
            # Write back with DOCTYPE
            with gzip.open(OUTPUT_NETWORK, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
                f.write(b'<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n')
                tree.write(f, encoding='utf-8', xml_declaration=False, short_empty_elements=True)
                
            print("Done.")
            
        except Exception as e:
            print(f"Error saving network: {e}")
            import traceback
            traceback.print_exc()

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate bridge links for PT network")
    parser.add_argument("--input_network", required=True, help="Path to input network xml.gz")
    parser.add_argument("--gap_report", required=True, help="Path to network_gaps_detailed.csv")
    parser.add_argument("--output_network", required=True, help="Path to output network xml.gz")
    
    args = parser.parse_args()
    
    # Update global config or pass to class
    INPUT_NETWORK = args.input_network
    OUTPUT_NETWORK = args.output_network
    
    patcher = NetworkPatcher()
    patcher.load_network(INPUT_NETWORK)
    patcher.create_bridges(args.gap_report)
    patcher.save_patched_network()
