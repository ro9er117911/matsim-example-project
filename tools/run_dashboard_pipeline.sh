#!/bin/bash
# Master pipeline to generate SimWrapper Dashboard for a MATSim output folder
# Usage: ./tools/run_dashboard_pipeline.sh <output_dir>
# Example: ./tools/run_dashboard_pipeline.sh output_staggered

OUTPUT_DIR=$1
MIN_VOLUME=${MIN_VOLUME:-0}
MIN_TT_RATIO=${MIN_TT_RATIO:-0}
# Optional overrides
NETWORK_GEOJSON=${NETWORK_GEOJSON:-network_wgs84_congestion.geojson}
export NETWORK_GEOJSON

if [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <output_dir>"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Directory $OUTPUT_DIR does not exist."
    exit 1
fi

echo "=== Starting Dashboard Pipeline for $OUTPUT_DIR ==="
echo "Filters: MIN_VOLUME=$MIN_VOLUME, MIN_TT_RATIO=$MIN_TT_RATIO (applied to link_congestion CSVs)"

# 1. Generate Advanced Dashboard Data (CSVs)
# Assumes generate_advanced_dashboard.py takes output_dir as argument
echo "[1/3] Generating Data CSVs..."
# Default to original network with Chinese attributes if not specified
INPUT_NETWORK="${INPUT_NETWORK:-scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz}"
CMD_ARGS=("$OUTPUT_DIR")
if [ -n "$INPUT_NETWORK" ]; then
  CMD_ARGS+=("--network" "$INPUT_NETWORK")
fi
python3 output/generate_advanced_dashboard.py "${CMD_ARGS[@]}"
python3 output/generate_advanced_dashboard.py "${CMD_ARGS[@]}"
if [ $? -ne 0 ]; then echo "Data generation failed."; exit 1; fi

# Copy Tsunami GeoJSON for visualization
# hazard_zone = buffered polygons (0-1km / 1-3km), moderate_closure = line closures
TSUNAMI_SRC="${TSUNAMI_SRC:-output/inundation_zones_buffered.geojson}"
TSUNAMI_LINES_SRC="${TSUNAMI_LINES_SRC:-output/moderate_closure.geojson}"
if [ -f "$TSUNAMI_SRC" ]; then
    echo "Copying Tsunami GeoJSON to output..."
    cp "$TSUNAMI_SRC" "$OUTPUT_DIR/hazard_zone.geojson"
else
    echo "Warning: Tsunami polygon GeoJSON not found at $TSUNAMI_SRC"
fi
if [ -f "$TSUNAMI_LINES_SRC" ]; then
    cp "$TSUNAMI_LINES_SRC" "$OUTPUT_DIR/moderate_closure.geojson"
else
    echo "Warning: Tsunami line GeoJSON not found at $TSUNAMI_LINES_SRC"
fi

# Optional visual filter to drop tiny-flow noise before mapping
filter_csv() {
  local src="$1"; local dest="$2"; local min_vol="$3"; local min_tt="$4"
  if [ ! -f "$src" ]; then
    echo "Warning: $src not found; skipping filter."
    return 1
  fi
  python3 - "$src" "$dest" "$min_vol" "$min_tt" <<'PY'
import sys
import pandas as pd

src, dest, min_vol, min_tt = sys.argv[1:]
min_vol = float(min_vol)
min_tt = float(min_tt)

df = pd.read_csv(src)
if not {'volume','tt_ratio'} <= set(df.columns):
    sys.exit("Missing required columns 'volume' and 'tt_ratio' in %s" % src)

use_tt = df['tt_ratio'].max() > 0
if use_tt:
    mask = (df['volume'] >= min_vol) & (df['tt_ratio'] >= min_tt)
else:
    mask = df['volume'] >= min_vol

filtered = df[mask]
if filtered.empty:
    print(f"Filter produced 0 rows for {src}; keeping original file.")
    sys.exit(2)

filtered.to_csv(dest, index=False)
print(f"Wrote {len(filtered)} filtered rows to {dest} (use_tt={use_tt})")
PY
  return $?
}

CSV1="$OUTPUT_DIR/link_congestion_0300_0315.csv"
CSV2="$OUTPUT_DIR/link_congestion_0315_0330.csv"
CSV1_USE="$CSV1"
CSV2_USE="$CSV2"

if filter_csv "$CSV1" "$OUTPUT_DIR/link_congestion_0300_0315_filtered.csv" "$MIN_VOLUME" "$MIN_TT_RATIO"; then
  CSV1_USE="$OUTPUT_DIR/link_congestion_0300_0315_filtered.csv"
fi

if filter_csv "$CSV2" "$OUTPUT_DIR/link_congestion_0315_0330_filtered.csv" "$MIN_VOLUME" "$MIN_TT_RATIO"; then
  CSV2_USE="$OUTPUT_DIR/link_congestion_0315_0330_filtered.csv"
fi

echo "Using whitelist files: $CSV1_USE $CSV2_USE"

# 2. Convert Network to Optimized GeoJSON
# Filter by the congestion CSVs generated in Step 1
echo "[2/3] Converting and Filtering Network..."
python3 5000_disatar/05_combined_evac/tools/network_to_geojson.py \
  --network "$OUTPUT_DIR/output_network.xml.gz" \
  --output "$OUTPUT_DIR/${NETWORK_GEOJSON}" \
  --whitelist "$CSV1_USE" "$CSV2_USE"
if [ $? -ne 0 ]; then echo "Network conversion failed."; exit 1; fi

# 3. Generate Dashboard YAML Configuration
echo "[3/3] Generating Dashboard Configuration..."
python3 tools/generate_dashboard_yamls.py --output_dir "$OUTPUT_DIR"
if [ $? -ne 0 ]; then echo "YAML generation failed."; exit 1; fi

echo "=== Pipeline Complete! ==="
echo "Open SimWrapper and navigate to: $OUTPUT_DIR"
