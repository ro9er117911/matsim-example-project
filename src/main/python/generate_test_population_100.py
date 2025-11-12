"""
Generate test population for MATSim with 100 agents:
- 50 PT agents (20 single-line + 30 transfer) - PT-ONLY (no car availability)
- 40 car agents
- 10 walk agents

Key Features:
- PT agents are PT-ONLY (no car in vehicles attribute)
- 30+ transfer agents to demonstrate SwissRailRaptor transfer capability
- Uses extended trip time limit (60 min) to allow more transfer routes
"""

import random

# Station data (stop_id, name, x, y)
STATIONS = {
    # BL Line (板南線/Blue Line)
    'BL02': ('永寧', 294035.051, 2762173.239),
    'BL06': ('府中', 296356.462, 2766793.711),
    'BL10': ('龍山寺', 300488.787, 2769778.539),
    'BL11': ('西門', 301278.155, 2770528.601),
    'BL12': ('台北車站', 302208.733, 2771006.763),
    'BL13': ('善導寺', 302862.286, 2770828.727),
    'BL14': ('忠孝新生', 303804.189, 2770590.711),
    'BL15': ('忠孝復興', 304996.853, 2770512.496),
    'BL16': ('忠孝敦化', 305544.293, 2770487.684),
    'BL19': ('永春', 308143.011, 2770426.5),
    'BL22': ('南港', 311242.46, 2771678.44),

    # G Line (松山新店線/Green Line)
    'G02': ('新店區公所', 304653.737, 2762280.146),
    'G05': ('景美', 304581.697, 2765091.555),
    'G07': ('公館', 303932.145, 2767521.084),
    'G08': ('台電大樓', 303302.341, 2768177.899),
    'G09': ('古亭', 302767.496, 2768800.549),
    'G10': ('中正紀念堂', 302301.052, 2769506.999),
    'G12': ('西門', 301278.155, 2770528.601),  # Transfer with BL11
    'G14': ('中山', 302503.613, 2771706.945),
    'G15': ('松江南京', 303763.415, 2771719.823),
    'G16': ('南京復興', 304919.31, 2771652.536),
    'G19': ('松山', 308290.602, 2771453.175),

    # O Line (中和新蘆線/Orange Line)
    'O02': ('景安', 300989.141, 2765199.101),
    'O03': ('永安市場', 301602.283, 2766195.525),
    'O04': ('頂溪', 302025.348, 2767411.46),
    'O05': ('古亭', 302767.496, 2768800.549),  # Transfer with G09
    'O06': ('東門', 303359.476, 2769635.926),
    'O07': ('忠孝新生', 303804.189, 2770590.711),  # Transfer with BL14
    'O08': ('松江南京', 303763.415, 2771719.823),  # Transfer with G15
    'O09': ('行天宮', 303790.827, 2772445.126),

    # R Line (淡水信義線/Red Line)
    'R02': ('象山', 307533.022, 2769486.821),
    'R03': ('台北101/世貿', 306881.993, 2769536.156),
    'R05': ('大安', 304732.584, 2769576.78),
    'R07': ('東門', 303359.476, 2769635.926),  # Transfer with O06
    'R08': ('中正紀念堂', 302301.052, 2769506.999),  # Transfer with G10
    'R10': ('台北車站', 302208.733, 2771006.763),  # Transfer with BL12
    'R11': ('中山', 302503.613, 2771706.945),  # Transfer with G14
    'R15': ('劍潭', 302953.213, 2775206.774),
    'R22': ('北投', 300280.051, 2780471.075),
    'R28': ('淡水', 294938.558, 2784431.865),

    # BR Line (文湖線/Brown Line)
    'BR03': ('萬芳社區', 307344.072, 2765739.316),
    'BR05': ('辛亥', 306226.261, 2766497.309),
    'BR07': ('六張犁', 305811.634, 2768528.744),
    'BR08': ('科技大樓', 304845.93, 2768780.707),
    'BR09': ('大安', 304732.584, 2769576.78),  # Transfer with R05
    'BR10': ('忠孝復興', 304996.853, 2770512.496),  # Transfer with BL15
    'BR11': ('南京復興', 304919.31, 2771652.536),  # Transfer with G16
    'BR12': ('中山國中', 304906.507, 2772627.905),
}

# ========== OSM BOUNDARY AND CONSTRAINTS ==========
OSM_BOUNDS = {
    'top_left': (288137, 2783823),
    'bottom_left': (287627, 2768820),
    'bottom_right': (314701, 2769311),
    'top_right': (314401, 2784363),
}

CITY_CENTER = (302416, 2770714)

# Trip constraints - INCREASED to 60 min to allow more transfer routes
MAX_TRIP_TIME_MINUTES = 60

MODE_SPEEDS_M_PER_MIN = {
    'pt': 500,     # PT average speed ~30 km/h
    'car': 417,    # Car average speed ~25 km/h
    'walk': 84,    # Walking speed 1.4 m/s
}

# ========== VALIDATION FUNCTIONS ==========

def is_within_osm_bounds(x, y):
    """Check if coordinates are within OSM network bounds."""
    xs = [OSM_BOUNDS[k][0] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]
    ys = [OSM_BOUNDS[k][1] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    return x_min <= x <= x_max and y_min <= y <= y_max

def euclidean_distance_m(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points in meters."""
    import math
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def get_station_distance_m(station1_id, station2_id):
    """Get Euclidean distance between two stations in meters."""
    _, x1, y1 = STATIONS[station1_id]
    _, x2, y2 = STATIONS[station2_id]
    return euclidean_distance_m(x1, y1, x2, y2)

def estimate_trip_time_minutes(distance_m, mode):
    """Estimate one-way trip time based on distance and mode."""
    if mode not in MODE_SPEEDS_M_PER_MIN:
        raise ValueError(f"Unknown mode: {mode}")
    speed = MODE_SPEEDS_M_PER_MIN[mode]
    base_time = distance_m / speed
    if mode == 'pt':
        base_time += 5  # 5 minutes waiting
    elif mode == 'car':
        base_time += 2  # 2 minutes overhead
    return base_time

def is_valid_trip(home_station_id, work_station_id, mode):
    """Check if a trip is valid based on constraints."""
    if home_station_id == work_station_id:
        return False
    _, home_x, home_y = STATIONS[home_station_id]
    _, work_x, work_y = STATIONS[work_station_id]
    if mode == 'car':
        if not is_within_osm_bounds(home_x, home_y):
            return False
        if not is_within_osm_bounds(work_x, work_y):
            return False
    distance_m = get_station_distance_m(home_station_id, work_station_id)
    estimated_time = estimate_trip_time_minutes(distance_m, mode)
    if estimated_time > MAX_TRIP_TIME_MINUTES:
        return False
    return True

def filter_valid_stations(mode):
    """Filter stations to only include valid ones for the given mode."""
    valid_stations = []
    for station_id in STATIONS.keys():
        if mode == 'car':
            _, x, y = STATIONS[station_id]
            if is_within_osm_bounds(x, y):
                valid_stations.append(station_id)
        else:
            valid_stations.append(station_id)
    return valid_stations

# ========== PT TRANSFER ROUTES ==========
# 30+ transfer routes to ensure sufficient transfer agents
PT_TRANSFER_ROUTES = [
    # Short distance transfers (high success rate)
    ('BL10', 'BL14', 'O07', 'O09'),      # BL → O transfer
    ('BL11', 'BL12', 'R10', 'R15'),      # BL → R transfer
    ('BL12', 'BL14', 'O07', 'O06'),      # BL → O transfer
    ('BL13', 'BL14', 'O07', 'O08'),      # BL → O transfer
    ('BL06', 'BL12', 'G12', 'G14'),      # BL → G transfer

    ('G07', 'G10', 'R08', 'R11'),        # G → R transfer
    ('G08', 'G09', 'O05', 'O08'),        # G → O transfer
    ('G09', 'G10', 'R08', 'R10'),        # G → R transfer
    ('G10', 'G14', 'R11', 'R15'),        # G → R transfer
    ('G14', 'G15', 'O08', 'O09'),        # G → O transfer

    ('O03', 'O06', 'R07', 'R10'),        # O → R transfer
    ('O04', 'O08', 'G15', 'G19'),        # O → G transfer
    ('O05', 'O06', 'R07', 'R08'),        # O → R transfer
    ('O06', 'O07', 'BL14', 'BL16'),      # O → BL transfer
    ('O02', 'O05', 'G09', 'G14'),        # O → G transfer

    ('R02', 'R05', 'BR09', 'BR12'),      # R → BR transfer
    ('R02', 'R05', 'BL15', 'BL19'),      # R → BL via 大安
    ('R03', 'R07', 'O06', 'O08'),        # R → O transfer
    ('R05', 'R07', 'O06', 'O09'),        # R → O transfer
    ('R08', 'R10', 'BL12', 'BL14'),      # R → BL transfer
    ('R08', 'R11', 'G14', 'G16'),        # R → G transfer

    ('BR03', 'BR10', 'BL15', 'BL16'),    # BR → BL transfer
    ('BR05', 'BR09', 'R05', 'R08'),      # BR → R transfer
    ('BR07', 'BR09', 'R05', 'R10'),      # BR → R transfer
    ('BR08', 'BR10', 'BL15', 'BL19'),    # BR → BL transfer
    ('BR05', 'BR11', 'G16', 'G19'),      # BR → G transfer

    # Additional routes
    ('BL02', 'BL12', 'G12', 'G19'),      # BL → G longer
    ('BL10', 'BL11', 'G12', 'G15'),      # BL → G
    ('G02', 'G10', 'R08', 'R15'),        # G → R longer
    ('G05', 'G09', 'O05', 'O07'),        # G → O
    ('O02', 'O07', 'BL14', 'BL19'),      # O → BL longer
    ('R07', 'R10', 'BL12', 'BL16'),      # R → BL
    ('BR03', 'BR09', 'R05', 'R11'),      # BR → R longer
    ('BL14', 'BL15', 'BR10', 'BR12'),    # BL → BR
    ('G15', 'G16', 'BR11', 'BR12'),      # G → BR
]

# Single-line PT routes
PT_SINGLE_LINE_ROUTES = [
    ('BL02', 'BL14'), ('BL02', 'BL16'), ('BL06', 'BL12'), ('BL10', 'BL15'),
    ('BL11', 'BL19'), ('BL13', 'BL22'), ('BL06', 'BL19'), ('BL10', 'BL16'),
    ('G02', 'G14'), ('G05', 'G15'), ('G07', 'G16'), ('G08', 'G19'),
    ('G09', 'G12'), ('G02', 'G16'), ('G05', 'G14'), ('G07', 'G15'),
    ('O02', 'O07'), ('O03', 'O08'), ('O04', 'O09'), ('O05', 'O06'),
]

# Car validation
MIN_CAR_TRIP_DISTANCE_M = 1000

# Time slots
PEAK_MORNING = [(6, 30), (7, 0), (7, 15), (7, 30), (7, 45), (8, 0)]
OFF_PEAK_MORNING = [(9, 0), (9, 30), (10, 0), (10, 30), (11, 0)]

# ========== AGENT GENERATION FUNCTIONS ==========

def format_time(hour, minute):
    """Format time as HH:MM:SS"""
    return f"{hour:02d}:{minute:02d}:00"

def generate_pt_agent(agent_id, home_station, work_station, departure_hour, departure_min, is_pt_only=True):
    """Generate a PT agent (PT-ONLY by default, no car availability)"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    # Work 8 hours
    arrival_hour = departure_hour
    arrival_min = departure_min + 30
    if arrival_min >= 60:
        arrival_hour += 1
        arrival_min -= 60

    evening_hour = arrival_hour + 8
    evening_min = arrival_min
    if evening_hour >= 24:
        evening_hour = 23
        evening_min = 59

    evening_depart = format_time(evening_hour, evening_min)

    # PT-ONLY: NO vehicles attribute
    xml = f'''	<!-- PT Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) -->
	<person id="pt_agent_{agent_id:02d}">
		<plan selected="yes">
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="pt" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<leg mode="pt" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

def generate_transfer_pt_agent(agent_id, home_station, transfer_station_1, transfer_station_2, work_station, departure_hour, departure_min):
    """Generate a PT transfer agent (PT-ONLY, no car availability)"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    # Work 8 hours
    arrival_hour = departure_hour + 1
    arrival_min = departure_min

    evening_hour = arrival_hour + 8
    evening_min = arrival_min
    if evening_hour >= 24:
        evening_hour = 23
        evening_min = 59

    evening_depart = format_time(evening_hour, evening_min)

    # PT-ONLY: NO vehicles attribute
    xml = f'''	<!-- PT Transfer Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) via transfer -->
	<person id="pt_transfer_agent_{agent_id:02d}">
		<plan selected="yes">
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="pt" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<leg mode="pt" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

def generate_car_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a car agent"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    evening_hour = departure_hour + 8
    evening_min = departure_min + 15
    if evening_min >= 60:
        evening_hour += 1
        evening_min -= 60
    if evening_hour >= 24:
        evening_hour = 23
        evening_min = 59

    evening_depart = format_time(evening_hour, evening_min)

    xml = f'''	<!-- Car Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) -->
	<person id="car_agent_{agent_id:02d}">
		<plan selected="yes">
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="car" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<leg mode="car" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

def generate_walk_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a walk agent"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    evening_hour = departure_hour + 6
    evening_min = departure_min + 30
    if evening_min >= 60:
        evening_hour += 1
        evening_min -= 60
    if evening_hour >= 24:
        evening_hour = 23
        evening_min = 59

    evening_depart = format_time(evening_hour, evening_min)

    xml = f'''	<!-- Walk Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) -->
	<person id="walk_agent_{agent_id:02d}">
		<plan selected="yes">
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="walk" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<leg mode="walk" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

# ========== MAIN GENERATION ==========

xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">
<population>
'''

# Generate 20 single-line PT agents (PT-ONLY)
print("=" * 70)
print("GENERATING 100 AGENTS POPULATION")
print("=" * 70)
print("\n[1/4] Generating 20 single-line PT agents (PT-ONLY)...")
pt_single_created = 0
pt_single_skipped = 0

for i in range(20):
    if i < len(PT_SINGLE_LINE_ROUTES):
        home_station, work_station = PT_SINGLE_LINE_ROUTES[i]
    else:
        home_station = random.choice(list(STATIONS.keys()))
        work_station = random.choice(list(STATIONS.keys()))
        while not is_valid_trip(home_station, work_station, 'pt'):
            work_station = random.choice(list(STATIONS.keys()))

    if is_valid_trip(home_station, work_station, 'pt'):
        hour, minute = random.choice(PEAK_MORNING if i < 14 else OFF_PEAK_MORNING)
        xml_content += generate_pt_agent(i + 1, home_station, work_station, hour, minute, is_pt_only=True)
        xml_content += '\n'
        pt_single_created += 1
    else:
        pt_single_skipped += 1

print(f"  ✓ Created: {pt_single_created}/20")
if pt_single_skipped > 0:
    print(f"  ⚠ Skipped: {pt_single_skipped}")

# Generate 30 PT transfer agents (PT-ONLY)
print("\n[2/4] Generating 30 PT transfer agents (PT-ONLY)...")
pt_transfer_created = 0
pt_transfer_skipped = 0
pt_transfer_skipped_list = []

for i in range(30):
    if i < len(PT_TRANSFER_ROUTES):
        home_station, transfer_station_1, transfer_station_2, work_station = PT_TRANSFER_ROUTES[i]
    else:
        pt_transfer_skipped += 1
        pt_transfer_skipped_list.append(f"pt_transfer_agent_{i+21:02d}")
        continue

    # Validate trip time
    total_distance = (get_station_distance_m(home_station, transfer_station_1) +
                      get_station_distance_m(transfer_station_2, work_station))
    total_time = estimate_trip_time_minutes(total_distance, 'pt') + 8

    if total_time <= MAX_TRIP_TIME_MINUTES:
        hour, minute = random.choice(PEAK_MORNING if i < 21 else OFF_PEAK_MORNING)
        xml_content += generate_transfer_pt_agent(i + 21, home_station, transfer_station_1, transfer_station_2, work_station, hour, minute)
        xml_content += '\n'
        pt_transfer_created += 1
    else:
        pt_transfer_skipped += 1
        pt_transfer_skipped_list.append(f"pt_transfer_agent_{i+21:02d} ({total_time:.1f}min)")

print(f"  ✓ Created: {pt_transfer_created}/30")
if pt_transfer_skipped > 0:
    print(f"  ⚠ Skipped: {pt_transfer_skipped}")
    print(f"    Skipped list: {', '.join(pt_transfer_skipped_list[:5])}" + (" ..." if len(pt_transfer_skipped_list) > 5 else ""))

# Generate 40 car agents
print("\n[3/4] Generating 40 car agents...")
car_valid_stations = filter_valid_stations('car')
print(f"  Car-valid stations: {len(car_valid_stations)}/{len(STATIONS)}")

car_created = 0
car_skipped = 0

for i in range(40):
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        home_station = random.choice(car_valid_stations)
        work_station = random.choice(car_valid_stations)

        if is_valid_trip(home_station, work_station, 'car') and \
           get_station_distance_m(home_station, work_station) >= MIN_CAR_TRIP_DISTANCE_M:
            break
        attempts += 1

    if attempts < max_attempts:
        hour, minute = random.choice(PEAK_MORNING if i < 28 else OFF_PEAK_MORNING)
        xml_content += generate_car_agent(i + 51, home_station, work_station, hour, minute)
        xml_content += '\n'
        car_created += 1
    else:
        car_skipped += 1

print(f"  ✓ Created: {car_created}/40")
if car_skipped > 0:
    print(f"  ⚠ Skipped: {car_skipped}")

# Generate 10 walk agents
print("\n[4/4] Generating 10 walk agents...")
walk_routes = [
    ('BL11', 'BL12'), ('G09', 'G10'), ('BL15', 'BL16'), ('G14', 'G15'),
    ('O05', 'O06'), ('BL12', 'BL13'), ('BL13', 'BL14'), ('BL14', 'BL15'),
    ('G15', 'G16'), ('O06', 'O07'),
]

walk_created = 0
walk_skipped = 0

for i in range(10):
    home_station, work_station = walk_routes[i]

    if is_valid_trip(home_station, work_station, 'walk'):
        hour, minute = random.choice(PEAK_MORNING + OFF_PEAK_MORNING)
        xml_content += generate_walk_agent(i + 91, home_station, work_station, hour, minute)
        xml_content += '\n'
        walk_created += 1
    else:
        walk_skipped += 1

print(f"  ✓ Created: {walk_created}/10")
if walk_skipped > 0:
    print(f"  ⚠ Skipped: {walk_skipped}")

xml_content += '</population>\n'

# Write to file
import os
output_file = os.getenv('POPULATION_OUTPUT_PATH', 'scenarios/corridor/taipei_test/test_population_100.xml')
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(xml_content)

# Summary
total_created = pt_single_created + pt_transfer_created + car_created + walk_created
total_skipped = pt_single_skipped + pt_transfer_skipped + car_skipped + walk_skipped

print("\n" + "=" * 70)
print("GENERATION COMPLETE")
print("=" * 70)
print(f"\n✓ Output: {output_file}")
print(f"\nAgent Summary:")
print(f"  PT single-line (PT-ONLY):  {pt_single_created}/20")
print(f"  PT transfer (PT-ONLY):     {pt_transfer_created}/30")
print(f"  Car agents:                 {car_created}/40")
print(f"  Walk agents:                {walk_created}/10")
print(f"  ────────────────────────────────")
print(f"  TOTAL:                      {total_created}/100")
print(f"  Skipped:                    {total_skipped}")

print(f"\nKey Features:")
print(f"  ✓ PT agents are PT-ONLY (no car availability)")
print(f"  ✓ {pt_transfer_created} transfer agents for SwissRailRaptor testing")
print(f"  ✓ Trip time limit: {MAX_TRIP_TIME_MINUTES} minutes")
print(f"\nNext Steps:")
print(f"  1. Verify config has: useIntermodalAccessEgress = false")
print(f"  2. Run simulation to validate transfers")
print(f"  3. Check events for PersonEntersVehicle (should see 2-4 per transfer agent)")
print("=" * 70)
