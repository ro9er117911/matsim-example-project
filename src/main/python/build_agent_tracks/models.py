"""
Data models for MATSim agents, activities, and legs.
"""
from __future__ import annotations

import typing as T
from dataclasses import dataclass, field


@dataclass
class Activity:
    """Represents a MATSim activity (home, work, etc.)"""
    type: str
    x: T.Optional[float]
    y: T.Optional[float]
    link: T.Optional[str]
    start_time_s: T.Optional[int]
    end_time_s: T.Optional[int]


@dataclass
class Leg:
    """Represents a MATSim leg (trip segment)"""
    mode: str
    dep_time_s: T.Optional[int]
    trav_time_s: T.Optional[int]
    attrs: dict = field(default_factory=dict)
    route_type: T.Optional[str] = None
    start_link: T.Optional[str] = None
    end_link: T.Optional[str] = None
    distance: T.Optional[float] = None
    vehicleRefId: T.Optional[str] = None
    route_raw: T.Optional[str] = None  # unparsed contents (for default_pt JSON etc.)


@dataclass
class PlanEntry:
    """Represents a single entry in an agent's plan (activity or leg)"""
    kind: str  # "act" or "leg"
    data: T.Union[Activity, Leg]


@dataclass
class PersonPlan:
    """Represents a complete plan for one agent"""
    person_id: str
    entries: list[PlanEntry]
