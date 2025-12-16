import xml.etree.ElementTree as ET
import json
import sqlite3
import os
import sys

def convert_osm_to_geojson(osm_file, output_file):
    print(f"Converting {osm_file} to {output_file}...")
    
    # 1. Setup SQLite for node cache (disk-based map)
    db_file = "nodes.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('CREATE TABLE nodes (id INTEGER PRIMARY KEY, lat REAL, lon REAL)')
    c.execute('PRAGMA synchronous = OFF') # Speed up
    c.execute('PRAGMA journal_mode = MEMORY')
    
    # Car tags
    car_highways = {
        'motorway', 'motorway_link', 
        'trunk', 'trunk_link', 
        'primary', 'primary_link', 
        'secondary', 'secondary_link', 
        'tertiary', 'tertiary_link', 
        'unclassified', 'residential', 'service'
    }

    print("Phase 1: Indexing nodes...")
    context = ET.iterparse(osm_file, events=('end',))
    nodes_batch = []
    
    count = 0
    for event, elem in context:
        if elem.tag == 'node':
            try:
                nid = int(elem.attrib['id'])
                lat = float(elem.attrib['lat'])
                lon = float(elem.attrib['lon'])
                nodes_batch.append((nid, lat, lon))
                
                if len(nodes_batch) >= 100000:
                    c.executemany('INSERT INTO nodes VALUES (?,?,?)', nodes_batch)
                    nodes_batch = []
                    conn.commit()
            except Exception:
                pass
            elem.clear()
            count += 1
            if count % 1000000 == 0:
                print(f"Indexed {count} nodes...")
                
    if nodes_batch:
        c.executemany('INSERT INTO nodes VALUES (?,?,?)', nodes_batch)
        conn.commit()
        
    print("Phase 1 Complete. Creating index...")
    # Index is implicitly created by PRIMARY KEY, but let's be sure
    # c.execute('CREATE INDEX idx_nodes_id ON nodes(id)') 
    
    print("Phase 2: Processing ways and writing GeoJSON...")
    
    features = []
    
    # Re-open file for ways
    context = ET.iterparse(osm_file, events=('end',))
    
    way_count = 0
    match_count = 0
    
    for event, elem in context:
        if elem.tag == 'way':
            tags = {tag.attrib['k']: tag.attrib['v'] for tag in elem.findall('tag')}
            
            if 'highway' in tags and tags['highway'] in car_highways:
                # Get node refs
                nd_refs = [int(nd.attrib['ref']) for nd in elem.findall('nd')]
                
                if len(nd_refs) > 1:
                    # Lookup coords
                    coords = []
                    valid = True
                    # Batch lookup is hard with sqlite here, doing simple loop for now
                    # For optimization, we could cache recent nodes or query in batch? 
                    # But distinct select is slow.
                    # Optimization: select * from nodes where id in (...)
                    
                    id_str = ",".join(map(str, nd_refs))
                    # This query might be too long for very long ways, but usually fine
                    try: 
                        c.execute(f'SELECT id, lat, lon FROM nodes WHERE id IN ({id_str})')
                        found_nodes = {row[0]: (row[2], row[1]) for row in c.fetchall()} # lon, lat
                        
                        line_coords = []
                        for ref in nd_refs:
                            if ref in found_nodes:
                                line_coords.append(found_nodes[ref])
                        
                        if len(line_coords) > 1:
                             feature = {
                                "type": "Feature",
                                "properties": tags,
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": line_coords
                                }
                            }
                             features.append(feature)
                             match_count += 1
                    except Exception as e:
                        print(f"Error processing way {elem.attrib.get('id')}: {e}")

            elem.clear()
            way_count += 1
            if way_count % 100000 == 0:
                 print(f"Processed {way_count} ways (found {match_count})...")
                 
    # Delete DB
    conn.close()
    if os.path.exists(db_file):
        os.remove(db_file)
        
    # Write GeoJSON
    print(f"Writing {len(features)} features to {output_file}...")
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_file, 'w') as f:
        json.dump(geojson, f)
        
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 osm_to_geojson.py <input.osm> <output.geojson>")
    else:
        convert_osm_to_geojson(sys.argv[1], sys.argv[2])
