"""
Build a legs table from agent plans with PT segment expansion.
"""
from __future__ import annotations

import typing as T

import pandas as pd

from .models import Activity, Leg, PersonPlan, PlanEntry
from .parsers import parse_pt_json
from .utils import hhmmss_to_seconds


def build_legs_table(
    plans: list[PersonPlan],
    route_modes: dict[str, str] | None = None,
    line_modes: dict[str, str] | None = None,
    stop_coords: dict[str, tuple[float, float]] | None = None,
    route_stops: dict[str, list] | None = None,
) -> pd.DataFrame:
    """
    Build a detailed legs table from agent plans.

    Supports PT leg expansion with intermediate stops from transitSchedule.

    Args:
        plans: List of PersonPlan objects
        route_modes: Dict mapping transitRouteId -> mode
        line_modes: Dict mapping transitLineId -> mode
        stop_coords: Dict mapping stop_id -> (x, y)
        route_stops: Dict mapping transitRouteId -> [(stop_ref_id, arrival_s, departure_s), ...]

    Returns:
        DataFrame with columns: person_id, leg_index, mode, start_time_s, end_time_s,
                              trav_time_s, start_x, start_y, end_x, end_y, start_link,
                              end_link, distance, vehicleRefId, route_type, mode_original,
                              pt_* fields (for PT legs)
    """
    rows = []
    route_modes = route_modes or {}
    line_modes = line_modes or {}

    for p in plans:
        seq = 0
        last_act_xy = None

        # Collect activity data
        for e in p.entries:
            if e.kind == "act":
                a: Activity = T.cast(Activity, e.data)
                last_act_xy = (a.x, a.y, a.link)

            elif e.kind == "leg":
                l: Leg = T.cast(Leg, e.data)

                # Find next activity
                end_x = end_y = None
                end_link = None
                start_x = start_y = None
                start_link = None

                if last_act_xy:
                    start_x, start_y, start_link = last_act_xy

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
                    # Expand PT leg into segments
                    _add_pt_segments(
                        rows, p.person_id, seq, l, start_x, start_y, end_x, end_y,
                        start_link, end_link, end_time_s, route_id, line_id,
                        extras, stop_coords, route_stops, pt_transport_mode
                    )
                else:
                    # Regular leg without PT expansion
                    _add_single_leg(
                        rows, p.person_id, seq, l, start_x, start_y, end_x, end_y,
                        start_link, end_link, end_time_s, extras, pt_transport_mode
                    )

                seq += 1

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["person_id", "start_time_s", "leg_index"], kind="stable").reset_index(drop=True)
    return df


def _add_pt_segments(
    rows: list,
    person_id: str,
    seq: int,
    leg: Leg,
    start_x, start_y, end_x, end_y,
    start_link, end_link, end_time_s,
    route_id, line_id,
    extras, stop_coords, route_stops,
    pt_transport_mode
):
    """Add PT leg segments for each stop pair."""
    boarding_facility = extras.get("accessFacilityId")
    alighting_facility = extras.get("egressFacilityId")
    boarding_time_s = hhmmss_to_seconds(extras.get("boardingTime")) if extras.get("boardingTime") else leg.dep_time_s

    stops_list = route_stops[route_id]

    # Find boarding and alighting indices
    boarding_idx = None
    alighting_idx = None
    for idx, (stop_ref, arr_s, dep_s) in enumerate(stops_list):
        if stop_ref == boarding_facility:
            boarding_idx = idx
        if stop_ref == alighting_facility:
            alighting_idx = idx

    if boarding_idx is not None and alighting_idx is not None and boarding_idx < alighting_idx:
        # Create segments for each consecutive pair
        for seg_idx in range(boarding_idx, alighting_idx):
            seg_start_facility = stops_list[seg_idx][0]
            seg_end_facility = stops_list[seg_idx + 1][0]
            seg_start_arr_s, seg_start_dep_s = stops_list[seg_idx][1], stops_list[seg_idx][2]
            seg_end_arr_s, seg_end_dep_s = stops_list[seg_idx + 1][1], stops_list[seg_idx + 1][2]

            seg_start_xy = stop_coords.get(seg_start_facility)
            seg_end_xy = stop_coords.get(seg_end_facility)

            if seg_start_xy and seg_end_xy:
                seg_start_x, seg_start_y = seg_start_xy
                seg_end_x, seg_end_y = seg_end_xy

                if seg_idx == boarding_idx:
                    seg_start_t = boarding_time_s
                else:
                    seg_start_t = boarding_time_s - seg_start_dep_s + seg_start_arr_s

                seg_end_t = boarding_time_s - stops_list[boarding_idx][2] + seg_end_arr_s

                rows.append({
                    "person_id": person_id,
                    "leg_index": seq,
                    "mode": leg.mode,
                    "start_time_s": seg_start_t,
                    "end_time_s": seg_end_t,
                    "trav_time_s": seg_end_t - seg_start_t if seg_end_t >= seg_start_t else None,
                    "start_x": seg_start_x,
                    "start_y": seg_start_y,
                    "end_x": seg_end_x,
                    "end_y": seg_end_y,
                    "start_link": leg.start_link if seg_idx == boarding_idx else seg_start_facility,
                    "end_link": leg.end_link if seg_idx == alighting_idx - 1 else seg_end_facility,
                    "distance": None,
                    "vehicleRefId": leg.vehicleRefId,
                    "route_type": leg.route_type,
                    "mode_original": leg.mode,
                    "pt_transitLineId": extras.get("transitLineId"),
                    "pt_transitRouteId": route_id,
                    "pt_boardingTime_s": boarding_time_s if seg_idx == boarding_idx else None,
                    "pt_accessFacilityId": boarding_facility,
                    "pt_egressFacilityId": alighting_facility,
                    "pt_transportMode": pt_transport_mode,
                    "pt_segment_start_stop": seg_start_facility,
                    "pt_segment_end_stop": seg_end_facility,
                })
    else:
        # Fallback: single entry if stops not found
        _add_single_leg(
            rows, person_id, seq, leg, start_x, start_y, end_x, end_y,
            start_link, end_link, end_time_s, extras, pt_transport_mode
        )


def _add_single_leg(
    rows: list,
    person_id: str,
    seq: int,
    leg: Leg,
    start_x, start_y, end_x, end_y,
    start_link, end_link, end_time_s,
    extras, pt_transport_mode
):
    """Add a single leg entry to rows."""
    rows.append({
        "person_id": person_id,
        "leg_index": seq,
        "mode": leg.mode,
        "start_time_s": leg.dep_time_s,
        "end_time_s": end_time_s,
        "trav_time_s": leg.trav_time_s,
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x,
        "end_y": end_y,
        "start_link": leg.start_link or start_link,
        "end_link": leg.end_link or end_link,
        "distance": leg.distance,
        "vehicleRefId": leg.vehicleRefId,
        "route_type": leg.route_type,
        "mode_original": leg.mode,
        "pt_transitLineId": extras.get("transitLineId"),
        "pt_transitRouteId": extras.get("transitRouteId"),
        "pt_boardingTime_s": hhmmss_to_seconds(extras.get("boardingTime")) if extras.get("boardingTime") else None,
        "pt_accessFacilityId": extras.get("accessFacilityId"),
        "pt_egressFacilityId": extras.get("egressFacilityId"),
        "pt_transportMode": pt_transport_mode,
    })
