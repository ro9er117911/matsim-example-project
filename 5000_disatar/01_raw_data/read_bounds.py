#!/usr/bin/env python3
import struct

# Read SHP file bounds directly from header
shp_path = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map/Q_ROAD.shp"
out_path = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/bounds.txt"

with open(shp_path, 'rb') as f:
    f.seek(36)
    xmin = struct.unpack('<d', f.read(8))[0]
    ymin = struct.unpack('<d', f.read(8))[0]
    xmax = struct.unpack('<d', f.read(8))[0]
    ymax = struct.unpack('<d', f.read(8))[0]

result = f"""Q_ROAD.shp Bounds (TWD97 EPSG:3826):
  Xmin: {xmin:.1f}
  Ymin: {ymin:.1f}
  Xmax: {xmax:.1f}
  Ymax: {ymax:.1f}

Reference TWD97 coordinates:
  Chiayi City: X~209000, Y~2593000
  Taipei City: X~302500, Y~2770000
  Tamsui: X~295000, Y~2785000
  Bali: X~291000, Y~2782000

Analysis:
"""

# Determine location (rough estimation)
if xmax < 250000 and ymax < 2650000:
    result += "==> This is CHIAYI ONLY data (southern Taiwan)\n"
elif xmax > 300000 and ymax > 2750000:
    result += "==> This includes NORTHERN TAIWAN (Taipei/Tamsui/Bali area)\n"
else:
    result += f"==> Unclear coverage, manual check needed\n"

with open(out_path, 'w') as f:
    f.write(result)
