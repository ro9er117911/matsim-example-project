#!/usr/bin/env python3
"""Check shapefile bounds and convert to WGS84 for verification"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pyproj import Transformer
import struct

# TWD97 bounds reference for Taiwan (in EPSG:3826)
# Taipei area: ~295000-310000 X, ~2765000-2780000 Y
# Chiayi area: ~185000-225000 X, ~2580000-2620000 Y
# Tamsui/Bali: ~290000-310000 X, ~2775000-2795000 Y

# Read SHP file bounds directly from header
def read_shp_bounds(shp_path):
    with open(shp_path, 'rb') as f:
        f.seek(36)  # Skip to bounding box
        xmin = struct.unpack('<d', f.read(8))[0]
        ymin = struct.unpack('<d', f.read(8))[0]
        xmax = struct.unpack('<d', f.read(8))[0]
        ymax = struct.unpack('<d', f.read(8))[0]
    return xmin, ymin, xmax, ymax

BASE = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map"
bounds = read_shp_bounds(f"{BASE}/Q_ROAD.shp")
print(f"Q_ROAD bounds (TWD97 EPSG:3826):")
print(f"  X: {bounds[0]:.1f} to {bounds[2]:.1f}")
print(f"  Y: {bounds[1]:.1f} to {bounds[3]:.1f}")

# Convert to WGS84
transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
lon_min, lat_min = transformer.transform(bounds[0], bounds[1])
lon_max, lat_max = transformer.transform(bounds[2], bounds[3])
print(f"\nConverted to WGS84:")
print(f"  Longitude: {lon_min:.4f} to {lon_max:.4f}")
print(f"  Latitude: {lat_min:.4f} to {lat_max:.4f}")

# Reference locations
print("\n--- Reference ---")
print("Chiayi City center: 120.4473°E, 23.4800°N")
print("Taipei City center: 121.5654°E, 25.0330°N")
print("Tamsui: 121.4630°E, 25.1745°N")
print("Bali: 121.4072°E, 25.1306°N")

# Determine coverage
if lon_max < 121.0 and lat_max < 24.0:
    print("\n==> This appears to be CHIAYI ONLY data")
elif lon_max > 121.3 and lat_max > 25.0:
    print("\n==> This data includes NORTHERN TAIWAN (Taipei area)")
