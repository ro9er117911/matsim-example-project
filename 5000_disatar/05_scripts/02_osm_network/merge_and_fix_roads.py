#!/usr/bin/env python3
"""
Merge Taipei & New Taipei Roads and Fix Topology with NeatNet.
Inputs:
- old_TPE: A_ROAD.shp (Taipei)
- new_TPE: F_ROAD.shp (New Taipei)
Output:
- merged_fixed_roads.gpkg
"""

import geopandas as gpd
import pandas as pd
import neatnet
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Config
BASE_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data")
TAIPEI_SHP = BASE_DIR / "taipei_shp_map/A_ROAD.shp"
NEW_TPE_SHP = BASE_DIR / "newTPE_shp_map/F_ROAD.shp"

OUTPUT_DIR = BASE_DIR / "GTFS_pt_mapping_v6/merged_network_v6"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "merged_fixed_roads.gpkg"

TARGET_CRS = "EPSG:3826"

def main():
    print("Reading Taipei roads (A_ROAD)...")
    try:
        a_road = gpd.read_file(TAIPEI_SHP, encoding='utf-8')
    except:
        print("UTF-8 failed, trying Big5...")
        a_road = gpd.read_file(TAIPEI_SHP, encoding='big5')

    if a_road.crs is None: 
        print("Warning: A_ROAD CRS missing, assuming EPSG:3826")
        a_road.set_crs(TARGET_CRS, inplace=True)
    a_road = a_road.to_crs(TARGET_CRS)
    
    print("Reading New Taipei roads (F_ROAD)...")
    try:
        f_road = gpd.read_file(NEW_TPE_SHP, encoding='utf-8')
    except:
        print("UTF-8 failed, trying Big5...")
        f_road = gpd.read_file(NEW_TPE_SHP, encoding='big5')

    if f_road.crs is None:
        print("Warning: F_ROAD CRS missing, assuming EPSG:3826")
        f_road.set_crs(TARGET_CRS, inplace=True)
    f_road = f_road.to_crs(TARGET_CRS)
    
    # Check compatibility (optional, but pandas concat usually handles it)
    print(f"Features: Taipei={len(a_road)}, New Taipei={len(f_road)}")
    
    print("Merging datasets...")
    # Common columns only or all? Let's use pd.concat
    merged = pd.concat([a_road, f_road], ignore_index=True)
    merged_gdf = gpd.GeoDataFrame(merged, geometry='geometry', crs=TARGET_CRS)
    print(f"Merged features: {len(merged_gdf)}")
    
    print("Running neatnet.fix_topology()...")
    # This might take a while for ~100k features
    try:
        fixed_gdf = neatnet.fix_topology(merged_gdf)
    except Exception as e:
        print(f"NeatNet failed: {e}")
        # Fallback: save merged only
        fixed_gdf = merged_gdf

    print(f"Saving to {OUTPUT_FILE}...")
    fixed_gdf.to_file(OUTPUT_FILE, layer="roads", driver="GPKG")
    print("Done.")

if __name__ == "__main__":
    main()
