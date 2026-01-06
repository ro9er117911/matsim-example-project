#!/usr/bin/env python3
"""
Inspect a parquet file without loading it all, and optionally stream it to JSON.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

try:
    import pyarrow.parquet as pq
except ImportError:
    sys.exit("pyarrow is required. Install with `pip install pyarrow`.")


DEFAULT_PARQUET = Path("AGENT/OUTPUT/5000_abm_format_outcome.parquet")


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024


def print_parquet_summary(parquet_path: Path, head: int) -> None:
    if not parquet_path.exists():
        print(f"Parquet not found: {parquet_path}")
        return

    pf = pq.ParquetFile(parquet_path)
    metadata = pf.metadata
    row_count = metadata.num_rows if metadata is not None else None
    print(f"File: {parquet_path}")
    print(f"Size: {format_bytes(parquet_path.stat().st_size)}")
    if row_count is not None:
        print(f"Rows (metadata): {row_count}")
    print("Columns:", list(pf.schema.names))
    print("Schema:")
    print(pf.schema)

    if head > 0:
        batch = next(pf.iter_batches(batch_size=head), None)
        if batch is None:
            print("Preview: file is empty")
            return
        preview = batch.to_pylist()[:head]
        print(f"Preview (first {len(preview)} rows):")
        print(json.dumps(preview, indent=2))


def convert_parquet_to_json(
    parquet_path: Path,
    json_path: Path,
    *,
    batch_size: int,
    limit: Optional[int],
    overwrite: bool,
) -> None:
    if not parquet_path.exists():
        raise FileNotFoundError(parquet_path)
    if json_path.exists() and not overwrite:
        raise FileExistsError(
            f"{json_path} already exists. Use --overwrite to replace it."
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    pf = pq.ParquetFile(parquet_path)
    rows_written = 0
    with json_path.open("w", encoding="utf-8") as handle:
        handle.write("[\n")
        first = True
        for batch in pf.iter_batches(batch_size=batch_size):
            rows = batch.to_pylist()
            for row in rows:
                if limit is not None and rows_written >= limit:
                    break
                if not first:
                    handle.write(",\n")
                json.dump(row, handle, ensure_ascii=False)
                first = False
                rows_written += 1
            if limit is not None and rows_written >= limit:
                break
        handle.write("\n]\n")
    print(f"Wrote {rows_written} row(s) to {json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a parquet file and optionally convert it to JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_PARQUET,
        help=f"Parquet file to read (default: {DEFAULT_PARQUET}).",
    )
    parser.add_argument(
        "--head",
        type=int,
        default=3,
        help="How many rows to show when inspecting.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path. If omitted, the script only shows a summary.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional number of rows to write to JSON (default: all rows).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Rows per chunk to process when writing JSON.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing JSON file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print_parquet_summary(args.input, args.head)

    if args.output:
        convert_parquet_to_json(
            args.input,
            args.output,
            batch_size=args.batch_size,
            limit=args.limit,
            overwrite=args.overwrite,
        )


if __name__ == "__main__":
    main()
