#!/usr/bin/env python3
"""
Stream a large JSON array into parquet without loading the full file.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Iterator, List, Optional

try:
    import ijson
except ImportError:
    sys.exit("ijson is required. Install with `pip install ijson`.")

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    sys.exit("pyarrow is required. Install with `pip install pyarrow`.")


DEFAULT_JSON = Path("AGENT/INPUT/5000_abm_format_outcome.json")
DEFAULT_PARQUET = Path("AGENT/OUTPUT/5000_abm_format_outcome_from_json.parquet")


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024


def iter_json_batches(
    json_path: Path, batch_size: int, limit: Optional[int]
) -> Iterator[List[dict]]:
    count = 0
    with json_path.open("rb") as handle:
        parser = ijson.items(handle, "item")
        batch: List[dict] = []
        for item in parser:
            if limit is not None and count >= limit:
                break
            batch.append(item)
            count += 1
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def print_json_summary(json_path: Path, head: int) -> None:
    if not json_path.exists():
        print(f"JSON not found: {json_path}")
        return

    print(f"File: {json_path}")
    print(f"Size: {format_bytes(json_path.stat().st_size)}")

    sample: List[dict] = []
    with json_path.open("rb") as handle:
        parser = ijson.items(handle, "item")
        for item in parser:
            sample.append(item)
            if len(sample) >= head:
                break

    if not sample:
        print("Preview: file is empty or not a top-level array.")
        return

    print(f"Preview (first {len(sample)} records):")
    print(json.dumps(sample, indent=2))


def convert_json_to_parquet(
    json_path: Path,
    parquet_path: Path,
    *,
    batch_size: int,
    limit: Optional[int],
    overwrite: bool,
) -> None:
    if not json_path.exists():
        raise FileNotFoundError(json_path)
    if parquet_path.exists() and not overwrite:
        raise FileExistsError(
            f"{parquet_path} already exists. Use --overwrite to replace it."
        )

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    writer: Optional[pq.ParquetWriter] = None
    rows_written = 0

    for batch in iter_json_batches(json_path, batch_size, limit):
        table = pa.Table.from_pylist(batch)
        if writer is None:
            writer = pq.ParquetWriter(parquet_path, table.schema, compression="snappy")
        writer.write_table(table)
        rows_written += len(batch)

    if writer is None:
        print("No rows were written; parquet file not created.")
        return

    writer.close()
    print(f"Wrote {rows_written} row(s) to {parquet_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a JSON array and optionally stream it to parquet."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_JSON,
        help=f"JSON file to read (default: {DEFAULT_JSON}).",
    )
    parser.add_argument(
        "--head",
        type=int,
        default=2,
        help="How many records to show when inspecting.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Parquet path to write. If omitted, the script only shows a summary. "
            f"(Recommended default: {DEFAULT_PARQUET})"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional number of records to convert (default: all records).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Records per chunk to process when writing parquet.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing parquet file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print_json_summary(args.input, args.head)

    if args.output:
        convert_json_to_parquet(
            args.input,
            args.output,
            batch_size=args.batch_size,
            limit=args.limit,
            overwrite=args.overwrite,
        )
    else:
        print("No --output provided; showing summary only.")


if __name__ == "__main__":
    main()
