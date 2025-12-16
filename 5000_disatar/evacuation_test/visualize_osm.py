import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import sys
import random

def parse_and_plot_osm(osm_file, output_image, sample_rate=0.1):
    """
    Parses OSM XML and plots nodes.
    Since 2GB is huge, we randomly sample nodes to plot to keep memory low and speed high.
    sample_rate: 0.1 means plot 10% of nodes.
    """
    print(f"Parsing {osm_file} with sample rate {sample_rate}...")
    
    lons = []
    lats = []
    
    # Streaming parser to handle large files
    context = ET.iterparse(osm_file, events=('end',))
    
    count = 0
    for event, elem in context:
        if elem.tag == 'node':
            if random.random() < sample_rate:
                try:
                    lat = float(elem.attrib['lat'])
                    lon = float(elem.attrib['lon'])
                    lats.append(lat)
                    lons.append(lon)
                except KeyError:
                    pass
            # Clear element to save memory
            elem.clear()
            count += 1
            if count % 100000 == 0:
                print(f"Processed {count} nodes...")
                
    print(f"Plotting {len(lats)} points...")
    
    plt.figure(figsize=(10, 10))
    plt.scatter(lons, lats, s=0.1, alpha=0.5, c='blue')
    plt.title(f"OSM Node Distribution: {osm_file.split('/')[-1]}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.axis('equal')
    plt.grid(True)
    
    plt.savefig(output_image, dpi=150)
    print(f"Saved visualization to {output_image}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 visualize_osm.py <input_osm_path> [output_png_path]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "osm_visualization.png"
    
    # For a 2GB file, 1% sample is likely enough to see the shape (~10 million nodes -> 100k points)
    parse_and_plot_osm(input_file, output_file, sample_rate=0.0001)
