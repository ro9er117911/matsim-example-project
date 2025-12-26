#!/usr/bin/env python3
"""Write shapefile analysis to file"""
from dbfread import DBF

BASE = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map"
OUT = "/Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/chayi_map/analysis.txt"

with open(OUT, 'w', encoding='utf-8') as f:
    # Q_ROAD
    f.write("=== Q_ROAD (道路) ===\n")
    db = DBF(f'{BASE}/Q_ROAD.dbf', encoding='big5')
    f.write("Fields:\n")
    for field in db.fields:
        f.write(f"  {field.name}: type={field.type}, len={field.length}\n")
    f.write("\nSample records:\n")
    for i, rec in enumerate(db):
        if i >= 3: break
        f.write(str(dict(rec)) + "\n")
    
    # Q_RDNODE  
    f.write("\n\n=== Q_RDNODE (節點) ===\n")
    db2 = DBF(f'{BASE}/Q_RDNODE.dbf', encoding='big5')
    f.write("Fields:\n")
    for field in db2.fields:
        f.write(f"  {field.name}: type={field.type}, len={field.length}\n")
    f.write("\nSample records:\n")
    for i, rec in enumerate(db2):
        if i >= 3: break
        f.write(str(dict(rec)) + "\n")

print(f"Analysis written to {OUT}")
