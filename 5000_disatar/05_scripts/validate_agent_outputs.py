#!/usr/bin/env python3
"""
Validate agent JSON/Parquet outputs against a template format.

Checks:
- JSON: top-level list of objects with keys agent_id (int), weekday_path (list of {position:[lat,lon], mode:str}),
        weekday_timestamp (list of int). Compares keys to a template JSON.
- Parquet: schema and field types compared to a template Parquet.

Usage:
  python validate_agent_outputs.py \
    --json /path/to/agent_traj.json \
    --parquet /path/to/agent_traj.parquet \
    --json-template 5000_disatar/01_raw_data/agent_abm/5000_abm_format_outcome.json \
    --parquet-template 5000_disatar/01_raw_data/agent_abm/5000_abm_format_outcome.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

import pyarrow.parquet as pq


def load_first_object_from_json(path: Path) -> Dict[str, Any]:
    """
    Read just the first JSON object from a large array file without loading everything.
    """
    with path.open("r", encoding="utf-8") as f:
        data = f.read(2_000_000)  # read first ~2MB
    start = data.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in {path}")
    stack = 0
    end = None
    for i, ch in enumerate(data[start:], start):
        if ch == "{":
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0:
                end = i
                break
    if end is None:
        raise ValueError(f"Could not parse first object in {path}")
    return json.loads(data[start : end + 1])


def compare_json_struct(sample: Dict[str, Any], template: Dict[str, Any]) -> List[str]:
    """
    Compare keys and basic types between sample and template JSON objects.
    """
    messages = []
    sample_keys = set(sample.keys())
    template_keys = set(template.keys())
    if sample_keys != template_keys:
        messages.append(f"JSON keys differ. sample={sorted(sample_keys)}, template={sorted(template_keys)}")
    for key in sorted(sample_keys & template_keys):
        s_val = sample[key]
        t_val = template[key]
        if isinstance(s_val, type(t_val)):
            continue
        messages.append(f"JSON field '{key}' type differs: sample={type(s_val).__name__}, template={type(t_val).__name__}")
    return messages


def compare_parquet_schema(sample_path: Path, template_path: Path) -> List[str]:
    """
    Compare Parquet schemas (field names and types).
    """
    messages = []
    sample_schema = pq.read_schema(sample_path)
    template_schema = pq.read_schema(template_path)
    if sample_schema != template_schema:
        messages.append(f"Parquet schema mismatch:\nSample:\n{sample_schema}\nTemplate:\n{template_schema}")
    return messages


def run_validation(args: argparse.Namespace) -> int:
    errors: List[str] = []

    # JSON validation
    sample_json_obj = load_first_object_from_json(Path(args.json))
    template_json_obj = load_first_object_from_json(Path(args.json_template))
    errors.extend(compare_json_struct(sample_json_obj, template_json_obj))

    # Parquet validation
    errors.extend(compare_parquet_schema(Path(args.parquet), Path(args.parquet_template)))

    if errors:
        print("Validation FAILED:")
        for msg in errors:
            print(" -", msg)
        return 1
    else:
        print("Validation PASSED: JSON structure and Parquet schema match the templates.")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate agent JSON/Parquet against templates.")
    parser.add_argument("--json", required=True, help="Sample JSON to validate")
    parser.add_argument("--parquet", required=True, help="Sample Parquet to validate")
    parser.add_argument(
        "--json-template",
        default="5000_disatar/01_raw_data/agent_abm/5000_abm_format_outcome.json",
        help="Template JSON file",
    )
    parser.add_argument(
        "--parquet-template",
        default="5000_disatar/01_raw_data/agent_abm/5000_abm_format_outcome.parquet",
        help="Template Parquet file",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    exit_code = run_validation(args)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
