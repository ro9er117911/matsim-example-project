#!/usr/bin/env python3
"""
Merge TPE and NWT Bus Shapefiles into unified GPKG.

Input:
- bus_shapefile.shp (809 TPE routes)
- new_bus_shapefile.shp (1091 NWT routes)

Output:
- merged_bus_shapes.gpkg (1900 total)
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

# Config
BASE_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS/BUS_shape_TPE_newTPE")
TPE_SHP = BASE_DIR / "bus_shapefile/bus_shapefile.shp"
NWT_SHP = BASE_DIR / "new_bus_shapefile/new_bus_shapefile.shp"
OUTPUT_DIR = BASE_DIR / "merged"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "merged_bus_shapes.gpkg"

def main():
    print("Loading TPE shapefile...")
    tpe = gpd.read_file(TPE_SHP)
    print(f"  TPE features: {len(tpe)}")
    
    print("Loading NWT shapefile...")
    nwt = gpd.read_file(NWT_SHP)
    print(f"  NWT features: {len(nwt)}")
    
    # Ensure same CRS
    if tpe.crs != nwt.crs:
        print(f"  Converting NWT CRS from {nwt.crs} to {tpe.crs}")
        nwt = nwt.to_crs(tpe.crs)
    
    print("Merging...")
    merged = pd.concat([tpe, nwt], ignore_index=True)
    merged_gdf = gpd.GeoDataFrame(merged, geometry='geometry', crs=tpe.crs)
    print(f"  Merged features: {len(merged_gdf)}")
    
    print(f"Saving to {OUTPUT_FILE}...")
    merged_gdf.to_file(OUTPUT_FILE, driver="GPKG")
    print("Done.")

if __name__ == "__main__":
    main()
