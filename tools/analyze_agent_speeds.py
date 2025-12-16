#!/usr/bin/env python3
"""
分析 MATSim events 中 agent 的速度分布，用於診斷紅點/慢速問題。
用法:
  python analyze_agent_speeds.py --events output_staggered_iter10/output_events.xml.gz \
    --network output_staggered_iter10/output_network.xml.gz \
    --slow-threshold 1.0 \
    --out slow_links_analysis.csv

輸出: 終端摘要 + CSV (link_id, avg_speed_m_s, avg_duration_s, pass_count, length_m, freespeed_m_s, modes)
"""

import argparse
import csv
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from statistics import mean


def load_network(network_file):
    """讀 network，回傳 link 屬性 (長度/限速/模式)。"""
    lengths = {}
    freespeeds = {}
    modes = {}
    opener = gzip.open if network_file.endswith(".gz") else open
    with opener(network_file, "rt", encoding="utf-8") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "link":
                lid = elem.attrib["id"]
                lengths[lid] = float(elem.attrib.get("length", 0))
                freespeeds[lid] = float(elem.attrib.get("freespeed", 0))
                modes[lid] = elem.attrib.get("modes", "")
            elem.clear()
    return lengths, freespeeds, modes


def parse_events(events_file):
    """解析 events，計算每個車輛在每個 link 上的 travel time。"""
    agent_link_entry = {}  # (vehicle, link) -> entry_time
    link_durations = defaultdict(list)  # link_id -> [durations]
    opener = gzip.open if events_file.endswith(".gz") else open
    with opener(events_file, "rt", encoding="utf-8") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if elem.tag != "event":
                continue
            etype = elem.get("type", "")
            t = float(elem.get("time", 0))
            if etype == "entered link":
                veh = elem.get("vehicle")
                link = elem.get("link")
                if veh and link:
                    agent_link_entry[(veh, link)] = t
            elif etype == "left link":
                veh = elem.get("vehicle")
                link = elem.get("link")
                key = (veh, link)
                if key in agent_link_entry:
                    dt = t - agent_link_entry.pop(key)
                    if dt > 0:
                        link_durations[link].append(dt)
            elem.clear()
    return link_durations


def summarize(link_durations, lengths, freespeeds, modes, slow_threshold, csv_path):
    rows = []
    all_durations = []
    slow_records = []
    for link, durations in link_durations.items():
        if not durations:
            continue
        avg_dt = mean(durations)
        length = lengths.get(link, 0)
        avg_speed = length / avg_dt if length and avg_dt > 0 else 0
        rows.append(
            {
                "link_id": link,
                "avg_speed_m_s": avg_speed,
                "avg_duration_s": avg_dt,
                "pass_count": len(durations),
                "length_m": length,
                "freespeed_m_s": freespeeds.get(link, 0),
                "modes": modes.get(link, ""),
            }
        )
        all_durations.extend(durations)
        if avg_speed < slow_threshold:
            slow_records.append((link, avg_speed, avg_dt, len(durations)))

    rows.sort(key=lambda r: r["avg_speed_m_s"])
    # Write CSV
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "link_id",
                "avg_speed_m_s",
                "avg_duration_s",
                "pass_count",
                "length_m",
                "freespeed_m_s",
                "modes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} link stats to {csv_path}")
    print(f"Slow threshold: {slow_threshold} m/s")
    print(f"Links below threshold: {len(slow_records)}")
    for link, spd, dt, cnt in slow_records[:20]:
        print(f"  {link}: {spd:.2f} m/s, {dt:.1f}s avg, {cnt} passes, length={lengths.get(link,0):.1f}m, free={freespeeds.get(link,0):.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True, help="output_events.xml(.gz)")
    ap.add_argument("--network", required=True, help="network xml(.gz) for length/freespeed")
    ap.add_argument("--slow-threshold", type=float, default=1.0, help="flag links with avg speed below this (m/s)")
    ap.add_argument("--out", default="slow_links_analysis.csv", help="CSV output path")
    args = ap.parse_args()

    lengths, freespeeds, modes = load_network(args.network)
    link_durations = parse_events(args.events)
    summarize(link_durations, lengths, freespeeds, modes, args.slow_threshold, args.out)


if __name__ == "__main__":
    main()
