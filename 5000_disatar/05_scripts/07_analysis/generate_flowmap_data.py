#!/usr/bin/env python3
"""
Generate synthetic TAZ hexagons and OD flows for SimWrapper Flowmap.
This script replaces the missing 'taz1454.geojson' and 'trip-od-flows.csv'.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
import argparse
import os
import gzip

def create_hex_grid(bounds, radius, crs="EPSG:3826"):
    """
    Create a hexagonal grid covering the bounds.
    radius: distance from center to vertex.
    """
    xmin, ymin, xmax, ymax = bounds
    
    # Horizontal spacing (width) = 1.5 * radius
    # Vertical spacing (height) = sqrt(3) * radius
    dx = 1.5 * radius
    dy = np.sqrt(3) * radius
    
    cols = int(np.ceil((xmax - xmin) / dx)) + 1
    rows = int(np.ceil((ymax - ymin) / dy)) + 1
    
    polygons = []
    ids = []
    
    for i in range(cols):
        for j in range(rows):
            x_offset = i * dx
            y_offset = j * dy
            if i % 2 == 1:
                y_offset += dy / 2
                
            cx = xmin + x_offset
            cy = ymin + y_offset
            
            # Pointy topped hexagon
            angles = np.linspace(0, 2*np.pi, 7)[:-1] + np.pi/6
            points = [(cx + radius * np.cos(a), cy + radius * np.sin(a)) for a in angles]
            
            polygons.append(Polygon(points))
            # Use 1-based indexing for IDs
            ids.append(f"TAZ_{len(ids) + 1}")
            
    gdf = gpd.GeoDataFrame({
        'TAZ1454': ids,
        'TAZ': ids, # Label
        'geometry': polygons
    }, crs=crs)
    
    return gdf

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trips', required=True, help='Path to output_trips.csv.gz')
    parser.add_argument('--output_dir', required=True, help='Directory to save output files')
    parser.add_argument('--radius', type=float, default=720.0, help='Hexagon radius in meters (default 720 for ~1450 zones)')
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Reading trips from {args.trips}...")
    # MATSim trips CSV uses semicolon separator
    df = pd.read_csv(args.trips, sep=';')
    
    # Use EPSG:3826 as assumed for the network
    crs_metric = "EPSG:3826"
    
    # Calculate bounds from trip coordinates
    xmin = min(df['start_x'].min(), df['end_x'].min())
    xmax = max(df['start_x'].max(), df['end_x'].max())
    ymin = min(df['start_y'].min(), df['end_y'].min())
    ymax = max(df['start_y'].max(), df['end_y'].max())
    
    # Add a small buffer to bounds
    buffer = 1000
    bounds = (xmin - buffer, ymin - buffer, xmax + buffer, ymax + buffer)
    
    print(f"Generating hex grid with radius {args.radius}m...")
    taz_gdf = create_hex_grid(bounds, args.radius, crs=crs_metric)
    print(f"Generated {len(taz_gdf)} zones.")
    
    # Save TAZ GeoJSON in WGS84 for SimWrapper
    taz_wgs84 = taz_gdf.to_crs("EPSG:4326")
    taz_path = os.path.join(args.output_dir, "taz1454.geojson")
    taz_wgs84.to_file(taz_path, driver='GeoJSON')
    print(f"Saved {taz_path}")
    
    # Map trips to zones
    print("Mapping trips to zones...")
    
    # Ensure unique index for sjoin
    df = df.reset_index(drop=True)
    
    # Start points
    start_points = gpd.GeoDataFrame(df[['person', 'trip_number']], 
                                   geometry=gpd.points_from_xy(df.start_x, df.start_y), 
                                   crs=crs_metric)
    start_joined = gpd.sjoin(start_points, taz_gdf[['TAZ1454', 'geometry']], how="left", predicate="within")
    # Handle points on boundaries by keeping only the first match
    start_joined = start_joined.drop_duplicates(subset=['person', 'trip_number'], keep='first')
    
    # End points
    end_points = gpd.GeoDataFrame(df[['person', 'trip_number']], 
                                 geometry=gpd.points_from_xy(df.end_x, df.end_y), 
                                 crs=crs_metric)
    end_joined = gpd.sjoin(end_points, taz_gdf[['TAZ1454', 'geometry']], how="left", predicate="within")
    # Handle points on boundaries by keeping only the first match
    end_joined = end_joined.drop_duplicates(subset=['person', 'trip_number'], keep='first')
    
    # Combine - use the index to align (they should be identical now)
    # However, to be extra safe, let's join them based on person and trip_number
    combined = pd.merge(
        start_joined[['person', 'trip_number', 'TAZ1454']].rename(columns={'TAZ1454': 'origin'}),
        end_joined[['person', 'trip_number', 'TAZ1454']].rename(columns={'TAZ1454': 'destination'}),
        on=['person', 'trip_number']
    )
    
    flow_df = combined[['origin', 'destination']]
    
    # Group and count flows
    # Drop rows where mapping failed (outside hex grid - shouldn't happen with our buffer)
    flow_df = flow_df.dropna()
    
    flows = flow_df.groupby(['origin', 'destination']).size().reset_index(name='trips')
    
    # Filter out flows with 0 trips or self-loops if desired, but let's keep all for now
    # Actually, flowmaps usually look better without self-loops
    flows = flows[flows['origin'] != flows['destination']]
    
    # Save OD flow CSV
    od_path = os.path.join(args.output_dir, "trip-od-flows.csv")
    flows.to_csv(od_path, index=False)
    print(f"Saved {od_path} with {len(flows)} flow records.")

if __name__ == "__main__":
    main()
