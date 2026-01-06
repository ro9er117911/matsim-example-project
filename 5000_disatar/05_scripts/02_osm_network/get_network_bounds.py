import gzip
import xml.etree.ElementTree as ET

network_file = "/Users/ro9air/matsim-example-project/scenarios/corridor/500_300-618/network-with-pt-metro-v7-carscc.xml.gz"

min_x, max_x = float('inf'), float('-inf')
min_y, max_y = float('inf'), float('-inf')

with gzip.open(network_file, 'rb') as f:
    context = ET.iterparse(f, events=('start',))
    for event, elem in context:
        if elem.tag == 'node':
            x = float(elem.get('x'))
            y = float(elem.get('y'))
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            elem.clear()

print(f"Network Bounds: X[{min_x}, {max_x}] Y[{min_y}, {max_y}]")
