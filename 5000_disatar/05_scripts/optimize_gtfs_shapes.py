import pandas as pd
import numpy as np
from pathlib import Path

def optimize_shapes(input_file, output_file, min_dist_m=50.0):
    print(f"Reading shapes: {input_file}")
    df = pd.read_csv(input_file)
    
    optimized_rows = []
    
    for shape_id, group in df.groupby('shape_id'):
        group = group.sort_values('shape_pt_sequence')
        
        # Always keep the first point
        last_kept_point = group.iloc[0]
        optimized_rows.append(last_kept_point)
        
        # Calculate distances (rough approximation since it's WGS84, but good enough for filtering)
        # 1 degree lat ~ 111km, 1 degree lon ~ 100km in Taiwan
        lat_scale = 111000.0
        lon_scale = 100000.0
        
        for i in range(1, len(group) - 1):
            curr_point = group.iloc[i]
            
            d_lat = (curr_point['shape_pt_lat'] - last_kept_point['shape_pt_lat']) * lat_scale
            d_lon = (curr_point['shape_pt_lon'] - last_kept_point['shape_pt_lon']) * lon_scale
            dist = np.sqrt(d_lat**2 + d_lon**2)
            
            if dist >= min_dist_m:
                optimized_rows.append(curr_point)
                last_kept_point = curr_point
        
        # Always keep the last point
        if len(group) > 1:
            optimized_rows.append(group.iloc[-1])
            
    reduced_df = pd.DataFrame(optimized_rows)
    # Fix sequences
    reduced_df['shape_pt_sequence'] = reduced_df.groupby('shape_id').cumcount() + 1
    
    reduced_df.to_csv(output_file, index=False)
    print(f"Success! Reduced points from {len(df)} to {len(reduced_df)} ({(1 - len(reduced_df)/len(df))*100:.1f}% reduction)")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    src = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes/shapes.txt"
    dst = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/GTFS_pt_mapping/GTFS_pt_mapping_v6/test_5routes/shapes_optimized.txt"
    optimize_shapes(src, dst)
