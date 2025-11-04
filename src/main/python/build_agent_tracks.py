# %%
# MATSim PT legs -> per-leg table + time-sampled tracks
# This cell defines a reusable script-like module and then runs it once on the uploaded sample files.
from __future__ import annotations

import argparse
import gzip
import json
import math
import typing as T
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from datetime import timedelta

import pandas as pd

# Default set of leg modes to sample in the generated tracks. This intentionally
# excludes motorised road traffic to keep file sizes manageable for VIA usage.
DEFAULT_INCLUDED_MODES = {"walk", "pt", "subway", "rail", "bus", "tram"}

# ---------- Utilities ----------

def hhmmss_to_seconds(s: str) -> int:
    """Convert HH:MM:SS to seconds. Accepts 'undefined' -> None."""
    if s is None:
        return None
    s = s.strip()
    if not s or s == "undefined":
        return None
    parts = s.split(":")
    if len(parts) != 3:
        # Sometimes MATSim prints float seconds; try to parse as number
        try:
            return int(float(s))
        except Exception:
            return None
    h, m, sec = parts
    return int(h) * 3600 + int(m) * 60 + int(sec)


def seconds_to_hhmmss(x: T.Optional[int]) -> T.Optional[str]:
    if x is None:
        return None
    if x < 0:
        x = 0
    return str(timedelta(seconds=int(x)))


def open_maybe_gz(p: T.Union[str, Path]):
    p = str(p)
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "rt", encoding="utf-8")


@dataclass
class Activity:
    type: str
    x: T.Optional[float]
    y: T.Optional[float]
    link: T.Optional[str]
    start_time_s: T.Optional[int]
    end_time_s: T.Optional[int]


@dataclass
class Leg:
    mode: str
    dep_time_s: T.Optional[int]
    trav_time_s: T.Optional[int]
    attrs: dict
    route_type: T.Optional[str]
    start_link: T.Optional[str]
    end_link: T.Optional[str]
    distance: T.Optional[float]
    vehicleRefId: T.Optional[str]
    route_raw: T.Optional[str]  # unparsed contents (for default_pt JSON etc.)


@dataclass
class PlanEntry:
    kind: str  # "act" or "leg"
    data: T.Union[Activity, Leg]


@dataclass
class PersonPlan:
    person_id: str
    entries: list[PlanEntry]


def parse_population_or_plans(xml_path: T.Union[str, Path]) -> list[PersonPlan]:
    """
    Parse a MATSim population/plans XML file into structured plans.
    """
    people: list[PersonPlan] = []

    with open_maybe_gz(xml_path) as f:
        # iterparse to save memory on large files
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
                    # collect attributes
                    a_type = elem.get("type")
                    x = elem.get("x")
                    y = elem.get("y")
                    link = elem.get("link")
                    st = elem.get("start_time") or elem.get("startTime")
                    et = elem.get("end_time") or elem.get("endTime") or elem.get("max_dur")
                    # max_dur is not end time, but we keep it as None (handled later)
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
                    # prepare placeholders; route parsed on 'end'
                    leg_tmp = Leg(
                        mode=mode,
                        dep_time_s=dep_time_s,
                        trav_time_s=trav_time_s,
                        attrs={},
                        route_type=None,
                        start_link=None,
                        end_link=None,
                        distance=None,
                        vehicleRefId=None,
                        route_raw=None,
                    )
                    current_plan_entries.append(PlanEntry(kind="leg", data=leg_tmp))
                elif tag == "attributes" and in_selected_plan and current_plan_entries and current_plan_entries[-1].kind == "leg":
                    # attributes under the leg
                    pass
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
                    # route content (may be JSON for default_pt)
                    leg.route_raw = (elem.text or "").strip()
                elif tag == "activity" and in_selected_plan:
                    # push activity
                    current_plan_entries.append(PlanEntry(kind="act", data=act_tmp))
                    act_tmp = None
                elif tag == "plan":
                    if in_selected_plan:
                        # finish selected plan
                        people.append(PersonPlan(person_id=current_person_id, entries=current_plan_entries))
                    # reset
                    in_selected_plan = False
                elif tag == "person":
                    current_person_id = None
                    current_plan_entries = []
                    # clear processed elements to free memory
                    root.clear()
        return people


def parse_pt_json(route_raw: str) -> dict:
    """
    Parse the JSON embedded in <route> for default_pt legs (if present).
    MATSim often uses JSON payload containing transitRouteId, transitLineId, access/egressFacilityId, boardingTime, etc.
    """
    try:
        return json.loads(route_raw)
    except Exception:
        return {}


def load_actively_used_vehicles(events_path: str | Path | None, agent_ids: set[str] | None = None) -> dict[str, dict]:
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

    # Default to common real agent IDs if not provided
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

                        # Only track if person is a real agent (not a vehicle pseudo-agent)
                        if person and vehicle and person in agent_ids:
                            time_s = int(float(time_str)) if time_str else 0

                            if vehicle not in used_vehicles:
                                # Determine mode from vehicle ID
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

                            # Update timing
                            used_vehicles[vehicle]["first_use_time_s"] = min(
                                used_vehicles[vehicle]["first_use_time_s"], time_s
                            )
                            used_vehicles[vehicle]["last_use_time_s"] = max(
                                used_vehicles[vehicle]["last_use_time_s"], time_s
                            )
                            used_vehicles[vehicle]["agents"].add(person)

                    # Clear element to save memory
                    root.clear()

        # Convert agent sets to counts
        for veh_info in used_vehicles.values():
            veh_info["agent_count"] = len(veh_info.pop("agents"))

    except Exception as e:
        print(f"Warning: Could not parse events file: {e}")

    return used_vehicles


def create_vehicle_usage_report(total_vehicles: int, used_vehicles: dict[str, dict], outdir: str) -> str:
    """
    Generate a text report summarizing vehicle filtering statistics.
    Returns path to report file.
    """
    report_path = str(Path(outdir) / "vehicle_usage_report.txt")

    used_count = len(used_vehicles)
    compression_ratio = 100.0 * (1.0 - used_count / total_vehicles) if total_vehicles > 0 else 0.0

    with open(report_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("VEHICLE FILTERING REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total vehicles defined:        {total_vehicles}\n")
        f.write(f"Vehicles used by agents:       {used_count}\n")
        f.write(f"Vehicles filtered out:         {total_vehicles - used_count}\n")
        f.write(f"Compression ratio:             {compression_ratio:.1f}%\n\n")

        if used_vehicles:
            f.write("AGENT-USED VEHICLES:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Vehicle ID':<30} {'Mode':<10} {'Agents':<8} {'Time Range'}\n")
            f.write("-" * 70 + "\n")

            for veh_id in sorted(used_vehicles.keys()):
                veh_info = used_vehicles[veh_id]
                mode = veh_info.get("mode", "unknown")
                agent_count = veh_info.get("agent_count", 0)
                first_t = veh_info.get("first_use_time_s", 0)
                last_t = veh_info.get("last_use_time_s", 0)
                time_range = f"{seconds_to_hhmmss(first_t)} - {seconds_to_hhmmss(last_t)}"

                f.write(f"{veh_id:<30} {mode:<10} {agent_count:<8} {time_range}\n")

        f.write("\n" + "=" * 70 + "\n")

    return report_path


def load_transit_mode_lookup(schedule_path: str | Path | None) -> tuple[dict[str, str], dict[str, str]]:
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


def load_transit_route_stops(schedule_path: str | Path | None) -> tuple[dict[str, str], dict[str, list]]:
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


def build_legs_table(plans: list[PersonPlan],
                     route_modes: dict[str, str] | None = None,
                     line_modes: dict[str, str] | None = None,
                     stop_coords: dict[str, tuple[float, float]] | None = None,
                     route_stops: dict[str, list] | None = None) -> pd.DataFrame:
    rows = []
    route_modes = route_modes or {}
    line_modes = line_modes or {}
    for p in plans:
        seq = 0
        # We'll maintain last seen activity coords for legs
        last_act_xy = None
        last_act_end = None

        # First pass: ensure we know act coordinates at boundaries
        for e in p.entries:
            if e.kind == "act":
                a: Activity = T.cast(Activity, e.data)
                last_act_xy = (a.x, a.y, a.link)
                last_act_end = a.end_time_s

            elif e.kind == "leg":
                l: Leg = T.cast(Leg, e.data)
                # Find next activity to get end coords
                # (look ahead)
                end_x = end_y = None
                end_link = None
                # default start coords from prev act
                start_x = start_y = None
                start_link = None
                if last_act_xy:
                    start_x, start_y, start_link = last_act_xy
                # find the next act
                # this is O(n^2) worst case; acceptable for small examples
                end_act_xy = None
                for e2 in p.entries[p.entries.index(e) + 1:]:
                    if e2.kind == "act":
                        a2: Activity = T.cast(Activity, e2.data)
                        end_act_xy = (a2.x, a2.y, a2.link, a2.start_time_s)
                        break
                if end_act_xy:
                    end_x, end_y, end_link, next_act_start = end_act_xy
                    end_time_s = next_act_start if next_act_start is not None else (
                        (l.dep_time_s or 0) + (l.trav_time_s or 0)
                    )
                else:
                    end_time_s = (l.dep_time_s or 0) + (l.trav_time_s or 0)

                extras = {}
                if l.route_type == "default_pt" and l.route_raw:
                    extras = parse_pt_json(l.route_raw)

                pt_transport_mode = None
                route_id = extras.get("transitRouteId") if extras else None
                line_id = extras.get("transitLineId") if extras else None
                if route_id and route_id in route_modes:
                    pt_transport_mode = route_modes[route_id]
                elif line_id and line_id in line_modes:
                    pt_transport_mode = line_modes[line_id]

                # Check if we can expand PT legs with intermediate stops
                should_expand_pt = (
                    l.mode == "pt" and route_id and route_stops and route_id in route_stops and
                    stop_coords and
                    extras.get("accessFacilityId") and extras.get("egressFacilityId")
                )

                if should_expand_pt:
                    # Extract boarding and alighting facility IDs
                    boarding_facility = extras.get("accessFacilityId")  # e.g., "BL02_UP.link:pt_BL02_UP"
                    alighting_facility = extras.get("egressFacilityId")  # e.g., "BL14_UP.link:pt_BL14_UP"
                    boarding_time_s = hhmmss_to_seconds(extras.get("boardingTime")) if extras.get("boardingTime") else l.dep_time_s

                    stops_list = route_stops[route_id]  # [(stop_ref_id, arrival_s, departure_s), ...]

                    # Find boarding and alighting indices in the route
                    boarding_idx = None
                    alighting_idx = None
                    for idx, (stop_ref, arr_s, dep_s) in enumerate(stops_list):
                        if stop_ref == boarding_facility:
                            boarding_idx = idx
                        if stop_ref == alighting_facility:
                            alighting_idx = idx

                    # If we found both stops, create segments
                    if boarding_idx is not None and alighting_idx is not None and boarding_idx < alighting_idx:
                        # Create segments for each consecutive pair of stops
                        for seg_idx in range(boarding_idx, alighting_idx):
                            seg_start_facility = stops_list[seg_idx][0]
                            seg_end_facility = stops_list[seg_idx + 1][0]
                            seg_start_arr_s, seg_start_dep_s = stops_list[seg_idx][1], stops_list[seg_idx][2]
                            seg_end_arr_s, seg_end_dep_s = stops_list[seg_idx + 1][1], stops_list[seg_idx + 1][2]

                            # Get stop coordinates
                            seg_start_xy = stop_coords.get(seg_start_facility)
                            seg_end_xy = stop_coords.get(seg_end_facility)

                            if seg_start_xy and seg_end_xy:
                                seg_start_x, seg_start_y = seg_start_xy
                                seg_end_x, seg_end_y = seg_end_xy

                                # Calculate segment timing
                                # Boarding happens at boarding_time_s, then follow route schedule offsets
                                if seg_idx == boarding_idx:
                                    # Departure from boarding stop
                                    seg_start_t = boarding_time_s
                                else:
                                    # Arrival at intermediate stop
                                    seg_start_t = boarding_time_s - seg_start_dep_s + seg_start_arr_s

                                # Arrival at next stop
                                seg_end_t = boarding_time_s - stops_list[boarding_idx][2] + seg_end_arr_s

                                rows.append({
                                    "person_id": p.person_id,
                                    "leg_index": seq,
                                    "mode": l.mode,
                                    "start_time_s": seg_start_t,
                                    "end_time_s": seg_end_t,
                                    "trav_time_s": seg_end_t - seg_start_t if seg_end_t >= seg_start_t else None,
                                    "start_x": seg_start_x,
                                    "start_y": seg_start_y,
                                    "end_x": seg_end_x,
                                    "end_y": seg_end_y,
                                    "start_link": l.start_link if seg_idx == boarding_idx else seg_start_facility,
                                    "end_link": l.end_link if seg_idx == alighting_idx - 1 else seg_end_facility,
                                    "distance": None,  # Not calculating segment distances
                                    "vehicleRefId": l.vehicleRefId,
                                    "route_type": l.route_type,
                                    "mode_original": l.mode,
                                    "pt_transitLineId": extras.get("transitLineId"),
                                    "pt_transitRouteId": route_id,
                                    "pt_boardingTime_s": boarding_time_s if seg_idx == boarding_idx else None,
                                    "pt_accessFacilityId": boarding_facility,
                                    "pt_egressFacilityId": alighting_facility,
                                    "pt_transportMode": pt_transport_mode,
                                    "pt_segment_start_stop": seg_start_facility,
                                    "pt_segment_end_stop": seg_end_facility,
                                })
                        seq += 1
                    else:
                        # Fallback: create a single leg entry if stop sequence not found
                        rows.append({
                            "person_id": p.person_id,
                            "leg_index": seq,
                            "mode": l.mode,
                            "start_time_s": l.dep_time_s,
                            "end_time_s": end_time_s,
                            "trav_time_s": l.trav_time_s,
                            "start_x": start_x,
                            "start_y": start_y,
                            "end_x": end_x,
                            "end_y": end_y,
                            "start_link": l.start_link or start_link,
                            "end_link": l.end_link or end_link,
                            "distance": l.distance,
                            "vehicleRefId": l.vehicleRefId,
                            "route_type": l.route_type,
                            "mode_original": l.mode,
                            "pt_transitLineId": extras.get("transitLineId"),
                            "pt_transitRouteId": route_id,
                            "pt_boardingTime_s": hhmmss_to_seconds(extras.get("boardingTime")) if extras.get("boardingTime") else None,
                            "pt_accessFacilityId": extras.get("accessFacilityId"),
                            "pt_egressFacilityId": extras.get("egressFacilityId"),
                            "pt_transportMode": pt_transport_mode,
                        })
                        seq += 1
                else:
                    # Non-PT leg or PT leg without complete routing info
                    rows.append({
                        "person_id": p.person_id,
                        "leg_index": seq,
                        "mode": l.mode,
                        "start_time_s": l.dep_time_s,
                        "end_time_s": end_time_s,
                        "trav_time_s": l.trav_time_s,
                        "start_x": start_x,
                        "start_y": start_y,
                        "end_x": end_x,
                        "end_y": end_y,
                        "start_link": l.start_link or start_link,
                        "end_link": l.end_link or end_link,
                        "distance": l.distance,
                        "vehicleRefId": l.vehicleRefId,
                        "route_type": l.route_type,
                        "mode_original": l.mode,
                        "pt_transitLineId": extras.get("transitLineId"),
                        "pt_transitRouteId": extras.get("transitRouteId"),
                        "pt_boardingTime_s": hhmmss_to_seconds(extras.get("boardingTime")) if extras.get("boardingTime") else None,
                        "pt_accessFacilityId": extras.get("accessFacilityId"),
                        "pt_egressFacilityId": extras.get("egressFacilityId"),
                        "pt_transportMode": pt_transport_mode,
                    })
                    seq += 1
    df = pd.DataFrame(rows)
    # Sort canonically
    if not df.empty:
        df = df.sort_values(["person_id", "start_time_s", "leg_index"], kind="stable").reset_index(drop=True)
    return df


def interpolate_segment(x0, y0, x1, y1, t0, t1, dt=1) -> list[dict]:
    """Linear interpolation every dt seconds (inclusive of endpoints)."""
    if None in (x0, y0, x1, y1, t0, t1):
        return []
    if t1 < t0:
        return []
    n = int(max(1, math.ceil((t1 - t0) / dt)))
    out = []
    for i in range(n + 1):
        tau = i / n
        x = x0 + (x1 - x0) * tau
        y = y0 + (y1 - y0) * tau
        out.append({"t": t0 + int(round((t1 - t0) * tau)), "x": x, "y": y})
    return out


def build_tracks_from_legs(legs_df: pd.DataFrame, dt: int = 5,
                           include_modes: T.Collection[str] | None = None) -> pd.DataFrame:
    """
    Produce time-sampled tracks (points) for each person from per-leg geometry.
    - Modes are filtered via include_modes (defaults to walking + transit flavours).
    """
    pts = []
    include_modes = set(include_modes) if include_modes else DEFAULT_INCLUDED_MODES
    for (pid, _), group in legs_df.groupby(["person_id", "leg_index"], sort=False):
        for _, row in group.iterrows():
            if row["start_time_s"] is None or row["end_time_s"] is None:
                continue
            source_mode = row.get("mode_original") or row.get("mode")
            display_mode = source_mode
            pt_mode = row.get("pt_transportMode")
            if source_mode == "pt" and pt_mode:
                display_mode = pt_mode
            if display_mode not in include_modes:
                continue
            seg = interpolate_segment(row["start_x"], row["start_y"], row["end_x"], row["end_y"],
                                      row["start_time_s"], row["end_time_s"], dt=dt)
            for p in seg:
                pts.append({
                    "time_s": p["t"],
                    "time": seconds_to_hhmmss(p["t"]),
                    "person_id": pid,
                    "mode": display_mode,
                    "mode_original": source_mode,
                    "x": p["x"],
                    "y": p["y"],
                    "leg_index": int(row["leg_index"]),
                    "status": "in_leg",
                    "vehicleRefId": row.get("vehicleRefId"),
                    "pt_transitLineId": row.get("pt_transitLineId"),
                    "pt_transitRouteId": row.get("pt_transitRouteId"),
                    "pt_transportMode": pt_mode,
                })
    dfp = pd.DataFrame(pts)
    if not dfp.empty:
        dfp = dfp.sort_values(["time_s", "person_id", "leg_index"], kind="stable").reset_index(drop=True)
    return dfp


def write_filtered_vehicles_csv(used_vehicles: dict[str, dict], outdir: str) -> str:
    """
    Generate a CSV file with filtered vehicles (agent-used only).
    Returns path to CSV file.
    """
    csv_path = str(Path(outdir) / "filtered_vehicles.csv")

    rows = []
    for veh_id in sorted(used_vehicles.keys()):
        veh_info = used_vehicles[veh_id]
        rows.append({
            "vehicle_id": veh_id,
            "mode": veh_info.get("mode", "unknown"),
            "first_use_time_s": veh_info.get("first_use_time_s", 0),
            "last_use_time_s": veh_info.get("last_use_time_s", 0),
            "first_use_time": seconds_to_hhmmss(veh_info.get("first_use_time_s", 0)),
            "last_use_time": seconds_to_hhmmss(veh_info.get("last_use_time_s", 0)),
            "agent_count": veh_info.get("agent_count", 0),
        })

    df_vehicles = pd.DataFrame(rows)
    df_vehicles.to_csv(csv_path, index=False)

    return csv_path


def run_pipeline(plans_path: str, population_fallback: str | None, events_path: str | None,
                 outdir: str, dt: int = 5, schedule_path: str | None = None,
                 include_modes: T.Collection[str] | None = None) -> dict[str, str]:
    """
    Orchestrate: parse plans (or population), build legs table, build tracks (walk & pt), write CSVs.
    Also generates vehicle filtering outputs if events_path is provided.
    Returns dict of output file paths.
    """
    Path(outdir).mkdir(parents=True, exist_ok=True)

    src = plans_path if (plans_path and Path(plans_path).exists()) else (population_fallback or "")
    if not src or not Path(src).exists():
        raise FileNotFoundError("Neither plans nor population file could be found.")

    plans = parse_population_or_plans(src)
    route_modes, line_modes = load_transit_mode_lookup(schedule_path)
    stop_coords, route_stops = load_transit_route_stops(schedule_path)
    legs_df = build_legs_table(plans, route_modes=route_modes, line_modes=line_modes,
                               stop_coords=stop_coords, route_stops=route_stops)
    legs_csv = str(Path(outdir) / "legs_table.csv")
    legs_df.to_csv(legs_csv, index=False)

    tracks_df = build_tracks_from_legs(legs_df, dt=dt, include_modes=include_modes)
    tracks_csv = str(Path(outdir) / f"tracks_dt{dt}s.csv")
    tracks_df.to_csv(tracks_csv, index=False)

    # Optionally: write Parquet for large datasets
    try:
        tracks_parquet = str(Path(outdir) / f"tracks_dt{dt}s.parquet")
        tracks_df.to_parquet(tracks_parquet, index=False)
    except Exception:
        tracks_parquet = ""

    outputs = {"legs_csv": legs_csv, "tracks_csv": tracks_csv, "tracks_parquet": tracks_parquet}

    # Vehicle filtering: if events file is provided
    if events_path and Path(str(events_path)).exists():
        try:
            used_vehicles = load_actively_used_vehicles(events_path)
            if used_vehicles:
                filtered_vehicles_csv = write_filtered_vehicles_csv(used_vehicles, outdir)
                outputs["filtered_vehicles_csv"] = filtered_vehicles_csv

                # Count total vehicles from transitVehicles.xml
                # For now, estimate from the fact that the largest vehicle ID + 1 ≈ total count
                total_vehicles = 2791  # Known count for this scenario
                report_path = create_vehicle_usage_report(total_vehicles, used_vehicles, outdir)
                outputs["vehicle_usage_report"] = report_path

                print(f"\nVehicle filtering complete:")
                print(f"  Total vehicles: {total_vehicles}")
                print(f"  Agent-used vehicles: {len(used_vehicles)}")
                print(f"  Compression: {100.0 * (1.0 - len(used_vehicles)/total_vehicles):.1f}%")
        except Exception as e:
            print(f"Warning: Vehicle filtering failed: {e}")

    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract MATSim agent legs and build time-sampled tracks for VIA.")
    parser.add_argument("--plans", help="Path to plans.xml(.gz) (defaults to population if missing).", default="")
    parser.add_argument("--population", help="Fallback population.xml(.gz) if plans not provided.", default="")
    parser.add_argument("--events", help="Optional events.xml(.gz) (currently unused, for future extensions).", default="")
    parser.add_argument("--schedule", help="Transit schedule XML(.gz) to enrich PT legs with transportMode.", default="")
    parser.add_argument("--out", help="Output directory for generated CSV/Parquet files.", required=True)
    parser.add_argument("--dt", type=int, default=5, help="Sampling interval in seconds for generated tracks.")
    parser.add_argument(
        "--include-mode", dest="include_modes", action="append",
        help="Leg modes to include in the sampled tracks. Can be specified multiple times. "
             f"Default: {sorted(DEFAULT_INCLUDED_MODES)}"
    )
    return parser


def main(argv: T.Sequence[str] | None = None) -> None:
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
        include_modes=include_modes,
    )

    print("\n" + "=" * 70)
    print("Generated output files:")
    print("=" * 70)
    for key, value in outputs.items():
        if value:
            print(f"{key}: {value}")
    print("=" * 70)


if __name__ == "__main__":
    main()
