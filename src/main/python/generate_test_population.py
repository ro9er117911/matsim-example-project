"""
Generate test population for MATSim with 50 agents:
- 30 PT agents using all metro lines (BL, G, O, R, BR)
- 15 car agents
- 5 walk agents
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
# OSM coverage area boundary (4 corners in TWD97 / EPSG:3826)
# This rectangular area covers the actual road network
# Taipei metro extends beyond this, so PT stations may be outside
OSM_BOUNDS = {
    'top_left': (288137, 2783823),     # 左上
    'bottom_left': (287627, 2768820),  # 左下
    'bottom_right': (314701, 2769311), # 右下
    'top_right': (314401, 2784363),    # 右上
}

# City center reference point (for prioritizing agent placement)
CITY_CENTER = (302416, 2770714)

# Trip constraints
MAX_TRIP_TIME_MINUTES = 40  # Maximum allowed one-way trip time
CITY_CENTER_PRIORITY_RADIUS_M = 5000  # 5km around city center

# Mode-specific travel time parameters (for validation, in m/min)
# Speeds are in meters per minute for consistency
MODE_SPEEDS_M_PER_MIN = {
    'pt': 500,     # PT average speed ~30 km/h (~500 m/min, includes stops)
    'car': 417,    # Car average speed ~25 km/h in Taipei traffic (~417 m/min)
    'walk': 84,    # Walking speed 1.4 m/s = 84 m/min
}

# ========== VALIDATION FUNCTIONS ==========

def is_within_osm_bounds(x, y):
    """Check if coordinates are within OSM network bounds.

    The OSM bounds define a rectangle. A point is inside if:
    - x is between min and max x values of the bounds
    - y is between min and max y values of the bounds
    """
    xs = [OSM_BOUNDS[k][0] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]
    ys = [OSM_BOUNDS[k][1] for k in ['top_left', 'bottom_left', 'bottom_right', 'top_right']]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    return x_min <= x <= x_max and y_min <= y <= y_max


def euclidean_distance_m(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points in meters.

    Works with TWD97/EPSG:3826 projected coordinates (meter-based).
    """
    import math
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def get_station_distance_m(station1_id, station2_id):
    """Get Euclidean distance between two stations in meters."""
    _, x1, y1 = STATIONS[station1_id]
    _, x2, y2 = STATIONS[station2_id]
    return euclidean_distance_m(x1, y1, x2, y2)


def estimate_trip_time_minutes(distance_m, mode):
    """Estimate one-way trip time based on distance and mode.

    Args:
        distance_m: Distance in meters (Euclidean)
        mode: 'pt', 'car', or 'walk'

    Returns:
        Estimated trip time in minutes
    """
    if mode not in MODE_SPEEDS_M_PER_MIN:
        raise ValueError(f"Unknown mode: {mode}")

    speed = MODE_SPEEDS_M_PER_MIN[mode]
    base_time = distance_m / speed

    # Add overhead time for mode-specific activities
    if mode == 'pt':
        base_time += 5  # 5 minutes waiting for PT
    elif mode == 'car':
        base_time += 2  # 2 minutes for parking/entering
    # walk has no additional overhead

    return base_time


def is_valid_trip(home_station_id, work_station_id, mode):
    """Check if a trip is valid based on spatial and temporal constraints.

    Args:
        home_station_id: Station ID for home
        work_station_id: Station ID for work
        mode: 'pt', 'car', or 'walk'

    Returns:
        True if trip is valid, False otherwise
    """
    # Basic check
    if home_station_id == work_station_id:
        return False

    # Get station coordinates
    _, home_x, home_y = STATIONS[home_station_id]
    _, work_x, work_y = STATIONS[work_station_id]

    # Check: Car agents must have both home and work within OSM bounds
    if mode == 'car':
        if not is_within_osm_bounds(home_x, home_y):
            return False
        if not is_within_osm_bounds(work_x, work_y):
            return False

    # Check: Trip time must be within MAX_TRIP_TIME_MINUTES
    distance_m = get_station_distance_m(home_station_id, work_station_id)
    estimated_time = estimate_trip_time_minutes(distance_m, mode)

    if estimated_time > MAX_TRIP_TIME_MINUTES:
        return False

    return True


def get_proximity_score(station_id):
    """Get a score for how close a station is to city center (0-1).

    Closer to city center = higher score.
    Used to prioritize station selection near city center.
    """
    _, x, y = STATIONS[station_id]
    dist_to_center = euclidean_distance_m(x, y, CITY_CENTER[0], CITY_CENTER[1])

    # Score: 1.0 at city center, 0.0 at priority radius boundary
    if dist_to_center <= CITY_CENTER_PRIORITY_RADIUS_M:
        return 1.0 - (dist_to_center / CITY_CENTER_PRIORITY_RADIUS_M)
    else:
        return max(0.0, 1.0 - (dist_to_center / (CITY_CENTER_PRIORITY_RADIUS_M * 2)))


def filter_valid_stations(mode):
    """Filter stations to only include valid ones for the given mode.

    For PT agents: accept all stations (can use virtual PT network outside OSM bounds).
    For car agents: only accept stations within OSM bounds.
    For walk agents: accept all (short distances).

    Returns:
        List of valid station IDs
    """
    valid_stations = []

    for station_id in STATIONS.keys():
        if mode == 'car':
            # Car agents: must be within OSM bounds
            _, x, y = STATIONS[station_id]
            if is_within_osm_bounds(x, y):
                valid_stations.append(station_id)
        else:
            # PT and walk: accept all (PT uses virtual network, walk is short distance)
            valid_stations.append(station_id)

    return valid_stations

# ========== PT TRANSFER SUPPORT ==========

# PT transfer stations: stations where line transfers are possible
PT_TRANSFER_STATIONS = {
    'BL12': ['G12'],      # 西門 - BL ↔ G transfer
    'BL14': ['O07'],      # 忠孝新生 - BL ↔ O transfer
    'G10': ['R08'],       # 中正紀念堂 - G ↔ R transfer
    'G14': ['R11'],       # 中山 - G ↔ R transfer
    'G15': ['O08'],       # 松江南京 - G ↔ O transfer
    'R05': ['BR09'],      # 大安 - R ↔ BR transfer
    'R07': ['O06'],       # 東門 - R ↔ O transfer
}

# PT transfer routes: (home_line1, transfer_line1, transfer_line2, work_line2)
# These create agents that need to transfer between metro lines
PT_TRANSFER_ROUTES = [
    ('BL02', 'BL12', 'G12', 'G19'),      # BL → G transfer
    ('BL06', 'BL12', 'G12', 'G14'),      # BL → G transfer
    ('G02', 'G10', 'R08', 'R28'),        # G → R transfer (淡水線)
    ('G05', 'G10', 'R08', 'R15'),        # G → R transfer
    ('O02', 'O07', 'BL14', 'BL22'),      # O → BL transfer
    ('O04', 'O08', 'G15', 'G19'),        # O → G transfer
    ('R02', 'R05', 'BR09', 'BR12'),      # R → BR transfer
    ('R03', 'R11', 'G14', 'G02'),        # R → G transfer
    ('BR03', 'BR10', 'BL15', 'BL16'),    # BR → BL transfer
    ('BR05', 'BR11', 'G16', 'G19'),      # BR → G transfer
]

# Car trip validation constraints
MIN_CAR_TRIP_DISTANCE_M = 1000      # Car trips should be >1km (not too short)
MAX_WALK_TRIP_DISTANCE_M = 2000     # Walk trips should be <2km
MAX_WALK_DURATION_MIN = 30          # Car agents shouldn't have walk leg > 30 min

# ========== END PT TRANSFER SUPPORT ==========


# Define route pairs for PT agents (home -> work)
PT_ROUTES = [
    # BL Line routes
    ('BL02', 'BL14'),  # 永寧 -> 忠孝新生
    ('BL02', 'BL16'),  # 永寧 -> 忠孝敦化
    ('BL06', 'BL12'),  # 府中 -> 台北車站
    ('BL10', 'BL15'),  # 龍山寺 -> 忠孝復興
    ('BL11', 'BL19'),  # 西門 -> 永春
    ('BL13', 'BL22'),  # 善導寺 -> 南港

    # G Line routes
    ('G02', 'G14'),   # 新店區公所 -> 中山
    ('G05', 'G15'),   # 景美 -> 松江南京
    ('G07', 'G16'),   # 公館 -> 南京復興
    ('G08', 'G19'),   # 台電大樓 -> 松山
    ('G09', 'G12'),   # 古亭 -> 西門

    # O Line routes
    ('O02', 'O07'),   # 景安 -> 忠孝新生 (transfer point)
    ('O03', 'O08'),   # 永安市場 -> 松江南京 (transfer point)
    ('O04', 'O09'),   # 頂溪 -> 行天宮
    ('O05', 'O06'),   # 古亭 -> 東門

    # R Line routes
    ('R02', 'R10'),   # 象山 -> 台北車站 (transfer point)
    ('R03', 'R11'),   # 台北101 -> 中山 (transfer point)
    ('R05', 'R15'),   # 大安 -> 劍潭
    ('R07', 'R22'),   # 東門 -> 北投
    ('R08', 'R28'),   # 中正紀念堂 -> 淡水

    # BR Line routes
    ('BR03', 'BR10'), # 萬芳社區 -> 忠孝復興 (transfer point)
    ('BR05', 'BR11'), # 辛亥 -> 南京復興 (transfer point)
    ('BR07', 'BR12'), # 六張犁 -> 中山國中
    ('BR08', 'BR09'), # 科技大樓 -> 大安 (transfer point)

    # Cross-line routes using transfer stations
    ('BL02', 'G14'),  # BL -> G via 台北車站
    ('O02', 'BL15'),  # O -> BL via 忠孝新生
    ('R02', 'BL12'),  # R -> BL via transfer
    ('BR03', 'R05'),  # BR -> R via 大安
    ('G02', 'O08'),   # G -> O via transfer
]

def format_time(hour, minute):
    """Format time as HH:MM:SS"""
    return f"{hour:02d}:{minute:02d}:00"

def generate_pt_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a PT agent with home->work->home pattern"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    # Morning departure time
    morning_depart = format_time(departure_hour, departure_min)
    pt_wait = 5  # 5 min wait at station
    pt_travel = 28  # approximate travel time
    morning_arrive_hour = departure_hour
    morning_arrive_min = departure_min + pt_wait + pt_travel
    if morning_arrive_min >= 60:
        morning_arrive_hour += morning_arrive_min // 60
        morning_arrive_min = morning_arrive_min % 60

    # Work 8 hours
    evening_hour = morning_arrive_hour + 8
    evening_min = morning_arrive_min
    if evening_hour >= 24:
        evening_hour = 23
        evening_min = 59

    evening_depart = format_time(evening_hour, evening_min)

    xml = f'''	<!-- PT Agent {agent_id}: {home_station}({home_name}) -> {work_station}({work_name}) -->
	<person id="pt_agent_{agent_id:02d}">
		<plan selected="yes">
			<!-- Morning trip: home to work -->
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="walk" />
			<activity type="pt interaction" x="{home_x:.2f}" y="{home_y:.2f}" max_dur="00:05:00" />
			<leg mode="pt" />
			<activity type="pt interaction" x="{work_x:.2f}" y="{work_y:.2f}" max_dur="00:05:00" />
			<leg mode="walk" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<!-- Evening trip: work to home -->
			<leg mode="walk" />
			<activity type="pt interaction" x="{work_x:.2f}" y="{work_y:.2f}" max_dur="00:05:00" />
			<leg mode="pt" />
			<activity type="pt interaction" x="{home_x:.2f}" y="{home_y:.2f}" max_dur="00:05:00" />
			<leg mode="walk" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

def generate_transfer_pt_agent(agent_id, home_station, transfer_station_1, transfer_station_2, work_station, departure_hour, departure_min):
    """Generate a PT agent that transfers between two metro lines"""
    home_name, home_x, home_y = STATIONS[home_station]
    transfer1_name, transfer1_x, transfer1_y = STATIONS[transfer_station_1]
    transfer2_name, transfer2_x, transfer2_y = STATIONS[transfer_station_2]
    work_name, work_x, work_y = STATIONS[work_station]

    # Morning departure time
    morning_depart = format_time(departure_hour, departure_min)

    # Leg 1: home to first transfer station
    leg1_distance = euclidean_distance_m(home_x, home_y, transfer1_x, transfer1_y)
    leg1_travel = int(leg1_distance / MODE_SPEEDS_M_PER_MIN['pt'])  # minutes
    leg1_wait = 5  # 5 min wait for first PT

    # Transfer time at station (5 min walk + 3 min wait for next train)
    transfer_time = 8

    # Leg 2: second station to work
    leg2_distance = euclidean_distance_m(transfer2_x, transfer2_y, work_x, work_y)
    leg2_travel = int(leg2_distance / MODE_SPEEDS_M_PER_MIN['pt'])  # minutes
    leg2_wait = 5  # 5 min wait for second PT

    # Calculate arrival time at work
    total_travel_min = leg1_wait + leg1_travel + transfer_time + leg2_wait + leg2_travel
    arrival_hour = departure_hour
    arrival_min = departure_min + total_travel_min
    if arrival_min >= 60:
        arrival_hour += arrival_min // 60
        arrival_min = arrival_min % 60

    # Work 8 hours
    evening_hour = arrival_hour + 8
    evening_min = arrival_min
    if evening_hour >= 24:
        evening_hour = 23
        evening_min = 59

    evening_depart = format_time(evening_hour, evening_min)

    xml = f'''	<!-- PT Transfer Agent {agent_id}: {home_station}({home_name}) -> {transfer_station_1}({transfer1_name}) -> {transfer_station_2}({transfer2_name}) -> {work_station}({work_name}) -->
	<person id="pt_transfer_agent_{agent_id:02d}">
		<plan selected="yes">
			<!-- Morning trip: home to work with transfer -->
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="walk" />
			<activity type="pt interaction" x="{home_x:.2f}" y="{home_y:.2f}" max_dur="00:05:00" />
			<!-- First PT leg: home to transfer station -->
			<leg mode="pt" />
			<activity type="pt interaction" x="{transfer1_x:.2f}" y="{transfer1_y:.2f}" max_dur="00:08:00" />
			<!-- Transfer: walk between stations -->
			<leg mode="walk" />
			<activity type="pt interaction" x="{transfer2_x:.2f}" y="{transfer2_y:.2f}" max_dur="00:05:00" />
			<!-- Second PT leg: transfer to work -->
			<leg mode="pt" />
			<activity type="pt interaction" x="{work_x:.2f}" y="{work_y:.2f}" max_dur="00:05:00" />
			<leg mode="walk" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<!-- Evening trip: work to home (reverse) -->
			<leg mode="walk" />
			<activity type="pt interaction" x="{work_x:.2f}" y="{work_y:.2f}" max_dur="00:05:00" />
			<leg mode="pt" />
			<activity type="pt interaction" x="{transfer2_x:.2f}" y="{transfer2_y:.2f}" max_dur="00:08:00" />
			<leg mode="walk" />
			<activity type="pt interaction" x="{transfer1_x:.2f}" y="{transfer1_y:.2f}" max_dur="00:05:00" />
			<leg mode="pt" />
			<activity type="pt interaction" x="{home_x:.2f}" y="{home_y:.2f}" max_dur="00:05:00" />
			<leg mode="walk" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

def is_valid_car_trip(home_station, work_station):
    """Check if a car trip meets minimum distance requirement"""
    distance_m = get_station_distance_m(home_station, work_station)
    return distance_m >= MIN_CAR_TRIP_DISTANCE_M

def generate_car_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a car agent"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    # Work 8 hours
    evening_hour = departure_hour + 8
    evening_min = departure_min + 15  # car travel time
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
			<!-- Morning trip: home to work -->
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="car" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<!-- Evening trip: work to home -->
			<leg mode="car" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

def generate_walk_agent(agent_id, home_station, work_station, departure_hour, departure_min):
    """Generate a walk agent for short distances"""
    home_name, home_x, home_y = STATIONS[home_station]
    work_name, work_x, work_y = STATIONS[work_station]

    morning_depart = format_time(departure_hour, departure_min)

    # Work 6 hours (shorter for walk)
    evening_hour = departure_hour + 6
    evening_min = departure_min + 30  # walk travel time
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
			<!-- Morning trip: home to work -->
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" end_time="{morning_depart}" />
			<leg mode="walk" />
			<activity type="work" x="{work_x:.2f}" y="{work_y:.2f}" end_time="{evening_depart}" />
			<!-- Evening trip: work to home -->
			<leg mode="walk" />
			<activity type="home" x="{home_x:.2f}" y="{home_y:.2f}" />
		</plan>
	</person>
'''
    return xml

# Time slots for peak and off-peak
PEAK_MORNING = [(6, 30), (7, 0), (7, 15), (7, 30), (7, 45), (8, 0)]
OFF_PEAK_MORNING = [(9, 0), (9, 30), (10, 0), (10, 30), (11, 0)]

# Generate XML
xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">
<population>
'''

# Generate 20 single-line PT agents
print("Generating 20 single-line PT agents...")
pt_agents_created = 0
pt_agents_skipped = 0
pt_skipped_list = []

for i in range(20):
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        if i < len(PT_ROUTES):
            home_station, work_station = PT_ROUTES[i]
        else:
            # Random route from available stations (all stations for PT)
            home_station = random.choice(list(STATIONS.keys()))
            work_station = random.choice(list(STATIONS.keys()))

        # Validate the trip
        if is_valid_trip(home_station, work_station, 'pt'):
            break
        attempts += 1

    if attempts >= max_attempts:
        # Trip validation failed
        pt_agents_skipped += 1
        pt_skipped_list.append(f"pt_agent_{i+1:02d}")
        print(f"  ⚠ Skipped pt_agent_{i+1:02d}: Could not find valid route")
        continue

    # Mix peak and off-peak
    if i < 15:  # 15 peak hour agents
        hour, minute = random.choice(PEAK_MORNING)
    else:  # 5 off-peak agents
        hour, minute = random.choice(OFF_PEAK_MORNING)

    distance_m = get_station_distance_m(home_station, work_station)
    trip_time = estimate_trip_time_minutes(distance_m, 'pt')

    xml_content += generate_pt_agent(i + 1, home_station, work_station, hour, minute)
    xml_content += '\n'
    pt_agents_created += 1

# Generate 10 PT transfer agents (multi-line routes)
print("Generating 10 PT transfer agents...")
pt_transfer_agents_created = 0
pt_transfer_agents_skipped = 0
pt_transfer_skipped_list = []

for i in range(10):
    if i < len(PT_TRANSFER_ROUTES):
        home_station, transfer_station_1, transfer_station_2, work_station = PT_TRANSFER_ROUTES[i]
    else:
        # If we run out of predefined routes, skip
        pt_transfer_agents_skipped += 1
        pt_transfer_skipped_list.append(f"pt_transfer_agent_{i+1:02d}")
        print(f"  ⚠ Skipped pt_transfer_agent_{i+1:02d}: No more predefined transfer routes")
        continue

    # Validate the transfer trip
    total_distance = (get_station_distance_m(home_station, transfer_station_1) +
                      get_station_distance_m(transfer_station_1, transfer_station_2) +
                      get_station_distance_m(transfer_station_2, work_station))
    total_time = estimate_trip_time_minutes(total_distance, 'pt') + 8  # Add 8 min for transfer wait

    if total_time > MAX_TRIP_TIME_MINUTES:
        pt_transfer_agents_skipped += 1
        pt_transfer_skipped_list.append(f"pt_transfer_agent_{i+1:02d}")
        print(f"  ⚠ Skipped pt_transfer_agent_{i+1:02d}: Trip exceeds {MAX_TRIP_TIME_MINUTES} minutes ({total_time:.1f} min)")
        continue

    # Mix peak and off-peak
    if i < 7:  # 7 peak hour agents
        hour, minute = random.choice(PEAK_MORNING)
    else:  # 3 off-peak agents
        hour, minute = random.choice(OFF_PEAK_MORNING)

    xml_content += generate_transfer_pt_agent(i + 1, home_station, transfer_station_1, transfer_station_2, work_station, hour, minute)
    xml_content += '\n'
    pt_transfer_agents_created += 1

# Generate 15 car agents
print("Generating 15 car agents...")
car_valid_stations = filter_valid_stations('car')
print(f"  Car-valid stations (within OSM bounds): {len(car_valid_stations)}/{len(STATIONS)}")
print(f"    Valid stations: {sorted(car_valid_stations)}")

car_agents_created = 0
car_agents_skipped = 0
car_skipped_list = []

for i in range(15):
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        # Car agents: only choose from stations within OSM bounds
        home_station = random.choice(car_valid_stations)
        work_station = random.choice(car_valid_stations)

        # Validate the trip: within bounds, valid distance, and minimum trip distance
        if is_valid_trip(home_station, work_station, 'car') and is_valid_car_trip(home_station, work_station):
            break
        attempts += 1

    if attempts >= max_attempts:
        # Trip validation failed
        car_agents_skipped += 1
        car_skipped_list.append(f"car_agent_{i+1:02d}")
        print(f"  ⚠ Skipped car_agent_{i+1:02d}: Could not find valid route within bounds (>1km)")
        continue

    # Mix peak and off-peak
    if i < 10:  # 10 peak hour agents
        hour, minute = random.choice(PEAK_MORNING)
    else:  # 5 off-peak agents
        hour, minute = random.choice(OFF_PEAK_MORNING)

    distance_m = get_station_distance_m(home_station, work_station)
    trip_time = estimate_trip_time_minutes(distance_m, 'car')

    xml_content += generate_car_agent(i + 1, home_station, work_station, hour, minute)
    xml_content += '\n'
    car_agents_created += 1

# Generate 5 walk agents (short distances)
print("Generating 5 walk agents...")
walk_agents_created = 0
walk_agents_skipped = 0
walk_skipped_list = []

walk_routes = [
    ('BL11', 'BL12'),  # 西門 -> 台北車站
    ('G09', 'G10'),    # 古亭 -> 中正紀念堂
    ('BL15', 'BL16'),  # 忠孝復興 -> 忠孝敦化
    ('G14', 'G15'),    # 中山 -> 松江南京
    ('O05', 'O06'),    # 古亭 -> 東門
]

for i in range(5):
    home_station, work_station = walk_routes[i]

    # Validate the trip
    if not is_valid_trip(home_station, work_station, 'walk'):
        walk_agents_skipped += 1
        walk_skipped_list.append(f"walk_agent_{i+1:02d}")
        print(f"  ⚠ Skipped walk_agent_{i+1:02d}: {home_station} -> {work_station} exceeds 40 min")
        continue

    hour, minute = random.choice(PEAK_MORNING + OFF_PEAK_MORNING)

    distance_m = get_station_distance_m(home_station, work_station)
    trip_time = estimate_trip_time_minutes(distance_m, 'walk')

    xml_content += generate_walk_agent(i + 1, home_station, work_station, hour, minute)
    xml_content += '\n'
    walk_agents_created += 1

xml_content += '</population>\n'

# Write to file - support custom output path via environment variable or use default
import os
output_file = os.getenv('POPULATION_OUTPUT_PATH', 'scenarios/corridor/taipei_test/test_population_50.xml')
# Create parent directories if they don't exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(xml_content)

# Calculate total agents
total_agents_created = pt_agents_created + pt_transfer_agents_created + car_agents_created + walk_agents_created
total_agents_skipped = pt_agents_skipped + pt_transfer_agents_skipped + car_agents_skipped + walk_agents_skipped

print(f"\n" + "=" * 70)
print(f"POPULATION GENERATION COMPLETE")
print(f"=" * 70)
print(f"\n✓ Output file: {output_file}")
print(f"\nAgent Generation Summary:")
print(f"  PT single-line agents:")
print(f"    - Created: {pt_agents_created}/20")
print(f"    - Skipped: {pt_agents_skipped}")
if pt_skipped_list:
    print(f"    - Skipped list: {', '.join(pt_skipped_list)}")

print(f"  PT transfer agents (multi-line):")
print(f"    - Created: {pt_transfer_agents_created}/10")
print(f"    - Skipped: {pt_transfer_agents_skipped}")
if pt_transfer_skipped_list:
    print(f"    - Skipped list: {', '.join(pt_transfer_skipped_list)}")

print(f"  Car agents:")
print(f"    - Created: {car_agents_created}/15")
print(f"    - Skipped: {car_agents_skipped}")
if car_skipped_list:
    print(f"    - Skipped list: {', '.join(car_skipped_list)}")
print(f"    - Valid stations used: {len(car_valid_stations)}/{len(STATIONS)}")

print(f"  Walk agents:")
print(f"    - Created: {walk_agents_created}/5")
print(f"    - Skipped: {walk_agents_skipped}")
if walk_skipped_list:
    print(f"    - Skipped list: {', '.join(walk_skipped_list)}")

print(f"\n  TOTAL AGENTS (Target: 50):")
print(f"    - PT single-line + PT transfer: {pt_agents_created + pt_transfer_agents_created}/30")
print(f"    - Car: {car_agents_created}/15")
print(f"    - Walk: {walk_agents_created}/5")
print(f"    - Created: {total_agents_created}/50")
print(f"    - Skipped: {total_agents_skipped}")

print(f"\nSpatial Constraints Applied:")
print(f"  - OSM bounds: ({OSM_BOUNDS['top_left']}) to ({OSM_BOUNDS['bottom_right']})")
print(f"  - Car agents: must be within OSM bounds (only used {len(car_valid_stations)} stations)")
print(f"  - PT agents: can use all stations (virtual network)")
print(f"  - Walk agents: all short-distance trips")

print(f"\nTemporal Constraints Applied:")
print(f"  - Maximum one-way trip time: {MAX_TRIP_TIME_MINUTES} minutes")
print(f"  - PT speed model: {MODE_SPEEDS_M_PER_MIN['pt']} m/min + 5min wait")
print(f"  - Car speed model: {MODE_SPEEDS_M_PER_MIN['car']} m/min + 2min overhead")
print(f"  - Walk speed model: {MODE_SPEEDS_M_PER_MIN['walk']} m/min")

print(f"\nLines covered:")
print(f"  - BL (板南線/Blue Line)")
print(f"  - G (松山新店線/Green Line)")
print(f"  - O (中和新蘆線/Orange Line)")
print(f"  - R (淡水信義線/Red Line)")
print(f"  - BR (文湖線/Brown Line)")

print(f"\nCity center priority: {CITY_CENTER}")
print(f"=" * 70)