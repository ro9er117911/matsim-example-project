import gzip
import xml.etree.ElementTree as ET
import sys
import os

def fix_network(input_path, output_path):
    print(f"Processing {input_path}...")
    
    try:
        with gzip.open(input_path, 'rb') as f:
            tree = ET.parse(f)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    root = tree.getroot()
    links_fixed = 0
    links = root.find('links')
    if links is None:
        # Fallback if structure is different, though standard MATSim has <links>
        iterator = root.iter('link')
    else:
        iterator = links.findall('link')

    for link in iterator:
        try:
            cap = float(link.get('capacity'))
            # Fix zero capacity
            if cap <= 0.0:
                print(f"Fixing Link {link.get('id')}: capacity {cap} -> 1500.0")
                link.set('capacity', '1500.0')
                
                # Also fix permlanes if 0 or missing
                pl = float(link.get('permlanes', '0.0'))
                if pl <= 0.0:
                     link.set('permlanes', '1.0')
                links_fixed += 1
            
            # Optional: Check for self-loops (Link 1033)
            # if link.get('from') == link.get('to'):
            #    print(f"Warning: Link {link.get('id')} is a self-loop.")
                
        except (ValueError, TypeError):
            continue
            
    if links_fixed > 0:
        print(f"Fixed {links_fixed} links.")
        print(f"Saving to {output_path}...")
        with gzip.open(output_path, 'wb') as f:
            f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(b'<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n')
            tree.write(f, encoding='utf-8', xml_declaration=False)
        print("Done.")
    else:
        print("No zero-capacity links found. Network appears clean regarding capacity.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_network_capacity.py <input_xml_gz> <output_xml_gz>")
        sys.exit(1)
    
    fix_network(sys.argv[1], sys.argv[2])
