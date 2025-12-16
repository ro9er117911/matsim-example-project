#!/usr/bin/env python3
"""
Remove car mode from all components except the largest car-connected component.
Keeps other modes (subway, walk, etc.) untouched and preserves the MATSim DTD.

Usage:
  python scripts/clean_car_components.py \
    --input-network scenarios/equil/network-with-pt-metro-v7-subway-only.xml.gz \
    --output-network scenarios/equil/network-with-pt-metro-v7-subway-only-carclean.xml.gz
"""
import argparse
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict, deque


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Keep only the largest car component; drop car mode elsewhere.")
    p.add_argument("--input-network", required=True)
    p.add_argument("--output-network", required=True)
    return p.parse_args()


def open_for_read(path: str):
    return gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")


def open_for_write(path: str):
    return gzip.open(path, "wb") if path.endswith(".gz") else open(path, "wb")


def main() -> None:
    args = parse_args()
    print(f"[info] loading network {args.input_network}")
    with open_for_read(args.input_network) as f:
        tree = ET.parse(f)
    root = tree.getroot()

    # Build directed car graph
    out = defaultdict(list)
    links = []
    for link in root.iter("link"):
        modes = link.attrib.get("modes", "")
        mode_set = set(modes.split(",")) if modes else set()
        links.append((link, mode_set))
        if "car" in mode_set:
            frm = link.attrib["from"]
            to = link.attrib["to"]
            out[frm].append(to)

    # Compute SCCs (Kosaraju) to keep only largest strongly connected component for car
    nodes = set(out.keys()) | {v for vs in out.values() for v in vs}
    visited = set()
    order = []
    for n in nodes:
        if n in visited:
            continue
        stack = [(n, 0)]
        while stack:
            u, state = stack.pop()
            if state == 0:
                if u in visited:
                    continue
                visited.add(u)
                stack.append((u, 1))
                for v in out.get(u, ()):
                    if v not in visited:
                        stack.append((v, 0))
            else:
                order.append(u)

    rev = defaultdict(list)
    for a, vs in out.items():
        for b in vs:
            rev[b].append(a)

    visited.clear()
    components = []
    while order:
        n = order.pop()
        if n in visited:
            continue
        stack = [n]
        visited.add(n)
        comp = []
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in rev.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    stack.append(v)
        components.append(comp)

    if not components:
        print("[warn] no car components found; writing input back unchanged")
        largest = set()
    else:
        components.sort(key=len, reverse=True)
        largest = set(components[0])
        print(f"[info] car SCCs: {len(components)}; largest size {len(largest)} nodes; rest total {sum(len(c) for c in components[1:])}")

    # Remove car from links whose from/to are not both in largest SCC
    removed = 0
    for link, mode_set in links:
        if "car" not in mode_set:
            continue
        if link.attrib["from"] in largest and link.attrib["to"] in largest:
            continue
        mode_set.discard("car")
        removed += 1
        if mode_set:
            link.set("modes", ",".join(sorted(mode_set)))
        else:
            link.attrib.pop("modes", None)

    print(f"[info] removed car mode from {removed} links outside largest car SCC")

    doctype = '<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">'
    with open_for_write(args.output_network) as f:
        f.write(b"<?xml version='1.0' encoding='UTF-8'?>\n")
        f.write((doctype + "\n").encode("utf-8"))
        f.write(ET.tostring(root, encoding="utf-8"))
    print(f"[info] wrote {args.output_network}")


if __name__ == "__main__":
    main()
