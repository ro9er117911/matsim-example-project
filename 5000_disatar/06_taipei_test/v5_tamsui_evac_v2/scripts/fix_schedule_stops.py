import gzip
import xml.etree.ElementTree as ET
import sys
import os

def fix_schedule_stops(input_file, output_file):
    print(f"Reading schedule {input_file}...")
    
    # We use a standard ElementTree here because the schedule file 
    # (while large) is usually manageable (~200MB unzipped).
    # If it fails, we'd need a more complex streaming re-orderer.
    
    try:
        with gzip.open(input_file, 'rb') as f:
            tree = ET.parse(f)
        root = tree.getroot()
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return

    count_corrected_routes = 0
    count_total_routes = 0

    # MATSim schedule XML structure: 
    # <transitSchedule>
    #   <transitLine id="...">
    #     <transitRoute id="...">
    #       <routeProfile>
    #         <stop refId="..." ... />
    #       </routeProfile>
    #       <route>
    #         <link refId="..." />
    #       </route>
    #     </transitRoute>
    #   </transitLine>
    # </transitSchedule>

    for t_line in root.findall('.//transitLine'):
        for t_route in t_line.findall('transitRoute'):
            count_total_routes += 1
            
            # 1. Get the link sequence for this route
            route_elem = t_route.find('route')
            if route_elem is None:
                continue
            
            links = [l.get('refId') for l in route_elem.findall('link')]
            link_to_index = {link_id: i for i, link_id in enumerate(links)}
            
            # 2. Get the stops
            profile_elem = t_route.find('routeProfile')
            if profile_elem is None:
                continue
            
            stops = profile_elem.findall('stop')
            if not stops:
                continue
            
            # 3. Associate each stop with its index in the link list
            # Note: refId of stop usually looks like "stopId.link:linkId" or just "stopId"
            # In our mapped file, it seems to be "stopId.link:linkId"
            
            stop_data = []
            for stop in stops:
                ref_id = stop.get('refId')
                link_id = None
                
                if '.link:' in ref_id:
                    link_id = ref_id.split('.link:')[1]
                
                # If we don't have the link ID in the refId, we might need stopFacilities
                # but in our case, the mapper uses the composite ID.
                
                index = link_to_index.get(link_id, -1)
                stop_data.append((stop, index))
            
            # 4. Check if re-ordering is needed
            # We want indices to be non-decreasing (except for stops on unknown links, which we keep in place)
            
            needs_reorder = False
            last_idx = -1
            for _, idx in stop_data:
                if idx != -1:
                    if idx < last_idx:
                        needs_reorder = True
                        break
                    last_idx = idx
            
            if needs_reorder:
                # Re-order stops based on link index
                # We use a stable sort to keep stops on the same link in their original relative order
                stop_data.sort(key=lambda x: x[1] if x[1] != -1 else 999999)
                
                # Update the XML
                # Remove all stops
                for stop in stops:
                    profile_elem.remove(stop)
                
                # Add them back in sorted order
                for sorted_stop, _ in stop_data:
                    profile_elem.append(sorted_stop)
                
                count_corrected_routes += 1

    print(f"Total Routes: {count_total_routes}")
    print(f"Corrected Routes: {count_corrected_routes}")
    
    print(f"Writing fixed schedule to {output_file}...")
    with gzip.open(output_file, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_schedule_stops.py <input_schedule.xml.gz> <output_schedule.xml.gz>")
    else:
        fix_schedule_stops(sys.argv[1], sys.argv[2])
