#!/usr/bin/env python3
"""
GTFS Taipei Filter Script (For gtfs_tw_v5 without stop_times.txt)

過濾全台灣 GTFS，只保留台北市範圍內的公共運輸數據：
- 捷運：所有 TRTC 路線
- 公車：台北市範圍內的所有公車（TPE_*, NWT_*）
- 火車：台北市內的台鐵線路（萬華→台北→松山→南港）
"""

import pandas as pd
import os
import sys
from pathlib import Path

# 台北市座標邊界 (緯度/經度 - WGS84)
TAIPEI_LAT_MIN = 25.00
TAIPEI_LAT_MAX = 25.20
TAIPEI_LON_MIN = 121.40
TAIPEI_LON_MAX = 121.70

# 台北市內火車站點識別
TAIPEI_STATIONS = ['萬華車站', '台北車站', '臺北車站', '松山車站', '南港車站']

# 設定基礎路徑
BASE_DIR = Path(__file__).parent
GTFS_DATA_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_tw_v5'
OUTPUT_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_taipei_filtered'

def ensure_output_dir():
    """確保輸出目錄存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ 輸出目錄已準備: {OUTPUT_DIR}")

def load_gtfs_file(filename):
    """載入 GTFS CSV 檔案"""
    filepath = GTFS_DATA_DIR / filename
    if not filepath.exists():
        print(f"✗ 檔案不存在: {filepath}")
        return None

    print(f"  載入 {filename}...", end=" ")
    df = pd.read_csv(filepath, dtype=str, low_memory=False)
    print(f"✓ ({len(df)} 筆)")
    return df

def save_gtfs_file(df, filename):
    """保存過濾後的 GTFS CSV 檔案"""
    if df.empty:
        return
    filepath = OUTPUT_DIR / filename
    df.to_csv(filepath, index=False)
    print(f"  保存 {filename}...", end=" ")
    print(f"✓ ({len(df)} 筆)")

def filter_stops_by_latlon(stops_df):
    """
    過濾 stops.txt
    保留所有座標在台北市範圍內的站點（按 stop_lat/stop_lon）
    """
    print("\n[1/5] 過濾 stops.txt (按座標邊界 WGS84)...")

    # 轉換座標為浮點數
    stops_df['stop_lat'] = pd.to_numeric(stops_df['stop_lat'], errors='coerce')
    stops_df['stop_lon'] = pd.to_numeric(stops_df['stop_lon'], errors='coerce')

    # 過濾座標在台北市範圍內的站點
    taipei_stops = stops_df[
        (stops_df['stop_lat'] >= TAIPEI_LAT_MIN) &
        (stops_df['stop_lat'] <= TAIPEI_LAT_MAX) &
        (stops_df['stop_lon'] >= TAIPEI_LON_MIN) &
        (stops_df['stop_lon'] <= TAIPEI_LON_MAX)
    ].copy()

    print(f"  原始站點數: {len(stops_df):,}")
    print(f"  過濾後站點數: {len(taipei_stops):,}")
    print(f"  移除的站點數: {len(stops_df) - len(taipei_stops):,}")

    return taipei_stops

def filter_routes(routes_df, stops_df, trips_df):
    """
    過濾 routes.txt
    - 保留所有捷運路線 (route_type = 1 或 agency = TRTC)
    - 保留所有台北市公車路線 (route_type = 3, agency like TPE_* or NWT_*)
    - 保留台北市內火車線路 (route_type = 2, 所有站點在台北市 + 包含主要車站)
    """
    print("\n[2/5] 過濾 routes.txt 並識別台北市內路線...")

    taipei_route_ids = set()
    taipei_stop_ids = set(stops_df['stop_id'].unique())

    # 轉換數值列
    routes_df['route_type'] = pd.to_numeric(routes_df['route_type'], errors='coerce').fillna(0).astype(int)

    print(f"  原始路線數: {len(routes_df):,}")
    print(f"  台北市內站點數: {len(taipei_stop_ids):,}")

    # 1. 保留所有捷運路線 (route_type = 1)
    metro_routes = routes_df[routes_df['route_type'] == 1]
    print(f"\n  捷運路線: {len(metro_routes):,}")
    taipei_route_ids.update(metro_routes['route_id'].unique())

    # 2. 保留台北市公車路線 (route_type = 3)
    bus_routes = routes_df[routes_df['route_type'] == 3]

    # 過濾：保留 agency_id 以 TPE_ 或 NWT_ 開頭的公車
    bus_routes_taipei = bus_routes[
        (bus_routes['agency_id'].str.startswith('TPE_', na=False)) |
        (bus_routes['agency_id'].str.startswith('NWT_', na=False))
    ].copy()

    print(f"  全部公車路線: {len(bus_routes):,}")
    print(f"  台北市公車路線 (TPE_/NWT_): {len(bus_routes_taipei):,}")
    taipei_route_ids.update(bus_routes_taipei['route_id'].unique())

    # 3. 保留台北市內火車線路
    rail_routes = routes_df[routes_df['route_type'] == 2]
    rail_routes_in_taipei = []

    print(f"  全部火車路線: {len(rail_routes):,}")

    # 根據 route 的所有 trips 對應的 stops 來判斷
    for _, route in rail_routes.iterrows():
        route_id = route['route_id']

        # 獲得該路線的所有 trips
        route_trips = trips_df[trips_df['route_id'] == route_id]['trip_id'].unique()
        if len(route_trips) == 0:
            continue

        # 獲得這些 trips 停靠的所有 stops（假設在 stops 中有記錄）
        # 因為我們沒有 stop_times，我們無法確切知道哪些 stops 被使用
        # 但我們可以檢查 stop_name 中是否包含台北市內火車站
        if any(station in route['route_long_name'] for station in TAIPEI_STATIONS if pd.notna(route['route_long_name'])):
            rail_routes_in_taipei.append(route_id)

    print(f"  台北市內火車線: {len(rail_routes_in_taipei)}")
    taipei_route_ids.update(rail_routes_in_taipei)

    # 過濾 routes.txt
    taipei_routes = routes_df[routes_df['route_id'].isin(taipei_route_ids)].copy()
    print(f"\n  過濾後總路線數: {len(taipei_routes):,}")

    return taipei_routes, taipei_stop_ids, taipei_route_ids

def main():
    print("=" * 60)
    print("GTFS 台北市過濾工具 (gtfs_tw_v5)")
    print("=" * 60)

    # 1. 準備輸出目錄
    ensure_output_dir()

    # 2. 載入原始 GTFS 檔案
    print("\n[載入檔案]")
    stops_df = load_gtfs_file('stops.txt')
    routes_df = load_gtfs_file('routes.txt')
    trips_df = load_gtfs_file('trips.txt')
    agency_df = load_gtfs_file('agency.txt')
    calendar_df = load_gtfs_file('calendar.txt')
    calendar_dates_df = load_gtfs_file('calendar_dates.txt')

    if not all([stops_df is not None, routes_df is not None, trips_df is not None,
                agency_df is not None]):
        print("✗ 無法載入所有必要的 GTFS 檔案")
        sys.exit(1)

    # 3. 過濾數據
    taipei_stops = filter_stops_by_latlon(stops_df)
    taipei_routes, taipei_stop_ids, taipei_route_ids = filter_routes(
        routes_df, taipei_stops, trips_df
    )

    print("\n[3/5] 過濾 trips.txt...")
    taipei_trips = trips_df[trips_df['route_id'].isin(taipei_route_ids)].copy()
    print(f"  原始 trips: {len(trips_df):,}")
    print(f"  過濾後 trips: {len(taipei_trips):,}")

    print("\n[4/5] 過濾 calendar 檔案...")
    service_ids = set(taipei_trips['service_id'].unique())

    if calendar_df is not None:
        taipei_calendar = calendar_df[calendar_df['service_id'].isin(service_ids)].copy()
        print(f"  calendar.txt: {len(taipei_calendar):,} 筆")
    else:
        taipei_calendar = pd.DataFrame()

    if calendar_dates_df is not None:
        taipei_calendar_dates = calendar_dates_df[
            calendar_dates_df['service_id'].isin(service_ids)
        ].copy()
        print(f"  calendar_dates.txt: {len(taipei_calendar_dates):,} 筆")
    else:
        taipei_calendar_dates = pd.DataFrame()

    print("\n[5/5] 過濾 agency.txt...")
    agency_ids = set(taipei_routes['agency_id'].unique())
    taipei_agency = agency_df[agency_df['agency_id'].isin(agency_ids)].copy()
    print(f"  過濾後 agency: {len(taipei_agency):,} 家")

    # 4. 保存過濾後的檔案
    print("\n[保存檔案到輸出目錄]")
    save_gtfs_file(taipei_stops, 'stops.txt')
    save_gtfs_file(taipei_routes, 'routes.txt')
    save_gtfs_file(taipei_trips, 'trips.txt')
    if not taipei_calendar.empty:
        save_gtfs_file(taipei_calendar, 'calendar.txt')
    if not taipei_calendar_dates.empty:
        save_gtfs_file(taipei_calendar_dates, 'calendar_dates.txt')
    save_gtfs_file(taipei_agency, 'agency.txt')

    # 5. 統計信息
    print("\n" + "=" * 60)
    print("過濾完成！統計信息：")
    print("=" * 60)
    print(f"站點數:        {len(taipei_stops):,}")
    print(f"路線數:        {len(taipei_routes):,}")

    # 按 route_type 統計
    route_type_counts = taipei_routes['route_type'].value_counts().sort_index()
    for rt, count in route_type_counts.items():
        rt_name = {1: '捷運', 2: '火車', 3: '公車'}.get(rt, f'其他({rt})')
        print(f"  - {rt_name:8}: {count:,}")

    print(f"Trips:         {len(taipei_trips):,}")
    print(f"機構數:        {len(taipei_agency):,}")
    print(f"服務日期:      {len(taipei_calendar):,}")
    print(f"服務異常日期:  {len(taipei_calendar_dates):,}")
    print("\n輸出目錄: " + str(OUTPUT_DIR))
    print("=" * 60)

if __name__ == '__main__':
    main()
