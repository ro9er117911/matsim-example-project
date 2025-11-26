"""
Public Transit (PT) coverage validator.

Validates PT agent accessibility to transit stops and route coverage.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

try:
    from scipy.spatial import KDTree
    KDTREE_AVAILABLE = True
except ImportError:
    KDTREE_AVAILABLE = False

from .utils import open_maybe_gz, hhmmss_to_seconds, euclidean_distance


class PTCoverageValidator:
    """
    Validate PT agent access to transit network.

    Strategy:
    1. Parse transit schedule to extract stops and routes
    2. Check if origin/destination within walking distance of stops
    3. Validate route exists between stop pairs (direct or single transfer)
    """

    def __init__(self, schedule_xml_path: str):
        """
        Parse transit schedule.

        Extracts:
        - stop_coords: Dict[stop_id] -> (x, y)
        - route_stops: Dict[route_id] -> [stop_id_1, stop_id_2, ...]
        - stop_routes: Dict[stop_id] -> set of route_ids serving this stop

        Args:
            schedule_xml_path: Path to transitSchedule.xml(.gz)
        """
        self.schedule_path = Path(schedule_xml_path)
        if not self.schedule_path.exists():
            raise FileNotFoundError(f"Transit schedule not found: {schedule_xml_path}")

        self.stop_coords: Dict[str, Tuple[float, float]] = {}
        self.route_stops: Dict[str, List[str]] = {}
        self.stop_routes: Dict[str, Set[str]] = {}
        self.stop_kdtree: Optional[KDTree] = None
        self.stop_ids_list: List[str] = []
        self.stop_coords_list: List[Tuple[float, float]] = []

        print(f"Parsing transit schedule: {schedule_xml_path}")
        self._parse_schedule()
        self._build_stop_index()
        self._build_stop_route_mapping()
        print(f"  ✓ Loaded {len(self.stop_coords)} stops, {len(self.route_stops)} routes")

    def _parse_schedule(self):
        """Parse transit schedule XML to extract stops and routes."""
        with open_maybe_gz(self.schedule_path) as f:
            tree = ET.parse(f)

        root = tree.getroot()

        # Parse stop facilities
        for stop_elem in root.findall(".//stopFacility"):
            stop_id = stop_elem.get("id")
            x = stop_elem.get("x")
            y = stop_elem.get("y")

            if stop_id and x and y:
                self.stop_coords[stop_id] = (float(x), float(y))

        # Parse transit routes
        for route in root.findall(".//transitRoute"):
            route_id = route.get("id")
            if not route_id:
                continue

            stops_in_route = []
            route_profile = route.find("./routeProfile")
            if route_profile is not None:
                for stop_elem in route_profile.findall("./stop"):
                    stop_ref_id = stop_elem.get("refId")
                    if stop_ref_id:
                        stops_in_route.append(stop_ref_id)

            if stops_in_route:
                self.route_stops[route_id] = stops_in_route

    def _build_stop_index(self):
        """Build KDTree for fast stop accessibility queries."""
        for stop_id, (x, y) in self.stop_coords.items():
            self.stop_ids_list.append(stop_id)
            self.stop_coords_list.append((x, y))

        if KDTREE_AVAILABLE and self.stop_coords_list:
            self.stop_kdtree = KDTree(self.stop_coords_list)
            print(f"  ✓ Built stop KDTree with {len(self.stop_coords_list)} stops")
        else:
            print(f"  ⚠ Using linear search for stop accessibility (scipy not available)")

    def _build_stop_route_mapping(self):
        """Build reverse mapping: stop_id -> routes serving that stop."""
        for route_id, stops in self.route_stops.items():
            for stop_id in stops:
                if stop_id not in self.stop_routes:
                    self.stop_routes[stop_id] = set()
                self.stop_routes[stop_id].add(route_id)

    def find_accessible_stops(
        self,
        x: float,
        y: float,
        max_walk_distance: float = 500.0
    ) -> List[Tuple[str, float]]:
        """
        Find PT stops within walking distance of coordinate.

        Args:
            x, y: Activity coordinates (EPSG:3826)
            max_walk_distance: Maximum walking distance in meters

        Returns:
            List of (stop_id, distance) tuples sorted by distance
        """
        results = []

        if self.stop_kdtree and KDTREE_AVAILABLE:
            # Use KDTree for fast spatial query
            indices = self.stop_kdtree.query_ball_point([x, y], r=max_walk_distance)

            for idx in indices:
                stop_id = self.stop_ids_list[idx]
                stop_x, stop_y = self.stop_coords_list[idx]
                dist = euclidean_distance(x, y, stop_x, stop_y)
                results.append((stop_id, dist))

            # Sort by distance
            results.sort(key=lambda x: x[1])
        else:
            # Fallback: linear search
            for stop_id, (stop_x, stop_y) in self.stop_coords.items():
                dist = euclidean_distance(x, y, stop_x, stop_y)
                if dist <= max_walk_distance:
                    results.append((stop_id, dist))

            # Sort by distance
            results.sort(key=lambda x: x[1])

        return results

    def has_pt_route(
        self,
        origin_stops: List[str],
        dest_stops: List[str]
    ) -> bool:
        """
        Check if PT route exists between any origin-destination stop pair.

        Strategy:
        1. Get all routes serving origin_stops
        2. For each route, check if it also serves any dest_stop
        3. Return True if direct route found

        Note: Does NOT check complex multi-transfer scenarios (simplified validation)

        Args:
            origin_stops: List of stop IDs at origin
            dest_stops: List of stop IDs at destination

        Returns:
            True if at least one route connects stops, False otherwise
        """
        # Get routes serving origin stops
        origin_routes = set()
        for stop_id in origin_stops:
            if stop_id in self.stop_routes:
                origin_routes.update(self.stop_routes[stop_id])

        # Get routes serving destination stops
        dest_routes = set()
        for stop_id in dest_stops:
            if stop_id in self.stop_routes:
                dest_routes.update(self.stop_routes[stop_id])

        # Check for direct route (route serves both origin and dest)
        common_routes = origin_routes & dest_routes
        if common_routes:
            return True

        # Check for transfer route (one-hop transfer)
        # If any origin route shares a stop with any dest route, transfer is possible
        for origin_route in origin_routes:
            origin_route_stops = set(self.route_stops.get(origin_route, []))
            for dest_route in dest_routes:
                dest_route_stops = set(self.route_stops.get(dest_route, []))
                # Check if routes share any transfer stop
                if origin_route_stops & dest_route_stops:
                    return True

        return False

    def validate_pt_accessibility(
        self,
        origin_x: float,
        origin_y: float,
        dest_x: float,
        dest_y: float,
        max_walk_distance: float = 500.0
    ) -> Dict[str, Any]:
        """
        Full PT accessibility check.

        Args:
            origin_x, origin_y: Origin activity coordinates
            dest_x, dest_y: Destination activity coordinates
            max_walk_distance: Maximum walking distance to stops

        Returns:
            Dictionary with validation result:
            {
                'valid': bool,
                'origin_stops': List[str],  # Accessible stops at origin
                'dest_stops': List[str],    # Accessible stops at destination
                'has_route': bool,
                'reason': str  # If invalid: 'no_origin_stops', 'no_dest_stops', 'no_route'
            }
        """
        # Find accessible stops at origin
        origin_stop_candidates = self.find_accessible_stops(origin_x, origin_y, max_walk_distance)

        if not origin_stop_candidates:
            return {
                'valid': False,
                'origin_stops': [],
                'dest_stops': [],
                'has_route': False,
                'reason': 'no_origin_stops'
            }

        origin_stops = [stop_id for stop_id, _ in origin_stop_candidates]

        # Find accessible stops at destination
        dest_stop_candidates = self.find_accessible_stops(dest_x, dest_y, max_walk_distance)

        if not dest_stop_candidates:
            return {
                'valid': False,
                'origin_stops': origin_stops,
                'dest_stops': [],
                'has_route': False,
                'reason': 'no_dest_stops'
            }

        dest_stops = [stop_id for stop_id, _ in dest_stop_candidates]

        # Check if route exists
        has_route = self.has_pt_route(origin_stops, dest_stops)

        return {
            'valid': has_route,
            'origin_stops': origin_stops[:5],  # Limit to top 5
            'dest_stops': dest_stops[:5],      # Limit to top 5
            'has_route': has_route,
            'reason': 'no_route' if not has_route else 'valid'
        }
