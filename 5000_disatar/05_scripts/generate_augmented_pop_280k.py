#!/usr/bin/env python3
"""
Generate a 280,000-agent MATSim population by augmenting a 5,000-agent template population.
This script follows the "augmentation logic" (cloning + jittering) to ensure realistic distribution.

Requirements:
- Target size: 280,000 agents
- Mode Split: 63% car / 37% pt
- Base Population: 5000_disatar/05_combined_evac/input/population_5000_staggered.xml
"""

import os
import gzip
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def to_seconds(hms: str) -> int:
    try:
        h, m, s = map(int, hms.split(":"))
        return h * 3600 + m * 60 + s
    except:
        return 0

def to_hms(seconds: int) -> str:
    seconds = int(seconds)
    h = (seconds // 3600) % 24
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_templates(input_file):
    print(f"Loading templates from {input_file}...")
    car_templates = []
    pt_templates = []
    
    # Simple parse as it's small enough (5000 agents)
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    for person in root.findall("person"):
        # Store the plan structure as a dictionary for easy cloning
        plan = person.find("plan")
        leg = plan.find("leg")
        mode = leg.get("mode")
        
        # Extract activities
        activities = []
        for act in plan.findall("activity"):
            activities.append({
                "type": act.get("type"),
                "x": float(act.get("x")),
                "y": float(act.get("y")),
                "end_time": act.get("end_time")
            })
        
        template = {
            "orig_id": person.get("id"),
            "activities": activities,
            "mode": mode
        }
        
        if mode == "car":
            car_templates.append(template)
        else:
            pt_templates.append(template)
            
    print(f"Found {len(car_templates)} car templates and {len(pt_templates)} pt templates.")
    return car_templates, pt_templates

def generate_augmented_population(num_agents=280000, 
                                 car_ratio=0.63, 
                                 input_file="/Users/ro9air/matsim-example-project/5000_disatar/05_combined_evac/input/population_5000_staggered.xml",
                                 output_file="/Users/ro9air/matsim-example-project/5000_disatar/05_combined_evac/input/population_280k.xml.gz",
                                 jitter_sigma=300.0,
                                 dep_window=1200):
    
    car_templates, pt_templates = load_templates(input_file)
    
    num_car = int(num_agents * car_ratio)
    num_pt = num_agents - num_car
    
    print(f"Targeting: {num_car} cars, {num_pt} pt agents (Total: {num_agents})")
    
    # Create modes list and shuffle
    # Actually, we can just iterate and generate
    
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n')
            f.write('<population>\n')
            
            # Generate car agents
            for i in range(num_car):
                if i % 50000 == 0:
                    print(f"Generating car agent {i}...")
                
                tmpl = random.choice(car_templates)
                write_person(f, f"car_{i:06d}", tmpl, jitter_sigma, dep_window)
                
            # Generate pt agents
            for i in range(num_pt):
                if i % 50000 == 0:
                    print(f"Generating pt agent {i}...")
                
                tmpl = random.choice(pt_templates)
                write_person(f, f"pt_{i:06d}", tmpl, jitter_sigma, dep_window)
                
            f.write('</population>\n')
            
        print(f"Successfully generated {num_agents} agents in {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")

def write_person(f, agent_id, tmpl, jitter_sigma, dep_window):
    f.write(f'  <person id="{agent_id}">\n')
    f.write('    <plan selected="yes">\n')
    
    for j, act in enumerate(tmpl["activities"]):
        # Apply jitter
        jx = act["x"] + random.gauss(0, jitter_sigma)
        jy = act["y"] + random.gauss(0, jitter_sigma)
        
        end_time_str = ""
        if act["end_time"]:
            base_sec = to_seconds(act["end_time"])
            jitter_sec = random.uniform(-dep_window/2, dep_window/2)
            end_time_str = f' end_time="{to_hms(base_sec + jitter_sec)}"'
            
        f.write(f'      <activity type="{act["type"]}" x="{jx:.2f}" y="{jy:.2f}"{end_time_str} />\n')
        
        # Write leg if not the last activity
        if j < len(tmpl["activities"]) - 1:
            f.write(f'      <leg mode="{tmpl["mode"]}" />\n')
            
    f.write('    </plan>\n')
    f.write('  </person>\n')

if __name__ == "__main__":
    generate_augmented_population()
