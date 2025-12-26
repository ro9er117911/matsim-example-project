#!/usr/bin/env python3
"""Check geographic extent of chayi_map"""
import fiona
import json

BASE = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map"
OUT = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map/extent_check.json"

result = {}

# Q_ROAD bounds
with fiona.open(f"{BASE}/Q_ROAD.shp") as src:
    result["Q_ROAD"] = {
        "bounds_twd97": src.bounds,
        "features": len(src),
        "crs": src.crs.get("init", str(src.crs))
    }

# Q_COUNTY
with fiona.open(f"{BASE}/Q_COUNTY.shp") as src:
    counties = []
    for feat in src:
        counties.append(feat['properties'])
    result["Q_COUNTY"] = counties

# Q_TOWN
with fiona.open(f"{BASE}/Q_TOWN.shp") as src:
    towns = []
    for feat in src:
        towns.append(feat['properties'])
    result["Q_TOWN"] = towns

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)

print(f"Written to {OUT}")
