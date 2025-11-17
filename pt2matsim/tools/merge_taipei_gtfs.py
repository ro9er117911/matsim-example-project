#!/usr/bin/env python3
"""
Merge TRA Railway GTFS with Taipei GTFS (Step 3 of 3)

將 TRA 台鐵數據合併到台北市 GTFS，生成完整的台北市多模式公共運輸 GTFS
包含: 捷運 + 公車 + 火車
"""

import pandas as pd
from pathlib import Path

# 路徑配置
BASE_DIR = Path(__file__).parent
TAIPEI_GTFS_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_taipei_filtered'
TRA_GTFS_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_taipei_tra'
OUTPUT_DIR = BASE_DIR / 'pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra'

def ensure_output_dir():
    """確保輸出目錄存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def merge_gtfs():
    """
    Step 3: 合併 TRA 和台北市 GTFS
    """
    print("=" * 70)
    print("Step 3: 合併 TRA 數據到台北市 GTFS")
    print("=" * 70)
    ensure_output_dir()

    # 1. 合併 agency.txt
    print("\n[1/7] 合併 agency.txt...")
    taipei_agency = pd.read_csv(TAIPEI_GTFS_DIR / 'agency.txt', dtype=str)
    tra_agency = pd.read_csv(TRA_GTFS_DIR / 'agency.txt', dtype=str)

    merged_agency = pd.concat([taipei_agency, tra_agency], ignore_index=True)
    merged_agency = merged_agency.drop_duplicates(subset=['agency_id'], keep='first')
    print(f"  台北市 agency: {len(taipei_agency)}, TRA agency: {len(tra_agency)}")
    print(f"  合併後: {len(merged_agency)} 家")

    # 2. 合併 stops.txt
    print("\n[2/7] 合併 stops.txt...")
    taipei_stops = pd.read_csv(TAIPEI_GTFS_DIR / 'stops.txt', dtype=str)
    tra_stops = pd.read_csv(TRA_GTFS_DIR / 'stops.txt', dtype=str)

    # 過濾掉 TRA stops 中與台北市 stops 重複的 stop_id
    tra_stops_unique = tra_stops[~tra_stops['stop_id'].isin(taipei_stops['stop_id'])]

    merged_stops = pd.concat([taipei_stops, tra_stops_unique], ignore_index=True)
    print(f"  台北市 stops: {len(taipei_stops)}, TRA stops: {len(tra_stops)}")
    print(f"  去重後 TRA stops: {len(tra_stops_unique)}")
    print(f"  合併後: {len(merged_stops)} 個")

    # 3. 合併 routes.txt
    print("\n[3/7] 合併 routes.txt...")
    taipei_routes = pd.read_csv(TAIPEI_GTFS_DIR / 'routes.txt', dtype=str)
    tra_routes = pd.read_csv(TRA_GTFS_DIR / 'routes.txt', dtype=str)

    merged_routes = pd.concat([taipei_routes, tra_routes], ignore_index=True)
    print(f"  台北市 routes: {len(taipei_routes)}, TRA routes: {len(tra_routes)}")
    print(f"  合併後: {len(merged_routes)} 條")

    # 統計路線類型
    print(f"\n  路線類型統計:")
    route_type_counts = merged_routes['route_type'].value_counts().sort_index()
    for rt, count in route_type_counts.items():
        rt_name = {1: '捷運', 2: '火車', 3: '公車'}.get(str(rt), f'其他({rt})')
        print(f"    - {rt_name:8}: {count:4} 條")

    # 4. 合併 trips.txt
    print("\n[4/7] 合併 trips.txt...")
    taipei_trips = pd.read_csv(TAIPEI_GTFS_DIR / 'trips.txt', dtype=str)
    tra_trips = pd.read_csv(TRA_GTFS_DIR / 'trips.txt', dtype=str)

    merged_trips = pd.concat([taipei_trips, tra_trips], ignore_index=True)
    print(f"  台北市 trips: {len(taipei_trips)}, TRA trips: {len(tra_trips)}")
    print(f"  合併後: {len(merged_trips)} 個")

    # 5. 合併 calendar.txt
    print("\n[5/7] 合併 calendar.txt...")

    taipei_calendar_path = TAIPEI_GTFS_DIR / 'calendar.txt'
    tra_calendar_path = TRA_GTFS_DIR / 'calendar.txt'

    taipei_calendar = pd.read_csv(taipei_calendar_path, dtype=str) if taipei_calendar_path.exists() else pd.DataFrame()
    tra_calendar = pd.read_csv(tra_calendar_path, dtype=str) if tra_calendar_path.exists() else pd.DataFrame()

    if not taipei_calendar.empty and not tra_calendar.empty:
        merged_calendar = pd.concat([taipei_calendar, tra_calendar], ignore_index=True)
        merged_calendar = merged_calendar.drop_duplicates(subset=['service_id'], keep='first')
    elif not taipei_calendar.empty:
        merged_calendar = taipei_calendar.copy()
    else:
        merged_calendar = tra_calendar.copy() if not tra_calendar.empty else pd.DataFrame()

    print(f"  台北市 calendar: {len(taipei_calendar)}, TRA calendar: {len(tra_calendar)}")
    print(f"  合併後: {len(merged_calendar)}")

    # 6. 合併 calendar_dates.txt
    print("\n[6/7] 合併 calendar_dates.txt...")

    taipei_calendar_dates_path = TAIPEI_GTFS_DIR / 'calendar_dates.txt'
    tra_calendar_dates_path = TRA_GTFS_DIR / 'calendar_dates.txt'

    taipei_calendar_dates = pd.read_csv(taipei_calendar_dates_path, dtype=str) if taipei_calendar_dates_path.exists() else pd.DataFrame()
    tra_calendar_dates = pd.read_csv(tra_calendar_dates_path, dtype=str) if tra_calendar_dates_path.exists() else pd.DataFrame()

    if not taipei_calendar_dates.empty and not tra_calendar_dates.empty:
        merged_calendar_dates = pd.concat([taipei_calendar_dates, tra_calendar_dates], ignore_index=True)
    elif not taipei_calendar_dates.empty:
        merged_calendar_dates = taipei_calendar_dates.copy()
    else:
        merged_calendar_dates = tra_calendar_dates.copy() if not tra_calendar_dates.empty else pd.DataFrame()

    print(f"  台北市 calendar_dates: {len(taipei_calendar_dates)}, TRA calendar_dates: {len(tra_calendar_dates)}")
    print(f"  合併後: {len(merged_calendar_dates)}")

    # 6.5. 合並 stop_times.txt (如果存在)
    print("\n[6.5/7] 合併 stop_times.txt...")

    taipei_stop_times_path = TAIPEI_GTFS_DIR / 'stop_times.txt'
    tra_stop_times_path = TRA_GTFS_DIR / 'stop_times.txt'

    taipei_stop_times = pd.read_csv(taipei_stop_times_path, dtype=str) if taipei_stop_times_path.exists() else pd.DataFrame()
    tra_stop_times = pd.read_csv(tra_stop_times_path, dtype=str) if tra_stop_times_path.exists() else pd.DataFrame()

    if not taipei_stop_times.empty and not tra_stop_times.empty:
        merged_stop_times = pd.concat([taipei_stop_times, tra_stop_times], ignore_index=True)
    elif not taipei_stop_times.empty:
        merged_stop_times = taipei_stop_times.copy()
    else:
        merged_stop_times = tra_stop_times.copy() if not tra_stop_times.empty else pd.DataFrame()

    print(f"  台北市 stop_times: {len(taipei_stop_times):,}, TRA stop_times: {len(tra_stop_times):,}")
    if not merged_stop_times.empty:
        print(f"  合併後: {len(merged_stop_times):,}")
    else:
        print(f"  ⚠️  警告: 未找到 stop_times.txt (可能影響 PT 映射)")

    # 7. 保存所有檔案
    print("\n[7/7] 保存合併後的 GTFS 檔案...")
    merged_agency.to_csv(OUTPUT_DIR / 'agency.txt', index=False)
    merged_stops.to_csv(OUTPUT_DIR / 'stops.txt', index=False)
    merged_routes.to_csv(OUTPUT_DIR / 'routes.txt', index=False)
    merged_trips.to_csv(OUTPUT_DIR / 'trips.txt', index=False)

    if not merged_calendar.empty:
        merged_calendar.to_csv(OUTPUT_DIR / 'calendar.txt', index=False)

    if not merged_calendar_dates.empty:
        merged_calendar_dates.to_csv(OUTPUT_DIR / 'calendar_dates.txt', index=False)

    if not merged_stop_times.empty:
        merged_stop_times.to_csv(OUTPUT_DIR / 'stop_times.txt', index=False)

    print(f"\n  ✓ 輸出目錄: {OUTPUT_DIR}")
    print(f"    - agency.txt")
    print(f"    - stops.txt")
    print(f"    - routes.txt")
    print(f"    - trips.txt")
    if not merged_calendar.empty:
        print(f"    - calendar.txt")
    if not merged_calendar_dates.empty:
        print(f"    - calendar_dates.txt")
    if not merged_stop_times.empty:
        print(f"    - stop_times.txt ✓ (重要！)")

    return merged_agency, merged_stops, merged_routes, merged_trips, merged_calendar, merged_calendar_dates, merged_stop_times

def main():
    print("\n")

    # Step 3: 合併 TRA 和台北市 GTFS
    merged_agency, merged_stops, merged_routes, merged_trips, merged_calendar, merged_calendar_dates, merged_stop_times = merge_gtfs()

    # 統計輸出
    print("\n" + "=" * 70)
    print("✓ Step 3 完成！最終 GTFS 統計信息：")
    print("=" * 70)

    print(f"\n  機構數 (Agency):        {len(merged_agency):,} 家")
    print(f"  路線數 (Routes):        {len(merged_routes):,} 條")
    print(f"    └ 捷運 (route_type=1) : {len(merged_routes[merged_routes['route_type'].astype(str).str.strip() == '1']):,}")
    print(f"    └ 火車 (route_type=2) : {len(merged_routes[merged_routes['route_type'].astype(str).str.strip() == '2']):,}")
    print(f"    └ 公車 (route_type=3) : {len(merged_routes[merged_routes['route_type'].astype(str).str.strip() == '3']):,}")
    print(f"  行程數 (Trips):         {len(merged_trips):,} 個")
    print(f"  車站數 (Stops):         {len(merged_stops):,} 個")
    print(f"  停靠時間 (Stop Times):  {len(merged_stop_times):,} 筆 {'✓' if not merged_stop_times.empty else '❌ (未找到)'}")
    print(f"  服務日期 (Calendar):    {len(merged_calendar):,} 種")
    print(f"  例外日期 (Calendar Dates): {len(merged_calendar_dates):,} 個")

    print(f"\n  輸出目錄: {OUTPUT_DIR}")
    print("\n✓ 台北市完整 GTFS 已生成！")
    print("  包含: 捷運 + 公車 + 火車")
    if not merged_stop_times.empty:
        print("  ✓ 包含 stop_times.txt - 支援 PT 映射")
    print("\n")

if __name__ == '__main__':
    main()
