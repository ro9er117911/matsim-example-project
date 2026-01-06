#!/usr/bin/env python3
"""
科學化 GTFS 裁剪腳本 - 災難撤離模擬專用

基於撤離區域空間分析，裁剪 GTFS 資料至有效服務範圍。
支援按經緯度邊界過濾站點，並保留相關路線、班次。

Usage:
    python clip_gtfs_scientific.py --input <gtfs_dir> --output <output_dir> --bounds "lon_min,lat_min,lon_max,lat_max"
    
Example:
    python clip_gtfs_scientific.py \
        --input 5000_disatar/01_raw_data/gtfs_original/bus_disaster_gtfs \
        --output 5000_disatar/01_raw_data/gtfs_clipped/bus_phase2 \
        --bounds "121.35,24.88,121.65,25.22"
"""

import argparse
import csv
import os
import shutil
from pathlib import Path
from typing import Set, Dict, List, Tuple


def parse_bounds(bounds_str: str) -> Tuple[float, float, float, float]:
    """解析邊界字串為 (lon_min, lat_min, lon_max, lat_max)"""
    parts = [float(x.strip()) for x in bounds_str.split(',')]
    if len(parts) != 4:
        raise ValueError("Bounds must be 4 comma-separated values: lon_min,lat_min,lon_max,lat_max")
    return tuple(parts)


def read_csv(filepath: Path) -> List[Dict[str, str]]:
    """讀取 CSV 檔案為字典列表"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv(filepath: Path, rows: List[Dict[str, str]], fieldnames: List[str] = None):
    """寫入 CSV 檔案"""
    if not rows:
        # 空檔案情況
        with open(filepath, 'w', encoding='utf-8') as f:
            if fieldnames:
                f.write(','.join(fieldnames) + '\n')
        return
    
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def filter_stops_by_bounds(
    stops: List[Dict[str, str]], 
    bounds: Tuple[float, float, float, float]
) -> Tuple[List[Dict[str, str]], Set[str]]:
    """
    按邊界過濾站點
    
    Returns:
        (filtered_stops, valid_stop_ids)
    """
    lon_min, lat_min, lon_max, lat_max = bounds
    filtered = []
    valid_ids = set()
    
    for stop in stops:
        try:
            lat = float(stop.get('stop_lat', 0))
            lon = float(stop.get('stop_lon', 0))
            
            if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
                filtered.append(stop)
                valid_ids.add(stop['stop_id'])
        except (ValueError, KeyError):
            continue
    
    return filtered, valid_ids


def filter_stop_times(
    stop_times: List[Dict[str, str]], 
    valid_stop_ids: Set[str]
) -> Tuple[List[Dict[str, str]], Set[str]]:
    """
    過濾 stop_times，保留有效站點的記錄
    
    Returns:
        (filtered_stop_times, valid_trip_ids)
    """
    filtered = []
    valid_trip_ids = set()
    
    for st in stop_times:
        if st.get('stop_id') in valid_stop_ids:
            filtered.append(st)
            valid_trip_ids.add(st.get('trip_id'))
    
    return filtered, valid_trip_ids


def filter_invalid_trips(
    stop_times: List[Dict[str, str]], 
    valid_trip_ids: Set[str]
) -> Tuple[List[Dict[str, str]], Set[str]]:
    """
    移除無效 Trip:
    1. 站點數量少於 2
    2. 首位或末位站點缺少時間 (arrival_time 或 departure_time)
    """
    from collections import defaultdict
    
    # 按 trip_id 分組並按 stop_sequence 排序
    trip_data = defaultdict(list)
    for st in stop_times:
        trip_data[st['trip_id']].append(st)
    
    final_trip_ids = set()
    final_stop_times = []
    
    removed_count_size = 0
    removed_count_time = 0
    
    for tid, st_list in trip_data.items():
        # 排序
        st_list.sort(key=lambda x: int(x['stop_sequence']))
        
        # 1. 檢查大小
        if len(st_list) < 2:
            removed_count_size += 1
            continue
            
        # 2. 檢查首尾時間
        first = st_list[0]
        last = st_list[-1]
        
        def has_time(st):
            t = st.get('arrival_time', '').strip()
            return t and t.lower() != 'nan'
            
        if not has_time(first) or not has_time(last):
            removed_count_time += 1
            continue
            
        # 通過驗證
        final_trip_ids.add(tid)
        final_stop_times.extend(st_list)
    
    print(f"  過濾無效 Trip:")
    print(f"    原始有效 Trip 數: {len(valid_trip_ids)}")
    print(f"    因站點數不足 (<2) 移除數: {removed_count_size}")
    print(f"    因首尾時間缺失移除數: {removed_count_time}")
    print(f"    修正後最終有效 Trip 數: {len(final_trip_ids)}")
    
    return final_stop_times, final_trip_ids


def filter_trips(
    trips: List[Dict[str, str]], 
    valid_trip_ids: Set[str]
) -> Tuple[List[Dict[str, str]], Set[str]]:
    """
    過濾 trips，保留有效 trip
    
    Returns:
        (filtered_trips, valid_route_ids)
    """
    filtered = []
    valid_route_ids = set()
    
    for trip in trips:
        if trip.get('trip_id') in valid_trip_ids:
            filtered.append(trip)
            valid_route_ids.add(trip.get('route_id'))
    
    return filtered, valid_route_ids


def filter_routes(
    routes: List[Dict[str, str]], 
    valid_route_ids: Set[str]
) -> List[Dict[str, str]]:
    """過濾 routes，保留有效路線"""
    return [r for r in routes if r.get('route_id') in valid_route_ids]


def filter_calendar(
    calendar: List[Dict[str, str]], 
    valid_service_ids: Set[str]
) -> List[Dict[str, str]]:
    """過濾 calendar，保留有效服務"""
    return [c for c in calendar if c.get('service_id') in valid_service_ids]


def filter_calendar_dates(
    calendar_dates: List[Dict[str, str]], 
    valid_service_ids: Set[str]
) -> List[Dict[str, str]]:
    """過濾 calendar_dates，保留有效服務"""
    return [c for c in calendar_dates if c.get('service_id') in valid_service_ids]


def get_service_ids_from_trips(trips: List[Dict[str, str]]) -> Set[str]:
    """從 trips 中提取 service_ids"""
    return {t.get('service_id') for t in trips if t.get('service_id')}


def filter_agency(
    agency: List[Dict[str, str]], 
    routes: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """過濾 agency，保留有路線的機構"""
    valid_agency_ids = {r.get('agency_id') for r in routes if r.get('agency_id')}
    if not valid_agency_ids:
        return agency  # 如果沒有 agency_id 欄位，保留全部
    return [a for a in agency if a.get('agency_id') in valid_agency_ids]


def clip_gtfs(input_dir: Path, output_dir: Path, bounds: Tuple[float, float, float, float]):
    """主裁剪函數"""
    
    print(f"=== GTFS 科學化裁剪工具 ===")
    print(f"輸入路徑: {input_dir}")
    print(f"輸出路徑: {output_dir}")
    print(f"裁剪邊界: lon=[{bounds[0]}, {bounds[2]}], lat=[{bounds[1]}, {bounds[3]}]")
    print()
    
    # 確保輸出目錄存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 讀取並過濾 stops
    print("步驟 1/7: 讀取並過濾站點...")
    stops = read_csv(input_dir / 'stops.txt')
    print(f"  原始站點數: {len(stops)}")
    
    filtered_stops, valid_stop_ids = filter_stops_by_bounds(stops, bounds)
    print(f"  過濾後站點數: {len(filtered_stops)} ({len(filtered_stops)/len(stops)*100:.1f}%)")
    
    # 2. 過濾 stop_times
    print("步驟 2/7: 過濾 stop_times...")
    stop_times = read_csv(input_dir / 'stop_times.txt')
    print(f"  原始記錄數: {len(stop_times)}")
    
    filtered_stop_times, valid_trip_ids = filter_stop_times(stop_times, valid_stop_ids)
    print(f"  過濾後記錄數: {len(filtered_stop_times)}")
    print(f"  初步有效 trip 數: {len(valid_trip_ids)}")
    
    # 2.5 移除少於 2 個站點的 Trip
    filtered_stop_times, valid_trip_ids = filter_invalid_trips(filtered_stop_times, valid_trip_ids)
    
    # 3. 過濾 trips
    print("步驟 3/7: 過濾 trips...")
    trips = read_csv(input_dir / 'trips.txt')
    print(f"  原始 trip 數: {len(trips)}")
    
    filtered_trips, valid_route_ids = filter_trips(trips, valid_trip_ids)
    print(f"  過濾後 trip 數: {len(filtered_trips)}")
    print(f"  有效 route 數: {len(valid_route_ids)}")
    
    # 4. 過濾 routes
    print("步驟 4/7: 過濾 routes...")
    routes = read_csv(input_dir / 'routes.txt')
    print(f"  原始 route 數: {len(routes)}")
    
    filtered_routes = filter_routes(routes, valid_route_ids)
    print(f"  過濾後 route 數: {len(filtered_routes)}")
    
    # 5. 過濾 calendar
    print("步驟 5/7: 過濾 calendar...")
    valid_service_ids = get_service_ids_from_trips(filtered_trips)
    
    calendar_path = input_dir / 'calendar.txt'
    if calendar_path.exists():
        calendar = read_csv(calendar_path)
        filtered_calendar = filter_calendar(calendar, valid_service_ids)
        print(f"  calendar: {len(calendar)} -> {len(filtered_calendar)}")
    else:
        filtered_calendar = []
        print("  calendar.txt 不存在，跳過")
    
    # 6. 過濾 calendar_dates
    print("步驟 6/7: 過濾 calendar_dates...")
    calendar_dates_path = input_dir / 'calendar_dates.txt'
    if calendar_dates_path.exists():
        calendar_dates = read_csv(calendar_dates_path)
        filtered_calendar_dates = filter_calendar_dates(calendar_dates, valid_service_ids)
        print(f"  calendar_dates: {len(calendar_dates)} -> {len(filtered_calendar_dates)}")
    else:
        filtered_calendar_dates = []
        print("  calendar_dates.txt 不存在，跳過")
    
    # 7. 過濾 agency
    print("步驟 7/7: 過濾 agency...")
    agency_path = input_dir / 'agency.txt'
    if agency_path.exists():
        agency = read_csv(agency_path)
        filtered_agency = filter_agency(agency, filtered_routes)
        print(f"  agency: {len(agency)} -> {len(filtered_agency)}")
    else:
        filtered_agency = []
        print("  agency.txt 不存在，跳過")
    
    # 寫入輸出檔案
    print()
    print("寫入輸出檔案...")
    
    write_csv(output_dir / 'stops.txt', filtered_stops)
    write_csv(output_dir / 'stop_times.txt', filtered_stop_times)
    write_csv(output_dir / 'trips.txt', filtered_trips)
    write_csv(output_dir / 'routes.txt', filtered_routes)
    
    if filtered_calendar:
        write_csv(output_dir / 'calendar.txt', filtered_calendar)
    if filtered_calendar_dates:
        write_csv(output_dir / 'calendar_dates.txt', filtered_calendar_dates)
    if filtered_agency:
        write_csv(output_dir / 'agency.txt', filtered_agency)
    
    # 複製其他必要檔案
    optional_files = ['feed_info.txt', 'shapes.txt', 'frequencies.txt', 'transfers.txt']
    for fname in optional_files:
        src = input_dir / fname
        if src.exists():
            shutil.copy(src, output_dir / fname)
            print(f"  複製 {fname}")
    
    print()
    print("=== 裁剪完成 ===")
    print(f"結果已寫入: {output_dir}")
    print()
    print("摘要:")
    print(f"  站點: {len(stops)} -> {len(filtered_stops)}")
    print(f"  路線: {len(routes)} -> {len(filtered_routes)}")
    print(f"  班次: {len(trips)} -> {len(filtered_trips)}")


def main():
    parser = argparse.ArgumentParser(
        description='科學化 GTFS 裁剪工具 - 災難撤離模擬專用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--input', '-i', required=True, 
                        help='輸入 GTFS 目錄路徑')
    parser.add_argument('--output', '-o', required=True, 
                        help='輸出 GTFS 目錄路徑')
    parser.add_argument('--bounds', '-b', required=True,
                        help='裁剪邊界 (WGS84): lon_min,lat_min,lon_max,lat_max')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    bounds = parse_bounds(args.bounds)
    
    if not input_dir.exists():
        print(f"錯誤: 輸入路徑不存在: {input_dir}")
        return 1
    
    if not (input_dir / 'stops.txt').exists():
        print(f"錯誤: 找不到 stops.txt，請確認輸入路徑是有效的 GTFS 目錄")
        return 1
    
    clip_gtfs(input_dir, output_dir, bounds)
    return 0


if __name__ == '__main__':
    exit(main())
