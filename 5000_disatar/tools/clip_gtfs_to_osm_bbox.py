#!/usr/bin/env python3
"""
Clip a GTFS feed to the bounding box of a MATSim network (in EPSG:3826).
Keeps referential integrity across routes/trips/stop_times/stops/shapes.

Usage:
  python clip_gtfs_to_osm_bbox.py \
      --network 5000_disatar/output_full/network.xml \
      --gtfs 5000_disatar/GTFS/bus_disaster_gtfs \
      --out 5000_disatar/GTFS_CLIPPED/bus_clipped \
      [--buffer-m 500]
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, Set, Tuple
import xml.etree.ElementTree as ET

from pyproj import Transformer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", required=True, help="Path to MATSim network.xml")
    parser.add_argument("--gtfs", required=True, help="Path to GTFS directory (un-zipped)")
    parser.add_argument("--out", required=True, help="Output directory for clipped GTFS")
    parser.add_argument(
        "--buffer-m",
        type=float,
        default=500.0,
        help="Expand network bbox by this many meters in EPSG:3826 before clipping (default: 500m)",
    )
    return parser.parse_args()


def network_bbox_epsg3826(network_path: Path) -> Tuple[float, float, float, float]:
    tree = ET.parse(network_path)
    root = tree.getroot()
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for node in root.iterfind(".//node"):
        x = float(node.attrib["x"])
        y = float(node.attrib["y"])
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
    return min_x, min_y, max_x, max_y


def expand_bbox(xmin: float, ymin: float, xmax: float, ymax: float, buffer_m: float):
    return xmin - buffer_m, ymin - buffer_m, xmax + buffer_m, ymax + buffer_m


def bbox_to_wgs84(xmin: float, ymin: float, xmax: float, ymax: float) -> Tuple[float, float, float, float]:
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    lon_min, lat_min = transformer.transform(xmin, ymin)
    lon_max, lat_max = transformer.transform(xmax, ymax)
    # Normalize ordering in case of projection quirks
    return min(lon_min, lon_max), min(lat_min, lat_max), max(lon_min, lon_max), max(lat_min, lat_max)


def read_csv(path: Path) -> Tuple[list, list]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        return rows[0], rows[1:]


def write_csv(path: Path, header: Iterable[str], rows: Iterable[Iterable[str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def clip_gtfs(gtfs_dir: Path, out_dir: Path, lon_min: float, lat_min: float, lon_max: float, lat_max: float):
    print(f"[CLIP] Using WGS84 bbox lon {lon_min:.4f}-{lon_max:.4f}, lat {lat_min:.4f}-{lat_max:.4f}")

    stops_header, stops_rows = read_csv(gtfs_dir / "stops.txt")
    stop_id_idx = stops_header.index("stop_id")
    stop_lat_idx = stops_header.index("stop_lat")
    stop_lon_idx = stops_header.index("stop_lon")

    kept_stops = []
    kept_stop_ids: Set[str] = set()
    for row in stops_rows:
        try:
            lon = float(row[stop_lon_idx])
            lat = float(row[stop_lat_idx])
        except ValueError:
            continue
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            kept_stops.append(row)
            kept_stop_ids.add(row[stop_id_idx])

    print(f"[CLIP] Stops kept: {len(kept_stop_ids)} / {len(stops_rows)}")

    # stop_times
    st_header, st_rows = read_csv(gtfs_dir / "stop_times.txt")
    st_trip_idx = st_header.index("trip_id")
    st_stop_idx = st_header.index("stop_id")

    kept_stop_times = []
    trips_with_stops: Dict[str, int] = {}
    for row in st_rows:
        stop_id = row[st_stop_idx]
        if stop_id not in kept_stop_ids:
            continue
        trip_id = row[st_trip_idx]
        kept_stop_times.append(row)
        trips_with_stops[trip_id] = trips_with_stops.get(trip_id, 0) + 1

    print(f"[CLIP] stop_times kept: {len(kept_stop_times)} / {len(st_rows)}")

    # trips
    trips_header, trips_rows = read_csv(gtfs_dir / "trips.txt")
    trip_trip_idx = trips_header.index("trip_id")
    trip_route_idx = trips_header.index("route_id")
    trip_shape_idx = trips_header.index("shape_id") if "shape_id" in trips_header else None

    kept_trips = []
    kept_route_ids: Set[str] = set()
    kept_shape_ids: Set[str] = set()
    for row in trips_rows:
        trip_id = row[trip_trip_idx]
        if trip_id not in trips_with_stops:
            continue
        kept_trips.append(row)
        kept_route_ids.add(row[trip_route_idx])
        if trip_shape_idx is not None:
            kept_shape_ids.add(row[trip_shape_idx])

    print(f"[CLIP] Trips kept: {len(kept_trips)} / {len(trips_rows)}")
    print(f"[CLIP] Routes referenced: {len(kept_route_ids)}")

    # routes
    routes_header, routes_rows = read_csv(gtfs_dir / "routes.txt")
    route_id_idx = routes_header.index("route_id")
    kept_routes = [row for row in routes_rows if row[route_id_idx] in kept_route_ids]
    print(f"[CLIP] Routes kept: {len(kept_routes)} / {len(routes_rows)}")

    # shapes
    shapes_path = gtfs_dir / "shapes.txt"
    if shapes_path.exists() and kept_shape_ids:
        shapes_header, shapes_rows = read_csv(shapes_path)
        shape_id_idx = shapes_header.index("shape_id")
        kept_shapes = [row for row in shapes_rows if row[shape_id_idx] in kept_shape_ids]
        print(f"[CLIP] Shape points kept: {len(kept_shapes)} / {len(shapes_rows)}")
    else:
        kept_shapes = None
        shapes_header = []

    # Write outputs
    write_csv(out_dir / "stops.txt", stops_header, kept_stops)
    write_csv(out_dir / "stop_times.txt", st_header, kept_stop_times)
    write_csv(out_dir / "trips.txt", trips_header, kept_trips)
    write_csv(out_dir / "routes.txt", routes_header, kept_routes)

    if kept_shapes is not None:
        write_csv(out_dir / "shapes.txt", shapes_header, kept_shapes)

    # Pass-through files
    for name in ["agency.txt", "calendar.txt", "calendar_dates.txt", "frequencies.txt", "transfers.txt", "feed_info.txt"]:
        src = gtfs_dir / name
        if src.exists():
            dst = out_dir / name
            dst.write_bytes(src.read_bytes())


def main():
    args = parse_args()
    gtfs_dir = Path(args.gtfs)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    xmin, ymin, xmax, ymax = network_bbox_epsg3826(Path(args.network))
    xmin, ymin, xmax, ymax = expand_bbox(xmin, ymin, xmax, ymax, args.buffer_m)
    lon_min, lat_min, lon_max, lat_max = bbox_to_wgs84(xmin, ymin, xmax, ymax)

    print(f"[BBOX] EPSG:3826 xmin={xmin:.1f}, ymin={ymin:.1f}, xmax={xmax:.1f}, ymax={ymax:.1f}")
    print(f"[BBOX] WGS84   lon={lon_min:.4f}-{lon_max:.4f}, lat={lat_min:.4f}-{lat_max:.4f}")

    clip_gtfs(gtfs_dir, out_dir, lon_min, lat_min, lon_max, lat_max)
    print(f"[DONE] Clipped GTFS written to {out_dir}")


if __name__ == "__main__":
    main()
