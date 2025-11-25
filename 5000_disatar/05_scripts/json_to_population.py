#!/usr/bin/env python3
"""
Convert ABM JSON format trajectory data to MATSim population.xml.gz

This script compresses each agent's 3-second interval trajectory into a simplified plan:
    start activity → car leg → end activity

As recommended in json_mapping_to_plan.md, this avoids creating hundreds of activities
per agent which would cause performance issues in MATSim QSim.
"""

import json
import gzip
import argparse
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from xml.dom import minidom

try:
    from pyproj import Transformer
except ImportError:
    print("ERROR: pyproj not installed. Please install with: pip install pyproj")
    exit(1)


class CoordinateTransformer:
    """Transform coordinates from WGS84 (lat/lon) to EPSG:3826 (TWD97)"""
    
    def __init__(self):
        # Create transformer from WGS84 (EPSG:4326) to TWD97 TM2 (EPSG:3826)
        self.transformer = Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)
    
    def transform(self, lat: float, lon: float) -> tuple:
        """
        Transform WGS84 coordinates to EPSG:3826
        
        Args:
            lat: Latitude in WGS84
            lon: Longitude in WGS84
            
        Returns:
            Tuple of (x, y) in EPSG:3826
        """
        # Note: pyproj expects (lon, lat) for EPSG:4326 when always_xy=True
        x, y = self.transformer.transform(lon, lat)
        return x, y


def format_time(seconds: int) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_time(time_str: str) -> int:
    """Parse HH:MM:SS to total seconds"""
    parts = time_str.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t", encoding='utf-8')


def convert_json_to_population(input_json: str, output_xml: str, start_time: str, interval: int):
    """
    Convert ABM JSON format to MATSim population.xml.gz
    
    Args:
        input_json: Path to input JSON file
        output_xml: Path to output population.xml.gz file
        start_time: Base start time in HH:MM:SS format
        interval: Seconds between waypoints (default: 3)
    """
    print(f"Reading JSON file: {input_json}")
    with open(input_json, 'r') as f:
        agents_data = json.load(f)
    
    print(f"Found {len(agents_data)} agents")
    
    # Initialize coordinate transformer
    coord_transformer = CoordinateTransformer()
    
    # Create XML root element
    root = Element('population')
    
    # Parse base start time
    base_start_seconds = parse_time(start_time)
    
    # Process each agent
    for i, agent_data in enumerate(agents_data):
        if (i + 1) % 100 == 0:
            print(f"Processing agent {i + 1}/{len(agents_data)}...")
        
        # Use enumeration index as person ID to avoid duplicates
        agent_id = str(i + 1)
        waypoints = agent_data['weekday_path']
        
        if len(waypoints) < 2:
            print(f"WARNING: Agent {agent_id} has less than 2 waypoints, skipping")
            continue
        
        # Extract first and last waypoints
        first_waypoint = waypoints[0]
        last_waypoint = waypoints[-1]
        
        # Get positions (lat, lon)
        first_lat, first_lon = first_waypoint['position']
        last_lat, last_lon = last_waypoint['position']
        
        # Transform to EPSG:3826
        start_x, start_y = coord_transformer.transform(first_lat, first_lon)
        end_x, end_y = coord_transformer.transform(last_lat, last_lon)
        
        # Calculate times
        # Assume each waypoint is 'interval' seconds apart
        trip_duration = (len(waypoints) - 1) * interval
        agent_start_time = base_start_seconds
        agent_end_time = agent_start_time + trip_duration
        
        # Create person element
        person = SubElement(root, 'person', id=agent_id)
        plan = SubElement(person, 'plan', selected='yes')
        
        # Start activity
        start_activity = SubElement(
            plan, 
            'activity',
            type='evacuation',
            x=f'{start_x:.2f}',
            y=f'{start_y:.2f}',
            end_time=format_time(agent_start_time)
        )
        
        # Leg (car mode)
        leg = SubElement(plan, 'leg', mode='car')
        
        # End activity (no end_time for last activity)
        end_activity = SubElement(
            plan,
            'activity',
            type='evacuation',
            x=f'{end_x:.2f}',
            y=f'{end_y:.2f}'
        )
    
    print(f"Generating XML with {len(agents_data)} agents...")
    
    # Generate pretty XML
    xml_bytes = prettify_xml(root)
    
    # Add DOCTYPE declaration manually
    xml_string = xml_bytes.decode('utf-8')
    # Insert DOCTYPE after XML declaration
    lines = xml_string.split('\n')
    doctype = '<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">'
    
    # Find the line with <?xml and insert DOCTYPE after it
    final_lines = []
    for line in lines:
        final_lines.append(line)
        if line.strip().startswith('<?xml'):
            final_lines.append(doctype)
            final_lines.append('')
    
    xml_output = '\n'.join(final_lines)
    
    # Write to compressed file
    print(f"Writing to {output_xml}...")
    with gzip.open(output_xml, 'wt', encoding='utf-8') as f:
        f.write(xml_output)
    
    print(f"✓ Successfully created {output_xml}")
    print(f"  - Total agents: {len(agents_data)}")
    print(f"  - Time range: {start_time} to {format_time(base_start_seconds + max([len(a['weekday_path']) for a in agents_data]) * interval)}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert ABM JSON format to MATSim population.xml.gz',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Test with small sample
  python3 json_to_population.py \\
    --input AGENT/INPUT/test_abm_format_outcome.json \\
    --output test_population.xml.gz \\
    --start-time "03:00:00"
  
  # Full 5000-agent conversion
  python3 json_to_population.py \\
    --input AGENT/INPUT/5000_abm_format_outcome.json \\
    --output population.xml.gz \\
    --start-time "03:00:00"
        """
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Path to input JSON file (ABM format)'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output population.xml.gz file'
    )
    
    parser.add_argument(
        '--start-time',
        default='00:00:00',
        help='Base start time in HH:MM:SS format (default: 00:00:00)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=3,
        help='Seconds between waypoints (default: 3)'
    )
    
    args = parser.parse_args()
    
    convert_json_to_population(
        args.input,
        args.output,
        args.start_time,
        args.interval
    )


if __name__ == '__main__':
    main()
