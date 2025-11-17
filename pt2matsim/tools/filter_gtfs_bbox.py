#!/usr/bin/env python3
"""Create a small GTFS feed subset by bounding box and route types.

Example:
    python pt2matsim/tools/filter_gtfs_bbox.py \
        --input pt2matsim/combine/input/gtfs_tw_v5 \
        --output pt2matsim/combine/input/gtfs_tw_v5_taipei_station \
        --lat-min 25.035 --lat-max 25.065 \
        --lon-min 121.50 --lon-max 121.535 \
        --route-types 2 3
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Set, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Source GTFS directory")
    parser.add_argument("--output", required=True, type=Path, help="Destination directory")
    parser.add_argument("--lat-min", type=float, required=True, help="Minimum latitude of bounding box")
    parser.add_argument("--lat-max", type=float, required=True, help="Maximum latitude of bounding box")
    parser.add_argument("--lon-min", type=float, required=True, help="Minimum longitude of bounding box")
    parser.add_argument("--lon-max", type=float, required=True, help="Maximum longitude of bounding box")
    parser.add_argument(
        "--route-types",
        nargs="*",
        help="Optional GTFS route_type numbers (e.g. 1 2 3). Missing values keep all route types.",
    )
    parser.add_argument(
        "--max-trips-per-route",
        type=int,
        default=0,
        help="If >0, keep at most this many trips per route_id (applied after bounding-box filtering).",
    )
    return parser.parse_args()


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        rows = list(reader)
    return header, rows


def write_csv(path: Path, header: Sequence[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(header), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in header})


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_route_types(routes_path: Path) -> Tuple[List[str], List[Dict[str, str]], Dict[str, str]]:
    header, rows = read_csv(routes_path)
    mapping: Dict[str, str] = {}
    for row in rows:
        rid = (row.get("route_id") or "").strip()
        rtype = (row.get("route_type") or "").strip()
        if rid:
            mapping[rid] = rtype
    return header, rows, mapping


def load_trips(trips_path: Path) -> Tuple[List[str], List[Dict[str, str]], Dict[str, str], Dict[str, str], Dict[str, str]]:
    header, rows = read_csv(trips_path)
    route_by_trip: Dict[str, str] = {}
    service_by_trip: Dict[str, str] = {}
    shape_by_trip: Dict[str, str] = {}
    for row in rows:
        trip_id = (row.get("trip_id") or "").strip()
        if not trip_id:
            continue
        route_by_trip[trip_id] = (row.get("route_id") or "").strip()
        service_by_trip[trip_id] = (row.get("service_id") or "").strip()
        shape_by_trip[trip_id] = (row.get("shape_id") or "").strip()
    return header, rows, route_by_trip, service_by_trip, shape_by_trip


def load_stops(stops_path: Path) -> Tuple[List[str], List[Dict[str, str]], Dict[str, Dict[str, str]]]:
    header, rows = read_csv(stops_path)
    mapping: Dict[str, Dict[str, str]] = {}
    for row in rows:
        sid = (row.get("stop_id") or "").strip()
        if sid:
            mapping[sid] = row
    return header, rows, mapping


def stops_in_bbox(
    stops_rows: Sequence[Dict[str, str]],
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
) -> Set[str]:
    keep: Set[str] = set()
    for row in stops_rows:
        stop_id = (row.get("stop_id") or "").strip()
        if not stop_id:
            continue
        lat = parse_float(row.get("stop_lat"))
        lon = parse_float(row.get("stop_lon"))
        if lat is None or lon is None:
            continue
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            keep.add(stop_id)
    return keep


def gather_candidate_trip_ids(stop_times_path: Path, nearby_stop_ids: Set[str]) -> Set[str]:
    candidate: Set[str] = set()
    if not stop_times_path.exists() or not nearby_stop_ids:
        return candidate
    with stop_times_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return candidate
        for row in reader:
            stop_id = (row.get("stop_id") or "").strip()
            trip_id = (row.get("trip_id") or "").strip()
            if stop_id in nearby_stop_ids and trip_id:
                candidate.add(trip_id)
    return candidate


def limit_trip_ids(
    selected_trip_ids: Set[str],
    trips_rows: Sequence[Dict[str, str]],
    limit: int,
) -> Set[str]:
    if limit <= 0:
        return selected_trip_ids
    counters: Dict[str, int] = defaultdict(int)
    kept: Set[str] = set()
    for row in trips_rows:
        trip_id = (row.get("trip_id") or "").strip()
        if trip_id not in selected_trip_ids:
            continue
        route_id = (row.get("route_id") or "").strip()
        if counters[route_id] >= limit:
            continue
        counters[route_id] += 1
        kept.add(trip_id)
    return kept


def filter_stop_times(
    stop_times_path: Path,
    selected_trip_ids: Set[str],
) -> Tuple[List[str], List[Dict[str, str]], Set[str]]:
    referenced_stops: Set[str] = set()
    if not stop_times_path.exists() or not selected_trip_ids:
        return [], [], referenced_stops
    with stop_times_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        rows: List[Dict[str, str]] = []
        if not header:
            return header, rows, referenced_stops
        for row in reader:
            trip_id = (row.get("trip_id") or "").strip()
            if trip_id not in selected_trip_ids:
                continue
            rows.append(row)
            stop_id = (row.get("stop_id") or "").strip()
            if stop_id:
                referenced_stops.add(stop_id)
    return header, rows, referenced_stops


def filter_calendar_file(path: Path, allowed_service_ids: Set[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    header, rows = read_csv(path)
    if not header:
        return header, rows
    filtered = [row for row in rows if (row.get("service_id") or "").strip() in allowed_service_ids]
    return header, filtered


def filter_frequencies(path: Path, selected_trip_ids: Set[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    header, rows = read_csv(path)
    if not header:
        return header, rows
    filtered = [row for row in rows if (row.get("trip_id") or "").strip() in selected_trip_ids]
    return header, filtered


def filter_shapes(path: Path, used_shape_ids: Set[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    header, rows = read_csv(path)
    if not header:
        return header, rows
    filtered = [row for row in rows if (row.get("shape_id") or "").strip() in used_shape_ids]
    return header, filtered


def main() -> None:
    args = parse_args()
    input_dir = args.input.resolve()
    output_dir = args.output.resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    allowed_route_types = {value.strip() for value in args.route_types} if args.route_types else set()

    routes_header, routes_rows, route_type_by_id = load_route_types(input_dir / "routes.txt")
    trips_header, trips_rows, route_by_trip, service_by_trip, shape_by_trip = load_trips(input_dir / "trips.txt")
    stops_header, stops_rows, stops_by_id = load_stops(input_dir / "stops.txt")

    bbox_stop_ids = stops_in_bbox(stops_rows, args.lat_min, args.lat_max, args.lon_min, args.lon_max)
    if not bbox_stop_ids:
        raise RuntimeError("Bounding box did not match any stops.")

    stop_times_path = input_dir / "stop_times.txt"
    trips_touching_bbox = gather_candidate_trip_ids(stop_times_path, bbox_stop_ids)

    selected_trip_ids: Set[str] = set()
    for trip_id in trips_touching_bbox:
        route_id = route_by_trip.get(trip_id)
        route_type = route_type_by_id.get(route_id, "")
        if allowed_route_types and route_type not in allowed_route_types:
            continue
        selected_trip_ids.add(trip_id)

    if args.max_trips_per_route and args.max_trips_per_route > 0:
        selected_trip_ids = limit_trip_ids(selected_trip_ids, trips_rows, args.max_trips_per_route)

    if not selected_trip_ids:
        raise RuntimeError("No trips matched bounding box and route types.")

    trip_rows_filtered = [row for row in trips_rows if (row.get("trip_id") or "").strip() in selected_trip_ids]
    selected_route_ids = {row.get("route_id", "").strip() for row in trip_rows_filtered}
    selected_service_ids = {row.get("service_id", "").strip() for row in trip_rows_filtered}
    selected_shape_ids = {row.get("shape_id", "").strip() for row in trip_rows_filtered if row.get("shape_id")}

    stop_times_header, stop_times_rows, referenced_stop_ids = filter_stop_times(stop_times_path, selected_trip_ids)

    route_rows_filtered = [row for row in routes_rows if (row.get("route_id") or "").strip() in selected_route_ids]

    stops_to_keep: Set[str] = set(referenced_stop_ids)
    # Retain parent stations for platforms/entrances.
    for stop_id in list(stops_to_keep):
        parent = (stops_by_id.get(stop_id, {}).get("parent_station") or "").strip()
        if parent:
            stops_to_keep.add(parent)
    stop_rows_filtered = [row for row in stops_rows if (row.get("stop_id") or "").strip() in stops_to_keep]

    calendar_header, calendar_rows = filter_calendar_file(input_dir / "calendar.txt", selected_service_ids)
    calendar_dates_header, calendar_dates_rows = filter_calendar_file(
        input_dir / "calendar_dates.txt", selected_service_ids
    )

    agency_header, agency_rows = read_csv(input_dir / "agency.txt")
    agencies_to_keep = {row.get("agency_id", "").strip() for row in route_rows_filtered if row.get("agency_id")}
    if agencies_to_keep:
        agency_rows = [row for row in agency_rows if (row.get("agency_id") or "").strip() in agencies_to_keep]

    freq_header, freq_rows = filter_frequencies(input_dir / "frequencies.txt", selected_trip_ids)
    shapes_header, shapes_rows = filter_shapes(input_dir / "shapes.txt", selected_shape_ids)

    if routes_header:
        write_csv(output_dir / "routes.txt", routes_header, route_rows_filtered)
    if trips_header:
        write_csv(output_dir / "trips.txt", trips_header, trip_rows_filtered)
    if stops_header:
        write_csv(output_dir / "stops.txt", stops_header, stop_rows_filtered)
    if stop_times_header:
        write_csv(output_dir / "stop_times.txt", stop_times_header, stop_times_rows)
    if calendar_header:
        write_csv(output_dir / "calendar.txt", calendar_header, calendar_rows)
    if calendar_dates_header:
        write_csv(output_dir / "calendar_dates.txt", calendar_dates_header, calendar_dates_rows)
    if agency_header:
        write_csv(output_dir / "agency.txt", agency_header, agency_rows)
    if freq_header:
        write_csv(output_dir / "frequencies.txt", freq_header, freq_rows)
    if shapes_header:
        write_csv(output_dir / "shapes.txt", shapes_header, shapes_rows)

    # Copy any remaining files untouched.
    produced = {path.name for path in output_dir.glob("*.txt")}
    for source in input_dir.glob("*.txt"):
        if source.name in produced:
            continue
        shutil.copy2(source, output_dir / source.name)

    print(f"Created subset in {output_dir}")
    print(f"Trips kept: {len(selected_trip_ids)}; Stops kept: {len(stops_to_keep)}; Routes kept: {len(selected_route_ids)}")


if __name__ == "__main__":
    main()
