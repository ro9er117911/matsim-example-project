#!/usr/bin/env python3
"""Quick inspection of Chiayi shapefile structure"""
import geopandas as gpd
import sys

BASE = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map"

# Q_ROAD
print("Loading Q_ROAD...")
gdf = gpd.read_file(f"{BASE}/Q_ROAD.shp")
print(f"Q_ROAD: {len(gdf)} features, CRS={gdf.crs}")
print(f"Columns: {list(gdf.columns)}")
print("\nSample 2 rows (no geometry):")
print(gdf.drop(columns=['geometry']).head(2))

# Q_RDNODE  
print("\n\nLoading Q_RDNODE...")
gdf2 = gpd.read_file(f"{BASE}/Q_RDNODE.shp")
print(f"Q_RDNODE: {len(gdf2)} features, CRS={gdf2.crs}")
print(f"Columns: {list(gdf2.columns)}")
print("\nSample 2 rows (no geometry):")
print(gdf2.drop(columns=['geometry']).head(2))
