import gzip
import xml.etree.ElementTree as ET
import re

schedule_file = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes/transitSchedule_mapped.xml.gz"

def analyze_schedule(file_path):
    print(f"Analyzing {file_path}...")
    
    with gzip.open(file_path, 'rb') as f:
        tree = ET.parse(f)
        root = tree.getroot()
    
    # Namespace handling (MATSim usually doesn't use namespaces in these files, but let's be safe)
    # Actually MATSim XMLs are usually simple.
    
    for line in root.findall('.//transitLine'):
        line_id = line.get('id')
        for route in line.findall('.//transitRoute'):
            route_id = route.get('id')
            mode = route.find('transportMode').text if route.find('transportMode') is not None else "Unknown"
            
            # Count links in the route
            links = route.findall('./route/link')
            total_links = len(links)
            
            # Count artificial links
            artificial_links = 0
            for link in links:
                ref_id = link.get('refId')
                if ref_id.startswith('pt_'):
                    artificial_links += 1
            
            print(f"Line: {line_id}, Route: {route_id}")
            print(f"  Mode: {mode}")
            print(f"  Total Links: {total_links}")
            print(f"  Artificial Links: {artificial_links}")
            print(f"  % Artificial: {(artificial_links/total_links*100 if total_links > 0 else 0):.1f}%")
            print("-" * 30)

if __name__ == "__main__":
    analyze_schedule(schedule_file)
