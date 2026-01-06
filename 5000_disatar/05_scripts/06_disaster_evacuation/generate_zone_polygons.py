#!/usr/bin/env python3
"""
Generate Buffered Polygons for Tsunami Zones.
Creates smooth zones by buffering and dissolving road links.
Distinguishes "Direct Inundation" (0-1km) from "Traffic Reception" (1-3km).
"""

import geopandas as gpd
import argparse
from shapely.ops import unary_union

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input moderate_closure.geojson')
    parser.add_argument('--output', required=True, help='Output zones geojson')
    parser.add_argument('--buffer', type=float, default=100.0, help='Buffer radius in meters')
    args = parser.parse_args()
    
    print(f"Reading {args.input}...")
    gdf = gpd.read_file(args.input)
    
    # Reproject to EPSG:3826 for metric buffering
    print("Reprojecting to EPSG:3826...")
    gdf_metric = gdf.to_crs("EPSG:3826")
    
    # Define groups
    # Stage 1-3: Direct Inundation
    # Stage 4-5: Traffic Reception
    
    direct_stages = ['stage_1', 'stage_2', 'stage_3']
    reception_stages = ['stage_4', 'stage_5']
    
    zones = []
    
    # 1. Direct Inundation Zone
    print("Processing Direct Inundation Zone (0-1km)...")
    direct_gdf = gdf_metric[gdf_metric['stage'].isin(direct_stages)]
    if not direct_gdf.empty:
        # Buffer
        buffered = direct_gdf.geometry.buffer(args.buffer)
        # Dissolve
        merged = unary_union(buffered)
        zones.append({
            'geometry': merged,
            'zone_type': 'direct',
            'label': '直接溢淹帶 (0-1km)',
            'color': '#ff4444', # Red
            'opacity': 0.5
        })
        
    # 2. Traffic Reception Zone
    print("Processing Traffic Reception Zone (1-3km)...")
    reception_gdf = gdf_metric[gdf_metric['stage'].isin(reception_stages)]
    if not reception_gdf.empty:
        # Buffer
        buffered = reception_gdf.geometry.buffer(args.buffer)
        # Dissolve
        merged = unary_union(buffered)
        
        # Optional: Subtract direct zone from reception zone if they overlap unnecessarily?
        # Usually reception is further out. But buffering might cause overlap.
        # Let's keep them simple for now. 
        # Actually proper visual implies removing the inner hole if reception surrounds direct.
        # But here they are likely distinct bands.
        
        # If we want distinct bands, we can subtract the Direct zone from Reception zone
        if not direct_gdf.empty:
            direct_poly = zones[0]['geometry']
            merged = merged.difference(direct_poly)
            
        zones.append({
            'geometry': merged,
            'zone_type': 'reception',
            'label': '交通承接帶 (1-3km)',
            'color': '#44aa44', # Green
            'opacity': 0.5
        })
    
    # Create GeoDataFrame
    result_gdf = gpd.GeoDataFrame(zones, crs="EPSG:3826")
    
    # Simplify to reduce file size and make it look smoother
    print("Simplifying geometries...")
    result_gdf['geometry'] = result_gdf.geometry.simplify(tolerance=10.0)
    
    # Reproject back to WGS84
    final_gdf = result_gdf.to_crs("EPSG:4326")
    
    print(f"Saving to {args.output}...")
    final_gdf.to_file(args.output, driver='GeoJSON')
    print("Done.")

if __name__ == "__main__":
    main()
