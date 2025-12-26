#!/usr/bin/env python3
"""
Inspect shapefile structure and output field schema to JSON
檢查 shapefile 結構並輸出欄位結構到 JSON
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import geopandas as gpd
except ImportError:
    print("ERROR: geopandas not installed. Install with: pip3 install geopandas", file=sys.stderr)
    sys.exit(1)


def inspect_shapefile(shapefile_path: Path, output_json: Path = None):
    """
    Inspect a single shapefile and return schema information
    
    Args:
        shapefile_path: Path to .shp file
        output_json: Optional path to save JSON output
        
    Returns:
        dict: Schema information including features, fields, CRS, bounds, and samples
    """
    print(f"Reading {shapefile_path}...", file=sys.stderr)
    gdf = gpd.read_file(shapefile_path)
    
    schema = {
        "filename": shapefile_path.name,
        "features": len(gdf),
        "crs": str(gdf.crs),
        "geometry_type": gdf.geometry.geom_type.unique().tolist(),
        "bounds": {
            "xmin": float(gdf.total_bounds[0]),
            "ymin": float(gdf.total_bounds[1]),
            "xmax": float(gdf.total_bounds[2]),
            "ymax": float(gdf.total_bounds[3])
        },
        "fields": {}
    }
    
    # Extract field info
    for col in gdf.columns:
        if col != 'geometry':
            schema["fields"][col] = {
                "dtype": str(gdf[col].dtype),
                "null_count": int(gdf[col].isnull().sum()),
                "unique_count": int(gdf[col].nunique())
            }
            
            # Add sample unique values for categorical fields
            if gdf[col].nunique() < 100:
                schema["fields"][col]["unique_values"] = gdf[col].dropna().unique()[:20].tolist()
    
    # Add sample records
    schema["sample_records"] = []
    for _, row in gdf.drop(columns=['geometry']).head(3).iterrows():
        schema["sample_records"].append(row.to_dict())
    
    # Save to JSON if output path specified
    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2, default=str)
        print(f"Schema saved to {output_json}", file=sys.stderr)
    
    return schema


def inspect_directory(dir_path: Path, output_dir: Path = None):
    """
    Inspect all shapefiles in a directory
    
    Args:
        dir_path: Directory containing shapefiles
        output_dir: Optional directory to save individual JSON files
    """
    results = {}
    
    # Find all shapefiles
    shapefiles = sorted(dir_path.glob("*.shp"))
    
    if not shapefiles:
        print(f"ERROR: No shapefiles found in {dir_path}", file=sys.stderr)
        return results
    
    print(f"Found {len(shapefiles)} shapefiles", file=sys.stderr)
    
    for shp_path in shapefiles:
        layer_name = shp_path.stem
        
        # Save individual JSON if output directory specified
        json_path = (output_dir / f"{layer_name}_schema.json") if output_dir else None
        
        try:
            schema = inspect_shapefile(shp_path, json_path)
            results[layer_name] = schema
        except Exception as e:
            print(f"ERROR processing {shp_path}: {e}", file=sys.stderr)
            results[layer_name] = {"error": str(e)}
    
    # Save combined summary
    if output_dir:
        summary_path = output_dir / "all_schemas_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"Combined summary saved to {summary_path}", file=sys.stderr)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Inspect shapefile structure and output field schema"
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to shapefile (.shp) or directory containing shapefiles"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory for JSON schema files (default: same as input directory)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout"
    )
    
    args = parser.parse_args()
    
    if not args.input_path.exists():
        print(f"ERROR: {args.input_path} does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Determine output directory
    if args.output:
        output_dir = args.output
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = args.input_path.parent if args.input_path.is_file() else args.input_path
    
    # Inspect shapefile(s)
    if args.input_path.is_file():
        # Single shapefile
        json_path = output_dir / f"{args.input_path.stem}_schema.json"
        result = inspect_shapefile(args.input_path, json_path)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        else:
            print(f"\n=== {args.input_path.name} ===")
            print(f"Features: {result['features']}")
            print(f"CRS: {result['crs']}")
            print(f"Fields: {', '.join(result['fields'].keys())}")
    
    elif args.input_path.is_dir():
        # Directory of shapefiles
        results = inspect_directory(args.input_path, output_dir)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        else:
            print(f"\n=== Shapefile Summary ===")
            for layer_name, schema in results.items():
                if "error" in schema:
                    print(f"  {layer_name}: ERROR - {schema['error']}")
                else:
                    print(f"  {layer_name}: {schema['features']} features, "
                          f"{len(schema['fields'])} fields")


if __name__ == "__main__":
    main()
