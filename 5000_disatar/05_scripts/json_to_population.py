#!/usr/bin/env python3
"""
Convert ABM JSON format trajectory data to MATSim population.xml.gz

This script compresses each agent's 3-second interval trajectory into a simplified plan:
    home activity (until 03:00:00) → mode leg → evacuation activity

Mode mapping:
    CAR → car
    BUS → pt (public transport)
    RAIL → pt (public transport)
    WALK → walk

For agents using multiple modes (e.g., WALK → BUS → WALK), the dominant non-WALK
mode is selected to represent the main transportation method.
"""

import json
import gzip
import argparse
from collections import Counter
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


def convert_abm_mode_to_matsim(abm_mode: str) -> str:
    """
    Convert ABM mode to MATSim mode

    Args:
        abm_mode: Mode from ABM JSON (CAR, BUS, RAIL, WALK)

    Returns:
        MATSim mode string (car, pt, walk)
    """
    mode_mapping = {
        'CAR': 'car',
        'BUS': 'pt',
        'RAIL': 'pt',
        'WALK': 'walk'
    }
    return mode_mapping.get(abm_mode, 'car')  # default to car if unknown


def determine_leg_mode(waypoints: list) -> str:
    """
    Determine leg mode from waypoint sequence.
    Strategy: Use dominant non-WALK mode, fallback to WALK if only WALK.

    For multi-modal agents (e.g., WALK → BUS → WALK):
    - WALK is typically access/egress (walking to/from stations)
    - The main transportation mode (BUS, CAR, RAIL) is selected

    Args:
        waypoints: List of waypoint dictionaries with 'mode' field

    Returns:
        MATSim mode string (car, pt, walk)
    """
    # Extract all modes except WALK
    non_walk_modes = [wp['mode'] for wp in waypoints if wp['mode'] != 'WALK']

    if non_walk_modes:
        # Use most common non-WALK mode
        dominant_mode = Counter(non_walk_modes).most_common(1)[0][0]
    else:
        # All waypoints are WALK
        dominant_mode = 'WALK'

    return convert_abm_mode_to_matsim(dominant_mode)


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t", encoding='utf-8')


def convert_json_to_population(input_json: str, output_xml: str):
    """
    Convert ABM JSON format to MATSim population.xml.gz

    Args:
        input_json: Path to input JSON file
        output_xml: Path to output population.xml.gz file
    """
    print(f"Reading JSON file: {input_json}")
    with open(input_json, 'r') as f:
        agents_data = json.load(f)

    print(f"Found {len(agents_data)} agents")

    # Initialize coordinate transformer
    coord_transformer = CoordinateTransformer()

    # Create XML root element
    root = Element('population')

    # Statistics tracking
    mode_stats = Counter()

    # Process each agent
    for i, agent_data in enumerate(agents_data):
        if (i + 1) % 500 == 0:
            print(f"Processing agent {i + 1}/{len(agents_data)}...")

        # Use agent_id from JSON (not enumeration index)
        agent_id = str(agent_data['agent_id'])
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

        # Determine leg mode from waypoint sequence
        leg_mode = determine_leg_mode(waypoints)
        mode_stats[leg_mode] += 1

        # Create person element
        person = SubElement(root, 'person', id=agent_id)
        plan = SubElement(person, 'plan', selected='yes')

        # Start activity: home (agent is at home until disaster occurs at 03:00:00)
        start_activity = SubElement(
            plan,
            'activity',
            type='home',
            x=f'{start_x:.2f}',
            y=f'{start_y:.2f}',
            end_time='03:00:00'
        )

        # Leg: evacuation trip using determined mode
        leg = SubElement(plan, 'leg', mode=leg_mode)

        # End activity: evacuation destination (no end_time for last activity)
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

    # Also write uncompressed version for easier inspection
    uncompressed_output = output_xml.replace('.gz', '')
    print(f"Writing uncompressed version to {uncompressed_output}...")
    with open(uncompressed_output, 'w', encoding='utf-8') as f:
        f.write(xml_output)

    print(f"\n✓ Successfully created {output_xml}")
    print(f"  - Total agents: {len(agents_data)}")
    print(f"  - Mode distribution:")
    for mode, count in sorted(mode_stats.items()):
        percentage = (count / len(agents_data)) * 100
        print(f"      {mode}: {count} agents ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Convert ABM JSON format to MATSim population.xml.gz',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Convert 5000-agent disaster evacuation data
  python3 json_to_population.py \\
    --input /path/to/5000_abm_format_outcome.json \\
    --output /path/to/working_temp/population.xml.gz

  # This will create:
  #   - population.xml.gz (compressed)
  #   - population.xml (uncompressed for inspection)

  # Each agent will have:
  #   <activity type="home" end_time="03:00:00"/>
  #   <leg mode="car|pt|walk"/>
  #   <activity type="evacuation"/>
        """
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Path to input JSON file (ABM format with 5000 agents)'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Path to output population.xml.gz file'
    )

    args = parser.parse_args()

    convert_json_to_population(
        args.input,
        args.output
    )


if __name__ == '__main__':
    main()
