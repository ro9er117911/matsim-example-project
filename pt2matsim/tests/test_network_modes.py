#!/usr/bin/env python3
"""
Regression test for the PT-prepared network.

Ensures the network exposes the expected set of modes and that every PT-relevant
link also allows the generic `pt` mode required by the mapper.
"""

from __future__ import annotations

import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_MODES = {"car", "pt", "bus", "rail", "subway", "walk"}
PT_COMPANION_MODES = {"bus", "rail", "subway", "tram", "light_rail"}


def iter_link_modes(network_path: Path):
    with gzip.open(network_path, "rt", encoding="utf-8") as handle:
        for _, elem in ET.iterparse(handle, events=("end",)):
            if elem.tag != "link":
                elem.clear()
                continue
            modes = {
                token
                for token in elem.get("modes", "").replace(",", " ").split()
                if token
            }
            yield elem.get("id", ""), modes
            elem.clear()


def main() -> None:
    network_path = Path(__file__).resolve().parents[1] / "output_v1" / "network-prepared.xml.gz"
    if not network_path.exists():
        print(f"[ERROR] network not found at {network_path}", file=sys.stderr)
        sys.exit(1)

    modes_found: set[str] = set()
    for link_id, modes in iter_link_modes(network_path):
        modes_found.update(modes)
        if PT_COMPANION_MODES & modes and "pt" not in modes:
            missing_modes = ", ".join(sorted(PT_COMPANION_MODES & modes))
            print(f"[FAIL] Link {link_id} supports {missing_modes} but lacks 'pt'.")
            sys.exit(1)

    missing = REQUIRED_MODES - modes_found
    if missing:
        print(f"[FAIL] Missing required modes: {', '.join(sorted(missing))}")
        print(f"       Present modes sample: {sorted(list(modes_found))[:10]}")
        sys.exit(1)

    print("[PASS] Network exposes required modes and PT links carry 'pt'.")


if __name__ == "__main__":
    main()

