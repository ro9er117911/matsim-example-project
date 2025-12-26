#!/usr/bin/env python3
"""
Generate a small Tamsui-focused population:
- 50 PT agents (mode=pt)
- 50 car agents (mode=car)
Using stop facilities from the mapped transit schedule.
"""

from __future__ import annotations

import gzip
import os
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Stop:
    stop_id: str
    name: str
    x: float
    y: float


SCHEDULE_PATH = Path(
    os.getenv(
        "SCHEDULE_PATH",
        "/Users/ro9air/matsim-example-project/5000_disatar/06_preference_tests/pt_0250_0850/transitSchedule.xml.gz",
    )
)
OUTPUT_PATH = Path(
    os.getenv(
        "POPULATION_OUTPUT_PATH",
        "/Users/ro9air/matsim-example-project/5000_disatar/06_preference_tests/pt_0250_0850/population_tamsui_100.xml",
    )
)

# Tamsui area bounds (EPSG:3826)
TAMSUI_BOUNDS = {
    "min_x": 293000.0,
    "max_x": 297000.0,
    "min_y": 2782000.0,
    "max_y": 2786000.0,
}

PT_COUNT = 50
CAR_COUNT = 50
BUS_ONLY_SHARE = 0.5
BUS_ONLY_MIN_TRIP_DISTANCE_M = 1500.0
RANDOM_SEED = 4711


def in_bounds(x: float, y: float) -> bool:
    return (
        TAMSUI_BOUNDS["min_x"] <= x <= TAMSUI_BOUNDS["max_x"]
        and TAMSUI_BOUNDS["min_y"] <= y <= TAMSUI_BOUNDS["max_y"]
    )


def load_schedule(schedule_path: Path) -> ET.Element:
    with gzip.open(schedule_path, "rt", encoding="utf-8") as handle:
        tree = ET.parse(handle)
    return tree.getroot()


def build_stop_index(root: ET.Element) -> dict[str, Stop]:
    stops: dict[str, Stop] = {}
    for stop in root.findall(".//stopFacility"):
        sid = stop.get("id")
        if not sid:
            continue
        stops[sid] = Stop(
            stop_id=sid,
            name=stop.get("name") or "",
            x=float(stop.get("x")),
            y=float(stop.get("y")),
        )
    return stops


def collect_stop_modes(root: ET.Element) -> dict[str, set[str]]:
    stop_modes: dict[str, set[str]] = {}
    for line in root.findall(".//transitLine"):
        for route in line.findall(".//transitRoute"):
            mode = route.findtext("transportMode")
            if not mode:
                continue
            for stop in route.findall(".//stop"):
                ref_id = stop.get("refId")
                if not ref_id:
                    continue
                stop_modes.setdefault(ref_id, set()).add(mode)
    return stop_modes


def collect_subway_line_stops(root: ET.Element, stop_index: dict[str, Stop]) -> dict[str, list[Stop]]:
    line_stops: dict[str, list[Stop]] = {}
    for line in root.findall(".//transitLine"):
        line_id = line.get("id")
        if not line_id:
            continue
        stops_for_line: list[Stop] = []
        for route in line.findall(".//transitRoute"):
            mode = route.findtext("transportMode")
            if mode != "subway":
                continue
            for stop in route.findall(".//stop"):
                ref_id = stop.get("refId")
                if ref_id and ref_id in stop_index:
                    stops_for_line.append(stop_index[ref_id])
        if stops_for_line:
            line_stops[line_id] = stops_for_line
    return line_stops


def collect_bus_line_stops(
    root: ET.Element, stop_index: dict[str, Stop], allowed_stop_ids: set[str]
) -> dict[str, list[Stop]]:
    line_stops: dict[str, list[Stop]] = {}
    for line in root.findall(".//transitLine"):
        line_id = line.get("id")
        if not line_id:
            continue
        stops_for_line: list[Stop] = []
        for route in line.findall(".//transitRoute"):
            mode = route.findtext("transportMode")
            if mode != "bus":
                continue
            for stop in route.findall(".//stop"):
                ref_id = stop.get("refId")
                if ref_id and ref_id in allowed_stop_ids and ref_id in stop_index:
                    stops_for_line.append(stop_index[ref_id])
        if len(stops_for_line) >= 2:
            line_stops[line_id] = stops_for_line
    return line_stops


def format_time(hour: int, minute: int) -> str:
    return f"{hour:02d}:{minute:02d}:00"


def random_departure_time() -> str:
    hour = random.randint(5, 8)
    minute = random.choice([0, 10, 20, 30, 40, 50])
    return format_time(hour, minute)


def distance_m(a: Stop, b: Stop) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    return (dx * dx + dy * dy) ** 0.5


def build_person(person_id: str, mode: str, home: Stop, work: Stop) -> str:
    depart = random_departure_time()
    end_hour = min(int(depart[:2]) + 4, 23)
    end_time = format_time(end_hour, int(depart[3:5]))
    return f"""  <person id=\"{person_id}\">
    <plan selected=\"yes\">
      <activity type=\"home\" x=\"{home.x:.2f}\" y=\"{home.y:.2f}\" end_time=\"{depart}\" />
      <leg mode=\"{mode}\" />
      <activity type=\"work\" x=\"{work.x:.2f}\" y=\"{work.y:.2f}\" end_time=\"{end_time}\" />
      <leg mode=\"{mode}\" />
      <activity type=\"home\" x=\"{home.x:.2f}\" y=\"{home.y:.2f}\" />
    </plan>
  </person>
"""


def main() -> None:
    random.seed(RANDOM_SEED)

    if not SCHEDULE_PATH.exists():
        raise SystemExit(f"Missing schedule: {SCHEDULE_PATH}")

    root = load_schedule(SCHEDULE_PATH)
    stop_index = build_stop_index(root)
    stop_modes = collect_stop_modes(root)
    subway_line_stops = collect_subway_line_stops(root, stop_index)

    tamsui_stops = [s for s in stop_index.values() if in_bounds(s.x, s.y)]
    if len(tamsui_stops) < 2:
        raise SystemExit("Not enough Tamsui stops found to build population.")

    subway_stops = [s for s in stop_index.values() if "subway" in stop_modes.get(s.stop_id, set())]
    bus_stops = [s for s in tamsui_stops if "bus" in stop_modes.get(s.stop_id, set())]
    if len(bus_stops) < 2:
        bus_stops = tamsui_stops
    bus_ids = {s.stop_id for s in bus_stops}
    bus_line_stops = collect_bus_line_stops(root, stop_index, bus_ids)

    subway_line_ids = sorted(subway_line_stops.keys())
    if not subway_line_ids:
        raise SystemExit("No subway lines found in schedule.")

    persons = []
    bus_only_count = max(1, int(PT_COUNT * BUS_ONLY_SHARE))
    subway_count = PT_COUNT - bus_only_count

    for i in range(bus_only_count):
        if bus_line_stops:
            line_id = list(bus_line_stops.keys())[i % len(bus_line_stops)]
            line_stops = bus_line_stops[line_id]
            home, work = random.sample(line_stops, 2)
        else:
            home, work = random.sample(bus_stops, 2)
        for _ in range(20):
            if distance_m(home, work) >= BUS_ONLY_MIN_TRIP_DISTANCE_M:
                break
            if bus_line_stops:
                line_id = list(bus_line_stops.keys())[i % len(bus_line_stops)]
                line_stops = bus_line_stops[line_id]
                home, work = random.sample(line_stops, 2)
            else:
                home, work = random.sample(bus_stops, 2)
        persons.append(build_person(f"pt_busonly_{i+1:02d}", "pt", home, work))

    for i in range(subway_count):
        line_id = subway_line_ids[i % len(subway_line_ids)]
        line_stops = subway_line_stops[line_id]
        if len(line_stops) < 2:
            line_stops = tamsui_stops
        home, work = random.sample(line_stops, 2)
        persons.append(build_person(f"pt_subway_{i+1:02d}", "pt", home, work))

    for i in range(CAR_COUNT):
        home, work = random.sample(tamsui_stops, 2)
        persons.append(build_person(f"car_tamsui_{i+1:02d}", "car", home, work))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        handle.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n')
        handle.write("<population>\n")
        handle.write("".join(persons))
        handle.write("</population>\n")

    print(f"✓ Wrote population: {OUTPUT_PATH}")
    print(f"  Stops used (Tamsui bounds): {len(tamsui_stops)}")
    print(f"  Bus stops (Tamsui): {len(bus_stops)}")
    print(f"  Bus lines (Tamsui bus stops): {len(bus_line_stops)}")
    print(f"  Subway stops (all): {len(subway_stops)}")
    print(f"  Subway lines: {len(subway_line_ids)} -> {', '.join(subway_line_ids)}")
    print(f"  PT agents: {PT_COUNT}")
    print(f"  Car agents: {CAR_COUNT}")


if __name__ == "__main__":
    main()
