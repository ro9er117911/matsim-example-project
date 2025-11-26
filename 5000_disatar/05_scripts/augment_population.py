"""
Augment a MATSim population by cloning agents with jittered coords/times.

Usage:
    python augment_population.py \
        --input 5000_disatar/working_temp/population.xml \
        --output 5000_disatar/working_temp/population_augmented_50k.xml.gz \
        --target-size 50000 \
        --start-jitter 300 \
        --end-jitter 300 \
        --dep-window 1200 \
        --seed 42

Notes:
- Designed for simple plans with two activities (home -> evacuation) and one leg.
- Departure times are 03:00:00 in the source; we randomize within dep-window seconds.
- Coordinates are in EPSG:3826 (meters); jitter is applied in meters.
"""

import argparse
import copy
import gzip
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input population XML(.gz)")
    parser.add_argument("--output", required=True, help="Output population XML(.gz)")
    parser.add_argument("--target-size", type=int, required=True, help="Total agents to output")
    parser.add_argument("--start-jitter", type=float, default=300.0, help="Std dev (m) for origin jitter")
    parser.add_argument("--end-jitter", type=float, default=300.0, help="Std dev (m) for destination jitter")
    parser.add_argument("--dep-window", type=int, default=1200, help="Uniform [0, dep_window] sec added to dep time")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def to_seconds(hms: str) -> int:
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def to_hms(seconds: int) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def jitter_coord(elem: ET.Element, sigma: float):
    x = float(elem.get("x")) + random.gauss(0, sigma)
    y = float(elem.get("y")) + random.gauss(0, sigma)
    elem.set("x", f"{x:.2f}")
    elem.set("y", f"{y:.2f}")


def load_base_population(path: Path) -> Tuple[ET.ElementTree, List[ET.Element]]:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(path)
    root = tree.getroot()
    persons = root.findall("person")
    if not persons:
        raise RuntimeError("No persons found in input population.")
    return tree, persons


def augment(persons: List[ET.Element], target_size: int, start_sigma: float, end_sigma: float, dep_window: int) -> ET.Element:
    base_count = len(persons)
    if target_size < base_count:
        raise ValueError(f"target_size {target_size} < base_count {base_count}")

    clones_needed = target_size - base_count
    print(f"Base agents: {base_count}, cloning {clones_needed} to reach {target_size}")

    # Start with originals (deepcopy so we can mutate times/coords uniformly)
    augmented: List[ET.Element] = [copy.deepcopy(p) for p in persons]

    # Sample with replacement for clones
    for i in range(clones_needed):
        base = random.choice(persons)
        new_person = copy.deepcopy(base)
        new_person.set("id", f"{base.get('id')}_aug{i+1}")

        plan = new_person.find("plan")
        activities = plan.findall("activity")
        if not activities:
            raise RuntimeError(f"Person {new_person.get('id')} has no activities")

        # Jitter origin/destination
        jitter_coord(activities[0], start_sigma)
        jitter_coord(activities[-1], end_sigma)

        # Jitter departure time on first activity if end_time exists
        end_time = activities[0].get("end_time")
        if end_time:
            base_sec = to_seconds(end_time)
            delta = random.uniform(0, dep_window)
            activities[0].set("end_time", to_hms(base_sec + delta))

        augmented.append(new_person)

    # Build new root
    root = ET.Element("population")
    for person in augmented:
        root.append(person)
    return root


def write_population(root: ET.Element, output: Path):
    # Inject DOCTYPE after XML declaration
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    header, rest = xml_bytes.split(b"\n", 1)
    doctype = b'<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">'
    final = header + b"\n" + doctype + b"\n\n" + rest

    if output.suffix == ".gz":
        with gzip.open(output, "wb") as f:
            f.write(final)
    else:
        output.write_bytes(final)


def main():
    args = parse_args()
    random.seed(args.seed)

    inp = Path(args.input)
    out = Path(args.output)

    tree, persons = load_base_population(inp)
    root = augment(
        persons=persons,
        target_size=args.target_size,
        start_sigma=args.start_jitter,
        end_sigma=args.end_jitter,
        dep_window=args.dep_window,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    write_population(root, out)
    print(f"✓ Augmented population saved: {out} (size={len(root.findall('person'))})")


if __name__ == "__main__":
    main()
