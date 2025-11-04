"""
XML parsers for MATSim files (population, events, schedule).
"""
from __future__ import annotations

import json
import typing as T
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Activity, Leg, PlanEntry, PersonPlan
from .utils import hhmmss_to_seconds, open_maybe_gz


def parse_population_or_plans(xml_path: T.Union[str, Path]) -> list[PersonPlan]:
    """
    Parse a MATSim population/plans XML file into structured plans.
    Uses iterparse to save memory on large files.
    """
    people: list[PersonPlan] = []

    with open_maybe_gz(xml_path) as f:
        context = ET.iterparse(f, events=("start", "end"))
        _, root = next(context)  # get root
        current_person_id = None
        current_plan_entries: list[PlanEntry] = []
        in_selected_plan = False

        act_tmp = None
        for event, elem in context:
            tag = elem.tag
            if event == "start":
                if tag == "person":
                    current_person_id = elem.get("id")
                    current_plan_entries = []
                elif tag == "plan":
                    in_selected_plan = (elem.get("selected", "no") == "yes")
                elif tag == "activity" and in_selected_plan:
                    a_type = elem.get("type")
                    x = elem.get("x")
                    y = elem.get("y")
                    link = elem.get("link")
                    st = elem.get("start_time") or elem.get("startTime")
                    et = elem.get("end_time") or elem.get("endTime") or elem.get("max_dur")
                    start_s = hhmmss_to_seconds(st)
                    end_s = hhmmss_to_seconds(et) if (et and ":" in et) else None
                    act_tmp = Activity(
                        type=a_type,
                        x=float(x) if x else None,
                        y=float(y) if y else None,
                        link=link,
                        start_time_s=start_s,
                        end_time_s=end_s,
                    )
                elif tag == "leg" and in_selected_plan:
                    mode = elem.get("mode")
                    dep_time_s = hhmmss_to_seconds(elem.get("dep_time") or elem.get("departure_time"))
                    trav_time_s = hhmmss_to_seconds(elem.get("trav_time") or elem.get("travel_time"))
                    leg_tmp = Leg(
                        mode=mode,
                        dep_time_s=dep_time_s,
                        trav_time_s=trav_time_s,
                    )
                    current_plan_entries.append(PlanEntry(kind="leg", data=leg_tmp))
            elif event == "end":
                if tag == "attribute" and in_selected_plan and current_plan_entries and current_plan_entries[-1].kind == "leg":
                    leg: Leg = T.cast(Leg, current_plan_entries[-1].data)
                    nm = elem.get("name")
                    val = elem.text or ""
                    leg.attrs[nm] = val
                elif tag == "route" and in_selected_plan and current_plan_entries and current_plan_entries[-1].kind == "leg":
                    leg: Leg = T.cast(Leg, current_plan_entries[-1].data)
                    leg.route_type = elem.get("type")
                    leg.start_link = elem.get("start_link")
                    leg.end_link = elem.get("end_link")
                    dist = elem.get("distance")
                    leg.distance = float(dist) if dist else None
                    leg.vehicleRefId = elem.get("vehicleRefId")
                    leg.route_raw = (elem.text or "").strip()
                elif tag == "activity" and in_selected_plan:
                    current_plan_entries.append(PlanEntry(kind="act", data=act_tmp))
                    act_tmp = None
                elif tag == "plan":
                    if in_selected_plan:
                        people.append(PersonPlan(person_id=current_person_id, entries=current_plan_entries))
                    in_selected_plan = False
                elif tag == "person":
                    current_person_id = None
                    current_plan_entries = []
                    root.clear()
        return people


def parse_pt_json(route_raw: str) -> dict:
    """
    Parse JSON embedded in <route> for default_pt legs.
    MATSim uses JSON payload containing transitRouteId, transitLineId, etc.
    """
    try:
        return json.loads(route_raw)
    except Exception:
        return {}


def load_transit_mode_lookup(schedule_path: T.Union[str, Path, None]) -> tuple[dict[str, str], dict[str, str]]:
    """
    Parse a transitSchedule and return (route_id -> mode, line_id -> mode).
    """
    route_modes: dict[str, str] = {}
    line_modes: dict[str, str] = {}

    if not schedule_path:
        return route_modes, line_modes

    schedule_path = str(schedule_path)
    if not Path(schedule_path).exists():
        return route_modes, line_modes

    with open_maybe_gz(schedule_path) as f:
        tree = ET.parse(f)

    root = tree.getroot()
    for line in root.findall(".//transitLine"):
        line_id = line.get("id")
        transport_elem = line.find("./transportMode")
        mode = None
        if transport_elem is not None and transport_elem.text:
            mode = transport_elem.text.strip()
        if line_id and mode:
            line_modes[line_id] = mode
        for route in line.findall("./transitRoute"):
            route_id = route.get("id")
            mode_elem = route.find("./transportMode")
            r_mode = mode_elem.text.strip() if (mode_elem is not None and mode_elem.text) else mode
            if route_id and r_mode:
                route_modes[route_id] = r_mode

    return route_modes, line_modes


def load_transit_route_stops(schedule_path: T.Union[str, Path, None]) -> tuple[dict[str, tuple[float, float]], dict[str, list]]:
    """
    Parse a transitSchedule and extract:
    - stop_coords: stop_id -> (x, y)
    - route_stops: transitRouteId -> [(stop_ref_id, arrival_offset_s, departure_offset_s), ...]

    Offsets are in seconds from the start of the route (first stop departs at offset 0).
    """
    stop_coords: dict[str, tuple[float, float]] = {}
    route_stops: dict[str, list] = {}

    if not schedule_path:
        return stop_coords, route_stops

    schedule_path = str(schedule_path)
    if not Path(schedule_path).exists():
        return stop_coords, route_stops

    with open_maybe_gz(schedule_path) as f:
        tree = ET.parse(f)

    root = tree.getroot()

    # Parse stop facilities
    for stop_elem in root.findall(".//stopFacility"):
        stop_id = stop_elem.get("id")
        x = stop_elem.get("x")
        y = stop_elem.get("y")
        if stop_id and x and y:
            stop_coords[stop_id] = (float(x), float(y))

    # Parse transit routes
    for route in root.findall(".//transitRoute"):
        route_id = route.get("id")
        if not route_id:
            continue

        stops_in_route = []
        route_profile = route.find("./routeProfile")
        if route_profile is not None:
            for stop_elem in route_profile.findall("./stop"):
                stop_ref_id = stop_elem.get("refId")
                arrival_str = stop_elem.get("arrivalOffset", "00:00:00")
                departure_str = stop_elem.get("departureOffset", "00:00:00")

                arrival_s = hhmmss_to_seconds(arrival_str)
                departure_s = hhmmss_to_seconds(departure_str)

                if stop_ref_id and arrival_s is not None and departure_s is not None:
                    stops_in_route.append((stop_ref_id, arrival_s, departure_s))

        if stops_in_route:
            route_stops[route_id] = stops_in_route

    return stop_coords, route_stops


def load_actively_used_vehicles(events_path: T.Union[str, Path, None], agent_ids: set[str] | None = None) -> dict[str, dict]:
    """
    Parse events.xml(.gz) to extract vehicles used by specific agents.

    Returns dict: vehicle_id -> {
        'mode': 'subway' or 'car',
        'first_use_time_s': int,
        'last_use_time_s': int,
        'agent_count': int (number of unique agents using this vehicle)
    }
    """
    used_vehicles: dict[str, dict] = {}

    if not events_path or not Path(str(events_path)).exists():
        return used_vehicles

    if agent_ids is None:
        agent_ids = {"metro_up_01", "metro_down_01", "car_commuter_01"}

    events_path = str(events_path)

    try:
        with open_maybe_gz(events_path) as f:
            context = ET.iterparse(f, events=("start", "end"))
            _, root = next(context)

            for event, elem in context:
                if event == "end" and elem.tag == "event":
                    event_type = elem.get("type")
                    if event_type == "PersonEntersVehicle":
                        person = elem.get("person")
                        vehicle = elem.get("vehicle")
                        time_str = elem.get("time")

                        if person and vehicle and person in agent_ids:
                            time_s = int(float(time_str)) if time_str else 0

                            if vehicle not in used_vehicles:
                                if "subway" in vehicle:
                                    mode = "subway"
                                elif "car" in vehicle:
                                    mode = "car"
                                else:
                                    mode = "unknown"

                                used_vehicles[vehicle] = {
                                    "mode": mode,
                                    "first_use_time_s": time_s,
                                    "last_use_time_s": time_s,
                                    "agents": set(),
                                }

                            used_vehicles[vehicle]["first_use_time_s"] = min(
                                used_vehicles[vehicle]["first_use_time_s"], time_s
                            )
                            used_vehicles[vehicle]["last_use_time_s"] = max(
                                used_vehicles[vehicle]["last_use_time_s"], time_s
                            )
                            used_vehicles[vehicle]["agents"].add(person)

                    root.clear()

        for veh_info in used_vehicles.values():
            veh_info["agent_count"] = len(veh_info.pop("agents"))

    except Exception as e:
        print(f"Warning: Could not parse events file: {e}")

    return used_vehicles
