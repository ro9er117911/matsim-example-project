import csv
from pathlib import Path

keywords = ['淡水客運', '指南客運', '淡水區公所', '臺北客運', '首都客運', '大都會客運', '三重客運']
agency_path = Path('5000_disatar/01_raw_data/gtfs_original/bus_disaster_gtfs/agency.txt')

print(f"Checking {agency_path}")
if not agency_path.exists():
    print("Agency file NOT found")
else:
    with open(agency_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        matches = []
        for row in reader:
            name = row.get('agency_name', '')
            if any(kw in name for kw in keywords):
                matches.append((name, row['agency_id']))
        
        print(f"Found {len(matches)} matches:")
        for m in matches:
            print(f"  {m[0]} -> {m[1]}")

# Try to write a file
with open('test_file_creation.txt', 'w') as f:
    f.write('success')
print("Attempted to write test_file_creation.txt")
