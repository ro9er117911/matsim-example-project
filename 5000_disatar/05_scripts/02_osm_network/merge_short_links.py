#!/usr/bin/env python3
"""
MATSim Network Short Link Merger

科學化合併超短 link，解決 storage capacity 不足問題。
保守原則：合併後 freespeed/capacity 取較小值，保留所有 modes。

Usage:
    python merge_short_links.py \
        --network network.xml.gz \
        --output network-merged.xml.gz \
        --min-length 15 \
        --report merge_report.txt
"""

import argparse
import gzip
import sys
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
from typing import Dict, Set, List, Tuple, Optional


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge ultra-short links in MATSim network",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--network", required=True, help="Input network file (.xml or .xml.gz)")
    parser.add_argument("--output", required=True, help="Output network file (.xml or .xml.gz)")
    parser.add_argument("--min-length", type=float, default=15.0, 
                        help="Minimum link length to preserve (default: 15m)")
    parser.add_argument("--report", help="Output report file path")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without writing output")
    return parser.parse_args()


class Node:
    def __init__(self, id: str, x: float, y: float, attrs: Dict = None):
        self.id = id
        self.x = x
        self.y = y
        self.attrs = attrs or {}
        self.in_links: List[str] = []
        self.out_links: List[str] = []


class Link:
    def __init__(self, id: str, from_node: str, to_node: str, 
                 length: float, freespeed: float, capacity: float,
                 permlanes: float, modes: str, attrs: Dict = None):
        self.id = id
        self.from_node = from_node
        self.to_node = to_node
        self.length = length
        self.freespeed = freespeed
        self.capacity = capacity
        self.permlanes = permlanes
        self.modes = modes
        self.attrs = attrs or {}
        self.merged_into: Optional[str] = None  # If merged, which link


class Network:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[str, Link] = {}
        self.xml_header: str = ""
        self.network_attrs: Dict = {}
    
    def node_degree(self, node_id: str) -> Tuple[int, int]:
        """Return (in_degree, out_degree) for a node."""
        node = self.nodes.get(node_id)
        if not node:
            return (0, 0)
        return (len(node.in_links), len(node.out_links))
    
    def is_simple_pass_through(self, node_id: str) -> bool:
        """
        Check if node is a simple pass-through (degree 2: 1 in, 1 out).
        These nodes can potentially be removed when merging links.
        """
        in_deg, out_deg = self.node_degree(node_id)
        return in_deg == 1 and out_deg == 1


def open_file(path: str, mode: str = 'rt'):
    """Open file, handling gzip compression."""
    if path.endswith('.gz'):
        return gzip.open(path, mode, encoding='utf-8')
    return open(path, mode, encoding='utf-8')


def parse_network(network_file: str) -> Network:
    """Parse MATSim network XML file."""
    print(f"Parsing network: {network_file}")
    
    network = Network()
    
    with open_file(network_file) as f:
        tree = ET.parse(f)
        root = tree.getroot()
    
    # Parse nodes
    nodes_elem = root.find('nodes')
    for node_elem in nodes_elem.findall('node'):
        node_id = node_elem.get('id')
        x = float(node_elem.get('x'))
        y = float(node_elem.get('y'))
        
        attrs = {}
        for attr in node_elem.findall('attributes/attribute'):
            attrs[attr.get('name')] = attr.text
        
        network.nodes[node_id] = Node(node_id, x, y, attrs)
    
    # Parse links
    links_elem = root.find('links')
    for link_elem in links_elem.findall('link'):
        link_id = link_elem.get('id')
        from_node = link_elem.get('from')
        to_node = link_elem.get('to')
        length = float(link_elem.get('length', 0))
        freespeed = float(link_elem.get('freespeed', 0))
        capacity = float(link_elem.get('capacity', 0))
        permlanes = float(link_elem.get('permlanes', 1))
        modes = link_elem.get('modes', 'car')
        
        attrs = {}
        for attr in link_elem.findall('attributes/attribute'):
            name = attr.get('name')
            attrs[name] = attr.text
        
        link = Link(link_id, from_node, to_node, length, freespeed, 
                    capacity, permlanes, modes, attrs)
        network.links[link_id] = link
        
        # Update node connectivity
        if from_node in network.nodes:
            network.nodes[from_node].out_links.append(link_id)
        if to_node in network.nodes:
            network.nodes[to_node].in_links.append(link_id)
    
    print(f"  Loaded {len(network.nodes)} nodes, {len(network.links)} links")
    return network


def analyze_short_links(network: Network, min_length: float) -> Dict:
    """Analyze short links and identify candidates for merging."""
    stats = {
        'total_links': len(network.links),
        'short_links': 0,
        'mergeable_links': 0,
        'unmergeable_short': 0,
        'length_distribution': defaultdict(int),
        'mergeable_by_length': defaultdict(int),
    }
    
    mergeable = []
    unmergeable = []
    
    for link_id, link in network.links.items():
        # Categorize by length
        if link.length < 5:
            stats['length_distribution']['< 5m'] += 1
        elif link.length < 10:
            stats['length_distribution']['5-10m'] += 1
        elif link.length < 15:
            stats['length_distribution']['10-15m'] += 1
        elif link.length < 30:
            stats['length_distribution']['15-30m'] += 1
        else:
            stats['length_distribution']['>= 30m'] += 1
        
        if link.length >= min_length:
            continue
            
        stats['short_links'] += 1
        
        # Check if to_node is a simple pass-through
        to_node = link.to_node
        if network.is_simple_pass_through(to_node):
            # Find the outgoing link from to_node
            out_links = network.nodes[to_node].out_links
            if len(out_links) == 1:
                next_link = network.links[out_links[0]]
                # Can merge if modes are compatible
                if set(link.modes.split(',')) == set(next_link.modes.split(',')):
                    stats['mergeable_links'] += 1
                    if link.length < 5:
                        stats['mergeable_by_length']['< 5m'] += 1
                    elif link.length < 10:
                        stats['mergeable_by_length']['5-10m'] += 1
                    else:
                        stats['mergeable_by_length']['10-15m'] += 1
                    mergeable.append(link_id)
                    continue
        
        stats['unmergeable_short'] += 1
        unmergeable.append(link_id)
    
    stats['mergeable_list'] = mergeable
    stats['unmergeable_list'] = unmergeable
    
    return stats


def merge_links(network: Network, min_length: float) -> Tuple[Network, Dict]:
    """
    Merge short links into their successor links.
    Returns updated network and merge statistics.
    """
    stats = analyze_short_links(network, min_length)
    
    merged_count = 0
    removed_nodes = set()
    removed_links = set()
    
    # Process mergeable links
    for link_id in stats['mergeable_list']:
        link = network.links.get(link_id)
        if not link or link.merged_into:
            continue
            
        to_node = link.to_node
        out_links = network.nodes[to_node].out_links
        
        if len(out_links) != 1:
            continue
            
        next_link_id = out_links[0]
        next_link = network.links.get(next_link_id)
        
        if not next_link or next_link.merged_into:
            continue
        
        # Merge: extend next_link to start from link's from_node
        next_link.from_node = link.from_node
        next_link.length += link.length
        
        # Conservative: take minimum freespeed and capacity
        next_link.freespeed = min(link.freespeed, next_link.freespeed)
        next_link.capacity = min(link.capacity, next_link.capacity)
        next_link.permlanes = min(link.permlanes, next_link.permlanes)
        
        # Merge attributes (keep both, prefer original)
        for key, val in link.attrs.items():
            if key not in next_link.attrs:
                next_link.attrs[key] = val
        
        # Mark as merged
        link.merged_into = next_link_id
        removed_links.add(link_id)
        removed_nodes.add(to_node)
        merged_count += 1
        
        # Update node connectivity
        from_node = network.nodes.get(link.from_node)
        if from_node:
            if link_id in from_node.out_links:
                from_node.out_links.remove(link_id)
            if next_link_id not in from_node.out_links:
                from_node.out_links.append(next_link_id)
    
    stats['merged_count'] = merged_count
    stats['removed_nodes'] = len(removed_nodes)
    stats['removed_links'] = len(removed_links)
    
    # Remove merged links and nodes from network
    for link_id in removed_links:
        del network.links[link_id]
    for node_id in removed_nodes:
        del network.nodes[node_id]
    
    return network, stats


def write_network(network: Network, output_file: str):
    """Write network to MATSim XML format."""
    print(f"Writing network: {output_file}")
    
    root = ET.Element('network')
    
    # Nodes
    nodes_elem = ET.SubElement(root, 'nodes')
    for node_id, node in sorted(network.nodes.items()):
        node_elem = ET.SubElement(nodes_elem, 'node', {
            'id': node_id,
            'x': str(node.x),
            'y': str(node.y)
        })
        if node.attrs:
            attrs_elem = ET.SubElement(node_elem, 'attributes')
            for name, value in node.attrs.items():
                attr_elem = ET.SubElement(attrs_elem, 'attribute', {'name': name, 'class': 'java.lang.String'})
                attr_elem.text = value
    
    # Links
    links_elem = ET.SubElement(root, 'links')
    for link_id, link in sorted(network.links.items()):
        link_elem = ET.SubElement(links_elem, 'link', {
            'id': link_id,
            'from': link.from_node,
            'to': link.to_node,
            'length': str(link.length),
            'freespeed': str(link.freespeed),
            'capacity': str(link.capacity),
            'permlanes': str(link.permlanes),
            'modes': link.modes
        })
        if link.attrs:
            attrs_elem = ET.SubElement(link_elem, 'attributes')
            for name, value in link.attrs.items():
                if value is not None:
                    attr_elem = ET.SubElement(attrs_elem, 'attribute', {'name': name, 'class': 'java.lang.String'})
                    attr_elem.text = str(value)
    
    # Write with proper formatting
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n'
    
    if output_file.endswith('.gz'):
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write(xml_header)
            tree.write(f, encoding='unicode')
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_header)
            tree.write(f, encoding='unicode')
    
    print(f"  Written {len(network.nodes)} nodes, {len(network.links)} links")


def write_report(stats: Dict, report_file: str):
    """Write merge statistics report."""
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("MATSim Network Short Link Merger Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("## Original Network Statistics\n\n")
        f.write(f"Total links: {stats['total_links']}\n")
        f.write(f"Short links (< min_length): {stats['short_links']}\n")
        f.write(f"  - Mergeable: {stats['mergeable_links']}\n")
        f.write(f"  - Unmergeable: {stats['unmergeable_short']}\n\n")
        
        f.write("## Length Distribution (Before)\n\n")
        for bucket, count in sorted(stats['length_distribution'].items()):
            f.write(f"  {bucket}: {count}\n")
        
        f.write("\n## Merge Results\n\n")
        f.write(f"Links merged: {stats.get('merged_count', 0)}\n")
        f.write(f"Nodes removed: {stats.get('removed_nodes', 0)}\n")
        f.write(f"Links removed: {stats.get('removed_links', 0)}\n")
        
        f.write("\n## Mergeable by Length\n\n")
        for bucket, count in sorted(stats['mergeable_by_length'].items()):
            f.write(f"  {bucket}: {count}\n")
        
        f.write("\n" + "=" * 60 + "\n")
    
    print(f"Report written: {report_file}")


def main():
    args = parse_args()
    
    print("=" * 60)
    print("MATSim Network Short Link Merger")
    print("=" * 60)
    print(f"Min length: {args.min_length}m")
    print()
    
    # Parse network
    network = parse_network(args.network)
    
    # Analyze and merge
    if args.dry_run:
        stats = analyze_short_links(network, args.min_length)
        print("\n[DRY RUN] Analysis only, no changes made")
    else:
        network, stats = merge_links(network, args.min_length)
        
        # Verify remaining short links
        remaining = sum(1 for l in network.links.values() if l.length < args.min_length)
        print(f"\nRemaining short links: {remaining}")
    
    # Print summary
    print("\n" + "-" * 40)
    print("Summary:")
    print(f"  Original links: {stats['total_links']}")
    print(f"  Short links (< {args.min_length}m): {stats['short_links']}")
    print(f"  Mergeable: {stats['mergeable_links']}")
    print(f"  Actually merged: {stats.get('merged_count', 'N/A')}")
    print("-" * 40)
    
    # Write output
    if not args.dry_run:
        write_network(network, args.output)
    
    if args.report:
        write_report(stats, args.report)
    
    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
