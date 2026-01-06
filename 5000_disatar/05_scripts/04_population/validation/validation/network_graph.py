"""
Directed network graph for MATSim route validation.

Parses network.xml into NetworkX DiGraph with spatial indexing for fast coordinate snapping.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx

try:
    from scipy.spatial import KDTree
    KDTREE_AVAILABLE = True
except ImportError:
    KDTREE_AVAILABLE = False
    print("Warning: scipy not available. Coordinate snapping will use slower linear search.")

from .utils import open_maybe_gz


class DirectedNetworkGraph:
    """
    Directed graph representation of MATSim network with spatial indexing.

    Attributes:
        graph: NetworkX DiGraph with nodes and directed edges
        nodes: Dict[node_id] -> (x, y)
        links: Dict[link_id] -> {'from': node_id, 'to': node_id, 'modes': set, 'length': float}
        kdtree: KDTree for fast coordinate-to-link snapping (if scipy available)
        link_coords: List of (x, y) coordinates for each link (midpoint)
        link_ids: List of link_ids (same order as link_coords)
    """

    def __init__(self, network_xml_path: str):
        """
        Parse network.xml and build directed graph.

        Uses iterparse for memory efficiency with large files (19 MB).

        Args:
            network_xml_path: Path to MATSim network.xml file
        """
        self.network_path = Path(network_xml_path)
        if not self.network_path.exists():
            raise FileNotFoundError(f"Network file not found: {network_xml_path}")

        self.graph = nx.DiGraph()
        self.nodes: Dict[str, Tuple[float, float]] = {}
        self.links: Dict[str, Dict] = {}
        self.link_coords: List[Tuple[float, float]] = []
        self.link_ids: List[str] = []
        self.kdtree: Optional[KDTree] = None

        print(f"Parsing network: {network_xml_path}")
        self._parse_network()
        self._build_graph()
        self._build_spatial_index()
        print(f"  ✓ Loaded {len(self.nodes)} nodes, {len(self.links)} links")

    def _parse_network(self):
        """Parse network.xml using iterparse for memory efficiency."""
        with open_maybe_gz(self.network_path) as f:
            context = ET.iterparse(f, events=("start", "end"))
            _, root = next(context)

            for event, elem in context:
                if event == "end":
                    if elem.tag == "node":
                        node_id = elem.get("id")
                        x = float(elem.get("x"))
                        y = float(elem.get("y"))
                        self.nodes[node_id] = (x, y)

                    elif elem.tag == "link":
                        link_id = elem.get("id")
                        from_node = elem.get("from")
                        to_node = elem.get("to")
                        length = float(elem.get("length", 0))
                        modes_str = elem.get("modes", "car")
                        modes = set(modes_str.split(','))

                        self.links[link_id] = {
                            'from': from_node,
                            'to': to_node,
                            'modes': modes,
                            'length': length
                        }

                    # Clear element to free memory
                    elem.clear()

    def _build_graph(self):
        """Build NetworkX directed graph from parsed nodes and links."""
        # Add edges to graph (from_node -> to_node)
        for link_id, link_data in self.links.items():
            from_node = link_data['from']
            to_node = link_data['to']
            self.graph.add_edge(
                from_node,
                to_node,
                link_id=link_id,
                modes=link_data['modes'],
                length=link_data['length']
            )

    def _build_spatial_index(self):
        """Build KDTree from link midpoints for fast coordinate snapping."""
        # Calculate link midpoints
        for link_id, link_data in self.links.items():
            from_node = link_data['from']
            to_node = link_data['to']

            if from_node in self.nodes and to_node in self.nodes:
                x1, y1 = self.nodes[from_node]
                x2, y2 = self.nodes[to_node]
                midpoint_x = (x1 + x2) / 2
                midpoint_y = (y1 + y2) / 2

                self.link_coords.append((midpoint_x, midpoint_y))
                self.link_ids.append(link_id)

        # Build KDTree if scipy available
        if KDTREE_AVAILABLE and self.link_coords:
            self.kdtree = KDTree(self.link_coords)
            print(f"  ✓ Built KDTree with {len(self.link_coords)} link midpoints")
        else:
            print(f"  ⚠ Using linear search for coordinate snapping (scipy not available)")

    def snap_coordinate_to_links(
        self,
        x: float,
        y: float,
        required_modes: Set[str],
        max_distance: float = 300.0,
        k_nearest: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find nearest links to coordinate that support required modes.

        Args:
            x, y: Activity coordinates (EPSG:3826)
            required_modes: Required modes (e.g., {'car'} or {'pt'})
            max_distance: Maximum snapping distance in meters
            k_nearest: Number of candidates to consider

        Returns:
            List of (link_id, distance) tuples sorted by distance
        """
        results = []

        if self.kdtree and KDTREE_AVAILABLE:
            # Use KDTree for fast spatial query
            distances, indices = self.kdtree.query([x, y], k=min(k_nearest, len(self.link_coords)))

            # Handle single result (not array)
            if not hasattr(distances, '__iter__'):
                distances = [distances]
                indices = [indices]

            for dist, idx in zip(distances, indices):
                if dist > max_distance:
                    continue

                link_id = self.link_ids[idx]
                link_modes = self.links[link_id]['modes']

                # Check if link supports required modes
                if required_modes.issubset(link_modes) or any(mode in link_modes for mode in required_modes):
                    results.append((link_id, dist))
        else:
            # Fallback: linear search
            for link_id, (link_x, link_y) in zip(self.link_ids, self.link_coords):
                dist = ((x - link_x) ** 2 + (y - link_y) ** 2) ** 0.5

                if dist > max_distance:
                    continue

                link_modes = self.links[link_id]['modes']
                if required_modes.issubset(link_modes) or any(mode in link_modes for mode in required_modes):
                    results.append((link_id, dist))

            # Sort by distance
            results.sort(key=lambda x: x[1])
            results = results[:k_nearest]

        return results

    def build_mode_subgraph(self, modes: Set[str]) -> nx.DiGraph:
        """
        Create subgraph containing only links with specified modes.

        Args:
            modes: Set of required modes (e.g., {'car'}, {'pt', 'bus', 'subway'})

        Returns:
            NetworkX DiGraph with only compatible links
        """
        subgraph = nx.DiGraph()

        for u, v, data in self.graph.edges(data=True):
            link_modes = data['modes']

            # Include link if it supports any of the required modes
            if any(mode in link_modes for mode in modes):
                subgraph.add_edge(u, v, **data)

        return subgraph

    def get_link_midpoint(self, link_id: str) -> Tuple[float, float]:
        """
        Get midpoint coordinates for a link.

        Args:
            link_id: Link identifier

        Returns:
            Tuple of (x, y) coordinates
        """
        if link_id not in self.links:
            raise ValueError(f"Link {link_id} not found in network")

        link_data = self.links[link_id]
        from_node = link_data['from']
        to_node = link_data['to']

        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Link {link_id} has invalid nodes")

        x1, y1 = self.nodes[from_node]
        x2, y2 = self.nodes[to_node]

        return (x1 + x2) / 2, (y1 + y2) / 2

    def get_link_from_node(self, link_id: str) -> str:
        """Get the from_node of a link."""
        return self.links[link_id]['from']

    def get_link_to_node(self, link_id: str) -> str:
        """Get the to_node of a link."""
        return self.links[link_id]['to']
