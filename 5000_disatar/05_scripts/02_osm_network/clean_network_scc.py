#!/usr/bin/env python3
"""
Network Connectivity Cleaner (Strongly Connected Components)
==========================================================
Keeps only the Largest STRONGLY Connected Component (LSCC).
This ensures that from any node in the network, you can reach 
any other node and RETURN. This is critical for public transit 
routing to prevent vehicles from getting stuck in "one-way traps" 
or dead-ends.

Usage: python clean_network_scc.py -i input.xml.gz -o output.xml.gz -m car
"""

import gzip
import xml.etree.ElementTree as ET
import networkx as nx
import argparse
from pathlib import Path
import sys

def clean_network_scc(input_path, output_path, mode_filter='car'):
    print(f"\n=== Network SCC Cleaner (Directed) ===")
    print(f"Input: {input_path}")
    print(f"Mode: {mode_filter}")
    
    # 1. Parse Links to Build Graph
    print("Parsing network...")
    G = nx.DiGraph()
    
    # We need to store XML elements to write them back later
    # Memory optimization: Only store IDs in graph, keep elements in a dict
    # But for 270k nodes / 440k links, we can probably hold it in memory (approx 1-2GB RAM).
    
    tree = None
    if str(input_path).endswith('.gz'):
        with gzip.open(input_path, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(input_path)
    
    root = tree.getroot()
    links_elem = root.find('links')
    nodes_elem = root.find('nodes')
    
    if links_elem is None or nodes_elem is None:
        # Try namespaced version if standard fails
        # MATSim sometimes uses namespaces like {http://www.matsim.org/files/dtd/network_v2.dtd}
        root_tag = root.tag
        if '}' in root_tag:
            ns = root_tag.split('}')[0] + '}'
            links_elem = root.find(f'{ns}links')
            nodes_elem = root.find(f'{ns}nodes')
    
    if links_elem is None:
        print("Error: Could not find <links> element.")
        sys.exit(1)
        
    print(f"Total links in XML: {len(links_elem)}")
    
    # Build Graph
    for link in links_elem:
        lid = link.attrib['id']
        u = link.attrib['from']
        v = link.attrib['to']
        modes = link.attrib.get('modes', '')
        
        # Only add edge to graph if it supports the mode
        if mode_filter in modes:
            G.add_edge(u, v, id=lid)
            
    print(f"Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} links (mode: {mode_filter})")
    
    # 2. Find Largest Strongly Connected Component
    print("calculating strongly connected components...")
    sccs = list(nx.strongly_connected_components(G))
    print(f"Found {len(sccs)} strong components.")
    
    if not sccs:
        print("Error: No strong components found!")
        sys.exit(1)
        
    largest_scc = max(sccs, key=len)
    print(f"Largest SCC size: {len(largest_scc)} nodes")
    
    # 3. Filter XML Elements
    print("Filtering network...")
    
    # Remove Nodes
    nodes_to_remove = []
    # Identify nodes to keep (set for O(1) lookup)
    keep_nodes = set(largest_scc)
    
    for node in list(nodes_elem):
        if node.attrib['id'] not in keep_nodes:
            nodes_elem.remove(node)
            
    # Remove Links
    links_to_remove = []
    kept_links_count = 0
    removed_links_count = 0
    
    for link in list(links_elem):
        u = link.attrib['from']
        v = link.attrib['to']
        
        # Keep link ONLY if both ends are in the LSCC
        if u in keep_nodes and v in keep_nodes:
            # SYSTEMATIC FIX: Add 'bus' mode to any link that allows 'car'
            # This ensures that strictLinkRule=true works for PT mapping
            modes = link.attrib.get('modes', '')
            if 'car' in modes and 'bus' not in modes:
                modes += ',bus'
                link.attrib['modes'] = modes
                
            kept_links_count += 1
        else:
            links_elem.remove(link)
            removed_links_count += 1
            
    print(f"\nFinal Statistics:")
    print(f"  Nodes kept: {len(keep_nodes)}")
    print(f"  Links kept: {kept_links_count}")
    print(f"  Links removed: {removed_links_count}")
    
    # 4. Write Output
    print(f"Writing to {output_path}...")
    
    # Ensure DOCTYPE
    if str(output_path).endswith('.gz'):
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n')
            # Write the root element (excluding the xml declaration since we wrote it manually to ensure order/doctype)
            # ElementTree.write usually adds declaration if asked, but handling DOCTYPE is tricky.
            # Best way: keep it simple.
            
            # Use tostring for the tree
            # But that's memory heavy. Let's use write without declaration.
            tree.write(f, encoding='unicode', xml_declaration=False)
    else:
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
    print("✅ Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o', required=True)
    parser.add_argument('--mode', '-m', default='car')
    args = parser.parse_args()
    
    clean_network_scc(args.input, args.output, args.mode)
