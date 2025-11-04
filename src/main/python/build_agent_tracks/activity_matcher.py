"""
Match activity information to track points.

For each track point, determine which activity it belongs to based on time ranges
and spatial proximity. This allows analysis like "how much time did agent X spend
in home activities?" or "what activities occurred before/after PT trips?"
"""
from __future__ import annotations

import typing as T
from dataclasses import dataclass

import pandas as pd

from .models import Activity, PersonPlan, PlanEntry


@dataclass
class ActivityInfo:
    """Information about an activity for matching."""
    type: str
    x: T.Optional[float]
    y: T.Optional[float]
    link: T.Optional[str]
    start_time_s: T.Optional[int]
    end_time_s: T.Optional[int]
    sequence: int  # Position in the plan


def extract_activities_by_person(plans: list[PersonPlan]) -> dict[str, list[ActivityInfo]]:
    """
    Extract all activities from plans, organized by person_id.

    Args:
        plans: List of PersonPlan objects

    Returns:
        Dict: person_id -> list of ActivityInfo (sorted by start_time_s)
    """
    activities_by_person: dict[str, list[ActivityInfo]] = {}

    for plan in plans:
        person_id = plan.person_id
        activities = []
        seq = 0

        for entry in plan.entries:
            if entry.kind == "act":
                a: Activity = T.cast(Activity, entry.data)
                act_info = ActivityInfo(
                    type=a.type,
                    x=a.x,
                    y=a.y,
                    link=a.link,
                    start_time_s=a.start_time_s,
                    end_time_s=a.end_time_s,
                    sequence=seq,
                )
                activities.append(act_info)
                seq += 1

        # Sort by start_time_s for easier matching
        activities.sort(key=lambda a: a.start_time_s or 0)
        activities_by_person[person_id] = activities

    return activities_by_person


def match_activity_to_tracks(
    tracks_df: pd.DataFrame,
    activities_by_person: dict[str, list[ActivityInfo]],
) -> pd.DataFrame:
    """
    Add activity information to each track point.

    Matching logic:
    - For each track point (time_s), find the activity that contains this time
    - If time_s falls within activity's [start_time_s, end_time_s], match it
    - Also check spatial proximity if coordinates available

    Args:
        tracks_df: DataFrame from build_tracks_from_legs
        activities_by_person: Dict from extract_activities_by_person

    Returns:
        New DataFrame with additional columns:
        - activity_type: Type of activity (home, work, etc.)
        - activity_sequence: Position in plan (0=first activity)
        - activity_link: Link ID of activity location
        - activity_dist_km: Distance from track point to activity location (if available)
        - activity_match_type: How the match was made ('time', 'spatial', 'none')
    """
    if tracks_df.empty:
        return tracks_df.copy()

    # Make a copy to avoid modifying original
    df = tracks_df.copy()

    # Initialize new columns
    df["activity_type"] = None
    df["activity_sequence"] = None
    df["activity_link"] = None
    df["activity_dist_km"] = None
    df["activity_match_type"] = None

    for idx, row in df.iterrows():
        person_id = row["person_id"]
        time_s = row["time_s"]
        x = row["x"]
        y = row["y"]

        if person_id not in activities_by_person:
            continue

        activities = activities_by_person[person_id]
        best_match = _find_best_activity_match(time_s, x, y, activities)

        if best_match:
            act_info, match_type, dist_km = best_match
            df.at[idx, "activity_type"] = act_info.type
            df.at[idx, "activity_sequence"] = act_info.sequence
            df.at[idx, "activity_link"] = act_info.link
            df.at[idx, "activity_dist_km"] = dist_km
            df.at[idx, "activity_match_type"] = match_type

    return df


def _find_best_activity_match(
    time_s: int,
    x: T.Optional[float],
    y: T.Optional[float],
    activities: list[ActivityInfo],
) -> T.Optional[tuple[ActivityInfo, str, T.Optional[float]]]:
    """
    Find the best matching activity for a track point.

    Returns:
        Tuple of (ActivityInfo, match_type, dist_km) or None
        match_type: 'time' | 'spatial' | None
    """
    # First: try time-based matching (most reliable)
    for act in activities:
        if _is_time_in_activity(time_s, act):
            return (act, "time", None)

    # Second: try spatial matching if time-based fails
    # (useful for activities at start of plan with undefined start_time)
    if x is not None and y is not None:
        best_spatial_match = None
        min_dist = float("inf")

        for act in activities:
            if act.x is not None and act.y is not None:
                dist_km = _euclidean_distance_km(x, y, act.x, act.y)
                if dist_km < min_dist:
                    min_dist = dist_km
                    best_spatial_match = (act, "spatial", dist_km)

        # Only return spatial match if close enough (within 500m)
        if best_spatial_match and best_spatial_match[2] < 0.5:
            return best_spatial_match

    return None


def _is_time_in_activity(time_s: int, activity: ActivityInfo) -> bool:
    """Check if time_s falls within activity's time window."""
    if activity.start_time_s is None or activity.end_time_s is None:
        return False
    return activity.start_time_s <= time_s <= activity.end_time_s


def _euclidean_distance_km(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate Euclidean distance in km.

    Note: This assumes coordinates are in a projected CRS (meters).
    For Taiwan TWD97 (EPSG:3826), this is valid.
    """
    import math
    dist_m = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return dist_m / 1000.0


def add_activity_summaries(
    tracks_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add summary statistics about activity types for each person.

    Args:
        tracks_df: DataFrame from match_activity_to_tracks (must have activity_type column)

    Returns:
        Same DataFrame with additional summary columns:
        - activity_count: Total number of unique activities visited
        - activity_types: Comma-separated list of all activity types in plan
    """
    if tracks_df.empty or "activity_type" not in tracks_df.columns:
        return tracks_df.copy()

    df = tracks_df.copy()
    df["activity_count"] = None
    df["activity_types"] = None

    # Group by person to compute summaries
    for person_id, group in df.groupby("person_id"):
        # Count unique activities
        activity_types = group["activity_type"].dropna().unique()
        activity_count = len(activity_types)
        activity_types_str = ",".join(sorted(activity_types))

        # Update all rows for this person
        mask = df["person_id"] == person_id
        df.loc[mask, "activity_count"] = activity_count
        df.loc[mask, "activity_types"] = activity_types_str

    return df
