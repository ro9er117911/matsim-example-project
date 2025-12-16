#!/usr/bin/env python3
"""
Create a properly formatted population shapefile for evacuation-gui.

The GUI requires a shapefile with:
- Polygon geometry (evacuation area)
- 'persons' attribute (Long type) - number of people in that area

Usage: python create_population_shapefile.py
"""
import geopandas as gpd
from shapely.geometry import Point, Polygon
import os

# Output directory
output_dir = "/Users/ro9air/matsim-example-project/5000_disatar/03_phase2_production/test_500m_shp"

# Read the evacuation area to get the bounds
evac_area = gpd.read_file(os.path.join(output_dir, "evacuation_area_500m.shp"))
print(f"Evacuation area CRS: {evac_area.crs}")
print(f"Evacuation area bounds: {evac_area.total_bounds}")

# Use the same geometry as evacuation area for population
# Create a simple polygon covering the evacuation area
geom = evac_area.geometry.iloc[0]

# Create population shapefile with 'persons' attribute (required by GUI!)
pop_data = {
    'persons': [500],  # Number of people in this area
    'geometry': [geom]
}

pop_gdf = gpd.GeoDataFrame(pop_data, crs=evac_area.crs)

# Save to shapefile
output_path = os.path.join(output_dir, "population_500m_fixed.shp")
pop_gdf.to_file(output_path)

print(f"Created population shapefile: {output_path}")
print(f"Attributes: {list(pop_gdf.columns)}")
print(f"Number of features: {len(pop_gdf)}")
print(f"Persons: {pop_gdf['persons'].iloc[0]}")
