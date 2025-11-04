#!/usr/bin/env python3
"""
Merge the GTFS feeds located in `../input/gtfs_tw_v5` and `../input/tp_metro_gtfs`.

The merged feed (plain text files) is written to `../middle/merged_gtfs` and
copied to `../output/merged_gtfs` with an additional ZIP archive
`../output/merged_gtfs.zip` for convenience.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Optional fallback headers to use when a source file does not include one.
FALLBACK_HEADERS: Dict[str, Sequence[str]] = {
    "agency.txt": (
        "agency_id",
        "agency_name",
        "agency_url",
        "agency_timezone",
        "agency_lang",
        "agency_phone",
        "agency_fare_url",
        "agency_email",
    ),
    "calendar.txt": (
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ),
    "calendar_dates.txt": ("service_id", "date", "exception_type"),
    "routes.txt": (
        "route_id",
        "agency_id",
        "route_short_name",
        "route_long_name",
        "route_desc",
        "route_type",
        "route_url",
        "route_color",
        "route_text_color",
    ),
    "stops.txt": (
        "stop_id",
        "stop_code",
        "stop_name",
        "stop_desc",
        "stop_lat",
        "stop_lon",
        "zone_id",
        "stop_url",
        "location_type",
        "parent_station",
        "stop_timezone",
        "wheelchair_boarding",
        "platform_code",
        "stop_x_EPSG3826",
        "stop_y_EPSG3826",
    ),
    "trips.txt": (
        "route_id",
        "service_id",
        "trip_id",
        "trip_headsign",
        "trip_short_name",
        "direction_id",
        "block_id",
        "shape_id",
        "wheelchair_accessible",
        "bikes_allowed",
    ),
    "frequencies.txt": ("trip_id", "start_time", "end_time", "headway_secs", "exact_times"),
    "stop_times.txt": (
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
        "pickup_type",
        "drop_off_type",
        "shape_dist_traveled",
        "timepoint",
    ),
}


def read_records(path: Path, fallback_header: Sequence[str] | None = None) -> Tuple[List[str], List[Dict[str, str]]]:
    """Read a GTFS CSV file and return (header, list of row dictionaries)."""
    rows: List[List[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for raw_row in reader:
            if not raw_row:
                continue
            # Preserve trailing empty fields
            rows.append([cell.strip() for cell in raw_row])

    if not rows:
        header = list(fallback_header) if fallback_header else []
        return header, []

    first_row = rows[0]
    expected_first_value = fallback_header[0] if fallback_header else None
    is_header = False
    if expected_first_value:
        is_header = first_row[0].strip().lower() == expected_first_value.lower()
    else:
        # Assume the first row is a header when it contains non-numeric text.
        is_header = any(c.isalpha() for c in "".join(first_row))

    if is_header:
        header = [col.strip() for col in first_row]
        data_rows = rows[1:]
    else:
        header = list(fallback_header) if fallback_header else [col.strip() for col in first_row]
        data_rows = rows if fallback_header else rows[1:]

    normalized_rows: List[Dict[str, str]] = []
    for raw in data_rows:
        if not any(cell for cell in raw):
            continue
        padded = list(raw) + [""] * max(0, len(header) - len(raw))
        record = {header[idx]: padded[idx] if idx < len(padded) else "" for idx in range(len(header))}
        normalized_rows.append(record)

    return list(header), normalized_rows


def merge_columns(headers: Iterable[Sequence[str]]) -> List[str]:
    merged: List[str] = []
    for header in headers:
        for column in header:
            if column not in merged:
                merged.append(column)
    return merged


def write_csv(path: Path, header: Sequence[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(header), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in header})


def filter_invalid_trips(base_dir: Path) -> None:
    trips_path = base_dir / "trips.txt"
    if not trips_path.exists():
        return

    service_ids: set[str] = set()
    for name in ("calendar.txt", "calendar_dates.txt"):
        path = base_dir / name
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "service_id" not in reader.fieldnames:
                continue
            for row in reader:
                sid = (row.get("service_id") or "").strip()
                if sid:
                    service_ids.add(sid)

    stop_times_path = base_dir / "stop_times.txt"
    stop_time_trip_ids: Optional[set[str]] = None
    if stop_times_path.exists():
        stop_time_trip_ids = set()
        with stop_times_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames and "trip_id" in reader.fieldnames:
                for row in reader:
                    tid = (row.get("trip_id") or "").strip()
                    if tid:
                        stop_time_trip_ids.add(tid)

    with trips_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        rows = list(reader)

    if not header or not rows:
        return

    filtered_rows: List[Dict[str, str]] = []
    kept_trip_ids: set[str] = set()
    for row in rows:
        sid = (row.get("service_id") or "").strip()
        tid = (row.get("trip_id") or "").strip()
        if sid and service_ids and sid not in service_ids:
            continue
        if stop_time_trip_ids is not None and tid and tid not in stop_time_trip_ids:
            continue
        filtered_rows.append(row)
        if tid:
            kept_trip_ids.add(tid)

    removed = len(rows) - len(filtered_rows)
    if removed > 0:
        write_csv(trips_path, header, filtered_rows)
        print(
            f"Filtered trips.txt: removed {removed} rows lacking calendar/stop_times. "
            f"Remaining: {len(filtered_rows)}"
        )
    else:
        print("Filtered trips.txt: no rows removed.")

    if stop_times_path.exists() and stop_time_trip_ids is not None:
        with stop_times_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            st_header = reader.fieldnames or []
            if kept_trip_ids:
                st_rows = [row for row in reader if (row.get("trip_id") or "").strip() in kept_trip_ids]
            else:
                st_rows = []
        if st_header:
            write_csv(stop_times_path, st_header, st_rows)
            print(f"Filtered stop_times.txt: kept {len(st_rows)} rows.")

    freq_path = base_dir / "frequencies.txt"
    if freq_path.exists():
        with freq_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            freq_header = reader.fieldnames or []
            if kept_trip_ids:
                freq_rows = [row for row in reader if (row.get("trip_id") or "").strip() in kept_trip_ids]
            else:
                freq_rows = []
        if freq_header:
            write_csv(freq_path, freq_header, freq_rows)
            print(f"Filtered frequencies.txt: kept {len(freq_rows)} rows.")

def main() -> None:
    combine_dir = Path(__file__).resolve().parent.parent
    input_dir = combine_dir / "input"
    middle_dir = combine_dir / "middle"
    output_dir = combine_dir / "output"

    feed_dirs = [
        input_dir / "gtfs_tw_v5",
        input_dir / "tp_metro_gtfs",
    ]
    for feed_dir in feed_dirs:
        if not feed_dir.exists():
            raise FileNotFoundError(f"Feed directory missing: {feed_dir}")

    work_dir = middle_dir / "merged_gtfs"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    file_names = sorted({path.name for feed_dir in feed_dirs for path in feed_dir.glob("*.txt")})
    for file_name in file_names:
        per_feed_rows: List[Tuple[List[str], List[Dict[str, str]]]] = []
        for feed_dir in feed_dirs:
            candidate = feed_dir / file_name
            if not candidate.exists():
                continue
            header, rows = read_records(candidate, FALLBACK_HEADERS.get(file_name))
            per_feed_rows.append((header, rows))

        if not per_feed_rows:
            continue

        merged_header = merge_columns(header for header, _ in per_feed_rows)
        merged_rows: List[Dict[str, str]] = []
        for header, rows in per_feed_rows:
            for row in rows:
                normalized = {column: row.get(column, "") for column in merged_header}
                merged_rows.append(normalized)

        write_csv(work_dir / file_name, merged_header, merged_rows)
        print(f"Merged {file_name}: {len(merged_rows)} rows, {len(merged_header)} columns.")

    filter_invalid_trips(work_dir)

    output_feed_dir = output_dir / "merged_gtfs"
    if output_feed_dir.exists():
        shutil.rmtree(output_feed_dir)
    shutil.copytree(work_dir, output_feed_dir)

    zip_base = output_dir / "merged_gtfs"
    zip_file = zip_base.with_suffix(".zip")
    if zip_file.exists():
        zip_file.unlink()
    shutil.make_archive(str(zip_base), "zip", output_feed_dir)
    print(f"\nMerged feed folder: {output_feed_dir}")
    print(f"Merged feed archive: {zip_file}")


if __name__ == "__main__":
    main()
