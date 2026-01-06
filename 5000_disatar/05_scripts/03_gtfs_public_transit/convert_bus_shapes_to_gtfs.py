#!/usr/bin/env python3
"""
Convert bus route shapefile to GTFS shapes.txt format.

This script reads a bus route shapefile and converts it to GTFS shapes.txt format
that can be used with pt2matsim's ScheduleRoutersGtfsShapes for better PT mapping.

Usage:
    python3 convert_bus_shapes_to_gtfs.py \
        --input bus_shapefile/bus_shapefile.shp \
        --output gtfs_filtered/shapes.txt \
        --trips-file gtfs_filtered/trips.txt

Output format (GTFS shapes.txt):
    shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled
    BUS_TPE10132_0,25.01192,121.44479,1,0.0
    BUS_TPE10132_0,25.01250,121.44589,2,120.5
    ...
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, Set, Tuple, List
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point


def parse_args():
    parser = argparse.ArgumentParser(description="Convert bus shapefile to GTFS shapes.txt")
    parser.add_argument("--input", required=True, help="Input shapefile path")
    parser.add_argument("--output", required=True, help="Output shapes.txt path")
    parser.add_argument("--trips-file", required=True, help="GTFS trips.txt to get required shape_ids")
    parser.add_argument("--include-mrt", action="store_true", help="Include existing MRT shapes from backup")
    parser.add_argument("--shapes-backup", default=None, help="Existing shapes.txt.bak for MRT shapes")
    return parser.parse_args()


def get_required_shape_ids(trips_file: str) -> Set[str]:
    """Extract unique shape_ids from trips.txt that start with BUS_"""
    shape_ids = set()
    with open(trips_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            shape_id = row.get("shape_id", "")
            if shape_id:
                shape_ids.add(shape_id)
    return shape_ids


def extract_line_points(geom) -> List[Tuple[float, float]]:
    """Extract points from LineString or MultiLineString geometry"""
    points = []
    
    if geom is None:
        return points
    
    if isinstance(geom, LineString):
        points = list(geom.coords)
    elif isinstance(geom, MultiLineString):
        # For MultiLineString, concatenate all parts
        for line in geom.geoms:
            points.extend(list(line.coords))
    
    return points


def calculate_cumulative_distance(points: List[Tuple[float, float]]) -> List[float]:
    """Calculate cumulative distance along the route (in meters, approximate)"""
    distances = [0.0]
    
    for i in range(1, len(points)):
        # Simple Haversine approximation for WGS84
        lon1, lat1 = points[i-1]
        lon2, lat2 = points[i]
        
        # Approximate conversion (1 degree ≈ 111km at equator)
        dx = (lon2 - lon1) * 111000 * 0.85  # cos(25°) ≈ 0.9
        dy = (lat2 - lat1) * 111000
        
        dist = (dx**2 + dy**2) ** 0.5
        distances.append(distances[-1] + dist)
    
    return distances


def convert_shapefile_to_gtfs_shapes(
    shp_path: str, 
    trips_file: str,
    output_path: str,
    include_mrt: bool = False,
    shapes_backup: str = None
):
    """Main conversion function"""
    
    print(f"Reading shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path)
    
    print(f"Reading required shape_ids from: {trips_file}")
    required_shape_ids = get_required_shape_ids(trips_file)
    bus_shape_ids = {s for s in required_shape_ids if s.startswith("BUS_")}
    mrt_shape_ids = {s for s in required_shape_ids if s.startswith("MRT_")}
    
    print(f"  Total required shape_ids: {len(required_shape_ids)}")
    print(f"  Bus shape_ids: {len(bus_shape_ids)}")
    print(f"  MRT shape_ids: {len(mrt_shape_ids)}")
    
    # Build mapping: RouteUID + direction -> shape_id
    # Shapefile: RouteUID like "TPE10132", direction 0 or 1
    # GTFS: shape_id like "BUS_TPE10132_0"
    
    shapefile_routes = {}  # (RouteUID, direction) -> geometry
    
    for idx, row in gdf.iterrows():
        try:
            model = json.loads(row["model"])
            route_uid = model.get("RouteUID", "")
            direction = model.get("Direction", 0)
            
            key = (route_uid, direction)
            if key not in shapefile_routes:
                shapefile_routes[key] = row.geometry
            else:
                # Merge geometries if multiple parts exist
                existing = shapefile_routes[key]
                if existing is not None and row.geometry is not None:
                    # Just keep the first one for simplicity
                    pass
        except Exception as e:
            print(f"  Warning: Could not parse row {idx}: {e}")
    
    print(f"  Parsed {len(shapefile_routes)} route+direction combinations from shapefile")
    
    # Generate shapes.txt content
    output_lines = []
    matched_count = 0
    unmatched_shape_ids = []
    
    for shape_id in sorted(bus_shape_ids):
        # Parse shape_id: BUS_TPE10132_0 -> RouteUID=TPE10132, direction=0
        parts = shape_id.split("_")
        if len(parts) >= 3 and parts[0] == "BUS":
            # Handle cases like BUS_TPE10132_0 or BUS_NWT10424_0
            route_uid = "_".join(parts[1:-1])  # TPE10132 or NWT10424
            direction = int(parts[-1])
            
            key = (route_uid, direction)
            
            if key in shapefile_routes:
                geom = shapefile_routes[key]
                points = extract_line_points(geom)
                
                if points:
                    distances = calculate_cumulative_distance(points)
                    
                    for seq, (coord, dist) in enumerate(zip(points, distances), start=1):
                        lon, lat = coord[:2]  # (lon, lat) from shapely
                        output_lines.append({
                            "shape_id": shape_id,
                            "shape_pt_lat": f"{lat:.7f}",
                            "shape_pt_lon": f"{lon:.7f}",
                            "shape_pt_sequence": seq,
                            "shape_dist_traveled": f"{dist:.1f}"
                        })
                    matched_count += 1
            else:
                unmatched_shape_ids.append(shape_id)
    
    print(f"  Matched {matched_count} bus shapes from shapefile")
    print(f"  Unmatched: {len(unmatched_shape_ids)} shape_ids")
    
    if unmatched_shape_ids[:5]:
        print(f"  Sample unmatched: {unmatched_shape_ids[:5]}")
    
    # Include MRT shapes from backup if requested
    if include_mrt and shapes_backup and Path(shapes_backup).exists():
        print(f"Adding MRT shapes from: {shapes_backup}")
        with open(shapes_backup, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            mrt_added = 0
            for row in reader:
                if row["shape_id"].startswith("MRT_"):
                    output_lines.append(row)
                    mrt_added += 1
        print(f"  Added {mrt_added} MRT shape points")
    
    # Write output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "shape_id", "shape_pt_lat", "shape_pt_lon", 
            "shape_pt_sequence", "shape_dist_traveled"
        ])
        writer.writeheader()
        writer.writerows(output_lines)
    
    print(f"\n✓ Wrote {len(output_lines)} shape points to: {output_path}")
    
    # Summary
    unique_shapes = len(set(row["shape_id"] for row in output_lines))
    print(f"  Total unique shapes: {unique_shapes}")
    
    return matched_count, len(unmatched_shape_ids)


def main():
    args = parse_args()
    
    print("=" * 60)
    print("Bus Shapefile to GTFS shapes.txt Converter")
    print("=" * 60)
    
    convert_shapefile_to_gtfs_shapes(
        shp_path=args.input,
        trips_file=args.trips_file,
        output_path=args.output,
        include_mrt=args.include_mrt,
        shapes_backup=args.shapes_backup
    )
    
    print("\nDone!")


if __name__ == "__main__":
    main()
