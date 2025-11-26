#!/usr/bin/env python3
"""
Convert MATSim events to agent-level JSON + Parquet with the simple schema:
  - agent_id (int)
  - weekday_path: list of {position: [lat, lon], mode: STR}
  - weekday_timestamp: list<int>

Coordinates are WGS84 lat/lon and aligned with the event-derived trajectories.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

from events_to_json_parquet import (
    MODE_ENCODING,
    create_coordinate_transformer,
    extract_agent_id,
    group_events_by_person,
    parse_events_xml,
    parse_network_xml,
    reconstruct_person_trajectory,
)


# --------------------------------------------------------------------------- #
# Core builder
# --------------------------------------------------------------------------- #
def build_agent_data(events_path: str, network_path: str) -> List[Dict]:
    """
    Parse events/network and reconstruct trajectories into agent-level records.
    """
    events = parse_events_xml(events_path)
    links, graph = parse_network_xml(network_path)
    transformer = create_coordinate_transformer()
    person_events = group_events_by_person(events)

    agent_data: List[Dict] = []
    for person_id, events_list in person_events.items():
        positions, modes_list, timestamps_list = reconstruct_person_trajectory(
            events_list, links, graph, transformer
        )
        if not positions:
            continue

        agent_id = extract_agent_id(person_id)
        agent_data.append(
            {
                "agent_id": agent_id,
                "positions": positions,  # [[lat, lon], ...]
                "modes": modes_list,  # ["CAR", "WALK", ...]
                "timestamps": [int(t) for t in timestamps_list],
            }
        )

    return agent_data


# --------------------------------------------------------------------------- #
# Export helpers
# --------------------------------------------------------------------------- #
def export_json(agent_data: List[Dict], json_path: Path):
    """
    Write JSON in the reference format:
    [
      {
        "agent_id": int,
        "weekday_path": [{"position": [lat, lon], "mode": "CAR"}, ...],
        "weekday_timestamp": [int, ...]
      },
      ...
    ]
    """
    json_path.parent.mkdir(parents=True, exist_ok=True)
    # Emit a small header preview
    if agent_data:
        first = agent_data[0]
        print("JSON fields:", list(first.keys()))
    else:
        print("JSON fields: <no agents>")

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(agent_data, f, ensure_ascii=False, indent=2)


def export_parquet(agent_data: List[Dict], parquet_path: Path):
    """
    Write Parquet in the template schema:
      agent_id: int64
      modes: list<int8>
      timestamps: list<int32>
      geometry: list<struct<x: double, y: double>>
    """
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    agent_ids = []
    modes_col = []
    timestamps_col = []
    geometry_col = []

    for rec in agent_data:
        agent_ids.append(int(rec["agent_id"]))
        mode_codes = [
            MODE_ENCODING.get(str(mode).lower(), (3, "PT"))[0]
            for mode in rec["modes"]
        ]
        modes_col.append(mode_codes)
        timestamps_col.append([int(t) for t in rec["timestamps"]])
        coords = [{"x": float(lat), "y": float(lon)} for lat, lon in rec["positions"]]
        geometry_col.append(coords)

    geometry_type = pa.list_(
        pa.struct(
            [
                pa.field("x", pa.float64(), nullable=False),
                pa.field("y", pa.float64(), nullable=False),
            ]
        )
    )

    schema = pa.schema(
        [
            pa.field("agent_id", pa.int64()),
            pa.field("modes", pa.list_(pa.int8())),
            pa.field("timestamps", pa.list_(pa.int32())),
            pa.field("geometry", geometry_type),
        ]
    )

    print("Parquet schema to be written:")
    print(schema)

    table = pa.Table.from_arrays(
        [
            pa.array(agent_ids, type=pa.int64()),
            pa.array(modes_col, type=pa.list_(pa.int8())),
            pa.array(timestamps_col, type=pa.list_(pa.int32())),
            pa.array(geometry_col, type=geometry_type),
        ],
        schema=schema,
    )
    pq.write_table(table, parquet_path, compression="snappy")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert MATSim output_events.xml to agent-level JSON + Parquet."
    )
    parser.add_argument("--events", required=True, help="Path to output_events.xml[.gz]")
    parser.add_argument("--network", required=True, help="Path to network.xml[.gz]")
    parser.add_argument("--json-out", required=True, help="Destination JSON path")
    parser.add_argument("--parquet-out", required=True, help="Destination Parquet path")
    return parser.parse_args()


def main():
    args = parse_args()
    events_path = args.events
    network_path = args.network
    json_path = Path(args.json_out)
    parquet_path = Path(args.parquet_out)

    print("=" * 70)
    print("MATSim events → Agent JSON & Parquet")
    print("=" * 70)
    print(f"Events : {events_path}")
    print(f"Network: {network_path}")
    print(f"JSON   : {json_path}")
    print(f"Parquet: {parquet_path}")

    print("\n[1/2] Reconstructing trajectories...")
    agent_data = build_agent_data(events_path, network_path)
    print(f"  Got {len(agent_data)} agents")

    print("\n[2/2] Writing outputs...")
    export_json(
        [
            {
                "agent_id": rec["agent_id"],
                "weekday_path": [
                    {"position": pos, "mode": mode}
                    for pos, mode in zip(rec["positions"], rec["modes"])
                ],
                "weekday_timestamp": rec["timestamps"],
            }
            for rec in agent_data
        ],
        json_path,
    )

    export_parquet(agent_data, parquet_path)
    print("  ✓ JSON and Parquet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
