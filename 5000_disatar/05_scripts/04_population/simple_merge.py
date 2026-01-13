"""
Merge multiple MATSim population files into one.

Usage:
    python simple_merge.py \
        --inputs pop1.xml.gz pop2.xml.gz \
        --output merged.xml.gz
"""

import argparse
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Merge population files.")
    parser.add_argument("--inputs", nargs="+", required=True, help="List of input population files")
    parser.add_argument("--output", required=True, help="Output merged population file")
    return parser.parse_args()

def main():
    args = parse_args()
    
    merged_root = ET.Element("population")
    seen_ids = set()
    total_agents = 0
    
    for input_file in args.inputs:
        path = Path(input_file)
        print(f"Reading {path}...")
        
        if path.suffix == ".gz":
            with gzip.open(path, "rb") as f:
                tree = ET.parse(f)
        else:
            tree = ET.parse(path)
            
        root = tree.getroot()
        persons = root.findall("person")
        print(f"  Found {len(persons)} agents.")
        
        for p in persons:
            pid = p.get("id")
            if pid in seen_ids:
                print(f"  Warning: Duplicate agent ID {pid} found in {path}. Skipping.")
                continue
            seen_ids.add(pid)
            merged_root.append(p)
            total_agents += 1
            
    print(f"Total agents in merged population: {total_agents}")
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing to {output_path}...")
    
    xml_bytes = ET.tostring(merged_root, encoding="utf-8")
    header = b'<?xml version="1.0" encoding="utf-8"?>\n'
    doctype = b'<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'
    
    with gzip.open(output_path, "wb") as f:
        f.write(header)
        f.write(doctype)
        f.write(xml_bytes)
        
    print("Done.")

if __name__ == "__main__":
    main()
