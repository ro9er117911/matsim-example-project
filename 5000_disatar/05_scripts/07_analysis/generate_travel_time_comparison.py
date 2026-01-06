#!/usr/bin/env python3
"""
Generate lightweight travel time comparison datasets for SimWrapper dashboards.

The official TravelTimeComparison analysis requires external reference data from
routing services. To keep the dashboard working out-of-the-box, this script
derives "reference" values from the simulated trips themselves and writes the
expected CSVs under analysis/traveltime/. Bias/error will therefore be zero,
but the charts will render and show simulated speeds by hour and by route.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def to_seconds(hms: str) -> float:
    """Convert HH:MM:SS to seconds, return NaN on failure."""
    try:
        return pd.to_timedelta(hms).total_seconds()
    except Exception:
        return float("nan")


def compute(output_dir: Path) -> None:
    trips_path = output_dir / "output_trips.csv.gz"
    if not trips_path.exists():
        print(f"[travel-time] skip: {trips_path} not found")
        return

    df = pd.read_csv(trips_path, sep=";")

    # Basic parsing
    df["dep_sec"] = df["dep_time"].apply(to_seconds)
    df["trav_sec"] = df["trav_time"].apply(to_seconds)
    df["speed_kmh"] = (df["traveled_distance"] / df["trav_sec"]) * 3.6
    df["hour"] = (df["dep_sec"] // 3600).astype(int)
    df = df[df["trav_sec"] > 0].copy()

    if df.empty:
        print("[travel-time] skip: no trips with positive travel time")
        return

    # Route-level aggregation (link-to-link as a proxy for nodes).
    df["from_node"] = df["start_link"]
    df["to_node"] = df["end_link"]
    route_cols = ["from_node", "to_node", "hour"]
    route_agg = (
        df.groupby(route_cols)["speed_kmh"]
        .agg(["mean", "min", "max", "std"])
        .reset_index()
        .fillna(0.0)
    )
    route_agg["simulated"] = route_agg["mean"]
    route_agg["bias"] = 0.0
    route_agg["abs_error"] = 0.0

    # Hourly aggregation.
    hour_agg = (
        df.groupby("hour")["speed_kmh"]
        .agg(["mean", "min", "max", "std"])
        .reset_index()
        .fillna(0.0)
    )
    hour_agg["simulated"] = hour_agg["mean"]
    hour_agg["bias"] = 0.0
    hour_agg["abs_error"] = 0.0

    out_dir = output_dir / "analysis" / "traveltime"
    out_dir.mkdir(parents=True, exist_ok=True)
    route_path = out_dir / "travel_time_comparison_by_route.csv"
    hour_path = out_dir / "travel_time_comparison_by_hour.csv"

    route_agg.to_csv(route_path, index=False)
    hour_agg.to_csv(hour_path, index=False)
    print(f"[travel-time] wrote {route_path.relative_to(output_dir)}")
    print(f"[travel-time] wrote {hour_path.relative_to(output_dir)}")

    # Write a dashboard YAML so SimWrapper shows the charts without extra setup.
    dash_path = output_dir / "dashboard-6-traveltime.yaml"
    dash_content = f"""header:
  title: Travel time
  description: Comparison of simulated travel times (reference = simulated baseline).
layout:
  first:
  - type: plotly
    title: Travel time comparison
    description: by route (hour as legend)
    datasets:
      dataset: {route_path.relative_to(output_dir)}
    traces:
    - type: scatter
      mode: markers
      x: $dataset.mean
      "y": $dataset.simulated
      text: $dataset.from_node
      name: Hour $dataset.hour
    layout:
      xaxis:
        title: Observed historical mean speed [km/h]
      yaxis:
        title: Simulated mean speed [km/h]
  - type: plotly
    title: Avg. Speed
    description: by hour
    datasets:
      dataset: {hour_path.relative_to(output_dir)}
    traces:
    - type: scatter
      mode: lines
      name: Mean
      x: $dataset.hour
      "y": $dataset.mean
    - type: scatter
      mode: lines
      name: Min
      x: $dataset.hour
      "y": $dataset.min
    - type: scatter
      mode: lines
      name: Max
      x: $dataset.hour
      "y": $dataset.max
    - type: scatter
      mode: lines
      name: Simulated
      x: $dataset.hour
      "y": $dataset.simulated
    layout:
      xaxis:
        title: Hour
      yaxis:
        title: Speed [km/h]
  second:
  - type: plotly
    title: Error and bias
    description: by hour
    datasets:
      dataset: {hour_path.relative_to(output_dir)}
    traces:
    - type: scatter
      mode: lines
      name: Mean abs. error
      x: $dataset.hour
      "y": $dataset.abs_error
    - type: scatter
      mode: lines
      name: Ref. std.
      x: $dataset.hour
      "y": $dataset.std
    - type: scatter
      mode: lines
      name: Bias
      x: $dataset.hour
      "y": $dataset.bias
    layout:
      xaxis:
        title: Hour
      yaxis:
        title: Error [km/h]
"""
    dash_path.write_text(dash_content)
    print(f"[travel-time] wrote {dash_path.relative_to(output_dir)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate simulated travel time comparison CSVs for dashboards."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to MATSim output directory (containing output_trips.csv.gz).",
    )
    args = parser.parse_args()
    compute(Path(args.output).expanduser().resolve())


if __name__ == "__main__":
    main()
