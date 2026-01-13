"""
Extract and sample agents from a MATSim population file by mode.

Usage:
    python extract_and_sample.py \
        --input input_pop.xml.gz \
        --output output_pop.xml.gz \
        --mode car \
        --count 63000 \
        --seed 42
"""

import argparse
import gzip
import random
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Extract and sample agents by mode.")
    parser.add_argument("--input", required=True, help="Input population XML file (can be .gz)")
    parser.add_argument("--output", required=True, help="Output population XML file (will be .gz)")
    parser.add_argument("--mode", required=True, help="Mode to filter by (e.g., 'car', 'pt')")
    parser.add_argument("--count", type=int, required=True, help="Target number of agents")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()

def has_mode(person, target_mode):
    """Check if person has a leg with the target mode."""
    for plan in person.findall("plan"):
        # Check only selected plans if multiple exist? 
        # MATSim usually simulates the selected plan.
        # But for simple populations, often just one plan.
        # Let's check all plans for safety or just the first one.
        # A safer check for 'is this a car agent' is if they have *any* car leg.
        for leg in plan.findall("leg"):
            if leg.get("mode") == target_mode:
                return True
    return False

def main():
    args = parse_args()
    random.seed(args.seed)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    print(f"Reading {input_path}...")
    
    if input_path.suffix == ".gz":
        with gzip.open(input_path, "rb") as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(input_path)
        
    root = tree.getroot()
    all_persons = root.findall("person")
    print(f"Total agents in input: {len(all_persons)}")
    
    # Filter by mode
    candidates = []
    print(f"Filtering for mode='{args.mode}'...")
    for p in all_persons:
        if has_mode(p, args.mode):
            candidates.append(p)
            
    print(f"Found {len(candidates)} candidate agents with mode '{args.mode}'.")
    
    if len(candidates) < args.count:
        print(f"Error: Not enough agents with mode '{args.mode}' to satisfy count {args.count}.")
        sys.exit(1)
        
    # Sample
    print(f"Sampling {args.count} agents...")
    selected_persons = random.sample(candidates, args.count)
    
    # Create new root
    new_root = ET.Element("population")
    for p in selected_persons:
        # We need to copy the element to avoid issues if we were doing more complex things,
        # but here we just append. Note: IDs must remain unique if we merge later.
        # They are unique in the source, so they remain unique here.
        new_root.append(p)
        
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing to {output_path}...")
    
    # Manual write to ensuring DOCTYPE and gzip
    xml_bytes = ET.tostring(new_root, encoding="utf-8")
    
    # Pretty print hack (optional, but good for readability if not huge)
    # For large files, skip pretty print to save time/memory. 
    # But usually <100k agents is manageable. Let's keep it compact.
    
    doctype = b'<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'
    
    # ET.tostring includes <?xml ... ?> if logical? No, usually just the element.
    # Let's add decl.
    header = b'<?xml version="1.0" encoding="utf-8"?>\n'
    
    with gzip.open(output_path, "wb") as f:
        f.write(header)
        f.write(doctype)
        f.write(xml_bytes)
        
    print("Done.")

if __name__ == "__main__":
    main()
