"""
Directional routing validator for MATSim networks.

Validates route reachability respecting one-way links using BFS.
"""
from typing import Dict, Any, Set, Optional
import networkx as nx

from .network_graph import DirectedNetworkGraph


class DirectionalRoutingValidator:
    """
    Check if origin link can reach destination link via directed graph.

    Uses BFS for reachability with result caching for performance.
    """

    def __init__(self, network_graph: DirectedNetworkGraph):
        """
        Initialize validator with network graph.

        Args:
            network_graph: DirectedNetworkGraph instance
        """
        self.network_graph = network_graph
        self.car_subgraph = network_graph.build_mode_subgraph({'car'})
        self.reachability_cache: Dict[tuple, bool] = {}

        print(f"  ✓ Built car subgraph with {len(self.car_subgraph.nodes())} nodes, "
              f"{len(self.car_subgraph.edges())} edges")

    def is_reachable(
        self,
        origin_link: str,
        dest_link: str,
        mode: str = 'car'
    ) -> bool:
        """
        Check if origin_link can reach dest_link via directional routing.

        Args:
            origin_link: Starting link ID
            dest_link: Destination link ID
            mode: Routing mode ('car' only for this validator)

        Returns:
            True if route exists, False otherwise

        Uses NetworkX has_path() for reachability check with caching.
        """
        cache_key = (origin_link, dest_link, mode)

        # Check cache first
        if cache_key in self.reachability_cache:
            return self.reachability_cache[cache_key]

        # Get from/to nodes for links
        try:
            origin_to_node = self.network_graph.get_link_to_node(origin_link)
            dest_from_node = self.network_graph.get_link_from_node(dest_link)
        except ValueError:
            # Link not found in network
            self.reachability_cache[cache_key] = False
            return False

        # Check if path exists in car subgraph
        if mode == 'car':
            result = nx.has_path(self.car_subgraph, origin_to_node, dest_from_node)
        else:
            # For other modes, use full graph (future enhancement)
            result = nx.has_path(self.network_graph.graph, origin_to_node, dest_from_node)

        # Cache result
        self.reachability_cache[cache_key] = result
        return result

    def validate_route(
        self,
        origin_x: float,
        origin_y: float,
        dest_x: float,
        dest_y: float,
        mode: str = 'car',
        max_snap_distance: float = 300.0
    ) -> Dict[str, Any]:
        """
        Full route validation from coordinates.

        Steps:
        1. Snap origin to network link
        2. Snap destination to network link
        3. Check reachability

        Args:
            origin_x, origin_y: Origin activity coordinates
            dest_x, dest_y: Destination activity coordinates
            mode: Routing mode ('car')
            max_snap_distance: Maximum snapping distance (meters)

        Returns:
            Dictionary with validation result:
            {
                'valid': bool,
                'origin_link': str or None,
                'dest_link': str or None,
                'reachable': bool or None,
                'reason': str  # If invalid: 'no_origin_link', 'no_dest_link', 'unreachable'
            }
        """
        required_modes = {mode}

        # Step 1: Snap origin to network
        origin_candidates = self.network_graph.snap_coordinate_to_links(
            origin_x, origin_y,
            required_modes=required_modes,
            max_distance=max_snap_distance,
            k_nearest=5
        )

        if not origin_candidates:
            return {
                'valid': False,
                'origin_link': None,
                'dest_link': None,
                'reachable': None,
                'reason': 'no_origin_link'
            }

        origin_link = origin_candidates[0][0]  # Closest link

        # Step 2: Snap destination to network
        dest_candidates = self.network_graph.snap_coordinate_to_links(
            dest_x, dest_y,
            required_modes=required_modes,
            max_distance=max_snap_distance,
            k_nearest=5
        )

        if not dest_candidates:
            return {
                'valid': False,
                'origin_link': origin_link,
                'dest_link': None,
                'reachable': None,
                'reason': 'no_dest_link'
            }

        dest_link = dest_candidates[0][0]  # Closest link

        # Step 3: Check reachability
        is_reachable = self.is_reachable(origin_link, dest_link, mode)

        return {
            'valid': is_reachable,
            'origin_link': origin_link,
            'dest_link': dest_link,
            'reachable': is_reachable,
            'reason': 'unreachable' if not is_reachable else 'valid'
        }

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for performance monitoring."""
        return {
            'cache_size': len(self.reachability_cache),
            'cache_hits': sum(1 for v in self.reachability_cache.values() if v),
            'cache_misses': sum(1 for v in self.reachability_cache.values() if not v)
        }
