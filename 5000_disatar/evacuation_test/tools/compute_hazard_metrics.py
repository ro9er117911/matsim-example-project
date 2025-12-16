#!/usr/bin/env python3
"""
Compute Hazard Zone Metrics for Tamsui Tsunami Evacuation

Computes:
- Centroid (lat, lon) in WGS84
- Area (km²)
- Affected population (optional, requires population shapefile)

Outputs:
- hazard_zone.geojson for Simwrapper visualization
- Console metrics summary

Usage:
    python compute_hazard_metrics.py [--hazard-shp PATH] [--population-shp PATH] [--output-dir PATH]
"""

import argparse
import json
from pathlib import Path

try:
    import geopandas as gpd
    from shapely.ops import unary_union
except ImportError:
    print("ERROR: geopandas not installed. Run: pip install geopandas shapely")
    exit(1)


def compute_hazard_metrics(hazard_shp: Path, population_shp: Path = None, output_dir: Path = None):
    """
    Compute centroid, area, and optionally affected population from hazard zone shapefile.
    """
    print(f"Reading hazard zone: {hazard_shp}")
    
    # Read hazard zone
    haz = gpd.read_file(hazard_shp)
    
    # Convert to TWD97 (EPSG:3826) for area calculation
    haz_3826 = haz.to_crs(epsg=3826)
    
    # Dissolve to single geometry (may be MultiPolygon)
    dissolved = haz_3826.dissolve()
    hazard_geom = dissolved.geometry.iloc[0]
    
    # Calculate centroid
    centroid_3826 = hazard_geom.centroid
    
    # Convert centroid to WGS84
    centroid_gdf = gpd.GeoDataFrame(geometry=[centroid_3826], crs=3826)
    centroid_wgs84 = centroid_gdf.to_crs(epsg=4326).geometry.iloc[0]
    
    # Calculate area in km²
    area_km2 = hazard_geom.area / 1_000_000
    
    # Calculate affected population (if population shapefile provided)
    affected_pop = None
    if population_shp and population_shp.exists():
        print(f"Reading population: {population_shp}")
        pop = gpd.read_file(population_shp).to_crs(epsg=3826)
        
        # Find population column (common names)
        pop_col = None
        for col in ['pop', 'population', 'POP', 'POPULATION', 'pop_count', 'total_pop']:
            if col in pop.columns:
                pop_col = col
                break
        
        if pop_col:
            # Intersection with hazard zone
            intersection = gpd.overlay(pop, dissolved.reset_index(drop=True), how='intersection')
            
            if not intersection.empty and pop_col in intersection.columns:
                # Calculate population by area ratio
                pop['orig_area'] = pop.geometry.area
                intersection['inter_area'] = intersection.geometry.area
                intersection = intersection.merge(
                    pop[['orig_area']], 
                    left_index=True, 
                    right_index=True
                )
                intersection['pop_fraction'] = intersection[pop_col] * (
                    intersection['inter_area'] / intersection['orig_area']
                )
                affected_pop = int(intersection['pop_fraction'].sum())
        else:
            print(f"  Warning: No population column found in {population_shp}")
    
    # Print results
    print("\n" + "="*50)
    print("HAZARD ZONE METRICS")
    print("="*50)
    print(f"Centroid (WGS84):  lat={centroid_wgs84.y:.6f}, lon={centroid_wgs84.x:.6f}")
    print(f"Area:              {area_km2:.3f} km²")
    if affected_pop is not None:
        print(f"Affected Pop:      {affected_pop:,}")
    else:
        print("Affected Pop:      N/A (no population data)")
    print("="*50 + "\n")
    
    # Export to GeoJSON
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        geojson_path = output_dir / "hazard_zone.geojson"
    else:
        geojson_path = hazard_shp.parent.parent / "output" / "hazard_zone.geojson"
        geojson_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to WGS84 for GeoJSON
    haz_wgs84 = haz.to_crs(epsg=4326)
    
    # Add metrics as properties
    haz_wgs84['centroid_lat'] = centroid_wgs84.y
    haz_wgs84['centroid_lon'] = centroid_wgs84.x
    haz_wgs84['area_km2'] = area_km2
    if affected_pop is not None:
        haz_wgs84['affected_population'] = affected_pop
    
    haz_wgs84.to_file(geojson_path, driver='GeoJSON')
    print(f"GeoJSON exported: {geojson_path}")
    
    return {
        'centroid_lat': centroid_wgs84.y,
        'centroid_lon': centroid_wgs84.x,
        'area_km2': area_km2,
        'affected_population': affected_pop
    }


def main():
    parser = argparse.ArgumentParser(description="Compute hazard zone metrics")
    parser.add_argument('--hazard-shp', type=Path, 
                        default=Path(__file__).parent.parent / 'input' / 'disaster_zone_tamsui.shp',
                        help='Path to hazard zone shapefile')
    parser.add_argument('--population-shp', type=Path,
                        default=Path(__file__).parent.parent / 'input' / 'population_areas.shp',
                        help='Path to population shapefile (optional)')
    parser.add_argument('--output-dir', type=Path,
                        help='Output directory for GeoJSON (default: ../output/)')
    
    args = parser.parse_args()
    
    if not args.hazard_shp.exists():
        print(f"ERROR: Hazard shapefile not found: {args.hazard_shp}")
        exit(1)
    
    compute_hazard_metrics(
        hazard_shp=args.hazard_shp,
        population_shp=args.population_shp if args.population_shp.exists() else None,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
