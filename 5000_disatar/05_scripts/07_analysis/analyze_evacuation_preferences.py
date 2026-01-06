#!/usr/bin/env python3
import csv
import gzip
import argparse
from collections import defaultdict

def analyze_trips(trips_file, output_file):
    print(f"Analyzing trips: {trips_file}")
    opener = gzip.open if trips_file.endswith(".gz") else open
    
    mode_counts = defaultdict(int)
    mode_travel_times = defaultdict(list)
    mode_distances = defaultdict(list)
    
    # spatial_bins: (grid_x, grid_y) -> mode -> count
    spatial_bins = defaultdict(lambda: defaultdict(int))
    grid_size = 1000 # 1km grid
    
    with opener(trips_file, "rt") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            mode = row["main_mode"]
            # MATSim CSV format might use different column names depending on version
            # Common names: trav_time, duration, trip_duration
            dur = float(row.get("trav_time") or row.get("duration") or 0)
            dist = float(row.get("distance") or row.get("trip_distance") or 0)
            
            mode_counts[mode] += 1
            mode_travel_times[mode].append(dur)
            mode_distances[mode].append(dist)
            
            # Spatial analysis
            start_x = float(row.get("start_x") or 0)
            start_y = float(row.get("start_y") or 0)
            if start_x and start_y:
                gx = int(start_x // grid_size)
                gy = int(start_y // grid_size)
                spatial_bins[(gx, gy)][mode] += 1

    # Write summary report
    with open(output_file, "w") as f:
        f.write("# Evacuation Preference Analysis Report\n\n")
        f.write("## Mode Share Summary\n")
        total_trips = sum(mode_counts.values())
        f.write(f"Total Trips: {total_trips}\n\n")
        f.write("| Mode | Count | Share (%) | Avg Travel Time (min) | Avg Distance (km) |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for mode in sorted(mode_counts.keys()):
            count = mode_counts[mode]
            share = (count / total_trips) * 100
            avg_time = (sum(mode_travel_times[mode]) / count) / 60 if count > 0 else 0
            avg_dist = (sum(mode_distances[mode]) / count) / 1000 if count > 0 else 0
            f.write(f"| {mode} | {count} | {share:.2f}% | {avg_time:.2f} | {avg_dist:.2f} |\n")
        
        f.write("\n## Spatial Distribution (Top 10 Grids)\n")
        # Sort grids by total trips
        sorted_grids = sorted(spatial_bins.items(), key=lambda x: sum(x[1].values()), reverse=True)
        f.write("| Grid (km) | Total | " + " | ".join(sorted(mode_counts.keys())) + " |\n")
        f.write("| --- | --- | " + " | ".join(["---"] * len(mode_counts)) + " |\n")
        for grid, modes in sorted_grids[:10]:
            total = sum(modes.values())
            m_shares = [str(modes.get(m, 0)) for m in sorted(mode_counts.keys())]
            f.write(f"| {grid} | {total} | " + " | ".join(m_shares) + " |\n")

    print(f"Analysis complete. Report written to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trips", required=True)
    parser.add_argument("--output", default="evacuation_analysis_report.md")
    args = parser.parse_args()
    analyze_trips(args.trips, args.output)
