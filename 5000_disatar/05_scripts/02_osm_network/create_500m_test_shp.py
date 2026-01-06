#!/usr/bin/env python3
"""
Create evacuation area and population shapefiles for 500m Tamsui test.
These are required by the evacuation-gui to proceed.
"""

import os
import sys

try:
    import shapefile
except ImportError:
    os.system(f"{sys.executable} -m pip install pyshp")
    import shapefile

# EPSG:3826 projection file
PRJ_CONTENT = '''PROJCS["TWD97 / TM2 zone 121",GEOGCS["TWD97",DATUM["Taiwan_Datum_1997",SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",121],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",250000],PARAMETER["false_northing",0],UNIT["metre",1]]'''

# 500m Tamsui test area  
# OSM bbox: 121.442,25.166,121.448,25.172
# Approximate EPSG:3826 coordinates:
# Center: lon 121.445, lat 25.169 → approx X=270500, Y=2786000

CENTER_X = 270500
CENTER_Y = 2786000
HALF_SIZE = 250  # 500m / 2

def create_evacuation_area_shapefile(output_dir):
    """Create evacuation area polygon shapefile."""
    
    output_path = os.path.join(output_dir, "evacuation_area_500m")
    
    w = shapefile.Writer(output_path)
    w.field('id', 'N', 10)
    w.field('name', 'C', 50)
    
    # Create rectangle polygon for evacuation area
    w.poly([[
        [CENTER_X - HALF_SIZE, CENTER_Y - HALF_SIZE],
        [CENTER_X + HALF_SIZE, CENTER_Y - HALF_SIZE],
        [CENTER_X + HALF_SIZE, CENTER_Y + HALF_SIZE],
        [CENTER_X - HALF_SIZE, CENTER_Y + HALF_SIZE],
        [CENTER_X - HALF_SIZE, CENTER_Y - HALF_SIZE]
    ]])
    
    w.record(1, "Tamsui 500m Test Area")
    w.close()
    
    with open(output_path + '.prj', 'w') as f:
        f.write(PRJ_CONTENT)
    
    print(f"✓ 已建立疏散區域: {output_path}.shp")
    return output_path + ".shp"


def create_population_shapefile(output_dir):
    """Create population shapefile with required attributes."""
    
    output_path = os.path.join(output_dir, "population_500m")
    
    w = shapefile.Writer(output_path)
    # These are the attributes required by evacuation-gui
    w.field('id', 'N', 10)
    w.field('pop', 'N', 10)  # population count - required!
    w.field('name', 'C', 50)
    
    # Create a smaller polygon for population area
    pop_half = 200  # slightly smaller than evac area
    
    w.poly([[
        [CENTER_X - pop_half, CENTER_Y - pop_half],
        [CENTER_X + pop_half, CENTER_Y - pop_half],
        [CENTER_X + pop_half, CENTER_Y + pop_half],
        [CENTER_X - pop_half, CENTER_Y + pop_half],
        [CENTER_X - pop_half, CENTER_Y - pop_half]
    ]])
    
    # Set population = 500 people in this area
    w.record(1, 500, "Population Area")
    w.close()
    
    with open(output_path + '.prj', 'w') as f:
        f.write(PRJ_CONTENT)
    
    print(f"✓ 已建立人口區域: {output_path}.shp (500人)")
    return output_path + ".shp"


def main():
    output_dir = "5000_disatar/03_phase2_production/test_500m_shp"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 50)
    print("建立 500m 測試區 Shapefile")
    print("=" * 50)
    
    print(f"\n中心點: ({CENTER_X}, {CENTER_Y})")
    print(f"區域大小: 500m x 500m")
    
    evac_shp = create_evacuation_area_shapefile(output_dir)
    pop_shp = create_population_shapefile(output_dir)
    
    print(f"\n✓ 完成！")
    print(f"\n疏散區域: {evac_shp}")
    print(f"人口區域: {pop_shp}")


if __name__ == "__main__":
    main()
