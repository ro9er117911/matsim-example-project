#!/usr/bin/env python3
"""
Clean MATSim network file by removing duplicate nodes.
This fixes the "There exists already a node with id" error.
"""

import gzip
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict

def clean_network(input_file, output_file):
    """Remove duplicate nodes from MATSim network file."""
    
    # Read the file
    if input_file.endswith('.gz'):
        with gzip.open(input_file, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(input_file)
    
    root = tree.getroot()
    
    # Find the nodes section
    nodes_elem = root.find('nodes')
    if nodes_elem is None:
        print(f"Error: No 'nodes' element found in {input_file}")
        return False
    
    # Track seen node IDs
    seen_node_ids = set()
    nodes_to_remove = []
    duplicate_count = 0
    
    for node in nodes_elem.findall('node'):
        node_id = node.get('id')
        if node_id in seen_node_ids:
            nodes_to_remove.append(node)
            duplicate_count += 1
            print(f"  Removing duplicate node: {node_id}")
        else:
            seen_node_ids.add(node_id)
    
    for node in nodes_to_remove:
        nodes_elem.remove(node)
    
    print(f"Removed {duplicate_count} duplicate nodes")
    print(f"Remaining nodes: {len(nodes_elem.findall('node'))}")
    
    # Write output
    if output_file.endswith('.gz'):
        import io
        xml_str = ET.tostring(root, encoding='unicode')
        # Add XML declaration
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n' + xml_str
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write(xml_str)
    else:
        # Add XML declaration
        xml_str = ET.tostring(root, encoding='unicode')
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n' + xml_str
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    
    print(f"Written to: {output_file}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: clean_network_duplicates.py <input.xml[.gz]> <output.xml[.gz]>")
        sys.exit(1)
    
    clean_network(sys.argv[1], sys.argv[2])
