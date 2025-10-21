#!/usr/bin/env python3
"""
Clip a GTFS feed to a corridor defined by an EPSG:3826 bounding box.

Example:
    python3 tools/clip_gtfs_bbox.py \
        --source src/test/resources/gtfs/source/source.gtfs.zip \
        --bbox3826 "303898.776,2770250.712,305064.492,2770996.136" \
        --out src/test/resources/gtfs/bl_corridor/bl_corridor.gtfs.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, Polygon


REQUIRED_GTFS_FILES = [
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
]


def parse_bbox(bbox_string: str) -> Tuple[float, float, float, float]:
    try:
        min_x, min_y, max_x, max_y = map(float, bbox_string.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "bbox must be four comma separated floats: minX,minY,maxX,maxY"
        ) from exc
    if not (min_x < max_x and min_y < max_y):
        raise argparse.ArgumentTypeError("bbox min values must be smaller than max values")
    return min_x, min_y, max_x, max_y


def transform_bbox_to_wgs84(min_x: float, min_y: float, max_x: float, max_y: float) -> Polygon:
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    corners_3826 = [
        (min_x, min_y),
        (min_x, max_y),
        (max_x, max_y),
        (max_x, min_y),
    ]
    corners_wgs84 = [transformer.transform(x, y) for x, y in corners_3826]
    return Polygon(corners_wgs84)


def read_gtfs_zip(zip_path: Path) -> Dict[str, pd.DataFrame]:
    feeds: Dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith(".txt"):
                with zf.open(name) as fh:
                    feeds[name.lower()] = pd.read_csv(fh, dtype=str)
    missing = [f for f in REQUIRED_GTFS_FILES if f not in feeds]
    if missing:
        raise FileNotFoundError(f"Source GTFS is missing required files: {missing}")
    return feeds


def filter_gtfs(
    feeds: Dict[str, pd.DataFrame],
    corridor_polygon: Polygon,
) -> Dict[str, pd.DataFrame]:
    # Stops inside bbox
    stops = feeds["stops.txt"].copy()
    stops["stop_lat"] = stops["stop_lat"].astype(float)
    stops["stop_lon"] = stops["stop_lon"].astype(float)

    mask = stops.apply(
        lambda row: corridor_polygon.contains(Point(row["stop_lon"], row["stop_lat"])),
        axis=1,
    )
    stops_kept = stops.loc[mask].copy()
    if stops_kept.empty:
        raise RuntimeError("No stops fall inside the provided bounding box.")

    stop_ids: Set[str] = set(stops_kept["stop_id"])

    # stop_times filtered by stops
    stop_times = feeds["stop_times.txt"]
    stop_times_filtered = stop_times[stop_times["stop_id"].isin(stop_ids)].copy()
    if stop_times_filtered.empty:
        raise RuntimeError("No stop_times remain after stop filtering.")

    trip_ids: Set[str] = set(stop_times_filtered["trip_id"])
    trips = feeds["trips.txt"]
    trips_filtered = trips[trips["trip_id"].isin(trip_ids)].copy()
    if trips_filtered.empty:
        raise RuntimeError("No trips remain after stop_time filtering.")

    route_ids: Set[str] = set(trips_filtered["route_id"])
    routes = feeds["routes.txt"]
    routes_filtered = routes[routes["route_id"].isin(route_ids)].copy()

    calendar = feeds["calendar.txt"]
    calendar_filtered = calendar[calendar["service_id"].isin(trips_filtered["service_id"])].copy()

    if "calendar_dates.txt" in feeds:
        calendar_dates = feeds["calendar_dates.txt"]
        calendar_dates_filtered = calendar_dates[
            calendar_dates["service_id"].isin(trips_filtered["service_id"])
        ].copy()
    else:
        calendar_dates_filtered = None

    shapes_filtered = feeds.get("shapes.txt")
    if shapes_filtered is not None:
        shapes_filtered = shapes_filtered[
            shapes_filtered["shape_id"].isin(trips_filtered.get("shape_id", []))
        ].copy()

    feeds_out: Dict[str, pd.DataFrame] = {
        "stops.txt": stops_kept.drop(columns=["stop_lat", "stop_lon"]).assign(
            stop_lat=stops_kept["stop_lat"].map("{:.6f}".format),
            stop_lon=stops_kept["stop_lon"].map("{:.6f}".format),
        ),
        "stop_times.txt": stop_times_filtered,
        "trips.txt": trips_filtered,
        "routes.txt": routes_filtered,
        "calendar.txt": calendar_filtered,
    }

    if calendar_dates_filtered is not None and not calendar_dates_filtered.empty:
        feeds_out["calendar_dates.txt"] = calendar_dates_filtered

    if shapes_filtered is not None and not shapes_filtered.empty:
        feeds_out["shapes.txt"] = shapes_filtered

    # Copy optional files that are referenced by surviving trips/routes if present.
    for optional_file in ["frequencies.txt", "agency.txt"]:
        if optional_file in feeds:
            feeds_out[optional_file] = feeds[optional_file].copy()

    return feeds_out


def write_gtfs_zip(feeds: Dict[str, pd.DataFrame], output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, df in feeds.items():
            buffer = io.StringIO()
            df.to_csv(buffer, index=False, lineterminator="\n")
            zf.writestr(name, buffer.getvalue())


def verify_non_empty(feeds: Dict[str, pd.DataFrame]) -> None:
    for name in REQUIRED_GTFS_FILES:
        if name not in feeds or feeds[name].empty:
            raise RuntimeError(f"Required GTFS table '{name}' is empty after clipping.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clip a GTFS feed to an EPSG:3826 bounding box."
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Source GTFS zip file.",
    )
    parser.add_argument(
        "--bbox3826",
        required=True,
        type=parse_bbox,
        help="Bounding box in EPSG:3826 as 'minX,minY,maxX,maxY'.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output GTFS zip file.",
    )
    args = parser.parse_args()

    if not args.source.exists():
        sys.exit(f"[ERROR] Source GTFS not found: {args.source}")

    min_x, min_y, max_x, max_y = args.bbox3826
    corridor_polygon = transform_bbox_to_wgs84(min_x, min_y, max_x, max_y)

    feeds = read_gtfs_zip(args.source)
    clipped = filter_gtfs(feeds, corridor_polygon)
    verify_non_empty(clipped)
    write_gtfs_zip(clipped, args.out)

    print(f"[INFO] Clipped GTFS written to {args.out}")
    print(f"[INFO] Tables:")
    for name, df in clipped.items():
        print(f"  - {name}: {len(df)} rows")


if __name__ == "__main__":
    main()
