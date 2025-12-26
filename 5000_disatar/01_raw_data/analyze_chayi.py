#!/usr/bin/env python3
"""
分析嘉義縣國土測繪圖資 shapefile 資料結構
Analyze Chiayi County government GIS shapefile data structure
"""

import geopandas as gpd
import warnings
warnings.filterwarnings("ignore")

BASE_PATH = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map"

def analyze_layer(filename, description):
    """Analyze a single shapefile layer"""
    print(f"\n{'='*60}")
    print(f"=== {filename} ({description}) ===")
    print('='*60)
    
    try:
        gdf = gpd.read_file(f"{BASE_PATH}/{filename}")
        print(f"Features: {len(gdf)}")
        print(f"CRS: {gdf.crs}")
        print(f"Geometry type: {gdf.geometry.geom_type.unique().tolist()}")
        print(f"Bounds: {gdf.total_bounds}")
        print()
        print("Columns:")
        for col in gdf.columns:
            if col != 'geometry':
                print(f"  - {col}: {gdf[col].dtype}")
        print()
        print("Sample data (first 2 records):")
        print(gdf.drop(columns=['geometry']).head(2).to_string(max_colwidth=30))
        
        # Show unique values for key columns if they exist
        key_cols = ['ROADCLASS', 'ONEWAY', 'ROADTYPE', 'RDCODE', 'NODETYPE', 'RDNAME1', 'ROADNAME']
        for col in key_cols:
            if col in gdf.columns:
                unique_vals = gdf[col].dropna().unique()[:10]
                print(f"\n{col} unique values (first 10): {list(unique_vals)}")
                
    except Exception as e:
        print(f"Error reading {filename}: {e}")

# Analyze key layers
layers = [
    ("Q_ROAD.shp", "道路網路 Road Network"),
    ("Q_RDNODE.shp", "道路節點 Road Nodes"),
    ("Q_BRIDGE.shp", "橋梁 Bridges"),
    ("Q_TUNNEL.shp", "隧道 Tunnels"),
    ("Q_RAIL.shp", "鐵路 Railway"),
    ("Q_HSRAIL.shp", "高鐵 High-Speed Rail"),
]

print("嘉義縣國土測繪圖資分析報告")
print("Chiayi County GIS Data Analysis Report")
print("="*60)

for filename, desc in layers:
    analyze_layer(filename, desc)
