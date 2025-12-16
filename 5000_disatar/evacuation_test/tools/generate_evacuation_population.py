#!/usr/bin/env python3
"""
Generate evacuation population for Tamsui-to-Wanlong simulation.
Creates agents in hazard zone with destination at Wanlong MRT.
"""
import gzip
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import math

# Configuration
HAZARD_CENTER = (25.18, 121.44)  # Tamsui (lat, lon)
HAZARD_RADIUS_DEG = 0.02  # ~2km radius
SAFE_DESTINATION = (25.001602, 121.539202)  # Wanlong MRT (lat, lon)
NUM_AGENTS = 500
DEPARTURE_TIME_START = 0  # seconds (00:00:00)
DEPARTURE_TIME_END = 3600  # seconds (01:00:00)
OUTPUT_FILE = "/Users/ro9air/matsim-example-project/5000_disatar/evacuation_test/input/evacuation_population.xml"

# TWD97 EPSG:3826 conversion (approximate)
def wgs84_to_twd97(lat, lon):
    """Approximate WGS84 to TWD97 conversion for Taiwan."""
    # Using simplified transformation
    # Reference: EPSG:3826 is TWD97 / TM2 zone 121
    x = (lon - 121.0) * 111320 * math.cos(math.radians(lat)) + 250000
    y = (lat - 0) * 110540 + 0
    return x, y

def generate_random_point_in_circle(center_lat, center_lon, radius_deg):
    """Generate random point within circle."""
    angle = random.uniform(0, 2 * math.pi)
    r = radius_deg * math.sqrt(random.random())
    lat = center_lat + r * math.sin(angle)
    lon = center_lon + r * math.cos(angle)
    return lat, lon

def create_population():
    """Create MATSim population XML."""
    root = ET.Element("population")
    
    # Convert safe destination to TWD97
    safe_x, safe_y = wgs84_to_twd97(*SAFE_DESTINATION)
    
    for i in range(NUM_AGENTS):
        # Random origin in hazard zone
        origin_lat, origin_lon = generate_random_point_in_circle(
            HAZARD_CENTER[0], HAZARD_CENTER[1], HAZARD_RADIUS_DEG
        )
        origin_x, origin_y = wgs84_to_twd97(origin_lat, origin_lon)
        
        # Random departure time
        departure_time = random.uniform(DEPARTURE_TIME_START, DEPARTURE_TIME_END)
        
        # Create person
        person = ET.SubElement(root, "person", id=f"evac_{i}")
        plan = ET.SubElement(person, "plan", selected="yes")
        
        # Pre-evacuation activity (origin in hazard zone)
        act1 = ET.SubElement(plan, "activity", 
                            type="pre-evac",
                            x=f"{origin_x:.2f}",
                            y=f"{origin_y:.2f}",
                            end_time=f"{int(departure_time // 3600):02d}:{int((departure_time % 3600) // 60):02d}:{int(departure_time % 60):02d}")
        
        # Leg (car mode)
        leg = ET.SubElement(plan, "leg", mode="car")
        
        # Post-evacuation activity (safe destination - Wanlong)
        act2 = ET.SubElement(plan, "activity",
                            type="post-evac",
                            x=f"{safe_x:.2f}",
                            y=f"{safe_y:.2f}")
    
    return root

def main():
    print(f"Generating evacuation population:")
    print(f"  Origin: Tamsui hazard zone ({HAZARD_CENTER[0]}, {HAZARD_CENTER[1]})")
    print(f"  Destination: Wanlong MRT ({SAFE_DESTINATION[0]}, {SAFE_DESTINATION[1]})")
    print(f"  Agents: {NUM_AGENTS}")
    
    root = create_population()
    
    # Pretty print and save
    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
    # Remove extra blank lines
    xml_str = '\n'.join([line for line in xml_str.split('\n') if line.strip()])
    
    # Add proper header
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n' + xml_str.replace('<?xml version="1.0" ?>', '')
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(xml_str)
    
    print(f"  Output: {OUTPUT_FILE}")
    print("Done!")

if __name__ == "__main__":
    main()
