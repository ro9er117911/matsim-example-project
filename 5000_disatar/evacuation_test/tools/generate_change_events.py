#!/usr/bin/env python3
"""
Phase 2: Generate NetworkChangeEvents for tsunami evacuation.

This script identifies roads near the coast (within hazard zone) and creates
MATSim NetworkChangeEvents to close them at a specified time (simulating tsunami arrival).

Usage:
    python3 generate_change_events.py \
        --network input/network_large.xml.gz \
        --hazard-center "25.18,121.44" \
        --hazard-radius 2.0 \
        --close-time 3600 \
        --output input/changeEvents.xml
"""
import argparse
import gzip
import xml.etree.ElementTree as ET
from xml.dom import minidom
import math


def wgs84_to_twd97_approx(lat, lon):
    """Approximate WGS84 to TWD97 conversion."""
    x = (lon - 121.0) * 111320 * math.cos(math.radians(lat)) + 250000
    y = lat * 110540
    return x, y


def twd97_to_wgs84_approx(x, y):
    """Approximate TWD97 to WGS84 conversion."""
    lat = y / 110540
    lon = (x - 250000) / (111320 * math.cos(math.radians(lat))) + 121.0
    return lat, lon


def distance_km(x1, y1, x2, y2):
    """Calculate distance in km between two TWD97 points."""
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2) / 1000


def parse_network(network_file):
    """Parse MATSim network and return links with their coordinates."""
    print(f"Reading network: {network_file}")
    
    if network_file.endswith('.gz'):
        with gzip.open(network_file, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(network_file)
    
    root = tree.getroot()
    
    # Parse nodes
    nodes = {}
    for node in root.findall('.//node'):
        node_id = node.get('id')
        x = float(node.get('x'))
        y = float(node.get('y'))
        nodes[node_id] = (x, y)
    
    print(f"  Nodes: {len(nodes)}")
    
    # Parse links
    links = []
    for link in root.findall('.//link'):
        link_id = link.get('id')
        from_node = link.get('from')
        to_node = link.get('to')
        
        if from_node in nodes and to_node in nodes:
            from_x, from_y = nodes[from_node]
            to_x, to_y = nodes[to_node]
            # Use midpoint for link location
            mid_x = (from_x + to_x) / 2
            mid_y = (from_y + to_y) / 2
            links.append({
                'id': link_id,
                'x': mid_x,
                'y': mid_y
            })
    
    print(f"  Links: {len(links)}")
    return links


def find_links_in_hazard_zone(links, center_lat, center_lon, radius_km):
    """Find links within the hazard zone."""
    center_x, center_y = wgs84_to_twd97_approx(center_lat, center_lon)
    
    affected_links = []
    for link in links:
        dist = distance_km(link['x'], link['y'], center_x, center_y)
        if dist <= radius_km:
            affected_links.append(link['id'])
    
    return affected_links


def format_time(seconds):
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def generate_change_events(affected_links, close_time, output_file):
    """Generate NetworkChangeEvents XML."""
    root = ET.Element('networkChangeEvents')
    root.set('xmlns', 'http://www.matsim.org/files/dtd')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation', 
             'http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/networkChangeEvents.xsd')
    
    # Add comment
    comment = ET.Comment(f' Tsunami road closure: {len(affected_links)} links closed at {format_time(close_time)} ')
    root.append(comment)
    
    # Create change event
    event = ET.SubElement(root, 'networkChangeEvent')
    event.set('startTime', format_time(close_time))
    
    for link_id in affected_links:
        link_elem = ET.SubElement(event, 'link')
        link_elem.set('refId', str(link_id))
    
    # Set freespeed to 0 (road closed)
    freespeed = ET.SubElement(event, 'freespeed')
    freespeed.set('type', 'absolute')
    freespeed.set('value', '0.0')
    
    # Pretty print
    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="\t")
    # Remove extra blank lines
    xml_str = '\n'.join([line for line in xml_str.split('\n') if line.strip()])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"Generated: {output_file}")
    print(f"  Links closed: {len(affected_links)}")
    print(f"  Close time: {format_time(close_time)}")


def main():
    parser = argparse.ArgumentParser(description='Generate NetworkChangeEvents for tsunami evacuation')
    parser.add_argument('--network', required=True, help='Path to network.xml.gz')
    parser.add_argument('--hazard-center', required=True, help='Hazard zone center as "lat,lon"')
    parser.add_argument('--hazard-radius', type=float, default=2.0, help='Hazard zone radius in km')
    parser.add_argument('--close-time', type=int, default=3600, help='Time when roads close (seconds)')
    parser.add_argument('--output', required=True, help='Output changeEvents.xml path')
    
    args = parser.parse_args()
    
    # Parse center coordinates
    lat, lon = map(float, args.hazard_center.split(','))
    
    print("=" * 50)
    print("PHASE 2: Network Change Events Generator")
    print("=" * 50)
    print(f"Hazard center: ({lat}, {lon})")
    print(f"Hazard radius: {args.hazard_radius} km")
    print(f"Close time: {format_time(args.close_time)}")
    print()
    
    # Parse network
    links = parse_network(args.network)
    
    # Find affected links
    affected_links = find_links_in_hazard_zone(links, lat, lon, args.hazard_radius)
    print(f"\nLinks in hazard zone: {len(affected_links)}")
    
    if len(affected_links) == 0:
        print("WARNING: No links found in hazard zone!")
        print("Check if coordinates match the network's coordinate system.")
        return
    
    # Generate change events
    generate_change_events(affected_links, args.close_time, args.output)
    print("\nDone!")


if __name__ == "__main__":
    main()
