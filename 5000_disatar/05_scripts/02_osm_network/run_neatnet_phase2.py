#!/usr/bin/env python3
"""
NeatNet Topology Fix Script for Phase 2 Test Routes.
1. Calc bbox from GTFS stops/shapes.
2. Clip A_ROAD.shp.
3. Apply neatnet.fix_topology.
"""

import geopandas as gpd
import pandas as pd
import neatnet
from shapely.geometry import box
from pathlib import Path

# Config
GTFS_DIR = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping_v6/test_phase2_neatnet")
ROAD_SHP = Path("/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/taipei_shp_map/A_ROAD.shp")
OUTPUT_GPKG = GTFS_DIR / "roads_neatnet_fixed.gpkg"
TARGET_CRS = "EPSG:3826"  # TWD97 / TM2 zone 121

def get_aoi_from_gtfs():
    print("Calculating AOI from GTFS stops...")
    stops = pd.read_csv(GTFS_DIR / "stops.txt")
    
    # Create GeoDataFrame from stops (assuming LatLon inputs in stops.txt)
    gdf_stops = gpd.GeoDataFrame(
        stops, 
        geometry=gpd.points_from_xy(stops.stop_lon, stops.stop_lat),
        crs="EPSG:4326"
    )
    
    # Convert to Target CRS for buffering
    gdf_stops_proj = gdf_stops.to_crs(TARGET_CRS)
    
    # Get bounds
    minx, miny, maxx, maxy = gdf_stops_proj.total_bounds
    bbox = box(minx, miny, maxx, maxy)
    
    # Create AOI with buffer (1000m)
    aoi_geom = bbox.buffer(1000)
    aoi = gpd.GeoDataFrame(geometry=[aoi_geom], crs=TARGET_CRS)
    
    print(f"AOI bounds: {aoi.total_bounds}")
    return aoi

def run_neatnet(aoi):
    print(f"Reading road network: {ROAD_SHP}")
    # Read roads
    # Note: A_ROAD might be in TWD97 already or LatLon. We ensure CRS match.
    # Reading bbox subset for speed if possible, but simplest is read & clip.
    # Check if we can read mostly by bbox? geopandas read_file supports bbox since recent versions.
    
    # First get bbox in original CRS if needed. 
    # Assuming A_ROAD is EPSG:3826 (usually is for gov data). 
    # But often .prj missing or custom.
    # Let's read full file (might be slow?) or use bbox.
    
    # Let's try reading using bbox of AOI (converted to likely input CRS if known)
    # safe bet: read filtered.
    
    try:
        roads = gpd.read_file(ROAD_SHP, bbox=aoi.to_crs("EPSG:3824")) # Assuming 3826/3824/3825... let's just use 3826 default
    except:
        print("bbox read failed, reading full file...")
        roads = gpd.read_file(ROAD_SHP)

    # Ensure CRS
    if roads.crs is None:
        print("Warning: Input CRS missing, assuming EPSG:3826")
        roads.set_crs(TARGET_CRS, allow_override=True, inplace=True)
    
    roads = roads.to_crs(TARGET_CRS)
    
    print(f"Roads loaded: {len(roads)} features")
    
    # Clip
    print("Clipping roads to AOI...")
    roads_clip = gpd.clip(roads, aoi)
    print(f"Roads after clip: {len(roads_clip)} features")
    
    # NeatNet Fix
    print("Running neatnet.fix_topology()...")
    roads_fixed = neatnet.fix_topology(roads_clip)
    
    print("Saving to GPKG...")
    roads_fixed.to_file(OUTPUT_GPKG, layer="roads", driver="GPKG")
    print(f"Saved: {OUTPUT_GPKG}")

def main():
    aoi = get_aoi_from_gtfs()
    run_neatnet(aoi)

if __name__ == "__main__":
    main()
