#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import gzip
import argparse
import csv
from collections import defaultdict

def parse_schedule(schedule_file):
    """
    Parses transit schedule to get expected arrival times for each departure.
    Returns: {vehicle_id: {stop_id: expected_time}}
    Note: In MATSim, transit vehicles are often named after their departure id or linked to it.
    """
    print(f"Loading schedule: {schedule_file}")
    opener = gzip.open if schedule_file.endswith(".gz") else open
    
    # Map departure_id -> {stop_index: (stop_id, arrival_offset)}
    route_stops = {}
    
    # Map vehicle_id -> {stop_id: scheduled_time}
    scheduled_arrivals = {}
    
    # Map departure_id -> transit_line_id, route_id
    departure_info = {}

    context = ET.iterparse(opener(schedule_file, "rb"), events=("start", "end"))
    
    current_line = None
    current_route = None
    
    for event, elem in context:
        if event == "start":
            if elem.tag == "transitLine":
                current_line = elem.get("id")
            elif elem.tag == "transitRoute":
                current_route = elem.get("id")
                route_id = f"{current_line}_{current_route}"
                route_stops[route_id] = []
            elif elem.tag == "stop":
                if current_route:
                    stop_id = elem.get("refId")
                    # Use arrivalOffset if available, else departureOffset
                    arr_offset = elem.get("arrivalOffset") or elem.get("departureOffset")
                    if arr_offset:
                        h, m, s = map(int, arr_offset.split(":"))
                        offset_sec = h * 3600 + m * 60 + s
                        route_stops[f"{current_line}_{current_route}"].append((stop_id, offset_sec))
            elif elem.tag == "departure":
                dep_id = elem.get("id")
                veh_id = elem.get("vehicleRefId")
                dep_time_str = elem.get("departureTime")
                if dep_time_str:
                    h, m, s = map(int, dep_time_str.split(":"))
                    dep_sec = h * 3600 + m * 60 + s
                    
                    route_id = f"{current_line}_{current_route}"
                    stops = route_stops.get(route_id, [])
                    
                    # We use veh_id as the primary key because events use vehicle
                    scheduled_arrivals[veh_id] = {}
                    for stop_id, offset in stops:
                        scheduled_arrivals[veh_id][stop_id] = dep_sec + offset
                    
                    departure_info[veh_id] = {
                        "line": current_line,
                        "route": current_route,
                        "dep_id": dep_id
                    }
        elif event == "end":
            if elem.tag == "transitRoute":
                current_route = None
            elif elem.tag == "transitLine":
                current_line = None
            elem.clear()
            
    return scheduled_arrivals, departure_info

def parse_events(events_file, scheduled_arrivals, departure_info):
    """
    Parses events to find actual arrival times at facilities.
    """
    print(f"Parsing events: {events_file}")
    opener = gzip.open if events_file.endswith(".gz") else open
    
    delays = []
    
    context = ET.iterparse(opener(events_file, "rb"), events=("end",))
    for event, elem in context:
        if elem.tag == "event":
            etype = elem.get("type")
            if etype == "VehicleArrivesAtFacility":
                veh_id = elem.get("vehicle")
                stop_id = elem.get("facility")
                time = float(elem.get("time"))
                
                if veh_id in scheduled_arrivals and stop_id in scheduled_arrivals[veh_id]:
                    expected = scheduled_arrivals[veh_id][stop_id]
                    delay = time - expected
                    
                    info = departure_info[veh_id]
                    delays.append({
                        "vehicle": veh_id,
                        "line": info["line"],
                        "route": info["route"],
                        "stop": stop_id,
                        "expected": expected,
                        "actual": time,
                        "delay_sec": delay
                    })
        elem.clear()
    return delays

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--output", default="pt_delay_analysis.csv")
    args = parser.parse_args()
    
    scheduled_arrivals, departure_info = parse_schedule(args.schedule)
    delays = parse_events(args.events, scheduled_arrivals, departure_info)
    
    if not delays:
        print("No delay data found. Check if VehicleArrivesAtFacility events exist.")
        return

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=delays[0].keys())
        writer.writeheader()
        writer.writerows(delays)
    
    print(f"Analysis complete. Results written to {args.output}")
    
    # Print summary
    avg_delay = sum(d["delay_sec"] for d in delays) / len(delays)
    max_delay = max(d["delay_sec"] for d in delays)
    print(f"Summary:")
    print(f"  Total Arrival Events: {len(delays)}")
    print(f"  Average Delay: {avg_delay:.2f}s")
    print(f"  Max Delay: {max_delay:.2f}s")

if __name__ == "__main__":
    main()
