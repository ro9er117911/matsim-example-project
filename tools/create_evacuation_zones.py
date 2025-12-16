#!/usr/bin/env python3
"""
Create evacuation scenario: Tamsui (淡水) → Wenshan (文山區)

Scenario:
- Disaster Zone: Tamsui District (淡水區), New Taipei City
- Safe Zone: Wenshan District (文山區), Taipei City
- Population: 5000 agents (2.5% of 220,000 total)
- Mode Split: 70% car, 30% PT (metro + walk)
- Structure prepared for future within-day replanning module
"""

import os
import sys
import random
import xml.etree.ElementTree as ET
from xml.dom import minidom

try:
    import shapefile
except ImportError:
    os.system(f"{sys.executable} -m pip install pyshp")
    import shapefile

# ============================================================
# COORDINATE DEFINITIONS (EPSG:3826 - TWD97 / TM2 zone 121)
# ============================================================

# Tamsui District (淡水區) - DISASTER ZONE
# Lat: 25.17, Lon: 121.44 → approx X=269000, Y=2786000
TAMSUI_ZONE = {
    'name': 'Tamsui District - Disaster Zone',
    'name_zh': '淡水區 - 災難區域',
    'min_x': 265000,
    'max_x': 280000,
    'min_y': 2780000,
    'max_y': 2798000,
    'center_x': 272500,
    'center_y': 2789000
}

# Wenshan District (文山區) - SAFE ZONE
# Lat: 24.99, Lon: 121.57 → approx X=303000, Y=2766000
WENSHAN_ZONE = {
    'name': 'Wenshan District - Safe Zone',
    'name_zh': '文山區 - 安全區域',
    'min_x': 299000,
    'max_x': 310000,
    'min_y': 2758000,
    'max_y': 2775000,
    'center_x': 304500,
    'center_y': 2766500
}

# ============================================================
# SCENARIO PARAMETERS
# ============================================================

SCENARIO = {
    'total_population': 220000,
    'sample_size': 5000,
    'sample_rate': 5000 / 220000,  # ~2.27%
    'mode_split': {
        'car': 0.70,  # 70% car
        'pt': 0.30    # 30% PT (metro + walk)
    },
    'evacuation_start_time': '03:00:00',  # 3 AM
    'evacuation_window_hours': 3,  # 3 hour evacuation window
    # Placeholder for within-day module (not implemented yet)
    'within_day': {
        'enabled': False,
        'disaster_alert_time': '03:30:00',  # When disaster alert triggers
        'replanning_interval': 300,  # seconds
        'affected_link_ids': []  # To be filled with damaged links
    }
}

# PRJ content for EPSG:3826
PRJ_CONTENT = '''PROJCS["TWD97 / TM2 zone 121",GEOGCS["TWD97",DATUM["Taiwan_Datum_1997",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","1026"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","3824"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",121],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",250000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3826"]]'''


def create_zone_shapefile(zone_data, output_path, zone_type):
    """Create polygon shapefile for zone."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    w = shapefile.Writer(output_path)
    w.field('NAME', 'C', 100)
    w.field('NAME_ZH', 'C', 100)
    w.field('ZONE_TYPE', 'C', 20)
    w.field('CENTER_X', 'N', decimal=2)
    w.field('CENTER_Y', 'N', decimal=2)
    
    min_x, max_x = zone_data['min_x'], zone_data['max_x']
    min_y, max_y = zone_data['min_y'], zone_data['max_y']
    
    w.poly([[
        [min_x, min_y], [max_x, min_y],
        [max_x, max_y], [min_x, max_y], [min_x, min_y]
    ]])
    
    w.record(zone_data['name'], zone_data['name_zh'], zone_type,
             zone_data['center_x'], zone_data['center_y'])
    w.close()
    
    with open(output_path + '.prj', 'w') as f:
        f.write(PRJ_CONTENT)
    
    print(f"✓ 已建立 {zone_type} shapefile: {os.path.basename(output_path)}.shp")


def create_evacuation_population(output_path, num_agents=5000):
    """Create evacuation population XML with mode split."""
    
    root = ET.Element('population')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    
    car_count = int(num_agents * SCENARIO['mode_split']['car'])
    pt_count = num_agents - car_count
    
    for i in range(num_agents):
        person = ET.SubElement(root, 'person')
        person.set('id', str(i + 1))
        
        plan = ET.SubElement(person, 'plan')
        plan.set('selected', 'yes')
        
        # Random home location in Tamsui
        home_x = random.uniform(TAMSUI_ZONE['min_x'], TAMSUI_ZONE['max_x'])
        home_y = random.uniform(TAMSUI_ZONE['min_y'], TAMSUI_ZONE['max_y'])
        
        # Random safe location in Wenshan
        safe_x = random.uniform(WENSHAN_ZONE['min_x'], WENSHAN_ZONE['max_x'])
        safe_y = random.uniform(WENSHAN_ZONE['min_y'], WENSHAN_ZONE['max_y'])
        
        # Random departure time within evacuation window
        base_hour = 3  # 03:00
        delta_seconds = random.randint(0, SCENARIO['evacuation_window_hours'] * 3600)
        hours = base_hour + delta_seconds // 3600
        minutes = (delta_seconds % 3600) // 60
        seconds = delta_seconds % 60
        end_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Home activity
        home = ET.SubElement(plan, 'activity')
        home.set('type', 'home')
        home.set('x', f"{home_x:.2f}")
        home.set('y', f"{home_y:.2f}")
        home.set('end_time', end_time)
        
        # Leg with mode split
        leg = ET.SubElement(plan, 'leg')
        if i < car_count:
            leg.set('mode', 'car')
        else:
            leg.set('mode', 'pt')
        
        # Evacuation destination
        evac = ET.SubElement(plan, 'activity')
        evac.set('type', 'evacuation')
        evac.set('x', f"{safe_x:.2f}")
        evac.set('y', f"{safe_y:.2f}")
    
    # Pretty print XML
    rough_string = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(rough_string)
    pretty_xml = dom.toprettyxml(indent="\t")
    
    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n')
        f.write('\n'.join(pretty_xml.split('\n')[1:]))  # Skip xml declaration
    
    print(f"✓ 已建立人口檔案: {os.path.basename(output_path)}")
    print(f"  - 總人數: {num_agents}")
    print(f"  - 汽車: {car_count} ({car_count/num_agents*100:.0f}%)")
    print(f"  - 捷運+步行: {pt_count} ({pt_count/num_agents*100:.0f}%)")


def create_within_day_placeholder(output_dir):
    """Create placeholder structure for within-day module."""
    
    module_dir = os.path.join(output_dir, 'within_day_module')
    os.makedirs(module_dir, exist_ok=True)
    
    # Create placeholder README
    readme_content = """# Within-Day Replanning Module (待實作)

## 目的
此模組將實作災難發生時的動態路線重規劃功能。

## 預計功能
1. 災難警報觸發器 (DisasterAlertListener)
2. 疏散計畫修改器 (EvacuationPlanModifier)
3. 動態路線計算 (TripRouter integration)
4. 受損路段管理 (NetworkChangeEvents)

## 使用方式
```java
// 未來實作
Controler controler = ...;
controler.addOverridingModule(new EvacuationWithinDayModule());
```

## 參考
- matsim-code-examples/withinday
- docs/evacuation.md (文件 3)
"""
    
    with open(os.path.join(module_dir, 'README.md'), 'w') as f:
        f.write(readme_content)
    
    # Create placeholder Java structure hint
    java_structure = """# 預計 Java 類別結構

```
src/main/java/org/matsim/project/evacuation/
├── RunEvacuationSimulation.java      # 主入口
├── EvacuationWithinDayModule.java    # Guice 模組
├── DisasterAlertListener.java        # MobsimBeforeSimStepListener
├── EvacuationPlanModifier.java       # 計畫修改邏輯
├── SafeZoneManager.java              # 安全區域管理
└── NetworkDamageManager.java         # 路網損壞管理
```
"""
    
    with open(os.path.join(module_dir, 'JAVA_STRUCTURE.md'), 'w') as f:
        f.write(java_structure)
    
    print(f"✓ 已建立 within-day 模組預留結構: {module_dir}/")


def main():
    output_dir = "5000_disatar/03_phase2_production"
    
    print("=" * 60)
    print("淡水 → 文山區 疏散場景")
    print("Tamsui → Wenshan Evacuation Scenario")
    print("=" * 60)
    
    print(f"\n【場景參數】")
    print(f"  總人口: {SCENARIO['total_population']:,}")
    print(f"  樣本數: {SCENARIO['sample_size']:,} ({SCENARIO['sample_rate']*100:.2f}%)")
    print(f"  汽車比例: {SCENARIO['mode_split']['car']*100:.0f}%")
    print(f"  捷運+步行: {SCENARIO['mode_split']['pt']*100:.0f}%")
    
    print(f"\n【災難區域 - 淡水區】")
    print(f"  X: {TAMSUI_ZONE['min_x']:,} - {TAMSUI_ZONE['max_x']:,}")
    print(f"  Y: {TAMSUI_ZONE['min_y']:,} - {TAMSUI_ZONE['max_y']:,}")
    
    print(f"\n【安全區域 - 文山區】")
    print(f"  X: {WENSHAN_ZONE['min_x']:,} - {WENSHAN_ZONE['max_x']:,}")
    print(f"  Y: {WENSHAN_ZONE['min_y']:,} - {WENSHAN_ZONE['max_y']:,}")
    
    # Calculate evacuation distance
    distance = ((WENSHAN_ZONE['center_x'] - TAMSUI_ZONE['center_x'])**2 + 
                (WENSHAN_ZONE['center_y'] - TAMSUI_ZONE['center_y'])**2)**0.5 / 1000
    print(f"\n【疏散距離】約 {distance:.1f} 公里")
    
    print("\n" + "-" * 60)
    print("建立 Shapefile...")
    
    # Create zone shapefiles
    shp_dir = os.path.join(output_dir, "evacuation_shp_tamsui")
    create_zone_shapefile(TAMSUI_ZONE, os.path.join(shp_dir, "disaster_zone_tamsui"), "disaster")
    create_zone_shapefile(WENSHAN_ZONE, os.path.join(shp_dir, "safe_zone_wenshan"), "safe")
    
    print("\n" + "-" * 60)
    print("建立人口檔案...")
    
    # Create population
    pop_dir = os.path.join(output_dir, "population")
    create_evacuation_population(
        os.path.join(pop_dir, "evacuation_tamsui_5000.xml"),
        SCENARIO['sample_size']
    )
    
    print("\n" + "-" * 60)
    print("建立 within-day 模組預留結構...")
    
    # Create within-day placeholder
    create_within_day_placeholder(output_dir)
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    
    print(f"\n【輸出檔案】")
    print(f"  📁 {shp_dir}/")
    print(f"     - disaster_zone_tamsui.shp (淡水災難區域)")
    print(f"     - safe_zone_wenshan.shp (文山安全區域)")
    print(f"  📁 {pop_dir}/")
    print(f"     - evacuation_tamsui_5000.xml (5000人口)")
    print(f"  📁 {output_dir}/within_day_module/")
    print(f"     - README.md (模組說明)")
    print(f"     - JAVA_STRUCTURE.md (預計類別結構)")


if __name__ == "__main__":
    main()
