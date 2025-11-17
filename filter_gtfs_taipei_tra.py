#!/usr/bin/env python3
"""
TRA Railway Filter Script (Step 1 of 3)

從全台灣 GTFS 提取台北市內的台鐵線路
策略: 只保留起點和終點都在台北市內的短途區間車
"""

import pandas as pd
import re
from pathlib import Path

# 台北市內台鐵車站清單
TAIPEI_STATIONS = ['基隆', '七堵', '南港', '松山', '臺北', '萬華', '板橋', '樹林', '鶯歌']

# 路徑配置
BASE_DIR = Path(__file__).parent
GTFS_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_tw_v5'
OUTPUT_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_taipei_tra'

def ensure_output_dir():
    """確保輸出目錄存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ 輸出目錄已準備: {OUTPUT_DIR}\n")

def step1_extract_tra_routes():
    """
    Step 1.1 + 1.2: 從 routes.txt 提取所有 TRA 路線並篩選台北市內線路
    """
    print("=" * 70)
    print("Step 1: 提取 TRA 台鐵線路")
    print("=" * 70)

    print("\n[1.1] 從 routes.txt 載入所有 TRA 路線...", end=" ")
    routes = pd.read_csv(GTFS_DIR / 'routes.txt', dtype=str)
    tra_routes = routes[routes['agency_id'] == 'TRA'].copy()
    print(f"✓ ({len(tra_routes)} 條)")

    print("\n[1.2] 篩選台北市內線路 (起點和終點都在台北市內)...\n")

    # 建立正則表達式，匹配起點和終點都在台北市內的路線
    stations_pattern = '|'.join(TAIPEI_STATIONS)
    pattern = f"^({stations_pattern})-({stations_pattern})$"

    # 篩選符合條件的路線
    taipei_tra_routes = tra_routes[
        tra_routes['route_long_name'].str.match(pattern, na=False)
    ].copy()

    print(f"  篩選結果:")
    print(f"    原始 TRA 路線數: {len(tra_routes)}")
    print(f"    台北市內線路數: {len(taipei_tra_routes)}")
    print(f"    過濾比例: {len(taipei_tra_routes)/len(tra_routes)*100:.1f}%\n")

    # 統計各起訖點組合
    print(f"  台北市內線路統計 (按起終點車站):\n")
    route_summary = taipei_tra_routes.groupby('route_long_name').size().sort_values(ascending=False)

    for route_name, count in route_summary.items():
        print(f"    {route_name:20} : {count:3} 條路線")

    return taipei_tra_routes

def step2_get_trips_and_stops(taipei_tra_routes):
    """
    Step 1.3: 從 trips.txt 找出這些路線的 trips 並驗證
    """
    print("\n" + "=" * 70)
    print("Step 2: 驗證路線和 Trips")
    print("=" * 70)

    route_ids = set(taipei_tra_routes['route_id'].unique())

    print(f"\n[2.1] 從 trips.txt 載入 TRA trips...", end=" ")
    trips = pd.read_csv(GTFS_DIR / 'trips.txt', dtype=str)
    tra_trips = trips[trips['agency_id'] == 'TRA'].copy() if 'agency_id' in trips.columns else \
                trips[trips['route_id'].str.startswith('TRA_', na=False)].copy()
    print(f"✓ ({len(tra_trips)} 條)")

    print(f"[2.2] 篩選台北市內路線的 trips...", end=" ")
    taipei_trips = tra_trips[tra_trips['route_id'].isin(route_ids)].copy()
    print(f"✓ ({len(taipei_trips)} 條)")

    # 統計每條路線的 trips 數
    print(f"\n[2.3] 每條台北市內路線的 trips 數:\n")
    trips_per_route = taipei_trips.groupby('route_id').size()

    for route_id in sorted(taipei_tra_routes['route_id'].unique()):
        if route_id in trips_per_route.index:
            route_info = taipei_tra_routes[taipei_tra_routes['route_id'] == route_id].iloc[0]
            trip_count = trips_per_route[route_id]
            print(f"    {route_id:30} ({route_info['route_long_name']:20}) : {trip_count:3} trips")

    # 載入 stops 進行驗證
    print(f"\n[2.4] 從 stops.txt 載入 TRA 停靠站...", end=" ")
    stops = pd.read_csv(GTFS_DIR / 'stops.txt', dtype=str)
    tra_stops = stops[stops['stop_id'].str.startswith('TRA_', na=False)].copy()
    print(f"✓ ({len(tra_stops)} 個)")

    # 找出台北市內主要車站
    main_stations = ['台北車站', '臺北車站', '萬華車站', '松山車站', '南港車站', '基隆車站', '七堵車站']
    print(f"\n[2.5] 台北市內 TRA 主要車站:\n")

    for station_name in main_stations:
        station_match = tra_stops[tra_stops['stop_name'].str.contains(station_name, na=False)]
        if not station_match.empty:
            for _, station in station_match.iterrows():
                print(f"    {station['stop_id']:10} : {station['stop_name']:15} (緯{float(station['stop_lat']):7.4f}, 經{float(station['stop_lon']):8.4f})")

    return taipei_tra_routes, taipei_trips, tra_stops

def step3_summary(taipei_tra_routes, taipei_trips, tra_stops):
    """
    Step 1.4: 輸出統計信息
    """
    print("\n" + "=" * 70)
    print("Step 3: 總結統計")
    print("=" * 70)

    print(f"\n  台北市內 TRA 線路統計:")
    print(f"    路線數 (routes):     {len(taipei_tra_routes):,}")
    print(f"    行程數 (trips):      {len(taipei_trips):,}")
    print(f"    車站數 (stops):      {len(tra_stops):,}")

    # 統計 service_id
    service_ids = set(taipei_trips['service_id'].unique())
    print(f"    服務日期種類:        {len(service_ids):,}")

    print(f"\n  包含的路線:")
    for _, route in taipei_tra_routes.iterrows():
        print(f"    {route['route_id']:30} : {route['route_long_name']}")

    return taipei_tra_routes, taipei_trips, service_ids

def main():
    print("\n")
    ensure_output_dir()

    # Step 1.1 + 1.2: 提取 TRA 路線
    taipei_tra_routes = step1_extract_tra_routes()

    # Step 1.3: 驗證 trips 和 stops
    taipei_tra_routes, taipei_trips, tra_stops = step2_get_trips_and_stops(taipei_tra_routes)

    # Step 1.4: 輸出統計
    taipei_tra_routes, taipei_trips, service_ids = step3_summary(taipei_tra_routes, taipei_trips, tra_stops)

    print("\n" + "=" * 70)
    print("✓ Step 1 完成！")
    print("=" * 70)
    print("\n下一步: 執行 filter_gtfs_taipei_tra_full.py 生成完整的 TRA GTFS 子集")
    print("\n")

if __name__ == '__main__':
    main()
