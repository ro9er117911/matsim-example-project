#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import random
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Link:
    link_id: str
    from_node: str
    to_node: str
    modes: set[str]
    x: float
    y: float


def open_maybe_gzip(path: Path):
    if path.suffixes[-2:] == [".xml", ".gz"] or path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def read_car_links(network_path: Path) -> list[Link]:
    with open_maybe_gzip(network_path) as fh:
        it = ET.iterparse(fh, events=("end",))
        nodes: dict[str, tuple[float, float]] = {}
        links: list[Link] = []
        for event, elem in it:
            if elem.tag == "node":
                node_id = elem.attrib.get("id")
                x = elem.attrib.get("x")
                y = elem.attrib.get("y")
                if node_id is not None and x is not None and y is not None:
                    nodes[node_id] = (float(x), float(y))
                elem.clear()
                continue

            if elem.tag != "link":
                elem.clear()
                continue

            link_id = elem.attrib["id"]
            from_node = elem.attrib["from"]
            to_node = elem.attrib["to"]
            modes_raw = elem.attrib.get("modes", "")
            modes = {m.strip() for m in modes_raw.split(",") if m.strip()}
            if "car" not in modes:
                elem.clear()
                continue

            from_xy = nodes.get(from_node)
            to_xy = nodes.get(to_node)
            if from_xy and to_xy:
                x = (from_xy[0] + to_xy[0]) / 2.0
                y = (from_xy[1] + to_xy[1]) / 2.0
            elif from_xy:
                x, y = from_xy
            elif to_xy:
                x, y = to_xy
            else:
                x, y = 0.0, 0.0

            links.append(Link(link_id=link_id, from_node=from_node, to_node=to_node, modes=modes, x=x, y=y))
            elem.clear()
        return links


def hhmmss(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def write_population(
    out_path: Path,
    links: list[Link],
    persons: int,
    seed: int,
    departure_start_s: int,
    departure_spread_s: int,
):
    random.seed(seed)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    population = ET.Element("population")

    for person_index in range(persons):
        person = ET.SubElement(population, "person", attrib={"id": f"person_{person_index:05d}"})
        plan = ET.SubElement(person, "plan", attrib={"selected": "yes"})

        home_link = random.choice(links)
        work_link = random.choice(links)
        while work_link.link_id == home_link.link_id and len(links) > 1:
            work_link = random.choice(links)

        depart = departure_start_s + random.randint(0, max(0, departure_spread_s))
        work_end = depart + 9 * 3600

        ET.SubElement(
            plan,
            "activity",
            attrib={
                "type": "home",
                "link": home_link.link_id,
                "x": f"{home_link.x:.2f}",
                "y": f"{home_link.y:.2f}",
                "end_time": hhmmss(depart),
            },
        )
        ET.SubElement(plan, "leg", attrib={"mode": "car"})
        ET.SubElement(
            plan,
            "activity",
            attrib={
                "type": "work",
                "link": work_link.link_id,
                "x": f"{work_link.x:.2f}",
                "y": f"{work_link.y:.2f}",
                "end_time": hhmmss(work_end),
            },
        )
        ET.SubElement(plan, "leg", attrib={"mode": "car"})
        ET.SubElement(
            plan,
            "activity",
            attrib={
                "type": "home",
                "link": home_link.link_id,
                "x": f"{home_link.x:.2f}",
                "y": f"{home_link.y:.2f}",
            },
        )

    xml_bytes = ET.tostring(population, encoding="utf-8")

    header = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'
    )

    if out_path.suffixes[-2:] == [".xml", ".gz"] or out_path.suffix == ".gz":
        with gzip.open(out_path, "wb") as f:
            f.write(header)
            f.write(xml_bytes)
    else:
        with out_path.open("wb") as f:
            f.write(header)
            f.write(xml_bytes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a tiny MATSim population (car-only) from a MATSim network.")
    parser.add_argument("--network", required=True, help="Input MATSim network.xml(.gz)")
    parser.add_argument("--out", required=True, help="Output population.xml(.gz)")
    parser.add_argument("--persons", type=int, default=50, help="Number of persons (default: 50)")
    parser.add_argument("--seed", type=int, default=4711, help="Random seed (default: 4711)")
    parser.add_argument("--depart-start", default="08:00:00", help="Departure window start (HH:MM:SS)")
    parser.add_argument("--depart-spread-s", type=int, default=3600, help="Random departure spread in seconds (default: 3600)")
    args = parser.parse_args()

    def parse_hhmmss(text: str) -> int:
        parts = text.strip().split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid time: {text}")
        h, m, s = (int(p) for p in parts)
        return h * 3600 + m * 60 + s

    network_path = Path(args.network)
    out_path = Path(args.out)
    links = read_car_links(network_path)
    if not links:
        print("[ERROR] No car-capable links found in network (modes must include 'car').", file=sys.stderr)
        return 2

    write_population(
        out_path=out_path,
        links=links,
        persons=max(1, args.persons),
        seed=args.seed,
        departure_start_s=parse_hhmmss(args.depart_start),
        departure_spread_s=max(0, args.depart_spread_s),
    )
    print(f"[INFO] Wrote population: {out_path}")
    print(f"[INFO] Used {len(links)} car-capable links")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
