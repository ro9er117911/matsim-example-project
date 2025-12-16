#!/usr/bin/env python3
"""
Generate Hexagonal Grid for Tsunami Zones.
Classifies areas into "Direct Inundation" (0-1km) and "Traffic Reception" (1-3km).
"""

import geopandas as gpd
import numpy as np
import argparse
from shapely.geometry import Polygon, box
from shapely import affinity

def create_hex_grid(bounds, radius):
    """
    Create a hexagonal grid covering the bounds.
    radius: distance from center to vertex (approx equal to side length).
    """
    xmin, ymin, xmax, ymax = bounds
    
    # height of a hex (flat topped) = 2 * radius
    # width of a hex = sqrt(3) * radius
    # But we usually use point-to-point layout. 
    # Let's use standard flat-top hexes.
    # Height = 2 * r * sin(60) = sqrt(3) * r (pointy top) ?
    # Let's assume radius is circumradius.
    
    # Horizontal spacing (width) = 3/2 * radius
    # Vertical spacing (height) = sqrt(3) * radius
    
    # Use approximate conversion for lat/lon degrees if needed, but better to project first.
    # However, source geojson might be WGS84. We should project to EPSG:3826 for metric sizing.
    
    w = 2 * radius # width (point to point) ? No, let's just make regular polygons.
    
    # Standard pointy-topped hexagon height = 2*size, width=sqrt(3)*size
    # Vert spacing = 1.5 * size? No.
    
    # Simplified approach: Generates offsets
    dx = 1.5 * radius
    dy = np.sqrt(3) * radius
    
    # Calculate grid dimensions
    cols = int(np.ceil((xmax - xmin) / dx)) + 1
    rows = int(np.ceil((ymax - ymin) / dy)) + 1
    
    polygons = []
    for i in range(cols):
        for j in range(rows):
            x_offset = i * dx
            y_offset = j * dy
            if i % 2 == 1:
                y_offset += dy / 2
                
            cx = xmin + x_offset
            cy = ymin + y_offset
            
            # Create hexagon points
            # Pointy topped
            angles = np.linspace(0, 2*np.pi, 7)[:-1] + np.pi/6
            points = []
            for angle in angles:
                px = cx + radius * np.cos(angle)
                py = cy + radius * np.sin(angle)
                points.append((px, py))
            
            polygons.append(Polygon(points))
            
    return polygons

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input moderate_closure.geojson')
    parser.add_argument('--output', required=True, help='Output hex grid geojson')
    parser.add_argument('--radius', type=float, default=250.0, help='Hexagon radius in meters')
    args = parser.parse_args()
    
    print(f"Reading {args.input}...")
    gdf = gpd.read_file(args.input)
    
    # Reproject to EPSG:3826 for metric calculations
    print("Reprojecting to EPSG:3826...")
    gdf_metric = gdf.to_crs("EPSG:3826")
    
    # Generate grid
    bounds = gdf_metric.total_bounds
    # Add some buffer
    buffer = 500
    grid_bounds = (bounds[0]-buffer, bounds[1]-buffer, bounds[2]+buffer, bounds[3]+buffer)
    
    print(f"Generating hex grid (radius={args.radius}m)...")
    hex_polys = create_hex_grid(grid_bounds, args.radius)
    hex_gdf = gpd.GeoDataFrame({'geometry': hex_polys}, crs="EPSG:3826")
    
    print(f"Generated {len(hex_gdf)} candidates. Performing spatial join...")
    
    # Spatial Join
    joined = gpd.sjoin(hex_gdf, gdf_metric, how="inner", predicate="intersects")
    
    # Classify
    # Direct Inundation: 0-1km (Stages 1, 2, 3)
    # Traffic Reception: 1-3km (Stages 4, 5)
    
    # Group by hex index
    results = []
    groups = joined.groupby(joined.index)
    
    direct_stages = ['stage_1', 'stage_2', 'stage_3']
    reception_stages = ['stage_4', 'stage_5']
    
    count = 0
    for idx, group in groups:
        count += 1
        stages = group['stage'].unique()
        
        is_direct = any(s in direct_stages for s in stages)
        is_reception = any(s in reception_stages for s in stages)
        
        # Priority: Direct Inundation > Traffic Reception
        # Or better: If it contains mostly direct, it is direct. 
        # But usually safety critical -> if it touches direct, prioritize direct.
        
        zone_type = "none"
        color = "#cccccc"
        label = ""
        opacity = 0.5
        
        if is_direct:
            zone_type = "direct_inundation"
            color = "#ff4444" # Reddish
            label = "直接溢淹帶 (0-1km)"
            opacity = 0.6
        elif is_reception:
            zone_type = "traffic_reception"
            color = "#44aa44" # Greenish
            label = "交通承接帶 (1-3km)"
            opacity = 0.4
            
        if zone_type != "none":
            results.append({
                'geometry': hex_gdf.loc[idx].geometry,
                'zone_type': zone_type,
                'label': label,
                'color': color,
                'opacity': opacity
            })
            
    result_gdf = gpd.GeoDataFrame(results, crs="EPSG:3826")
    
    # Reproject back to WGS84 for GeoJSON
    final_gdf = result_gdf.to_crs("EPSG:4326")
    
    print(f"Saving {len(final_gdf)} hex zones to {args.output}...")
    final_gdf.to_file(args.output, driver='GeoJSON')
    print("Done.")

if __name__ == "__main__":
    main()
