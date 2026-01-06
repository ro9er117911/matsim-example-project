#!/usr/bin/env python3
"""
Network Connectivity Cleaner for PT Mapping

Preprocesses MATSim network to:
1. Remove disconnected components (keep only largest connected component)
2. Ensure all links have proper modes
3. Fix any orphan nodes

Run BEFORE pt2matsim mapping to avoid "No route found" errors.
"""

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, Tuple
import argparse


def find_connected_components(nodes: Set[str], edges: Dict[str, Tuple[str, str]]) -> list:
    """Find all connected components using BFS."""
    visited = set()
    components = []
    
    # Build adjacency list (undirected)
    adj = defaultdict(set)
    for link_id, (from_node, to_node) in edges.items():
        adj[from_node].add(to_node)
        adj[to_node].add(from_node)
    
    for start_node in nodes:
        if start_node in visited:
            continue
        
        # BFS from this node
        component = set()
        queue = [start_node]
        
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        if component:
            components.append(component)
    
    return components


def clean_network(input_path: Path, output_path: Path, mode_filter: str = None):
    """
    Clean network by keeping only the largest connected component.
    """
    print(f"\n=== Network Connectivity Cleaner ===")
    print(f"Input: {input_path}")
    
    # Parse network
    if str(input_path).endswith('.gz'):
        with gzip.open(input_path, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(input_path)
    
    root = tree.getroot()
    
    # Collect nodes and links
    nodes_elem = root.find('.//nodes')
    links_elem = root.find('.//links')
    
    all_nodes = {}  # id -> element
    for node in list(nodes_elem):
        all_nodes[node.attrib['id']] = node
    
    all_links = {}  # id -> (element, from, to)
    edges = {}  # id -> (from, to) for connectivity analysis
    
    for link in list(links_elem):
        link_id = link.attrib['id']
        from_node = link.attrib['from']
        to_node = link.attrib['to']
        modes = link.attrib.get('modes', '')
        
        # Skip links without proper modes if filtering
        if mode_filter and mode_filter not in modes:
            continue
            
        all_links[link_id] = (link, from_node, to_node)
        edges[link_id] = (from_node, to_node)
    
    print(f"  Total nodes: {len(all_nodes)}")
    print(f"  Total links: {len(all_links)}")
    
    # Find connected components
    node_ids_in_links = set()
    for link_id, (from_node, to_node) in edges.items():
        node_ids_in_links.add(from_node)
        node_ids_in_links.add(to_node)
    
    components = find_connected_components(node_ids_in_links, edges)
    
    print(f"\n  Connected components: {len(components)}")
    if components:
        sizes = sorted([len(c) for c in components], reverse=True)
        print(f"  Component sizes (top 5): {sizes[:5]}")
    
    # Keep only largest component
    if not components:
        print("  ERROR: No components found!")
        return
    
    largest_component = max(components, key=len)
    print(f"\n  Keeping largest component: {len(largest_component)} nodes")
    
    # Remove nodes not in largest component
    nodes_to_remove = []
    for node_id, node_elem in all_nodes.items():
        if node_id not in largest_component:
            nodes_to_remove.append(node_elem)
    
    for node_elem in nodes_to_remove:
        nodes_elem.remove(node_elem)
    
    # Remove links not in largest component
    links_to_remove = []
    for link_id, (link_elem, from_node, to_node) in all_links.items():
        if from_node not in largest_component or to_node not in largest_component:
            links_to_remove.append(link_elem)
    
    for link_elem in links_to_remove:
        try:
            links_elem.remove(link_elem)
        except ValueError:
            pass  # Already removed
    
    # Also remove orphan links (pointing to non-existent nodes)
    remaining_node_ids = {n.attrib['id'] for n in nodes_elem}
    orphan_links = []
    for link in list(links_elem):
        if link.attrib['from'] not in remaining_node_ids or link.attrib['to'] not in remaining_node_ids:
            orphan_links.append(link)
    
    for link in orphan_links:
        links_elem.remove(link)
    
    final_nodes = len(list(nodes_elem))
    final_links = len(list(links_elem))
    
    print(f"\n  Removed {len(nodes_to_remove)} disconnected nodes")
    print(f"  Removed {len(links_to_remove) + len(orphan_links)} disconnected/orphan links")
    print(f"\n  Final: {final_nodes} nodes, {final_links} links")
    
    # Write output
    if str(output_path).endswith('.gz'):
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            tree.write(f, encoding='unicode', xml_declaration=True)
    else:
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\n✅ Cleaned network written to: {output_path}")
    
    return final_nodes, final_links


def main():
    parser = argparse.ArgumentParser(description='Clean network connectivity for PT mapping')
    parser.add_argument('--input', '-i', required=True, help='Input network file')
    parser.add_argument('--output', '-o', required=True, help='Output cleaned network file')
    parser.add_argument('--mode', '-m', default=None, help='Filter by mode (e.g., car, bus)')
    
    args = parser.parse_args()
    clean_network(Path(args.input), Path(args.output), args.mode)


if __name__ == '__main__':
    main()
