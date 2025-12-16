import gzip
import xml.etree.ElementTree as ET
from pyproj import Transformer
import folium
from folium.plugins import TimestampedGeoJson
import datetime
import os
from collections import defaultdict
import argparse

# Argument Parsing
parser = argparse.ArgumentParser(description='Generate Filtered Metro Visualization')
parser.add_argument('--output-dir', type=str, required=True, help='Path to the simulation output directory (e.g., 100000_output_v3)')
parser.add_argument('--output-html', type=str, default='metro_viz_filtered.html', help='Output HTML filename')
parser.add_argument('--sample-rate', type=int, default=5, help='Keep 1 event per N entered-link events (higher -> smaller file)')
parser.add_argument('--max-features', type=int, default=200000, help='Stop after this many features to avoid huge HTML')
parser.add_argument('--start-time', type=float, default=0.0, help='Include events after this sim time (sec)')
parser.add_argument('--end-time', type=float, default=None, help='Include events before this sim time (sec)')
parser.add_argument('--only-transit', action='store_true', help='If set, only plot occupied transit vehicles')
args = parser.parse_args()

OUTPUT_DIR = args.output_dir
NETWORK_FILE = os.path.join(OUTPUT_DIR, 'output_network.xml.gz')
EVENTS_FILE = os.path.join(OUTPUT_DIR, 'output_events.xml.gz')
TRANSIT_VEHICLES_FILE = os.path.join(OUTPUT_DIR, 'output_transitVehicles.xml.gz')
OUTPUT_HTML = args.output_html
CRS_FROM = 'EPSG:3826'
CRS_TO = 'EPSG:4326'

# Initialize transformer
transformer = Transformer.from_crs(CRS_FROM, CRS_TO, always_xy=True)

# 1. Load Transit Vehicle IDs
print(f"Loading transit vehicles from {TRANSIT_VEHICLES_FILE}...")
transit_ids = set()
if os.path.exists(TRANSIT_VEHICLES_FILE):
    with gzip.open(TRANSIT_VEHICLES_FILE, 'rb') as f:
        context = ET.iterparse(f, events=('end',))
        for event, elem in context:
            if elem.tag.endswith('vehicle'): # Handle namespaces
                transit_ids.add(elem.attrib['id'])
                elem.clear()
else:
    print(f"Warning: {TRANSIT_VEHICLES_FILE} not found. Visualization might be incorrect.")

print(f"Found {len(transit_ids)} transit vehicles.")

# 2. Parse Network
print(f"Parsing network from {NETWORK_FILE}...")
nodes = {}
links = {}

if not os.path.exists(NETWORK_FILE):
    print(f"Error: {NETWORK_FILE} not found.")
    exit(1)

with gzip.open(NETWORK_FILE, 'rb') as f:
    context = ET.iterparse(f, events=('end',))
    for event, elem in context:
        if elem.tag == 'node':
            nid = elem.attrib['id']
            x = float(elem.attrib['x'])
            y = float(elem.attrib['y'])
            lon, lat = transformer.transform(x, y)
            nodes[nid] = [lon, lat]
            elem.clear()
        elif elem.tag == 'link':
            lid = elem.attrib['id']
            from_node = elem.attrib['from']
            if from_node in nodes:
                links[lid] = nodes[from_node]
            elem.clear()

# 3. Parse Events and Filter
print(f"Parsing events from {EVENTS_FILE}...")
features = []
vehicle_occupancy = defaultdict(int)
SAMPLE_RATE = max(1, args.sample_rate)
MAX_FEATURES = args.max_features
counter = 0

# Time helper (Sim starts at 03:00:00)
def to_timestamp(seconds):
    base = datetime.datetime(2025, 12, 1, 0, 0, 0) + datetime.timedelta(seconds=seconds)
    return base.isoformat()

if not os.path.exists(EVENTS_FILE):
    print(f"Error: {EVENTS_FILE} not found.")
    exit(1)

with gzip.open(EVENTS_FILE, 'rb') as f:
    context = ET.iterparse(f, events=('end',))
    for event, elem in context:
        if elem.tag == 'event':
            etype = elem.attrib['type']
            time = float(elem.attrib['time'])
            
            # Track Occupancy
            if etype == 'PersonEntersVehicle':
                pid = elem.attrib['person']
                if pid.startswith('pt_'): continue # Ignore drivers
                
                vid = elem.attrib['vehicle']
                if vid in transit_ids:
                    vehicle_occupancy[vid] += 1
            elif etype == 'PersonLeavesVehicle':
                pid = elem.attrib['person']
                if pid.startswith('pt_'): continue # Ignore drivers
                
                vid = elem.attrib['vehicle']
                if vid in transit_ids:
                    vehicle_occupancy[vid] = max(0, vehicle_occupancy[vid] - 1)
            
            # Movement
            elif etype == 'entered link':
                vid = elem.attrib['vehicle']
                lid = elem.attrib['link']
                
                if lid in links:
                    if time < args.start_time:
                        elem.clear()
                        continue
                    if args.end_time is not None and time > args.end_time:
                        elem.clear()
                        continue

                    counter += 1
                    if counter % SAMPLE_RATE != 0:
                        elem.clear()
                        continue
                        
                    # Logic:
                    # If Transit: Show only if Occupancy > 0
                    # If Not Transit: Show (it's a person/car)
                    
                    is_transit = vid in transit_ids
                    if args.only_transit and not is_transit:
                        elem.clear()
                        continue

                    occupancy = vehicle_occupancy[vid] if is_transit else 1 # Persons always occupy their car
                    
                    if is_transit and occupancy == 0:
                        elem.clear()
                        continue # Skip empty bus/train
                    
                    # Style
                    if is_transit:
                        color = '#d63031' # Red
                        radius = 5
                        popup = f"Metro {vid}<br>Pax: {occupancy}"
                    else:
                        color = '#0984e3' # Blue
                        radius = 2
                        popup = f"Car {vid}"
                        
                    coord = links[lid]
                    
                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': coord,
                        },
                        'properties': {
                            'time': to_timestamp(time),
                            'style': {'color': color},
                            'icon': 'circle',
                            'iconstyle': {
                                'fillColor': color,
                                'fillOpacity': 0.8,
                                'stroke': 'false',
                                'radius': radius
                            },
                            'popup': popup
                        }
                    }
                    features.append(feature)
                    if len(features) >= MAX_FEATURES:
                        print(f"Reached max features {MAX_FEATURES}, truncating output.")
                        break
            
            elem.clear()
        if len(features) >= MAX_FEATURES:
            break

print(f"Events parsed. {len(features)} features created.")

# 4. Generate Map
print("Generating map...")
if nodes:
    avg_lat = sum(n[1] for n in nodes.values()) / len(nodes)
    avg_lon = sum(n[0] for n in nodes.values()) / len(nodes)
    
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles='CartoDB positron')
    
    # Legend
    legend_html = '''
         <div style="position: fixed; 
         bottom: 50px; left: 50px; width: 150px; height: 100px; 
         border:2px solid grey; z-index:9999; font-size:14px;
         background-color:white; opacity: 0.8;
         padding: 10px;">
         <b>Filtered View</b><br>
         <i style="background:#d63031; width:10px; height:10px; float:left; margin-right:5px; border-radius:50%;"></i> Occupied Metro<br>
         <i style="background:#0984e3; width:10px; height:10px; float:left; margin-right:5px; border-radius:50%;"></i> Agent Car<br>
         (Empty metros hidden)
         </div>
         '''
    m.get_root().html.add_child(folium.Element(legend_html))

    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features},
        period='PT10S',
        duration='PT2M',
        transition_time=200,
        auto_play=False,
        loop=False,
    ).add_to(m)

    m.save(OUTPUT_HTML)
    print(f"Map saved to {OUTPUT_HTML}")
else:
    print("No nodes found.")
