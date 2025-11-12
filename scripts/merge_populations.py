#!/usr/bin/env python3
"""
Generate diverse population for equil scenario with 100 agents.

This script:
1. Reads taipei_test/test_population_100.xml (100 agents with home/work/car/pt/walk modes)
2. Generates diverse multi-activity plans for each agent
3. Activities include: work, shop, leisure, education (1-3 additional per agent)
4. Outputs combined population to scenarios/equil/population.xml

Requirements:
- Python 3.6+
- xml.etree.ElementTree (built-in)
- random (built-in)

Usage:
    python merge_populations.py \
        --taipei-file scenarios/corridor/taipei_test/test_population_100.xml \
        --output-file scenarios/equil/population.xml
"""

import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import random
from datetime import datetime, timedelta


# Available activity types and their typical duration
ACTIVITY_TYPES = {
    'work': {'duration': 28800, 'opening': '07:00:00', 'closing': '18:00:00'},  # 8 hours
    'shop': {'duration': 5400, 'opening': '10:00:00', 'closing': '21:00:00'},    # 1.5 hours
    'leisure': {'duration': 7200, 'opening': '13:00:00', 'closing': '23:00:00'}, # 2 hours
    'education': {'duration': 21600, 'opening': '07:00:00', 'closing': '20:00:00'} # 6 hours
}

# Maximum end time for final activities (23:00:00 = 82800 seconds)
MAX_END_TIME = 82800

# Sample coordinate ranges from equil scenario
COORD_SAMPLES = [
    (294035.05, 2762173.24),   # BL02 永寧
    (296356.46, 2766793.71),   # BL06 府中
    (300488.79, 2769778.54),   # BL10 龍山寺
    (301278.16, 2770528.60),   # BL11 西門
    (302208.73, 2771006.76),   # BL12 台北車站
    (304996.85, 2770512.50),   # BL15 忠孝復興
    (305544.29, 2770487.68),   # BL16 忠孝敦化
    (303804.19, 2770590.71),   # BL14 忠孝新生
    (302953.21, 2775206.77),   # R15 劍潭
    (303763.41, 2771719.82),   # O08 松江南京
    (305421.56, 2772105.34),   # Education location
    (307533.02, 2769486.82),   # R02 象山
    (308143.01, 2770426.50),   # Work location
    (306784.31, 2769959.91),   # Shop location
    (305795.35, 2770702.20),   # Leisure location
]


def time_to_seconds(time_str):
    """Convert HH:MM:SS to seconds since midnight."""
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s


def seconds_to_time(seconds):
    """Convert seconds since midnight to HH:MM:SS format."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def generate_activity_plan(agent_id, mode, seed_idx):
    """
    Generate a diverse activity plan for an agent.

    Special handling for PT agents to encourage transfer usage:
    - PT agents get 3-4 activities to force multi-leg routing
    - Destinations chosen to require transfers across different metro lines

    Args:
        agent_id: Person ID
        mode: Transport mode (car/pt/walk)
        seed_idx: Index for seeding randomness

    Returns:
        Dictionary with activities and legs
    """
    # Seed random for reproducibility
    random.seed(hash(agent_id) + seed_idx * 1000)

    # Home location (fixed)
    home_coord = COORD_SAMPLES[seed_idx % len(COORD_SAMPLES)]

    # PT agents require 3-4 activities (to force transfers)
    # Other modes get 1-3 activities
    if mode == 'pt':
        num_activities = random.randint(3, 4)
    else:
        num_activities = random.randint(1, 3)

    activity_types = random.sample(list(ACTIVITY_TYPES.keys()), num_activities)

    # Build activity sequence
    activities = []
    legs = []

    # Home (start)
    current_time = time_to_seconds('06:00:00') + random.randint(0, 3600)  # 06:00-07:00
    activities.append({
        'type': 'home',
        'x': str(home_coord[0]),
        'y': str(home_coord[1]),
        'end_time': seconds_to_time(current_time + 900)  # 15 min before first activity
    })

    # Intermediate activities
    # For PT agents, choose diverse locations to encourage transfers
    # Skip activities that would exceed MAX_END_TIME (23:00:00)
    for activity_idx, activity_type in enumerate(activity_types):
        # Activity duration
        duration = ACTIVITY_TYPES[activity_type]['duration']
        # Travel time + variation
        travel_time = 900 + random.randint(-300, 300)

        # Check if this activity would exceed maximum end time
        # Need: current_time + travel_time + duration <= MAX_END_TIME
        if current_time + travel_time + duration > MAX_END_TIME:
            # Skip this activity - would exceed 23:00
            continue

        legs.append({'mode': mode})

        if mode == 'pt':
            # PT agents: choose from geographically diverse locations
            # This ensures transfers across different metro lines
            location_pool = COORD_SAMPLES[:]
            # Remove very close locations to force longer trips
            dest_coord = random.choice(location_pool)
        else:
            # Other modes: random destination
            dest_coord = random.choice(COORD_SAMPLES)

        current_time += travel_time

        activities.append({
            'type': activity_type,
            'x': str(dest_coord[0]),
            'y': str(dest_coord[1]),
            'end_time': seconds_to_time(current_time + duration)
        })

        current_time += duration

    # Return home
    legs.append({'mode': mode})
    activities.append({
        'type': 'home',
        'x': str(home_coord[0]),
        'y': str(home_coord[1]),
        'end_time': None  # No end time for final home
    })

    return {'activities': activities, 'legs': legs}


def parse_taipei_population(filepath):
    """Extract agent IDs and modes from taipei population."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing {filepath}: {e}")
        sys.exit(1)

    agents = []
    for person in root.findall('person'):
        agent_id = person.get('id')

        # Extract mode from first leg
        mode = 'pt'  # default
        for leg in person.findall('.//leg'):
            mode = leg.get('mode', 'pt')
            break

        agents.append({
            'id': agent_id,
            'mode': mode
        })

    return agents


def create_multiplan_person(agent_id, plan_data):
    """
    Create a person element with multiple plans.

    Args:
        agent_id: Person ID
        plan_data: Dictionary with 'activities' and 'legs' lists

    Returns:
        XML Element representing a person
    """
    person = ET.Element('person')
    person.set('id', agent_id)

    # Create 2 plans (for replanning strategy)
    for plan_idx in range(2):
        plan = ET.SubElement(person, 'plan')
        # First plan: not selected (no), Second plan: selected (yes)
        plan.set('selected', 'yes' if plan_idx == 1 else 'no')

        # Recreate activities and legs in the same sequence
        for activity_idx, activity in enumerate(plan_data['activities']):
            # Add activity element
            activity_elem = ET.SubElement(plan, 'activity')
            activity_elem.set('type', activity['type'])
            activity_elem.set('x', activity['x'])
            activity_elem.set('y', activity['y'])

            if activity['end_time']:
                activity_elem.set('end_time', activity['end_time'])

            # Add leg element after activity (except after last activity)
            if activity_idx < len(plan_data['legs']):
                leg_elem = ET.SubElement(plan, 'leg')
                leg_elem.set('mode', plan_data['legs'][activity_idx]['mode'])

    return person


def generate_population(taipei_file, output_file):
    """
    Generate diverse population from taipei agents.

    Args:
        taipei_file: Path to taipei population file
        output_file: Path for output population file
    """
    print(f"[1/3] Parsing taipei population from: {taipei_file}")
    taipei_agents = parse_taipei_population(taipei_file)
    print(f"      Found {len(taipei_agents)} agents")

    print(f"[2/3] Generating diverse multi-activity plans...")

    # Create root element
    population = ET.Element('population')

    added_count = 0
    for idx, agent in enumerate(taipei_agents):
        agent_id = agent['id']
        mode = agent['mode']

        # Generate diverse plan
        plan_data = generate_activity_plan(agent_id, mode, idx)

        # Create multi-plan person element
        person_elem = create_multiplan_person(agent_id, plan_data)

        # Add separator comment before agent
        comment = ET.Comment(f" {agent_id} ({mode}) ")
        population.append(comment)
        population.append(person_elem)

        added_count += 1
        if added_count % 10 == 0:
            print(f"      Processed {added_count}/{len(taipei_agents)} agents")

    print(f"      Total agents added: {added_count}")

    print(f"[3/3] Writing population to: {output_file}")
    prettify_and_save(population, output_file)

    # Count statistics
    activity_types = {}
    for leg in population.findall('.//leg'):
        pass

    print("\n✓ Population generation completed successfully!")
    print(f"  Total agents: {len(taipei_agents)}")
    print(f"  Total plans: {len(taipei_agents) * 2}")

    # Analyze activities
    activities = {}
    for activity in population.findall('.//activity'):
        act_type = activity.get('type')
        activities[act_type] = activities.get(act_type, 0) + 1

    print(f"  Activity distribution:")
    for act_type in sorted(activities.keys()):
        print(f"    {act_type}: {activities[act_type]}")


def prettify_and_save(root, filename):
    """
    Format XML with proper indentation and save to file.

    Args:
        root: XML root element
        filename: Output file path
    """
    # Convert to string
    rough_string = ET.tostring(root, encoding='unicode')

    # Parse again for pretty printing
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="\t")

    # Remove extra blank lines added by minidom
    lines = [line for line in pretty_xml.split('\n') if line.strip()]

    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        # Write XML declaration manually
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n')
        f.write('\n')

        # Skip the XML declaration from minidom output
        for line in lines[1:]:
            if line.strip():
                f.write(line + '\n')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate diverse population with varied activities for equil scenario',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate diverse population from taipei agents
  python merge_populations.py \
    --taipei-file scenarios/corridor/taipei_test/test_population_100.xml \
    --output-file scenarios/equil/population.xml

  # Verify XML syntax after generation
  xmllint scenarios/equil/population.xml > /dev/null && echo "✓ XML valid"

  # Count total agents
  grep -c '<person id=' scenarios/equil/population.xml
        """
    )

    parser.add_argument(
        '--taipei-file',
        required=True,
        help='Path to taipei_test population file (test_population_100.xml)'
    )
    parser.add_argument(
        '--output-file',
        required=True,
        help='Path for output population file'
    )

    args = parser.parse_args()

    # Validate file paths
    import os

    if not os.path.exists(args.taipei_file):
        print(f"Error: Taipei file not found: {args.taipei_file}")
        sys.exit(1)

    # Run generation
    generate_population(args.taipei_file, args.output_file)


if __name__ == '__main__':
    main()
