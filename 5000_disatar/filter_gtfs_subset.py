#!/usr/bin/env python3
"""
Filter GTFS to a test subset of routes.
Preserves referential integrity across all GTFS files.
"""

import os
import sys
import shutil
from pathlib import Path


def filter_gtfs_to_subset(input_dir, output_dir, num_routes=50):
    """
    Filter GTFS to subset of routes while maintaining referential integrity.

    Args:
        input_dir: Path to input GTFS directory
        output_dir: Path to output GTFS directory
        num_routes: Number of unique route_short_name to include (default 50 = ~100 route_ids)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"[1/8] Reading routes.txt...")
    # Read routes and select first N unique route_short_name
    with open(input_path / "routes.txt", encoding="utf-8") as f:
        routes_header = f.readline().strip()
        routes_lines = f.readlines()

    # Parse route_short_name (column 2)
    unique_route_names = set()
    selected_route_ids = set()
    selected_routes_lines = []

    for line in routes_lines:
        parts = line.strip().split(',')
        route_id = parts[0]
        route_short_name = parts[2]

        if len(unique_route_names) < num_routes:
            unique_route_names.add(route_short_name)
            selected_route_ids.add(route_id)
            selected_routes_lines.append(line)
        elif route_short_name in unique_route_names:
            # Include both directions of existing routes
            selected_route_ids.add(route_id)
            selected_routes_lines.append(line)

    print(f"  ✓ Selected {len(unique_route_names)} route names → {len(selected_route_ids)} route_ids")

    # Write filtered routes.txt
    with open(output_path / "routes.txt", "w", encoding="utf-8") as f:
        f.write(routes_header + "\n")
        f.writelines(selected_routes_lines)

    print(f"[2/8] Reading trips.txt...")
    # Filter trips by selected route_ids
    with open(input_path / "trips.txt", encoding="utf-8") as f:
        trips_header = f.readline().strip()
        trips_lines = f.readlines()

    # Parse route_id (column 0) and trip_id (column 2)
    selected_trip_ids = set()
    selected_trips_lines = []
    selected_shape_ids = set()

    for line in trips_lines:
        parts = line.strip().split(',')
        route_id = parts[0]
        trip_id = parts[2]
        shape_id = parts[6] if len(parts) > 6 else None

        if route_id in selected_route_ids:
            selected_trip_ids.add(trip_id)
            selected_trips_lines.append(line)
            if shape_id:
                selected_shape_ids.add(shape_id)

    print(f"  ✓ Selected {len(selected_trip_ids)} trips")

    # Write filtered trips.txt
    with open(output_path / "trips.txt", "w", encoding="utf-8") as f:
        f.write(trips_header + "\n")
        f.writelines(selected_trips_lines)

    print(f"[3/8] Reading stop_times.txt (this may take a while)...")
    # Filter stop_times by selected trip_ids
    with open(input_path / "stop_times.txt", encoding="utf-8") as f:
        stop_times_header = f.readline().strip()

        selected_stop_ids = set()
        selected_stop_times_lines = []
        line_count = 0

        for line in f:
            line_count += 1
            if line_count % 100000 == 0:
                print(f"    ... processed {line_count:,} lines")

            parts = line.strip().split(',')
            trip_id = parts[0]
            stop_id = parts[3]

            if trip_id in selected_trip_ids:
                selected_stop_ids.add(stop_id)
                selected_stop_times_lines.append(line)

    print(f"  ✓ Selected {len(selected_stop_times_lines):,} stop_times for {len(selected_stop_ids)} stops")

    # Write filtered stop_times.txt
    with open(output_path / "stop_times.txt", "w", encoding="utf-8") as f:
        f.write(stop_times_header + "\n")
        f.writelines(selected_stop_times_lines)

    print(f"[4/8] Reading stops.txt...")
    # Filter stops by selected stop_ids
    with open(input_path / "stops.txt", encoding="utf-8") as f:
        stops_header = f.readline().strip()
        stops_lines = f.readlines()

    selected_stops_lines = []
    for line in stops_lines:
        parts = line.strip().split(',')
        stop_id = parts[0]

        if stop_id in selected_stop_ids:
            selected_stops_lines.append(line)

    print(f"  ✓ Selected {len(selected_stops_lines)} stop records")

    # Write filtered stops.txt
    with open(output_path / "stops.txt", "w", encoding="utf-8") as f:
        f.write(stops_header + "\n")
        f.writelines(selected_stops_lines)

    print(f"[5/8] Reading shapes.txt (this may take a while)...")
    # Filter shapes by selected shape_ids
    if (input_path / "shapes.txt").exists():
        with open(input_path / "shapes.txt", encoding="utf-8") as f:
            shapes_header = f.readline().strip()

            selected_shapes_lines = []
            line_count = 0

            for line in f:
                line_count += 1
                if line_count % 100000 == 0:
                    print(f"    ... processed {line_count:,} lines")

                parts = line.strip().split(',')
                shape_id = parts[0]

                if shape_id in selected_shape_ids:
                    selected_shapes_lines.append(line)

        print(f"  ✓ Selected {len(selected_shapes_lines):,} shape points")

        # Write filtered shapes.txt
        with open(output_path / "shapes.txt", "w", encoding="utf-8") as f:
            f.write(shapes_header + "\n")
            f.writelines(selected_shapes_lines)

    print(f"[6/8] Copying agency.txt...")
    # Copy agency.txt as-is
    if (input_path / "agency.txt").exists():
        shutil.copy(input_path / "agency.txt", output_path / "agency.txt")
        print("  ✓ Copied agency.txt")

    print(f"[7/8] Copying calendar.txt...")
    # Copy calendar.txt as-is (service_ids will be filtered naturally by trips)
    if (input_path / "calendar.txt").exists():
        shutil.copy(input_path / "calendar.txt", output_path / "calendar.txt")
        print("  ✓ Copied calendar.txt")

    print(f"[8/8] Copying calendar_dates.txt...")
    # Copy calendar_dates.txt as-is
    if (input_path / "calendar_dates.txt").exists():
        shutil.copy(input_path / "calendar_dates.txt", output_path / "calendar_dates.txt")
        print("  ✓ Copied calendar_dates.txt")

    print(f"\n✅ GTFS subset created successfully!")
    print(f"   Input:  {input_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Routes: {len(unique_route_names)} route names ({len(selected_route_ids)} route_ids)")
    print(f"   Trips:  {len(selected_trip_ids):,}")
    print(f"   Stops:  {len(selected_stop_ids):,}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python filter_gtfs_subset.py <input_gtfs_dir> <output_gtfs_dir> [num_routes]")
        print("Example: python filter_gtfs_subset.py 5000_disatar/GTFS/bus_disaster_gtfs 5000_disatar/GTFS_TEST/bus_test 50")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    num_routes = int(sys.argv[3]) if len(sys.argv) > 3 else 50

    filter_gtfs_to_subset(input_dir, output_dir, num_routes)
