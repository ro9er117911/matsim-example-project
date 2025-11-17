#!/usr/bin/env python3
"""
TRA Railway Filter Script (Step 2 of 3)

生成台北市內 TRA 線路的完整 GTFS 子集
"""

import pandas as pd
from pathlib import Path

# 台北市內台鐵車站清單
TAIPEI_STATIONS = ['基隆', '七堵', '南港', '松山', '臺北', '萬華', '板橋', '樹林', '鶯歌']

# 路徑配置
BASE_DIR = Path(__file__).parent
GTFS_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_tw_v5'
OUTPUT_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_taipei_tra'

def step2_generate_tra_gtfs_subset():
    """
    Step 2: 生成台北市 TRA GTFS 子集
    """
    print("=" * 70)
    print("Step 2: 生成台北市 TRA GTFS 子集")
    print("=" * 70)

    # 1. 提取台北市內 TRA 路線
    print("\n[1/6] 提取台北市內 TRA 路線...")
    routes = pd.read_csv(GTFS_DIR / 'routes.txt', dtype=str)
    tra_routes = routes[routes['agency_id'] == 'TRA'].copy()

    stations_pattern = '|'.join(TAIPEI_STATIONS)
    pattern = f"^({stations_pattern})-({stations_pattern})$"
    taipei_tra_routes = tra_routes[
        tra_routes['route_long_name'].str.match(pattern, na=False)
    ].copy()

    route_ids = set(taipei_tra_routes['route_id'].unique())
    print(f"  台北市內 TRA 路線: {len(taipei_tra_routes)} 條")

    # 2. 過濾 trips.txt
    print("\n[2/6] 過濾 trips.txt...")
    trips = pd.read_csv(GTFS_DIR / 'trips.txt', dtype=str)
    tra_trips = trips[trips['route_id'].str.startswith('TRA_', na=False)].copy()
    taipei_trips = tra_trips[tra_trips['route_id'].isin(route_ids)].copy()
    print(f"  台北市內 TRA trips: {len(taipei_trips)} 個")

    trip_ids = set(taipei_trips['trip_id'].unique())
    service_ids = set(taipei_trips['service_id'].unique())

    # 3. 過濾 stops.txt
    print("\n[3/6] 過濾 stops.txt...")
    stops = pd.read_csv(GTFS_DIR / 'stops.txt', dtype=str)

    # 保留所有 TRA_* stops（因為我們不知道哪些會被使用，保留所有是安全的）
    taipei_stops = stops[stops['stop_id'].str.startswith('TRA_', na=False)].copy()
    print(f"  TRA 停靠站: {len(taipei_stops)} 個")

    # 4. 過濾 calendar.txt
    print("\n[4/6] 過濾 calendar.txt...")
    calendar = pd.read_csv(GTFS_DIR / 'calendar.txt', dtype=str)
    taipei_calendar = calendar[calendar['service_id'].isin(service_ids)].copy()
    print(f"  服務日期: {len(taipei_calendar)} 種")

    # 5. 過濾 calendar_dates.txt
    print("\n[5/6] 過濾 calendar_dates.txt...")
    calendar_dates = pd.read_csv(GTFS_DIR / 'calendar_dates.txt', dtype=str)
    taipei_calendar_dates = calendar_dates[
        calendar_dates['service_id'].isin(service_ids)
    ].copy()
    print(f"  例外日期: {len(taipei_calendar_dates)} 個")

    # 6. 過濾 agency.txt
    print("\n[6/6] 過濾 agency.txt...")
    agency = pd.read_csv(GTFS_DIR / 'agency.txt', dtype=str)
    taipei_agency = agency[agency['agency_id'] == 'TRA'].copy()
    print(f"  TRA 機構: {len(taipei_agency)} 家")

    # 保存所有檔案
    print("\n[保存] 將過濾後的檔案保存到輸出目錄...")
    taipei_agency.to_csv(OUTPUT_DIR / 'agency.txt', index=False)
    taipei_stops.to_csv(OUTPUT_DIR / 'stops.txt', index=False)
    taipei_tra_routes.to_csv(OUTPUT_DIR / 'routes.txt', index=False)
    taipei_trips.to_csv(OUTPUT_DIR / 'trips.txt', index=False)
    taipei_calendar.to_csv(OUTPUT_DIR / 'calendar.txt', index=False)
    if not taipei_calendar_dates.empty:
        taipei_calendar_dates.to_csv(OUTPUT_DIR / 'calendar_dates.txt', index=False)

    print("\n  agency.txt      ✓")
    print("  stops.txt       ✓")
    print("  routes.txt      ✓")
    print("  trips.txt       ✓")
    print("  calendar.txt    ✓")
    if not taipei_calendar_dates.empty:
        print("  calendar_dates.txt ✓")

    return taipei_tra_routes, taipei_stops, taipei_trips, taipei_calendar, taipei_calendar_dates, taipei_agency

def main():
    print("\n")

    # Step 2: 生成 TRA GTFS 子集
    taipei_tra_routes, taipei_stops, taipei_trips, taipei_calendar, taipei_calendar_dates, taipei_agency = \
        step2_generate_tra_gtfs_subset()

    # 統計輸出
    print("\n" + "=" * 70)
    print("✓ Step 2 完成！統計信息：")
    print("=" * 70)
    print(f"\n  Agency:       {len(taipei_agency)} 家")
    print(f"  Routes:       {len(taipei_tra_routes)} 條")
    print(f"  Trips:        {len(taipei_trips)} 個")
    print(f"  Stops:        {len(taipei_stops)} 個")
    print(f"  Calendar:     {len(taipei_calendar)} 種")
    print(f"  Calendar Dates: {len(taipei_calendar_dates)} 個")

    print(f"\n  輸出目錄: {OUTPUT_DIR}")
    print("\n下一步: 執行 merge_taipei_gtfs.py 將 TRA 數據合併到台北市 GTFS")
    print("\n")

if __name__ == '__main__':
    main()
