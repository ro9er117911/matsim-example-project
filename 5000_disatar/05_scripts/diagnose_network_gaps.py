import re
import pandas as pd
from pathlib import Path
import argparse

def parse_pt_log_gaps(log_path, output_csv):
    """
    Parses PT Mapping log for 'No route was found' warnings.
    Extracts from_link -> to_link pairs and counts occurrences.
    """
    print(f"Scanning log: {log_path} ...")
    
    # ... regex patterns ...
    pattern_gap = re.compile(r"No route was found from link (link_[0-9_a-zA-Z]+) to link (link_[0-9_a-zA-Z]+|pt_bridge_[0-9_a-zA-Z]+)")
    pattern_route = re.compile(r"TransitRoute: [0-9]+_([0-9]+)") # Captures route_num
    
    gaps = []
    current_route = None
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Track current route being processed
            m_route = pattern_route.search(line)
            if m_route:
                current_route = m_route.group(1)
            
            # Detect gaps
            m_gap = pattern_gap.search(line)
            if m_gap:
                from_link = m_gap.group(1)
                to_link = m_gap.group(2)
                gaps.append({
                    'route_num': current_route if current_route else "unknown",
                    'from_link': from_link,
                    'to_link': to_link
                })

    if not gaps:
        print("No gaps found!")
        # Create empty CSV with headers
        pd.DataFrame(columns=['route_num', 'from_link', 'to_link', 'count']).to_csv(output_csv, index=False)
        return

    df = pd.DataFrame(gaps)
    # Group by link pair to count frequency
    summary = df.groupby(['route_num', 'from_link', 'to_link']).size().reset_index(name='count')
    
    print(f"Total Gaps detected: {len(gaps)}")
    print(f"Unique Gaps: {len(summary)}")
    
    summary.to_csv(output_csv, index=False)
    print(f"Saved summary to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnose PT Mapping Gaps")
    parser.add_argument("log_file", help="Path to PTMapper log file")
    parser.add_argument("output_csv", help="Path to output CSV")
    
    args = parser.parse_args()
    
    parse_pt_log_gaps(args.log_file, args.output_csv)
