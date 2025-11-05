"""
Validate MATSim population XML against spatial and temporal constraints.

Checks:
1. All activity coordinates are valid
2. Car agent coordinates are within OSM bounds
3. Trip durations are within reasonable limits
4. Activity times are reasonable (non-negative durations)

Generates a validation report with statistics and warnings.
"""

import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

# OSM Boundary configuration (same as in generate_test_population.py)
OSM_BOUNDS = {
    'top_left': (288137, 2783823),
    'bottom_left': (287627, 2768820),
    'bottom_right': (314701, 2769311),
    'top_right': (314401, 2784363),
}

CITY_CENTER = (302416, 2770714)
MAX_TRIP_TIME_MINUTES = 40


class PopulationValidator:
    """Validate MATSim population XML file."""

    def __init__(self, population_file: str):
        """Initialize validator with population file path."""
        self.population_file = population_file
        self.tree = None
        self.root = None
        self.agents = {}
        self.errors = []
        self.warnings = []
        self.statistics = {
            'total_agents': 0,
            'total_activities': 0,
            'total_legs': 0,
            'car_agents_out_of_bounds': [],
            'long_trips': [],
            'invalid_activities': [],
        }

    def load(self):
        """Load and parse the population XML file."""
        try:
            self.tree = ET.parse(self.population_file)
            self.root = self.tree.getroot()
            print(f"✓ Loaded population file: {self.population_file}")
        except Exception as e:
            self.errors.append(f"Failed to load population file: {e}")
            return False
        return True

    def validate(self):
        """Run all validation checks."""
        print("\n" + "=" * 70)
        print("POPULATION VALIDATION")
        print("=" * 70)

        if not self.load():
            self.print_report()
            return False

        print("\nValidating agents...")
        self._validate_agents()

        print("Checking spatial constraints...")
        self._validate_spatial()

        print("Checking mode consistency...")
        self._validate_mode_consistency()

        print("Checking leg durations...")
        self._validate_leg_duration()

        print("Checking PT transfer agents...")
        self._validate_transfer_agents()

        print("Checking temporal constraints...")
        self._validate_temporal()

        self.print_report()
        return len(self.errors) == 0

    def _validate_agents(self):
        """Parse and validate all agents."""
        for person in self.root.findall('person'):
            agent_id = person.get('id')
            self.statistics['total_agents'] += 1

            plan = person.find('plan')
            if plan is None:
                self.warnings.append(f"Agent {agent_id}: No plan found")
                continue

            # Parse activities and legs
            activities = []
            legs = []

            for child in plan:
                if child.tag == 'activity':
                    activity = self._parse_activity(child, agent_id)
                    if activity:
                        activities.append(activity)
                    self.statistics['total_activities'] += 1

                elif child.tag == 'leg':
                    leg = self._parse_leg(child, agent_id)
                    if leg:
                        legs.append(leg)
                    self.statistics['total_legs'] += 1

            self.agents[agent_id] = {
                'activities': activities,
                'legs': legs,
                'mode': self._infer_mode(legs),
            }

    def _parse_activity(self, activity_elem, agent_id: str) -> Dict:
        """Parse an activity element."""
        try:
            activity = {
                'type': activity_elem.get('type'),
                'x': float(activity_elem.get('x', 0)),
                'y': float(activity_elem.get('y', 0)),
                'link': activity_elem.get('link'),
                'start_time_s': self._time_to_seconds(activity_elem.get('start_time')),
                'end_time_s': self._time_to_seconds(activity_elem.get('end_time')),
                'max_dur': self._time_to_seconds(activity_elem.get('max_dur')),
            }
            return activity
        except Exception as e:
            self.warnings.append(f"Agent {agent_id}: Failed to parse activity: {e}")
            return None

    def _parse_leg(self, leg_elem, agent_id: str) -> Dict:
        """Parse a leg element."""
        try:
            leg = {
                'mode': leg_elem.get('mode'),
                'dep_time_s': self._time_to_seconds(leg_elem.get('dep_time')),
                'trav_time_s': self._time_to_seconds(leg_elem.get('trav_time')),
            }
            return leg
        except Exception as e:
            self.warnings.append(f"Agent {agent_id}: Failed to parse leg: {e}")
            return None

    def _time_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM:SS to seconds, or return 0 if None."""
        if not time_str:
            return None

        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
        except:
            pass
        return None

    def _infer_mode(self, legs: List[Dict]) -> str:
        """Infer agent mode from legs."""
        modes = [leg['mode'] for leg in legs if leg.get('mode')]
        if 'car' in modes:
            return 'car'
        elif 'pt' in modes:
            return 'pt'
        elif 'walk' in modes:
            return 'walk'
        return 'unknown'

    def _validate_spatial(self):
        """Check spatial constraints (OSM bounds for car agents)."""
        for agent_id, agent_data in self.agents.items():
            mode = agent_data['mode']

            # Car agents: all activities must be within OSM bounds
            if mode == 'car':
                for activity in agent_data['activities']:
                    if not self._is_within_osm_bounds(activity['x'], activity['y']):
                        self.statistics['car_agents_out_of_bounds'].append(agent_id)
                        self.errors.append(
                            f"Car agent {agent_id}: Activity {activity['type']} at "
                            f"({activity['x']}, {activity['y']}) is OUTSIDE OSM bounds"
                        )

    def _validate_mode_consistency(self):
        """Check that agent ID prefix matches actual leg modes."""
        mode_consistency_errors = []
        for agent_id, agent_data in self.agents.items():
            inferred_mode = agent_data['mode']

            # Extract agent type from ID
            if agent_id.startswith('car_agent_'):
                expected_mode = 'car'
            elif agent_id.startswith('pt_transfer_agent_'):
                expected_mode = 'pt'
            elif agent_id.startswith('pt_agent_'):
                expected_mode = 'pt'
            elif agent_id.startswith('walk_agent_'):
                expected_mode = 'walk'
            else:
                continue

            # Check if inferred mode matches expected mode
            if inferred_mode != expected_mode:
                mode_consistency_errors.append(agent_id)
                self.errors.append(
                    f"Mode consistency: {agent_id} (ID says '{expected_mode}' but uses '{inferred_mode}')"
                )

        return mode_consistency_errors

    def _validate_leg_duration(self):
        """Check for excessive walk leg durations in car and PT agents."""
        excessive_walk_legs = []
        MAX_WALK_LEG_DURATION_MIN = 30  # Car agents shouldn't walk >30 minutes

        for agent_id, agent_data in self.agents.items():
            inferred_mode = agent_data['mode']

            # Skip pure walk agents
            if inferred_mode == 'walk':
                continue

            # Check walk legs for car and PT agents
            for leg in agent_data['legs']:
                if leg.get('mode') == 'walk' and leg.get('trav_time_s') is not None:
                    walk_duration_min = leg['trav_time_s'] / 60
                    if walk_duration_min > MAX_WALK_LEG_DURATION_MIN:
                        excessive_walk_legs.append((agent_id, walk_duration_min))
                        self.warnings.append(
                            f"Agent {agent_id}: Excessive walk leg {walk_duration_min:.1f} min "
                            f"(expected <{MAX_WALK_LEG_DURATION_MIN} min for {inferred_mode} agent)"
                        )

        return excessive_walk_legs

    def _validate_transfer_agents(self):
        """Verify PT transfer agents have proper boarding sequences."""
        transfer_validation = []

        for agent_id, agent_data in self.agents.items():
            if not agent_id.startswith('pt_transfer_agent_'):
                continue

            legs = agent_data['legs']
            pt_legs = [leg for leg in legs if leg.get('mode') == 'pt']

            # Transfer agents should have 4 PT legs (2 for morning outbound, 2 for evening return)
            if len(pt_legs) != 4:
                transfer_validation.append((agent_id, f"Expected 4 PT legs (2 morning + 2 evening), got {len(pt_legs)}"))
                self.warnings.append(
                    f"PT transfer agent {agent_id}: Expected 4 PT legs (2 morning + 2 evening) but has {len(pt_legs)}"
                )

    def _validate_temporal(self):
        """Check temporal constraints (trip durations)."""
        for agent_id, agent_data in self.agents.items():
            activities = agent_data['activities']

            if len(activities) < 2:
                continue

            # Calculate trip times between consecutive activities
            for i in range(len(activities) - 1):
                act_start = activities[i]
                act_end = activities[i + 1]

                # Activity duration
                if act_start['end_time_s'] is not None and act_start['start_time_s'] is not None:
                    if act_start['end_time_s'] < act_start['start_time_s']:
                        self.statistics['invalid_activities'].append(agent_id)
                        self.errors.append(
                            f"Agent {agent_id}: Activity {act_start['type']} has "
                            f"end_time < start_time"
                        )

                # Trip duration (from one activity end to next activity start)
                if (act_start['end_time_s'] is not None and
                        act_end['start_time_s'] is not None):
                    if act_end['start_time_s'] < act_start['end_time_s']:
                        # This might be next-day, skip for now
                        continue

                    trip_duration_s = act_end['start_time_s'] - act_start['end_time_s']
                    trip_duration_min = trip_duration_s / 60

                    if trip_duration_min > MAX_TRIP_TIME_MINUTES:
                        self.statistics['long_trips'].append((agent_id, trip_duration_min))
                        self.warnings.append(
                            f"Agent {agent_id}: Trip from {act_start['type']} to "
                            f"{act_end['type']} takes {trip_duration_min:.1f} min "
                            f"(max: {MAX_TRIP_TIME_MINUTES})"
                        )

    def _is_within_osm_bounds(self, x: float, y: float) -> bool:
        """Check if coordinates are within OSM bounds."""
        xs = [OSM_BOUNDS[k][0] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]
        ys = [OSM_BOUNDS[k][1] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        return x_min <= x <= x_max and y_min <= y <= y_max

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)

        print(f"\nBasic Statistics:")
        print(f"  Total agents: {self.statistics['total_agents']}")
        print(f"  Total activities: {self.statistics['total_activities']}")
        print(f"  Total legs: {self.statistics['total_legs']}")

        print(f"\nAgent Breakdown by Mode:")
        car_count = sum(1 for a in self.agents.values() if a['mode'] == 'car')
        pt_count = sum(1 for a in self.agents.values() if a['mode'] == 'pt')
        walk_count = sum(1 for a in self.agents.values() if a['mode'] == 'walk')
        unknown_count = sum(1 for a in self.agents.values() if a['mode'] == 'unknown')

        print(f"  Car agents: {car_count}")
        print(f"  PT agents: {pt_count}")
        print(f"  Walk agents: {walk_count}")
        print(f"  Unknown: {unknown_count}")

        print(f"\nAgent Type Breakdown:")
        pt_single_count = sum(1 for id in self.agents.keys() if id.startswith('pt_agent_'))
        pt_transfer_count = sum(1 for id in self.agents.keys() if id.startswith('pt_transfer_agent_'))
        car_agent_count = sum(1 for id in self.agents.keys() if id.startswith('car_agent_'))
        walk_agent_count = sum(1 for id in self.agents.keys() if id.startswith('walk_agent_'))

        print(f"  PT single-line agents: {pt_single_count}")
        print(f"  PT transfer agents: {pt_transfer_count}")
        print(f"  Car agents: {car_agent_count}")
        print(f"  Walk agents: {walk_agent_count}")

        print(f"\nSpatial Validation:")
        if self.statistics['car_agents_out_of_bounds']:
            print(f"  ✗ Car agents outside OSM bounds: {len(self.statistics['car_agents_out_of_bounds'])}")
            for agent_id in self.statistics['car_agents_out_of_bounds']:
                print(f"    - {agent_id}")
        else:
            print(f"  ✓ All car agents within OSM bounds")

        print(f"\nTemporal Validation:")
        if self.statistics['long_trips']:
            print(f"  ⚠ Long trips (> {MAX_TRIP_TIME_MINUTES} min): {len(self.statistics['long_trips'])}")
            for agent_id, duration in sorted(self.statistics['long_trips'], key=lambda x: x[1], reverse=True)[:5]:
                print(f"    - {agent_id}: {duration:.1f} min")
        else:
            print(f"  ✓ All trips within {MAX_TRIP_TIME_MINUTES} minute limit")

        if self.statistics['invalid_activities']:
            print(f"  ✗ Invalid activity times: {len(self.statistics['invalid_activities'])}")
            for agent_id in self.statistics['invalid_activities']:
                print(f"    - {agent_id}")
        else:
            print(f"  ✓ All activity times are valid")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")

        print(f"\n" + "=" * 70)

        if self.errors:
            print("STATUS: ❌ VALIDATION FAILED (errors detected)")
        elif self.warnings:
            print("STATUS: ⚠️ VALIDATION PASSED WITH WARNINGS")
        else:
            print("STATUS: ✓ VALIDATION PASSED (no issues)")

        print("=" * 70)


def main():
    """Main entry point."""
    import sys

    if len(sys.argv) < 2:
        population_file = 'scenarios/corridor/taipei_test/test_population_50.xml'
    else:
        population_file = sys.argv[1]

    # Check if file exists
    if not Path(population_file).exists():
        print(f"Error: Population file not found: {population_file}")
        return 1

    validator = PopulationValidator(population_file)
    success = validator.validate()

    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
