"""
Build time-sampled tracks from legs table using linear interpolation.
"""
from __future__ import annotations

import math
import typing as T

import pandas as pd

from .utils import seconds_to_hhmmss


# Default modes to include in generated tracks (excludes motorized road traffic)
DEFAULT_INCLUDED_MODES = {"walk", "pt", "subway", "rail", "bus", "tram"}


def interpolate_segment(x0, y0, x1, y1, t0, t1, dt=1) -> list[dict]:
    """
    Linear interpolation every dt seconds (inclusive of endpoints).

    Args:
        x0, y0: Start coordinates
        x1, y1: End coordinates
        t0, t1: Start and end time in seconds
        dt: Sampling interval in seconds

    Returns:
        List of dicts with keys: t, x, y
    """
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


def build_tracks_from_legs(
    legs_df: pd.DataFrame,
    dt: int = 5,
    include_modes: T.Collection[str] | None = None,
) -> pd.DataFrame:
    """
    Produce time-sampled tracks (points) for each person from per-leg geometry.

    Args:
        legs_df: DataFrame from build_legs_table
        dt: Sampling interval in seconds
        include_modes: Modes to include (defaults to walking + transit flavours)

    Returns:
        DataFrame with columns: time_s, time, person_id, mode, mode_original, x, y,
                              leg_index, status, vehicleRefId, pt_* fields
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

            seg = interpolate_segment(
                row["start_x"], row["start_y"],
                row["end_x"], row["end_y"],
                row["start_time_s"], row["end_time_s"],
                dt=dt
            )

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
