#!/usr/bin/env python3
"""
車輛捷運網頁: Generate a folium map showing occupied metro vehicles (and optionally cars)
from an existing MATSim output directory without re-running the simulation.

Usage:
  python3 src/main/python/visualization/vehicle_metro_webpage.py \
    --output-dir output_metro_0300_0618_5000 \
    --output-html metro_viz_filtered.html

Dependencies: folium, pyproj
"""
import argparse
import datetime
import gzip
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

import folium
from folium.plugins import TimestampedGeoJson
from pyproj import Transformer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="車輛捷運網頁: create map of occupied metro vehicles (and cars) from MATSim outputs"
    )
    parser.add_argument("--output-dir", required=True, help="MATSim output directory (contains output_events.xml.gz, output_network.xml.gz, ...)")
    parser.add_argument("--output-html", default="metro_viz_filtered.html", help="Where to write the generated HTML map")
    parser.add_argument("--sample-rate", type=int, default=5, help="Keep 1 in N entered-link events (higher -> smaller file)")
    parser.add_argument("--max-features", type=int, default=200000, help="Stop after this many features to keep HTML manageable")
    parser.add_argument("--start-time", type=float, default=0.0, help="Include events after this sim time (sec)")
    parser.add_argument("--end-time", type=float, default=None, help="Include events before this sim time (sec)")
    parser.add_argument("--only-transit", action="store_true", help="Show only occupied transit vehicles (hide cars)")
    parser.add_argument("--tiles", default="CartoDB positron", help="Folium tiles name")
    parser.add_argument(
        "--base-date",
        default="2025-12-01",
        help="Base date for timestamps (YYYY-MM-DD). Only affects playback clock.",
    )
    return parser.parse_args()


def ensure_exists(path: str, label: str) -> None:
    if not os.path.exists(path):
        sys.exit(f"[error] {label} not found: {path}")


def load_transit_ids(transit_vehicles_file: str) -> set[str]:
    transit_ids: set[str] = set()
    with gzip.open(transit_vehicles_file, "rb") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if elem.tag.endswith("vehicle"):
                transit_ids.add(elem.attrib["id"])
            elem.clear()
    return transit_ids


def load_network(network_file: str, transformer: Transformer) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    nodes: dict[str, list[float]] = {}
    links: dict[str, list[float]] = {}
    with gzip.open(network_file, "rb") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "node":
                nid = elem.attrib["id"]
                x = float(elem.attrib["x"])
                y = float(elem.attrib["y"])
                lon, lat = transformer.transform(x, y)
                nodes[nid] = [lon, lat]
            elif elem.tag == "link":
                lid = elem.attrib["id"]
                from_node = elem.attrib["from"]
                if from_node in nodes:
                    links[lid] = nodes[from_node]
            elem.clear()
    return nodes, links


def to_timestamp(seconds: float, base: datetime.datetime) -> str:
    return (base + datetime.timedelta(seconds=seconds)).isoformat()


def events_to_features(
    events_file: str,
    links: dict[str, list[float]],
    transit_ids: set[str],
    args: argparse.Namespace,
) -> tuple[list[dict], dict[str, int]]:
    vehicle_occupancy: defaultdict[str, int] = defaultdict(int)
    features: list[dict] = []
    SAMPLE_RATE = max(1, args.sample_rate)
    MAX_FEATURES = args.max_features
    base_dt = datetime.datetime.fromisoformat(args.base_date)

    stats = {"entered_link_events": 0, "features_kept": 0, "transit_movements": 0, "car_movements": 0}

    with gzip.open(events_file, "rb") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if elem.tag != "event":
                elem.clear()
                continue

            etype = elem.attrib.get("type")
            time_val = float(elem.attrib["time"])

            if etype == "PersonEntersVehicle":
                pid = elem.attrib["person"]
                if pid.startswith("pt_"):
                    elem.clear()
                    continue  # driver
                vid = elem.attrib["vehicle"]
                if vid in transit_ids:
                    vehicle_occupancy[vid] += 1

            elif etype == "PersonLeavesVehicle":
                pid = elem.attrib["person"]
                if pid.startswith("pt_"):
                    elem.clear()
                    continue
                vid = elem.attrib["vehicle"]
                if vid in transit_ids:
                    vehicle_occupancy[vid] = max(0, vehicle_occupancy[vid] - 1)

            elif etype == "entered link":
                stats["entered_link_events"] += 1
                vid = elem.attrib.get("vehicle")
                lid = elem.attrib.get("link")
                if lid not in links:
                    elem.clear()
                    continue
                if time_val < args.start_time:
                    elem.clear()
                    continue
                if args.end_time is not None and time_val > args.end_time:
                    elem.clear()
                    continue
                if stats["entered_link_events"] % SAMPLE_RATE != 0:
                    elem.clear()
                    continue

                is_transit = vid in transit_ids
                if args.only_transit and not is_transit:
                    elem.clear()
                    continue

                occupancy = vehicle_occupancy[vid] if is_transit else 1
                if is_transit and occupancy == 0:
                    elem.clear()
                    continue

                color = "#d63031" if is_transit else "#0984e3"
                radius = 5 if is_transit else 2
                popup = f"Metro {vid}<br>Pax: {occupancy}" if is_transit else f"Car {vid}"
                coord = links[lid]

                feature = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": coord},
                    "properties": {
                        "time": to_timestamp(time_val, base_dt),
                        "style": {"color": color},
                        "icon": "circle",
                        "iconstyle": {
                            "fillColor": color,
                            "fillOpacity": 0.8,
                            "stroke": "false",
                            "radius": radius,
                        },
                        "popup": popup,
                    },
                }
                features.append(feature)
                if is_transit:
                    stats["transit_movements"] += 1
                else:
                    stats["car_movements"] += 1

                if len(features) >= MAX_FEATURES:
                    print(f"[warn] Reached max features {MAX_FEATURES}, truncating output.")
                    elem.clear()
                    break

            elem.clear()

    stats["features_kept"] = len(features)
    return features, stats


def build_map(nodes: dict[str, list[float]], features: list[dict], output_html: str, tiles: str) -> None:
    if not nodes:
        sys.exit("[error] No nodes found in network; cannot compute map center.")
    avg_lat = sum(n[1] for n in nodes.values()) / len(nodes)
    avg_lon = sum(n[0] for n in nodes.values()) / len(nodes)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles=tiles)
    legend_html = """
         <div style="position: fixed;
         bottom: 50px; left: 50px; width: 180px; height: 120px;
         border:2px solid grey; z-index:9999; font-size:14px;
         background-color:white; opacity: 0.8;
         padding: 10px;">
         <b>車輛捷運網頁</b><br>
         <i style="background:#d63031; width:10px; height:10px; float:left; margin-right:5px; border-radius:50%;"></i> Occupied Metro<br>
         <i style="background:#0984e3; width:10px; height:10px; float:left; margin-right:5px; border-radius:50%;"></i> Agent Car<br>
         (Empty metros hidden)
         </div>
         """
    m.get_root().html.add_child(folium.Element(legend_html))

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT10S",
        duration="PT2M",
        transition_time=200,
        auto_play=False,
        loop=False,
    ).add_to(m)

    m.save(output_html)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir

    network_file = os.path.join(output_dir, "output_network.xml.gz")
    events_file = os.path.join(output_dir, "output_events.xml.gz")
    transit_vehicles_file = os.path.join(output_dir, "output_transitVehicles.xml.gz")

    ensure_exists(network_file, "network file")
    ensure_exists(events_file, "events file")
    ensure_exists(transit_vehicles_file, "transit vehicles file")

    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)

    print(f"[info] Loading transit vehicles from {transit_vehicles_file} ...")
    transit_ids = load_transit_ids(transit_vehicles_file)
    print(f"[info] Found {len(transit_ids)} transit vehicles in schedule.")

    print(f"[info] Parsing network from {network_file} ...")
    nodes, links = load_network(network_file, transformer)
    print(f"[info] Loaded {len(nodes)} nodes and {len(links)} link geometries.")

    print(f"[info] Parsing events from {events_file} ...")
    features, stats = events_to_features(events_file, links, transit_ids, args)
    print(f"[info] Features kept: {stats['features_kept']} (sampled from {stats['entered_link_events']} entered-link events)")
    print(f"[info] Transit movements kept: {stats['transit_movements']}; car movements kept: {stats['car_movements']}")

    print(f"[info] Building map -> {args.output_html}")
    build_map(nodes, features, args.output_html, args.tiles)
    print("[info] Done.")


if __name__ == "__main__":
    main()
