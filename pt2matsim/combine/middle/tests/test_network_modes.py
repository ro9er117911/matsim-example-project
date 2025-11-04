#!/usr/bin/env python3
"""
Minimal regression test for the OSM → MATSim network conversion.

Ensures that the prepared network used for PT mapping exposes the key
multimodal modes required by the merged GTFS feed.
"""

from __future__ import annotations

import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def collect_modes(network_path: Path) -> set[str]:
    modes: set[str] = set()
    with gzip.open(network_path, "rt", encoding="utf-8") as handle:
        for _, elem in ET.iterparse(handle, events=("end",)):
            if elem.tag == "link":
                raw = elem.get("modes", "")
                for candidate in raw.replace(",", " ").split():
                    if candidate:
                        modes.add(candidate)
            elem.clear()
    return modes


def main() -> None:
    network_path = Path(__file__).resolve().parents[1] / "output_v1" / "network-prepared.xml.gz"
    if not network_path.exists():
        print(f"[ERROR] network not found at {network_path}", file=sys.stderr)
        sys.exit(1)

    modes = collect_modes(network_path)
    required = {"car", "pt", "bus", "rail", "subway", "walk"}
    missing = required - modes
    if missing:
        print(f"[FAIL] Missing required modes: {', '.join(sorted(missing))}")
        print(f"       Present modes sample: {sorted(list(modes))[:10]}")
        sys.exit(1)

    print("[PASS] Multimodal network exposes all required modes.")


if __name__ == "__main__":
    main()

