#!/usr/bin/env python3
"""
Convert MATSim population.xml to ESRI Shapefile for evacuation-gui.

This script extracts home locations from a MATSim population file
and creates a shapefile suitable for use with the evacuation-gui's
population selector module.

Usage:
    python population_to_shapefile.py input.xml output_dir [--crs EPSG:3826]
"""

import xml.etree.ElementTree as ET
import os
import sys
import gzip
from collections import defaultdict

try:
    import shapefile
except ImportError:
    print("正在安裝 pyshp...")
    os.system(f"{sys.executable} -m pip install pyshp")
    import shapefile

def parse_population_xml(input_file):
    """Parse MATSim population XML and extract home locations."""
    
    # Handle gzipped files
    if input_file.endswith('.gz'):
        with gzip.open(input_file, 'rt', encoding='utf-8') as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(input_file)
    
    root = tree.getroot()
    agents = []
    
    for person in root.findall('.//person'):
        person_id = person.get('id')
        
        # Find home activity in selected plan
        for plan in person.findall('plan[@selected="yes"]'):
            for activity in plan.findall('activity'):
                if activity.get('type') == 'home':
                    x = float(activity.get('x'))
                    y = float(activity.get('y'))
                    agents.append({
                        'id': person_id,
                        'x': x,
                        'y': y
                    })
                    break
            break
    
    return agents

def aggregate_to_grid(agents, cell_size=500):
    """Aggregate agents into grid cells for population density."""
    
    grid = defaultdict(int)
    
    for agent in agents:
        # Round to grid cell
        grid_x = int(agent['x'] // cell_size) * cell_size + cell_size // 2
        grid_y = int(agent['y'] // cell_size) * cell_size + cell_size // 2
        grid[(grid_x, grid_y)] += 1
    
    return grid

def create_point_shapefile(agents, output_dir, filename="population_points"):
    """Create point shapefile with one point per agent."""
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    w = shapefile.Writer(output_path)
    w.field('ID', 'C', 40)
    w.field('X', 'N', decimal=2)
    w.field('Y', 'N', decimal=2)
    
    for agent in agents:
        w.point(agent['x'], agent['y'])
        w.record(agent['id'], agent['x'], agent['y'])
    
    w.close()
    
    # Create .prj file for coordinate system (EPSG:3826)
    prj_content = '''PROJCS["TWD97 / TM2 zone 121",GEOGCS["TWD97",DATUM["Taiwan_Datum_1997",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","1026"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","3824"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",121],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",250000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3826"]]'''
    
    with open(output_path + '.prj', 'w') as f:
        f.write(prj_content)
    
    print(f"✓ 已建立點位 shapefile: {output_path}.shp ({len(agents)} 個點)")
    return output_path

def create_polygon_shapefile(grid, output_dir, cell_size=500, filename="population_areas"):
    """Create polygon shapefile with population counts per grid cell."""
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    w = shapefile.Writer(output_path)
    w.field('POPULATION', 'N', 10)
    w.field('CENTER_X', 'N', decimal=2)
    w.field('CENTER_Y', 'N', decimal=2)
    
    half = cell_size // 2
    
    for (cx, cy), pop in grid.items():
        # Create square polygon
        w.poly([[
            [cx - half, cy - half],
            [cx + half, cy - half],
            [cx + half, cy + half],
            [cx - half, cy + half],
            [cx - half, cy - half]  # Close polygon
        ]])
        w.record(pop, cx, cy)
    
    w.close()
    
    # Create .prj file
    prj_content = '''PROJCS["TWD97 / TM2 zone 121",GEOGCS["TWD97",DATUM["Taiwan_Datum_1997",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","1026"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","3824"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",121],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",250000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3826"]]'''
    
    with open(output_path + '.prj', 'w') as f:
        f.write(prj_content)
    
    print(f"✓ 已建立區域 shapefile: {output_path}.shp ({len(grid)} 個區域)")
    return output_path

def main():
    if len(sys.argv) < 3:
        print("用法: python population_to_shapefile.py <input.xml> <output_dir>")
        print("範例: python population_to_shapefile.py population_5000.xml ./output_shp")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    cell_size = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    
    print(f"讀取人口檔案: {input_file}")
    agents = parse_population_xml(input_file)
    print(f"找到 {len(agents)} 個代理人")
    
    # Calculate bounds
    xs = [a['x'] for a in agents]
    ys = [a['y'] for a in agents]
    print(f"座標範圍:")
    print(f"  X: {min(xs):.2f} - {max(xs):.2f}")
    print(f"  Y: {min(ys):.2f} - {max(ys):.2f}")
    
    # Create point shapefile
    create_point_shapefile(agents, output_dir, "population_points")
    
    # Create aggregated polygon shapefile
    grid = aggregate_to_grid(agents, cell_size)
    create_polygon_shapefile(grid, output_dir, cell_size, "population_areas")
    
    print(f"\n完成！Shapefile 已儲存至: {output_dir}")
    print("\n檔案清單:")
    for f in os.listdir(output_dir):
        print(f"  - {f}")

if __name__ == "__main__":
    main()
