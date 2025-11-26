"""
Agent route processor with car→PT mode conversion.

Processes population agents, validates routes, and attempts mode conversion for unreachable car agents.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple, Optional

from .routing_validator import DirectionalRoutingValidator
from .pt_validator import PTCoverageValidator
from .network_graph import DirectedNetworkGraph


class AgentRouteProcessor:
    """
    Process population agents and validate/convert routes.

    Workflow:
    1. Parse agent from population.xml
    2. Extract mode and activity coordinates
    3. Validate route based on mode
    4. If car unreachable, attempt PT conversion
    5. Track validation status
    """

    def __init__(
        self,
        routing_validator: DirectionalRoutingValidator,
        pt_validator: PTCoverageValidator,
        max_snap_distance: float = 300.0,
        max_walk_distance: float = 500.0
    ):
        """
        Initialize agent processor with validators.

        Args:
            routing_validator: DirectionalRoutingValidator instance
            pt_validator: PTCoverageValidator instance
            max_snap_distance: Maximum distance for link snapping (meters)
            max_walk_distance: Maximum walking distance to PT stops (meters)
        """
        self.routing_validator = routing_validator
        self.pt_validator = pt_validator
        self.max_snap_distance = max_snap_distance
        self.max_walk_distance = max_walk_distance

    def process_agent(self, person_elem: ET.Element) -> Dict[str, Any]:
        """
        Process single agent from population XML.

        Steps:
        1. Extract agent_id, mode, activities
        2. For car agents: validate car reachability
        3. If unreachable: check PT accessibility
        4. Return validation result with conversion status

        Args:
            person_elem: XML element for <person>

        Returns:
            Dictionary with validation result:
            {
                'agent_id': str,
                'original_mode': str,
                'final_mode': str,
                'status': 'valid' | 'converted' | 'invalid',
                'reason': str,
                'origin_coords': (x, y),
                'dest_coords': (x, y),
                'car_reachable': bool or None,
                'pt_accessible': bool or None
            }
        """
        agent_id = person_elem.get('id')
        plan = person_elem.find('plan')

        if plan is None:
            return {
                'agent_id': agent_id,
                'original_mode': 'unknown',
                'final_mode': 'unknown',
                'status': 'invalid',
                'reason': 'no_plan',
                'origin_coords': None,
                'dest_coords': None,
                'car_reachable': None,
                'pt_accessible': None
            }

        # Extract activities and legs
        activities = []
        legs = []

        for child in plan:
            if child.tag == 'activity':
                x = child.get('x')
                y = child.get('y')
                if x and y:
                    activities.append({
                        'type': child.get('type'),
                        'x': float(x),
                        'y': float(y),
                        'end_time': child.get('end_time')
                    })
            elif child.tag == 'leg':
                legs.append({
                    'mode': child.get('mode'),
                    'elem': child  # Keep reference for potential mode conversion
                })

        if len(activities) < 2:
            return {
                'agent_id': agent_id,
                'original_mode': 'unknown',
                'final_mode': 'unknown',
                'status': 'invalid',
                'reason': 'insufficient_activities',
                'origin_coords': None,
                'dest_coords': None,
                'car_reachable': None,
                'pt_accessible': None
            }

        # Get origin and destination
        origin = activities[0]
        destination = activities[-1]
        origin_coords = (origin['x'], origin['y'])
        dest_coords = (destination['x'], destination['y'])

        # Infer mode from legs
        original_mode = self._infer_mode(legs)

        # Validate based on mode
        if original_mode == 'car':
            return self._process_car_agent(
                agent_id, person_elem, legs,
                origin_coords, dest_coords
            )
        elif original_mode == 'pt':
            return self._process_pt_agent(
                agent_id, origin_coords, dest_coords
            )
        elif original_mode == 'walk':
            return {
                'agent_id': agent_id,
                'original_mode': 'walk',
                'final_mode': 'walk',
                'status': 'valid',
                'reason': 'walk_always_valid',
                'origin_coords': origin_coords,
                'dest_coords': dest_coords,
                'car_reachable': None,
                'pt_accessible': None
            }
        else:
            return {
                'agent_id': agent_id,
                'original_mode': original_mode,
                'final_mode': original_mode,
                'status': 'invalid',
                'reason': 'unknown_mode',
                'origin_coords': origin_coords,
                'dest_coords': dest_coords,
                'car_reachable': None,
                'pt_accessible': None
            }

    def _process_car_agent(
        self,
        agent_id: str,
        person_elem: ET.Element,
        legs: List[Dict],
        origin_coords: Tuple[float, float],
        dest_coords: Tuple[float, float]
    ) -> Dict[str, Any]:
        """Process car agent with potential PT conversion."""
        origin_x, origin_y = origin_coords
        dest_x, dest_y = dest_coords

        # Validate car route
        car_result = self.routing_validator.validate_route(
            origin_x, origin_y, dest_x, dest_y,
            mode='car',
            max_snap_distance=self.max_snap_distance
        )

        if car_result['valid']:
            # Car route is valid
            return {
                'agent_id': agent_id,
                'original_mode': 'car',
                'final_mode': 'car',
                'status': 'valid',
                'reason': 'car_reachable',
                'origin_coords': origin_coords,
                'dest_coords': dest_coords,
                'car_reachable': True,
                'pt_accessible': None
            }
        else:
            # Car route unreachable, try PT
            pt_result = self.pt_validator.validate_pt_accessibility(
                origin_x, origin_y, dest_x, dest_y,
                max_walk_distance=self.max_walk_distance
            )

            if pt_result['valid']:
                # Convert car → PT
                self._convert_car_to_pt(person_elem, legs)

                return {
                    'agent_id': agent_id,
                    'original_mode': 'car',
                    'final_mode': 'pt',
                    'status': 'converted',
                    'reason': 'car_unreachable_pt_available',
                    'origin_coords': origin_coords,
                    'dest_coords': dest_coords,
                    'car_reachable': False,
                    'pt_accessible': True
                }
            else:
                # Neither car nor PT works
                return {
                    'agent_id': agent_id,
                    'original_mode': 'car',
                    'final_mode': None,
                    'status': 'invalid',
                    'reason': f'car_unreachable_no_pt_{pt_result["reason"]}',
                    'origin_coords': origin_coords,
                    'dest_coords': dest_coords,
                    'car_reachable': False,
                    'pt_accessible': False
                }

    def _process_pt_agent(
        self,
        agent_id: str,
        origin_coords: Tuple[float, float],
        dest_coords: Tuple[float, float]
    ) -> Dict[str, Any]:
        """Process PT agent with accessibility validation."""
        origin_x, origin_y = origin_coords
        dest_x, dest_y = dest_coords

        # Validate PT accessibility
        pt_result = self.pt_validator.validate_pt_accessibility(
            origin_x, origin_y, dest_x, dest_y,
            max_walk_distance=self.max_walk_distance
        )

        if pt_result['valid']:
            return {
                'agent_id': agent_id,
                'original_mode': 'pt',
                'final_mode': 'pt',
                'status': 'valid',
                'reason': 'pt_accessible',
                'origin_coords': origin_coords,
                'dest_coords': dest_coords,
                'car_reachable': None,
                'pt_accessible': True
            }
        else:
            return {
                'agent_id': agent_id,
                'original_mode': 'pt',
                'final_mode': None,
                'status': 'invalid',
                'reason': f'pt_{pt_result["reason"]}',
                'origin_coords': origin_coords,
                'dest_coords': dest_coords,
                'car_reachable': None,
                'pt_accessible': False
            }

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

    def _convert_car_to_pt(self, person_elem: ET.Element, legs: List[Dict]) -> bool:
        """
        Convert agent legs from 'car' to 'pt'.

        Modifies XML in-place by changing <leg mode="car"> to <leg mode="pt">.

        Args:
            person_elem: XML element for <person>
            legs: List of leg dictionaries with 'elem' references

        Returns:
            True if conversion successful
        """
        try:
            for leg in legs:
                if leg['mode'] == 'car':
                    leg_elem = leg['elem']
                    leg_elem.set('mode', 'pt')
                    # Remove car-specific route attributes if present
                    route_elem = leg_elem.find('route')
                    if route_elem is not None:
                        leg_elem.remove(route_elem)

            return True
        except Exception as e:
            print(f"Warning: Failed to convert car→PT: {e}")
            return False
