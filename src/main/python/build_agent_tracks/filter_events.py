"""
Filter MATSim events XML to keep only specified agents.
Used to create lightweight event files for Via platform visualization.
"""
from __future__ import annotations

import typing as T
import xml.etree.ElementTree as ET
from pathlib import Path

from .utils import open_maybe_gz


def filter_events_by_agents(
    input_events_path: T.Union[str, Path],
    output_events_path: T.Union[str, Path],
    agent_ids: set[str],
    vehicle_ids: set[str] | None = None,
    time_ranges: dict[tuple[str, str], list[tuple[int, int]]] | None = None,
) -> int:
    """
    Filter events XML to keep only events involving specified agents and/or vehicles.

    Processes PersonEntersVehicle, PersonLeavesVehicle, vehicle traffic events, and other events.
    Optionally filters vehicle events to specific time ranges when agents use them.
    Outputs filtered events as XML file.

    Args:
        input_events_path: Path to input events.xml(.gz)
        output_events_path: Path to output events.xml (will be created/overwritten)
        agent_ids: Set of agent IDs to keep
        vehicle_ids: Set of vehicle IDs to keep (optional, for including vehicle trajectory events)
        time_ranges: Optional dict {(agent_id, vehicle_id): [(enter_s, leave_s), ...]}
                    If provided, vehicle events outside these ranges are filtered out

    Returns:
        Number of events written to output file
    """
    input_path = str(input_events_path)
    output_path = str(output_events_path)

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input events file not found: {input_path}")

    if not agent_ids:
        raise ValueError("agent_ids cannot be empty")

    events_written = 0
    events_skipped = 0

    # Initialize vehicle_ids if not provided
    if vehicle_ids is None:
        vehicle_ids = set()

    if time_ranges is None:
        time_ranges = {}

    def is_event_in_timerange(vehicle_id: str, time_s: int) -> bool:
        """Check if vehicle event is within allowed time ranges for any agent."""
        for (agent, veh), ranges in time_ranges.items():
            if veh == vehicle_id:
                for enter_s, leave_s in ranges:
                    if enter_s <= time_s <= leave_s:
                        return True
        return False

    try:
        # Open input (possibly compressed)
        with open_maybe_gz(input_path) as f:
            context = ET.iterparse(f, events=("start", "end"))
            _, root = next(context)

        # Create output root element
        output_root = ET.Element("events", version="1.0")

        # Reopen for reading
        with open_maybe_gz(input_path) as f:
            context = ET.iterparse(f, events=("start", "end"))
            _, root = next(context)

            for event, elem in context:
                if event == "end" and elem.tag == "event":
                    # Check if event involves any of our agents or vehicles
                    person_attr = elem.get("person")
                    vehicle_attr = elem.get("vehicle")
                    time_str = elem.get("time")

                    # Event passes filter if:
                    # - person is in agent_ids, OR
                    # - vehicle is in vehicle_ids AND (no time_ranges OR time is in allowed range)
                    agent_involved = (person_attr and person_attr in agent_ids)

                    vehicle_involved = False
                    if vehicle_attr and vehicle_attr in vehicle_ids:
                        # If we have time ranges, check if this vehicle event is in allowed time
                        if time_ranges:
                            time_s = int(float(time_str)) if time_str else 0
                            vehicle_involved = is_event_in_timerange(vehicle_attr, time_s)
                        else:
                            # No time ranges, keep all vehicle events
                            vehicle_involved = True

                    if agent_involved or vehicle_involved:
                        # Copy event to output
                        output_root.append(elem)
                        events_written += 1
                    else:
                        events_skipped += 1

                    root.clear()

        # Write output XML
        output_tree = ET.ElementTree(output_root)
        ET.indent(output_tree, space="  ")  # Pretty print (Python 3.9+)
        output_tree.write(output_path, encoding="utf-8", xml_declaration=True)

        print(f"Events filtering complete:")
        print(f"  Input: {input_path}")
        print(f"  Output: {output_path}")
        print(f"  Agents kept: {sorted(agent_ids)}")
        if vehicle_ids:
            print(f"  Vehicles kept: {sorted(vehicle_ids)}")
        print(f"  Events written: {events_written}")
        print(f"  Events skipped: {events_skipped}")
        print(f"  Compression ratio: {100.0 * events_written / (events_written + events_skipped):.1f}%")

        return events_written

    except Exception as e:
        raise RuntimeError(f"Error filtering events: {e}") from e


def filter_events_for_via(
    input_events_path: T.Union[str, Path],
    output_dir: T.Union[str, Path],
    agent_ids: set[str],
    vehicle_ids: set[str] | None = None,
) -> str:
    """
    Convenience function to filter events and save to output directory.

    Args:
        input_events_path: Path to input events.xml(.gz)
        output_dir: Output directory
        agent_ids: Set of agent IDs to keep
        vehicle_ids: Set of vehicle IDs to keep (optional, for vehicle trajectory events)

    Returns:
        Path to output events file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "output_events.xml"

    filter_events_by_agents(input_events_path, output_path, agent_ids, vehicle_ids=vehicle_ids)

    return str(output_path)


def filter_events_for_via_with_timeranges(
    input_events_path: T.Union[str, Path],
    output_dir: T.Union[str, Path],
    agent_ids: set[str],
    vehicle_ids: set[str] | None = None,
    time_ranges: dict[tuple[str, str], list[tuple[int, int]]] | None = None,
) -> str:
    """
    Filter events with fine-grained time range filtering for Via platform.

    Keeps only vehicle events that occur within the time ranges when agents
    actually use those vehicles (based on PersonEntersVehicle/LeavesVehicle events).

    Args:
        input_events_path: Path to input events.xml(.gz)
        output_dir: Output directory
        agent_ids: Set of agent IDs to keep
        vehicle_ids: Set of vehicle IDs to keep (optional)
        time_ranges: Dict {(agent_id, vehicle_id): [(enter_s, leave_s), ...]}
                    If provided, vehicle events outside these ranges are filtered out

    Returns:
        Path to output events file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "output_events.xml"

    filter_events_by_agents(
        input_events_path,
        output_path,
        agent_ids,
        vehicle_ids=vehicle_ids,
        time_ranges=time_ranges,
    )

    return str(output_path)
