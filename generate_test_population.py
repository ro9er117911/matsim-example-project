#!/usr/bin/env python3
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

# Generate 30 PT agents
print("Generating 30 PT agents...")
for i in range(30):
    if i < len(PT_ROUTES):
        home_station, work_station = PT_ROUTES[i]
    else:
        # Random route from available stations
        home_station = random.choice(list(STATIONS.keys()))
        work_station = random.choice(list(STATIONS.keys()))
        while work_station == home_station:
            work_station = random.choice(list(STATIONS.keys()))

    # Mix peak and off-peak
    if i < 20:  # 20 peak hour agents
        hour, minute = random.choice(PEAK_MORNING)
    else:  # 10 off-peak agents
        hour, minute = random.choice(OFF_PEAK_MORNING)

    xml_content += generate_pt_agent(i + 1, home_station, work_station, hour, minute)
    xml_content += '\n'

# Generate 15 car agents
print("Generating 15 car agents...")
car_stations = list(STATIONS.keys())
for i in range(15):
    home_station = random.choice(car_stations)
    work_station = random.choice(car_stations)
    while work_station == home_station:
        work_station = random.choice(car_stations)

    # Mix peak and off-peak
    if i < 10:  # 10 peak hour agents
        hour, minute = random.choice(PEAK_MORNING)
    else:  # 5 off-peak agents
        hour, minute = random.choice(OFF_PEAK_MORNING)

    xml_content += generate_car_agent(i + 1, home_station, work_station, hour, minute)
    xml_content += '\n'

# Generate 5 walk agents (short distances)
print("Generating 5 walk agents...")
walk_routes = [
    ('BL11', 'BL12'),  # 西門 -> 台北車站
    ('G09', 'G10'),    # 古亭 -> 中正紀念堂
    ('BL15', 'BL16'),  # 忠孝復興 -> 忠孝敦化
    ('G14', 'G15'),    # 中山 -> 松江南京
    ('O05', 'O06'),    # 古亭 -> 東門
]

for i in range(5):
    home_station, work_station = walk_routes[i]
    hour, minute = random.choice(PEAK_MORNING + OFF_PEAK_MORNING)

    xml_content += generate_walk_agent(i + 1, home_station, work_station, hour, minute)
    xml_content += '\n'

xml_content += '</population>\n'

# Write to file
output_file = 'scenarios/corridor/taipei_test/test_population_50.xml'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(xml_content)

print(f"\n✓ Generated {output_file}")
print(f"  - 30 PT agents (20 peak, 10 off-peak)")
print(f"  - 15 car agents (10 peak, 5 off-peak)")
print(f"  - 5 walk agents")
print(f"  Total: 50 agents")
print(f"\nLines covered:")
print(f"  - BL (板南線/Blue Line)")
print(f"  - G (松山新店線/Green Line)")
print(f"  - O (中和新蘆線/Orange Line)")
print(f"  - R (淡水信義線/Red Line)")
print(f"  - BR (文湖線/Brown Line)")
print(f"\nTransfer stations included:")
print(f"  - BL02, G02, O02, R02, BR03")
