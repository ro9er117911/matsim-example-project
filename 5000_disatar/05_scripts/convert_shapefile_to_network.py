#!/usr/bin/env python3
"""
Convert Taiwan Government GIS Shapefile (國土測繪圖資) to MATSim Network
將台灣國土測繪圖資 shapefile 轉換為 MATSim 路網格式

Requirements:
- Q_ROAD.shp: Road segments (LineString)
- Q_RDNODE.shp: Road nodes (Point)

Output:
- raw_network.xml.gz: MATSim network (car, walk modes)
"""
import argparse
import gzip
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

try:
    import geopandas as gpd
    from shapely.geometry import Point, LineString
except ImportError:
    print("ERROR: geopandas not installed. Install with: pip3 install geopandas", file=sys.stderr)
    sys.exit(1)


# Road class to MATSim parameter mapping
# Based on Taiwan road classification standards
ROAD_CLASS_PARAMS = {
    # Class: (freespeed_m/s, capacity_veh/h/lane, lanes, description)
    '1': (33.3, 2000, 3, '國道 National Highway'),
    '2': (25.0, 1500, 2, '省道/快速道路 Provincial Road'),
    '3': (16.7, 1000, 2, '縣道 County Road'),
    '4': (13.9, 800, 1, '鄉道 Township Road'),
    '5': (11.1, 600, 1, '市區道路 Urban Street'),
    '6': (8.3, 400, 1, '其他 Other'),
    'default': (11.1, 600, 1, '預設 Default')
}


def get_road_params(road_class: str) -> Tuple[float, int, int]:
    """
    Get MATSim parameters for a road class
    
    Args:
        road_class: Road class identifier (1-6)
        
    Returns:
        tuple: (freespeed_m/s, capacity_veh/h/lane, lanes)
    """
    road_class_str = str(road_class).strip() if road_class else 'default'
    params = ROAD_CLASS_PARAMS.get(road_class_str, ROAD_CLASS_PARAMS['default'])
    return params[0], params[1], params[2]


def load_nodes(rdnode_shapefile: Path) -> Dict[str, Tuple[float, float]]:
    """
    Load road nodes from Q_RDNODE.shp
    
    Args:
        rdnode_shapefile: Path to Q_RDNODE.shp
        
    Returns:
        dict: node_id -> (x, y) coordinates
    """
    print(f"Loading nodes from {rdnode_shapefile}...")
    gdf = gpd.read_file(rdnode_shapefile)
    
    node_dict = {}
    
    # Try different possible node ID field names
    node_id_fields = ['NODEID', 'NODE_ID', 'ID', 'FID']
    node_id_field = None
    
    for field in node_id_fields:
        if field in gdf.columns:
            node_id_field = field
            break
    
    if not node_id_field:
        # Use index as node ID
        print(f"WARNING: No standard node ID field found. Using index.")
        node_id_field = 'index'
        gdf['index'] = gdf.index
    
    for idx, row in gdf.iterrows():
        node_id = str(row[node_id_field])
        geom = row.geometry
        
        if geom.geom_type == 'Point':
            node_dict[node_id] = (geom.x, geom.y)
        else:
            print(f"WARNING: Node {node_id} has geometry type {geom.geom_type}, skipping")
    
    print(f"Loaded {len(node_dict)} nodes")
    return node_dict


def convert_shapefile_to_network(
    road_shapefile: Path,
    rdnode_shapefile: Path,
    output_file: Path,
    modes: str = "car,walk"
):
    """
    Convert Taiwan GIS shapefile to MATSim network
    
    Args:
        road_shapefile: Path to Q_ROAD.shp
        rdnode_shapefile: Path to Q_RDNODE.shp
        output_file: Path to output raw_network.xml.gz
        modes: Comma-separated modes (default: "car,walk")
    """
    # Load nodes
    node_dict = load_nodes(rdnode_shapefile)
    
    # Load roads
    print(f"Loading roads from {road_shapefile}...")
    roads_gdf = gpd.read_file(road_shapefile)
    print(f"Loaded {len(roads_gdf)} road segments")
    
    # Identify field names (handle different naming conventions)
    road_id_field = next((f for f in ['ROADID', 'ROAD_ID', 'ID', 'FID'] if f in roads_gdf.columns), None)
    road_class_field = next((f for f in ['ROADCLASS', 'ROAD_CLASS', 'CLASS'] if f in roads_gdf.columns), None)
    oneway_field = next((f for f in ['ONEWAY', 'ONE_WAY', 'DIRECTION'] if f in roads_gdf.columns), None)
    fnode_field = next((f for f in ['FNODE', 'FROM_NODE', 'FROMNODE'] if f in roads_gdf.columns), None)
    tnode_field = next((f for f in ['TNODE', 'TO_NODE', 'TONODE'] if f in roads_gdf.columns), None)
    
    print(f"Detected fields: road_id={road_id_field}, road_class={road_class_field}, "
          f"oneway={oneway_field}, fnode={fnode_field}, tnode={tnode_field}")
    
    # Create MATSim network XML
    print("Building MATSim network XML...")
    network = Element('network')
    
    # Add nodes
    nodes_elem = SubElement(network, 'nodes')
    for node_id, (x, y) in node_dict.items():
        SubElement(nodes_elem, 'node', {
            'id': str(node_id),
            'x': f"{x:.2f}",
            'y': f"{y:.2f}"
        })
    
    # Add links
    links_elem = SubElement(network, 'links')
    
    links_created = 0
    links_skipped = 0
    
    for idx, row in roads_gdf.iterrows():
        # Get link ID
        link_id = str(row[road_id_field]) if road_id_field else f"link_{idx}"
        
        # Get road class and parameters
        road_class = row[road_class_field] if road_class_field and row[road_class_field] else 'default'
        freespeed, capacity_per_lane, lanes = get_road_params(road_class)
        
        # Get geometry
        geom = row.geometry
        if geom.geom_type != 'LineString' and geom.geom_type != 'MultiLineString':
            links_skipped += 1
            continue
        
        # Extract start/end points
        if geom.geom_type == 'LineString':
            start_point = Point(geom.coords[0])
            end_point = Point(geom.coords[-1])
        else:  # MultiLineString
            start_point = Point(geom.geoms[0].coords[0])
            end_point = Point(geom.geoms[-1].coords[-1])
        
        # Find from/to nodes
        if fnode_field and tnode_field:
            from_node = str(row[fnode_field])
            to_node = str(row[tnode_field])
        else:
            # Find nearest nodes
            from_node = find_nearest_node(start_point, node_dict)
            to_node = find_nearest_node(end_point, node_dict)
        
        if not from_node or not to_node:
            links_skipped += 1
            continue
        
        # Calculate length
        length = geom.length
        
        # Check oneway
        oneway = row[oneway_field] if oneway_field and row[oneway_field] else '0'
        
        # Create link (forward direction)
        create_link(links_elem, link_id, from_node, to_node, length, freespeed, 
                   capacity_per_lane * lanes, lanes, modes)
        links_created += 1
        
        # Create reverse link if bidirectional
        if str(oneway) == '0':  # Bidirectional
            create_link(links_elem, f"{link_id}_reverse", to_node, from_node, length, 
                       freespeed, capacity_per_lane * lanes, lanes, modes)
            links_created += 1
    
    print(f"Created {links_created} links ({links_skipped} skipped)")
    
    # Write XML
    print(f"Writing network to {output_file}...")
    xml_str = prettify_xml(network)
    
    # Write gzipped XML
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"✓ Network written to {output_file}")
    print(f"  Nodes: {len(node_dict)}")
    print(f"  Links: {links_created}")


def find_nearest_node(point: Point, node_dict: Dict[str, Tuple[float, float]], 
                     tolerance: float = 10.0) -> str:
    """Find the nearest node to a point within tolerance"""
    min_dist = float('inf')
    nearest_id = None
    
    for node_id, (x, y) in node_dict.items():
        dist = ((point.x - x)**2 + (point.y - y)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest_id = node_id
    
    if min_dist > tolerance:
        return None
    
    return nearest_id


def create_link(parent, link_id, from_node, to_node, length, freespeed, capacity, lanes, modes):
    """Create a link element"""
    SubElement(parent, 'link', {
        'id': str(link_id),
        'from': str(from_node),
        'to': str(to_node),
        'length': f"{length:.2f}",
        'freespeed': f"{freespeed:.2f}",
        'capacity': f"{int(capacity)}",
        'permlanes': f"{int(lanes)}",
        'modes': modes
    })


def prettify_xml(elem):
    """Return a pretty-printed XML string"""
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Taiwan GIS shapefile to MATSim network"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Directory containing Q_ROAD.shp and Q_RDNODE.shp"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output raw_network.xml.gz file"
    )
    parser.add_argument(
        "--modes",
        type=str,
        default="car,walk",
        help="Modes for links (default: car,walk)"
    )
    parser.add_argument(
        "--road-file",
        type=str,
        default="Q_ROAD.shp",
        help="Road shapefile name (default: Q_ROAD.shp)"
    )
    parser.add_argument(
        "--node-file",
        type=str,
        default="Q_RDNODE.shp",
        help="Node shapefile name (default: Q_RDNODE.shp)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    road_shapefile = args.input / args.road_file
    rdnode_shapefile = args.input / args.node_file
    
    if not road_shapefile.exists():
        print(f"ERROR: {road_shapefile} not found", file=sys.stderr)
        sys.exit(1)
    
    if not rdnode_shapefile.exists():
        print(f"ERROR: {rdnode_shapefile} not found", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert
    convert_shapefile_to_network(
        road_shapefile,
        rdnode_shapefile,
        args.output,
        args.modes
    )


if __name__ == "__main__":
    main()
