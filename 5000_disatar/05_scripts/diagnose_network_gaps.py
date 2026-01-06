import re
import pandas as pd
from pathlib import Path

def extract_gaps(file_path):
    gaps = []
    current_route = "Unknown"
    
    # Pattern for route start: 2026-01-06T15:41:56,306  INFO Counter:70  route # 1
    # Or maybe it shows the actual ID later?
    # In PTMapper: 2026-01-06T15:41:56,241  INFO Progress:40 Calculating pseudoTransitRoutes ... 0/8 (0.00%)
    
    route_pattern = re.compile(r"route # (\d+)")
    gap_pattern = re.compile(r"No route was found from link ([\w_]+) to link ([\w_]+)")
    
    if not file_path.exists():
        print(f"Log file {file_path} not found.")
        return
    
    with open(file_path, 'r') as f:
        for line in f:
            route_match = route_pattern.search(line)
            if route_match:
                current_route = route_match.group(1)
            
            gap_match = gap_pattern.search(line)
            if gap_match:
                gaps.append({
                    'route_num': current_route,
                    'from_link': gap_match.group(1), 
                    'to_link': gap_match.group(2)
                })
    
    df = pd.DataFrame(gaps)
    if df.empty:
        print("No routing gaps found in log.")
        return
    
    # Summary by route and link pair
    summary = df.groupby(['route_num', 'from_link', 'to_link']).size().reset_index(name='count')
    summary = summary.sort_values(['route_num', 'count'], ascending=[True, False])
    
    print(f"Total Gaps detected: {len(df)}")
    print(f"Unique Gaps (Route + Link Pair): {len(summary)}")
    
    print("\nGaps per Route:")
    print(df.groupby('route_num').size())
    
    output_csv = "network_gaps_detailed.csv"
    summary.to_csv(output_csv, index=False)
    print(f"\nSaved detailed summary to {output_csv}")

if __name__ == "__main__":
    # Test with the large log file
    log_file = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes/pt_mapping_final.log")
    extract_gaps(log_file)
