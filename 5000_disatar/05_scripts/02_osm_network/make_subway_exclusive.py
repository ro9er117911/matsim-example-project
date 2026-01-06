#!/usr/bin/env python3
"""
Convert metro/subway links to subway-only (remove car) and optionally lower subway PCE.

Examples:
  python 5000_disatar/05_scripts/02_osm_network/make_subway_exclusive.py \
    --input-network scenarios/equil/network-with-pt-metro-v7-carscc.xml.gz \
    --output-network scenarios/equil/network-with-pt-metro-v7-subway-only.xml.gz \
    --input-vehicles scenarios/equil/transitVehicles.xml \
    --output-vehicles scenarios/equil/transitVehicles-subway-lowpce.xml \
    --subway-pce 1.0
"""
import argparse
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Make subway links exclusive and reduce subway PCE.")
    p.add_argument("--input-network", required=True, help="Input network XML (gz ok).")
    p.add_argument("--output-network", required=True, help="Output network XML (gz ok).")
    p.add_argument("--input-vehicles", required=False, help="Input transit vehicles XML.")
    p.add_argument("--output-vehicles", required=False, help="Output transit vehicles XML.")
    p.add_argument("--subway-pce", type=float, default=None, help="If set, override subway vehicle PCE to this value.")
    return p.parse_args()


def open_for_read(path: str):
    return gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")


def open_for_write(path: str):
    return gzip.open(path, "wb") if path.endswith(".gz") else open(path, "wb")


def convert_network(in_path: str, out_path: str) -> tuple[int, int]:
    print(f"[info] Loading network {in_path}")
    with open_for_read(in_path) as f:
        tree = ET.parse(f)
    root = tree.getroot()
    total = 0
    touched = 0
    for link in root.iter("link"):
        total += 1
        modes = link.attrib.get("modes")
        if not modes:
            continue
        mode_list = modes.split(",")
        if "subway" in mode_list:
            touched += 1
            # Subway-exclusive: strip everything else, keep only subway
            link.set("modes", "subway")
    print(f"[info] Subway links touched: {touched}/{total}")
    print(f"[info] Writing {out_path}")
    # Preserve MATSim DTD so the parser recognizes the file
    doctype = '<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">'
    with open_for_write(out_path) as f:
        f.write(b"<?xml version='1.0' encoding='UTF-8'?>\n")
        f.write((doctype + "\n").encode("utf-8"))
        f.write(ET.tostring(root, encoding="utf-8"))
    return touched, total


def convert_vehicles(in_path: str, out_path: str, subway_pce: float) -> int:
    print(f"[info] Loading vehicles {in_path}")
    tree = ET.parse(in_path)
    root = tree.getroot()
    changed = 0
    for vtype in root.iter("{http://www.matsim.org/files/dtd}vehicleType"):
        modes = []
        # networkMode is optional; if not present, we still treat type id containing 'subway'
        for nm in vtype.findall("{http://www.matsim.org/files/dtd}networkMode"):
            modes.append(nm.attrib.get("networkMode"))
        is_subway = "subway" in modes or "subway" in vtype.attrib.get("id", "").lower()
        if not is_subway:
            continue
        pce_elem = vtype.find("{http://www.matsim.org/files/dtd}passengerCarEquivalents")
        if pce_elem is None:
            continue
        old = pce_elem.attrib.get("pce")
        pce_elem.set("pce", str(subway_pce))
        changed += 1
        print(f"[info] Set subway PCE {old} -> {subway_pce} for vehicleType {vtype.attrib.get('id')}")
    print(f"[info] Writing vehicles to {out_path}")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return changed


def main() -> None:
    args = parse_args()
    convert_network(args.input_network, args.output_network)
    if args.subway_pce is not None and args.input_vehicles and args.output_vehicles:
        convert_vehicles(args.input_vehicles, args.output_vehicles, args.subway_pce)
    elif args.subway_pce is not None:
        print("[warn] subway-pce provided but vehicles input/output missing; skipping vehicle conversion.")


if __name__ == "__main__":
    main()
