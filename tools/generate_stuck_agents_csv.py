#!/usr/bin/env python3
"""
Generate stuck agents CSV files for SimWrapper Dashboard.
Analyzes stuckAndAbort events from MATSim output.
Includes Chinese road names from network attributes.
"""

import gzip
import sys
import csv
import re
import os
import html
from collections import defaultdict
from pathlib import Path

def parse_network_names(network_file):
    """Parse link names from network XML file."""
    link_names = {}
    
    if not network_file or not Path(network_file).exists():
        return link_names
    
    print(f"Loading link names from {network_file}...")
    opener = gzip.open if str(network_file).endswith('.gz') else open
    
    current_link_id = None
    
    with opener(network_file, 'rt', encoding='utf-8') as f:
        for line in f:
            # Find link id
            link_match = re.search(r'<link id="([^"]+)"', line)
            if link_match:
                current_link_id = link_match.group(1)
            
            # Find osm:way:name attribute
            name_match = re.search(r'name="osm:way:name"[^>]*>([^<]+)<', line)
            if name_match and current_link_id:
                # Decode HTML entities like &#20843; to actual Chinese characters
                raw_name = name_match.group(1)
                link_names[current_link_id] = html.unescape(raw_name)
    
    print(f"Loaded {len(link_names)} link names")
    return link_names

def parse_stuck_events(events_file):
    """Parse stuck events from events XML file."""
    stuck_agents = []
    
    opener = gzip.open if str(events_file).endswith('.gz') else open
    
    with opener(events_file, 'rt', encoding='utf-8') as f:
        for line in f:
            if 'stuckAndAbort' in line:
                time_match = re.search(r'time="([^"]+)"', line)
                person_match = re.search(r'person="([^"]+)"', line)
                link_match = re.search(r'link="([^"]+)"', line)
                mode_match = re.search(r'legMode="([^"]+)"', line)
                
                if time_match and person_match:
                    stuck_agents.append({
                        'time': float(time_match.group(1)),
                        'person': person_match.group(1),
                        'link': link_match.group(1) if link_match else 'unknown',
                        'mode': mode_match.group(1) if mode_match else 'unknown'
                    })
    
    return stuck_agents

def generate_stuck_agents_csv(stuck_agents, output_dir, link_names=None):
    """Generate all stuck agents CSV files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if link_names is None:
        link_names = {}
    
    # 1. stuck_agents.csv - summary
    with open(output_dir / 'stuck_agents.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['person', 'link', 'mode', 'time'])
        for agent in stuck_agents:
            writer.writerow([agent['person'], agent['link'], agent['mode'], agent['time']])
    print(f"Generated stuck_agents.csv with {len(stuck_agents)} entries")
    
    # 2. stuck_agents_per_mode.csv
    mode_counts = defaultdict(int)
    for agent in stuck_agents:
        mode_counts[agent['mode']] += 1
    
    with open(output_dir / 'stuck_agents_per_mode.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Mode', 'Agents'])
        for mode, count in sorted(mode_counts.items(), key=lambda x: -x[1]):
            writer.writerow([mode, count])
    print(f"Generated stuck_agents_per_mode.csv with {len(mode_counts)} modes")
    
    # 3. stuck_agents_per_hour.csv
    hour_counts = defaultdict(int)
    for agent in stuck_agents:
        hour = int(agent['time'] // 3600)
        hour_counts[hour] += 1
    
    with open(output_dir / 'stuck_agents_per_hour.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Hour', 'Agents'])
        for hour in sorted(hour_counts.keys()):
            writer.writerow([hour, hour_counts[hour]])
    print(f"Generated stuck_agents_per_hour.csv with {len(hour_counts)} hours")
    
    # 4. stuck_agents_per_link.csv (Top 20) - with Chinese names
    link_counts = defaultdict(int)
    for agent in stuck_agents:
        link_counts[agent['link']] += 1
    
    top_links = sorted(link_counts.items(), key=lambda x: -x[1])[:20]
    
    with open(output_dir / 'stuck_agents_per_link.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Link', 'Agents'])
        for link, count in top_links:
            # Use Chinese name if available, otherwise show "link_id"
            name = link_names.get(link, '')
            display_name = f"{name} ({link})" if name else link
            writer.writerow([display_name, count])
    print(f"Generated stuck_agents_per_link.csv with {len(top_links)} links")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_stuck_agents_csv.py /path/to/output_dir [/path/to/input_network.xml.gz]")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    events_file = output_dir / 'output_events.xml.gz'
    
    # Optional: input network for road names
    input_network = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('INPUT_NETWORK')
    
    if not events_file.exists():
        print(f"Error: Events file not found: {events_file}")
        sys.exit(1)
    
    # Load link names from network
    link_names = {}
    if input_network:
        link_names = parse_network_names(input_network)
    
    print(f"Parsing stuck events from {events_file}...")
    stuck_agents = parse_stuck_events(events_file)
    print(f"Found {len(stuck_agents)} stuck agents")
    
    if not stuck_agents:
        print("No stuck agents found - creating empty files")
        population_dir = output_dir / 'analysis' / 'population'
        population_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, header in [
            ('stuck_agents.csv', 'person;link;mode;time'),
            ('stuck_agents_per_mode.csv', 'Mode;Agents'),
            ('stuck_agents_per_hour.csv', 'Hour;Agents'),
            ('stuck_agents_per_link.csv', 'Link;Agents')
        ]:
            with open(population_dir / filename, 'w', encoding='utf-8') as f:
                f.write(header + '\n')
        print("Created empty stuck agents files")
    else:
        generate_stuck_agents_csv(stuck_agents, output_dir / 'analysis' / 'population', link_names)
    
    print("Done!")

if __name__ == "__main__":
    main()
