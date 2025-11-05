"""
Main entry point for the build_agent_tracks pipeline.

Orchestrates: parse plans → build legs table → build tracks → match activities → write outputs.
"""
from __future__ import annotations

import argparse
import shutil
import typing as T
from pathlib import Path

import pandas as pd

from .activity_matcher import (
    add_activity_summaries,
    extract_activities_by_person,
    match_activity_to_tracks,
)
from .filter_events import filter_events_for_via, filter_events_for_via_with_timeranges
from .legs_builder import build_legs_table
from .parsers import (
    count_total_vehicles_from_xml,
    extract_agent_vehicle_timeranges,
    load_actively_used_vehicles,
    load_transit_mode_lookup,
    load_transit_route_stops,
    parse_population_or_plans,
)
from .tracks_builder import DEFAULT_INCLUDED_MODES, build_tracks_from_legs
from .vehicle_filter import create_vehicle_usage_report, write_filtered_vehicles_csv


def run_pipeline(
    plans_path: str,
    population_fallback: str | None,
    events_path: str | None,
    outdir: str,
    dt: int = 5,
    schedule_path: str | None = None,
    vehicles_path: str | None = None,
    network_path: str | None = None,
    include_modes: T.Collection[str] | None = None,
    add_activity_matching: bool = True,
    export_filtered_events: bool = False,
) -> dict[str, str]:
    """
    Orchestrate: parse plans (or population), build legs table, build tracks,
    match activities, write CSVs, optionally filter events.

    Args:
        plans_path: Path to plans.xml(.gz)
        population_fallback: Fallback to population.xml(.gz) if plans not found
        events_path: Optional events.xml(.gz) for vehicle filtering
        outdir: Output directory for generated CSVs
        dt: Sampling interval in seconds for tracks
        schedule_path: Optional transitSchedule.xml(.gz) for PT enrichment
        vehicles_path: Optional transitVehicles.xml(.gz) for total vehicle count
        network_path: Optional network.xml(.gz) to copy for Via visualization
        include_modes: Modes to include in tracks (defaults to walk + transit)
        add_activity_matching: Whether to match activities to tracks (default: True)
        export_filtered_events: Whether to export filtered events.xml for Via (default: False)

    Returns:
        Dict of output file paths
    """
    Path(outdir).mkdir(parents=True, exist_ok=True)

    # Load plans/population
    src = plans_path if (plans_path and Path(plans_path).exists()) else (population_fallback or "")
    if not src or not Path(src).exists():
        raise FileNotFoundError("Neither plans nor population file could be found.")

    print(f"Loading plans from: {src}")
    plans = parse_population_or_plans(src)
    print(f"  Loaded {len(plans)} agents")

    # Load transit schedule info (optional)
    route_modes, line_modes = load_transit_mode_lookup(schedule_path)
    stop_coords, route_stops = load_transit_route_stops(schedule_path)

    # Build legs table
    print("Building legs table...")
    legs_df = build_legs_table(
        plans,
        route_modes=route_modes,
        line_modes=line_modes,
        stop_coords=stop_coords,
        route_stops=route_stops,
    )
    print(f"  Created {len(legs_df)} leg entries")

    # Save legs table
    legs_csv = str(Path(outdir) / "legs_table.csv")
    legs_df.to_csv(legs_csv, index=False)
    outputs = {"legs_csv": legs_csv}

    # Build tracks
    print(f"Building tracks (sampling every {dt}s)...")
    tracks_df = build_tracks_from_legs(legs_df, dt=dt, include_modes=include_modes)
    print(f"  Created {len(tracks_df)} track points")

    # Match activities to tracks
    if add_activity_matching:
        print("Matching activities to tracks...")
        activities_by_person = extract_activities_by_person(plans)
        tracks_df = match_activity_to_tracks(tracks_df, activities_by_person)
        tracks_df = add_activity_summaries(tracks_df)
        print(f"  Matched activities for {len(activities_by_person)} agents")

    # Save tracks (CSV)
    tracks_csv = str(Path(outdir) / f"tracks_dt{dt}s.csv")
    tracks_df.to_csv(tracks_csv, index=False)
    outputs["tracks_csv"] = tracks_csv

    # Save tracks (Parquet, optional)
    try:
        tracks_parquet = str(Path(outdir) / f"tracks_dt{dt}s.parquet")
        tracks_df.to_parquet(tracks_parquet, index=False)
        outputs["tracks_parquet"] = tracks_parquet
    except Exception as e:
        print(f"Warning: Could not write Parquet: {e}")

    # Vehicle filtering (optional)
    if events_path and Path(str(events_path)).exists():
        try:
            print("Processing vehicle usage...")

            # Dynamically extract agent IDs from parsed plans
            real_agent_ids = {plan.person_id for plan in plans}
            print(f"  Found {len(real_agent_ids)} real agents: {sorted(real_agent_ids)}")

            # Load vehicles used by these agents from events
            used_vehicles = load_actively_used_vehicles(events_path, agent_ids=real_agent_ids)

            if used_vehicles:
                filtered_vehicles_csv = write_filtered_vehicles_csv(used_vehicles, outdir)
                outputs["filtered_vehicles_csv"] = filtered_vehicles_csv

                # Count total vehicles dynamically from transitVehicles.xml if provided
                # Otherwise fall back to estimating from used vehicles
                if vehicles_path and Path(str(vehicles_path)).exists():
                    total_vehicles = count_total_vehicles_from_xml(vehicles_path)
                    print(f"  Total vehicles (from {vehicles_path}): {total_vehicles}")
                else:
                    # Fallback: estimate based on used vehicles (conservative estimate)
                    total_vehicles = len(used_vehicles)
                    print(f"  No vehicles_path provided. Using used vehicles count: {total_vehicles}")

                report_path = create_vehicle_usage_report(total_vehicles, used_vehicles, outdir)
                outputs["vehicle_usage_report"] = report_path

                print(f"\nVehicle filtering complete:")
                print(f"  Total vehicles: {total_vehicles}")
                print(f"  Agent-used vehicles: {len(used_vehicles)}")
                if total_vehicles > 0:
                    compression = 100.0 * (1.0 - len(used_vehicles) / total_vehicles)
                    print(f"  Compression: {compression:.1f}%")
        except Exception as e:
            print(f"Warning: Vehicle filtering failed: {e}")

    # Export filtered events for Via (optional) with fine-grained time filtering
    if export_filtered_events and events_path and Path(str(events_path)).exists():
        try:
            print("\n" + "=" * 70)
            print("VIA事件精細過濾開始")
            print("=" * 70)
            real_agent_ids = {plan.person_id for plan in plans}

            # CHECKPOINT 1: Extract time ranges
            print("\n[1/3] 提取 agent-vehicle 使用時間範圍...")
            time_ranges = extract_agent_vehicle_timeranges(events_path, agent_ids=real_agent_ids)

            if time_ranges:
                print(f"  ✓ 發現 {len(time_ranges)} 個 agent-vehicle 組合")
                for (agent, veh), times in sorted(time_ranges.items()):
                    time_strs = [
                        f"({int(enter/3600):02d}:{int((enter%3600)/60):02d}:{enter%60:02d}-"
                        f"{int(leave/3600):02d}:{int((leave%3600)/60):02d}:{leave%60:02d})"
                        for enter, leave in times
                    ]
                    print(f"    {agent} × {veh}: {', '.join(time_strs)}")

            # Get vehicle IDs from time ranges
            vehicle_ids = set(veh for (agent, veh) in time_ranges.keys())

            # CHECKPOINT 2: Pre-filter confirmation
            print("\n[2/3] 準備事件過濾參數...")
            print(f"  原始事件檔案: {events_path}")
            print(f"  輸出目錄: {outdir}")
            print(f"  Agent 數量: {len(real_agent_ids)}")
            print(f"  Vehicle 數量: {len(vehicle_ids)}")
            print(f"  時間範圍數: {sum(len(times) for times in time_ranges.values())}")

            # CHECKPOINT 3: Execute fine-grained filtering
            print("\n[3/3] 執行精細過濾 (處理中...)...")
            filtered_events_path = filter_events_for_via_with_timeranges(
                events_path, outdir, real_agent_ids,
                vehicle_ids=vehicle_ids if vehicle_ids else None,
                time_ranges=time_ranges if time_ranges else None
            )
            outputs["filtered_events_xml"] = filtered_events_path
            print(f"  ✓ 過濾完成: {filtered_events_path}")
            print("=" * 70)

        except Exception as e:
            print(f"Warning: Event filtering failed: {e}")

    # Copy network file for Via (optional)
    if network_path and Path(str(network_path)).exists():
        try:
            print("\nCopying network file for Via...")
            outdir_path = Path(outdir)
            network_filename = Path(network_path).name
            network_dest = outdir_path / network_filename
            shutil.copy2(str(network_path), str(network_dest))
            outputs["network_file"] = str(network_dest)
            print(f"  Network file copied: {network_dest}")
        except Exception as e:
            print(f"Warning: Network file copy failed: {e}")

    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract MATSim agent legs and build time-sampled tracks for visualization."
    )
    parser.add_argument(
        "--plans",
        help="Path to plans.xml(.gz) (defaults to population if missing).",
        default="",
    )
    parser.add_argument(
        "--population",
        help="Fallback population.xml(.gz) if plans not provided.",
        default="",
    )
    parser.add_argument(
        "--events",
        help="Optional events.xml(.gz) for vehicle usage filtering.",
        default="",
    )
    parser.add_argument(
        "--schedule",
        help="Transit schedule XML(.gz) to enrich PT legs with transportMode.",
        default="",
    )
    parser.add_argument(
        "--vehicles",
        help="Transit vehicles XML(.gz) to count total vehicles for compression reporting.",
        default="",
    )
    parser.add_argument(
        "--network",
        help="Network XML(.gz) to copy for Via visualization.",
        default="",
    )
    parser.add_argument(
        "--export-filtered-events",
        action="store_true",
        help="Export filtered events.xml for Via (keeps only real agents).",
    )
    parser.add_argument(
        "--out",
        help="Output directory for generated CSV/Parquet files.",
        required=True,
    )
    parser.add_argument(
        "--dt",
        type=int,
        default=5,
        help="Sampling interval in seconds for generated tracks.",
    )
    parser.add_argument(
        "--include-mode",
        dest="include_modes",
        action="append",
        help="Leg modes to include in the sampled tracks. Can be specified multiple times. "
        f"Default: {sorted(DEFAULT_INCLUDED_MODES)}",
    )
    parser.add_argument(
        "--skip-activity-matching",
        action="store_true",
        help="Skip activity matching (faster for large datasets).",
    )
    return parser


def main(argv: T.Sequence[str] | None = None) -> None:
    """CLI entry point."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    include_modes = args.include_modes if args.include_modes else DEFAULT_INCLUDED_MODES
    outputs = run_pipeline(
        plans_path=args.plans,
        population_fallback=args.population or None,
        events_path=args.events or None,
        outdir=args.out,
        dt=args.dt,
        schedule_path=args.schedule or None,
        vehicles_path=args.vehicles or None,
        network_path=args.network or None,
        include_modes=include_modes,
        add_activity_matching=not args.skip_activity_matching,
        export_filtered_events=args.export_filtered_events,
    )

    print("\n" + "=" * 70)
    print("Generated output files:")
    print("=" * 70)
    for key, value in outputs.items():
        if value:
            print(f"  {key}: {value}")
    print("=" * 70)


if __name__ == "__main__":
    main()
