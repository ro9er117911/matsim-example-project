#!/usr/bin/env python3
"""
Generate simple evacuation population for MATSim testing.
Creates agents starting from random points in the network, 
ending at a single evacuation destination.
"""

import gzip
import random
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Read network and extract node coordinates
def parse_network(network_file):
    """Parse MATSim network and return node coordinates."""
    nodes = {}
    
    if network_file.endswith('.gz'):
        import gzip
        f = gzip.open(network_file, 'rt', encoding='utf-8')
    else:
        f = open(network_file, 'r', encoding='utf-8')
    
    try:
        tree = ET.parse(f)
        root = tree.getroot()
        
        for node in root.findall('.//node'):
            node_id = node.get('id')
            x = float(node.get('x'))
            y = float(node.get('y'))
            nodes[node_id] = (x, y)
    finally:
        f.close()
    
    return nodes

def generate_evacuation_population(network_file, output_file, num_agents=50):
    """Generate population with evacuation plans."""
    
    nodes = parse_network(network_file)
    node_ids = list(nodes.keys())
    
    if len(node_ids) < 2:
        print(f"Error: Network has only {len(node_ids)} nodes")
        return
    
    # Find network bounds
    coords = list(nodes.values())
    min_x = min(c[0] for c in coords)
    max_x = max(c[0] for c in coords)
    min_y = min(c[1] for c in coords)
    max_y = max(c[1] for c in coords)
    
    # Evacuation destination (southeast corner - representing safe zone)
    dest_x = (min_x + max_x) / 2 + (max_x - min_x) * 0.3
    dest_y = (min_y + max_y) / 2 + (max_y - min_y) * 0.3
    
    print(f"Network bounds: X[{min_x:.1f}, {max_x:.1f}] Y[{min_y:.1f}, {max_y:.1f}]")
    print(f"Evacuation destination: ({dest_x:.1f}, {dest_y:.1f})")
    
    # Create population XML
    population = Element('population')
    
    for i in range(num_agents):
        person = SubElement(population, 'person', id=f'evac_{i:04d}')
        plan = SubElement(person, 'plan', selected='yes')
        
        # Random starting point (origin coordinates)
        origin_x = min_x + random.random() * (max_x - min_x) * 0.8
        origin_y = min_y + random.random() * (max_y - min_y) * 0.8
        
        # Home activity (disaster zone)
        home = SubElement(plan, 'activity', type='home', 
                         x=str(origin_x), y=str(origin_y))
        # Departure time: 5AM-8AM (randomized evacuation start)
        dep_time = 5*3600 + random.random() * 3 * 3600  # 5:00 - 8:00
        hours = int(dep_time // 3600)
        minutes = int((dep_time % 3600) // 60)
        seconds = int(dep_time % 60)
        home.set('end_time', f'{hours:02d}:{minutes:02d}:{seconds:02d}')
        
        # Leg to evacuation point
        SubElement(plan, 'leg', mode='car')
        
        # Evacuation activity (safe zone)
        SubElement(plan, 'activity', type='evacuation',
                  x=str(dest_x), y=str(dest_y))
    
    # Prettify and write
    rough_string = tostring(population, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    if output_file.endswith('.gz'):
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write(pretty_xml)
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    print(f"Generated {num_agents} agents → {output_file}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: generate_evacuation_population.py <network.xml.gz> <output_population.xml> [num_agents]")
        sys.exit(1)
    
    network_file = sys.argv[1]
    output_file = sys.argv[2]
    num_agents = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    generate_evacuation_population(network_file, output_file, num_agents)
