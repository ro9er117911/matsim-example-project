#!/usr/bin/env python3
"""
Build MATSim network from OSM using subprocess call to Java tool.
Alternative: use osmosis to filter first, then convert.
"""
import subprocess
import sys
import os

def main():
    base_dir = "/Users/ro9air/matsim-example-project/5000_disatar/evacuation_test"
    osm_file = f"{base_dir}/input/tamsui_wanlong_large.osm"
    
    # Check OSM file format
    with open(osm_file, 'rb') as f:
        header = f.read(100)
        
    if b'<?xml' in header:
        print("OSM file is XML format")
    elif b'OSMHeader' in header or header[:4] == b'OBF':
        print("OSM file is PBF format - needs conversion")
    else:
        print(f"Unknown format, first bytes: {header[:20]}")
        
    # Check file size
    size_gb = os.path.getsize(osm_file) / (1024**3)
    print(f"File size: {size_gb:.2f} GB")

if __name__ == "__main__":
    main()
