#!/usr/bin/env python3
import gzip
import random
import sys
import os

def generate_population(num_agents=280000, mode_split_car=0.63, output_file="population_280k.xml.gz"):
    """
    Generate a large population for Tamsui disaster simulation.
    Streaming version to avoid memory issues.
    """
    print(f"Generating {num_agents} agents and writing to {output_file}...")
    
    # Tamsui Center (approx EPSG:3826)
    center_x = 285000
    center_y = 2785000
    radius = 5000 # 5km radius
    
    # Destination (Evacuation Safe Zone - Southeast)
    dest_x = 305000
    dest_y = 2765000
    dest_radius = 2000
    
    num_car = int(num_agents * mode_split_car)
    num_pt = num_agents - num_car
    
    modes = ['car'] * num_car + ['pt'] * num_pt
    random.shuffle(modes)
    
    try:
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n')
            f.write('<population>\n')
            
            for i in range(num_agents):
                if i % 50000 == 0:
                    print(f"Processed {i} agents...")
                    
                agent_id = f"evac_{i:06d}"
                mode = modes[i]
                
                # Random origin in Tamsui (uniform in circle)
                r = radius * (random.random()**0.5)
                angle = random.random() * 2 * 3.14159
                orig_x = center_x + r * random.uniform(-1, 1)
                orig_y = center_y + r * random.uniform(-1, 1)
                
                # Random dest in Safe Zone
                dr = dest_radius * (random.random()**0.5)
                d_x = dest_x + dr * random.uniform(-1, 1)
                d_y = dest_y + dr * random.uniform(-1, 1)
                
                f.write(f'  <person id="{agent_id}">\n')
                f.write('    <plan selected="yes">\n')
                f.write(f'      <activity type="home" x="{orig_x:.2f}" y="{orig_y:.2f}" end_time="03:00:00" />\n')
                f.write(f'      <leg mode="{mode}" />\n')
                f.write(f'      <activity type="evacuation" x="{d_x:.2f}" y="{d_y:.2f}" />\n')
                f.write('    </plan>\n')
                f.write('  </person>\n')
            
            f.write('</population>\n')
        
        print(f"Done! Generated {num_agents} agents.")
        print(f"Mode split: Car={num_car} ({num_car/num_agents:.1%}), PT={num_pt} ({num_pt/num_agents:.1%})")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    out_path = "/Users/ro9air/matsim-example-project/5000_disatar/05_combined_evac/input/population_280k.xml.gz"
    # Ensure directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    generate_population(output_file=out_path)
