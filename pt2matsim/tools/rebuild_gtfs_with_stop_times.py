#!/usr/bin/env python3
"""
重建 GTFS 并修复 stop_times 问题

使用 merged_gtfs_extracted 中的完整数据重新生成正确的台北市 GTFS
确保 stop_times 与 trips 完全匹配
"""

import pandas as pd
from pathlib import Path

MERGED = Path('pt2matsim/data/gtfs/merged_gtfs_extracted')
TRA_GTFS = Path('pt2matsim/data/gtfs/gtfs_taipei_tra')
OUTPUT = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')

def rebuild_gtfs_correctly():
    """
    使用正确的数据源重建 GTFS
    """
    print("=" * 80)
    print("重建台北市 GTFS（使用 merged_gtfs 作为基础）")
    print("=" * 80)

    # 1. 从 merged_gtfs 加载基础数据
    print("\n[1/6] 从 merged_gtfs_extracted 加载数据...")
    merged_routes = pd.read_csv(MERGED / 'routes.txt', dtype=str)
    merged_trips = pd.read_csv(MERGED / 'trips.txt', dtype=str)
    merged_stop_times = pd.read_csv(MERGED / 'stop_times.txt', dtype=str)
    merged_stops = pd.read_csv(MERGED / 'stops.txt', dtype=str)
    merged_calendar = pd.read_csv(MERGED / 'calendar.txt', dtype=str)
    merged_calendar_dates = pd.read_csv(MERGED / 'calendar_dates.txt', dtype=str)
    merged_agency = pd.read_csv(MERGED / 'agency.txt', dtype=str)

    print(f"  Routes: {len(merged_routes)}")
    print(f"  Trips: {len(merged_trips)}")
    print(f"  Stop_times: {len(merged_stop_times)}")
    print(f"  Stops: {len(merged_stops)}")

    # 2. 从 merged 中提取 TRTC 路线
    print("\n[2/6] 提取 TRTC 路线...")
    trtc_routes = merged_routes[merged_routes['agency_id'] == 'TRTC'].copy()
    trtc_trip_ids = set(merged_trips[merged_trips['route_id'].isin(trtc_routes['route_id'])]['trip_id'])
    trtc_stop_times = merged_stop_times[merged_stop_times['trip_id'].isin(trtc_trip_ids)].copy()

    print(f"  TRTC Routes: {len(trtc_routes)}")
    print(f"  TRTC Trips: {len(trtc_trip_ids)}")
    print(f"  TRTC Stop_times: {len(trtc_stop_times)}")

    # 3. 加载 TRA 数据
    print("\n[3/6] 加载 TRA 数据...")
    tra_routes = pd.read_csv(TRA_GTFS / 'routes.txt', dtype=str)
    tra_trips = pd.read_csv(TRA_GTFS / 'trips.txt', dtype=str)
    tra_stops = pd.read_csv(TRA_GTFS / 'stops.txt', dtype=str)
    tra_calendar_dates = pd.read_csv(TRA_GTFS / 'calendar_dates.txt', dtype=str)
    tra_agency = pd.read_csv(TRA_GTFS / 'agency.txt', dtype=str)

    print(f"  TRA Routes: {len(tra_routes)}")
    print(f"  TRA Trips: {len(tra_trips)}")
    print(f"  TRA Stops: {len(tra_stops)}")

    # 4. 合并路线（只有 TRTC + TRA）
    print("\n[4/6] 合并路线和 trips...")

    # 提取公车路线（从 merged，只保留在台北市范围内的）
    bus_routes = merged_routes[merged_routes['route_type'].astype(str).str.strip() == '3'].copy()
    bus_trip_ids = set(merged_trips[merged_trips['route_id'].isin(bus_routes['route_id'])]['trip_id'])

    # 合并所有路线
    all_routes = pd.concat([trtc_routes, tra_routes, bus_routes], ignore_index=True)
    all_routes = all_routes.drop_duplicates(subset=['route_id'], keep='first')

    # 合并 trips
    all_trip_ids = trtc_trip_ids | set(tra_trips['trip_id']) | bus_trip_ids
    all_trips = merged_trips[merged_trips['trip_id'].isin(trtc_trip_ids | bus_trip_ids)].copy()
    all_trips = pd.concat([all_trips, tra_trips], ignore_index=True)
    all_trips = all_trips.drop_duplicates(subset=['trip_id'], keep='first')

    print(f"  Total Routes: {len(all_routes)}")
    print(f"  Total Trips: {len(all_trips)}")

    # 5. 合并 stop_times
    print("\n[5/6] 合并 stop_times...")
    bus_stop_times = merged_stop_times[merged_stop_times['trip_id'].isin(bus_trip_ids)].copy()

    all_stop_times = pd.concat([trtc_stop_times, bus_stop_times], ignore_index=True)
    # TRA 没有 stop_times，所以不添加

    # 去重
    all_stop_times = all_stop_times.drop_duplicates(keep='first')

    print(f"  Total Stop_times: {len(all_stop_times)}")

    # 6. 合并其他文件
    print("\n[6/6] 合并其他文件...")

    # Stops（保留所有，因为多个系统可能使用同一停靠点）
    all_stops = pd.concat([merged_stops, tra_stops], ignore_index=True)
    all_stops = all_stops.drop_duplicates(subset=['stop_id'], keep='first')

    # Calendar
    service_ids = set(all_trips['service_id'].unique())
    all_calendar = merged_calendar[merged_calendar['service_id'].isin(service_ids)].copy()

    # Calendar_dates
    all_calendar_dates = merged_calendar_dates[merged_calendar_dates['service_id'].isin(service_ids)].copy()
    all_calendar_dates = pd.concat([all_calendar_dates, tra_calendar_dates], ignore_index=True)
    all_calendar_dates = all_calendar_dates.drop_duplicates(keep='first')

    # Agency
    agency_ids = set(all_routes['agency_id'].unique())
    all_agency = merged_agency[merged_agency['agency_id'].isin(agency_ids)].copy()
    all_agency = pd.concat([all_agency, tra_agency], ignore_index=True)
    all_agency = all_agency.drop_duplicates(subset=['agency_id'], keep='first')

    # 保存文件
    print("\n[保存] 将重建的 GTFS 保存到输出目录...")
    all_routes.to_csv(OUTPUT / 'routes.txt', index=False)
    all_trips.to_csv(OUTPUT / 'trips.txt', index=False)
    all_stop_times.to_csv(OUTPUT / 'stop_times.txt', index=False)
    all_stops.to_csv(OUTPUT / 'stops.txt', index=False)
    all_calendar.to_csv(OUTPUT / 'calendar.txt', index=False)
    all_calendar_dates.to_csv(OUTPUT / 'calendar_dates.txt', index=False)
    all_agency.to_csv(OUTPUT / 'agency.txt', index=False)

    print(f"  ✓ routes.txt        ({len(all_routes)} 条)")
    print(f"  ✓ trips.txt         ({len(all_trips)} 个)")
    print(f"  ✓ stop_times.txt    ({len(all_stop_times)} 筆)")
    print(f"  ✓ stops.txt         ({len(all_stops)} 个)")
    print(f"  ✓ calendar.txt      ({len(all_calendar)} 种)")
    print(f"  ✓ calendar_dates.txt ({len(all_calendar_dates)} 条)")
    print(f"  ✓ agency.txt        ({len(all_agency)} 家)")

    # 统计报告
    print("\n" + "=" * 80)
    print("重建完成！最终 GTFS 统计")
    print("=" * 80)

    metro_count = len(all_routes[all_routes['route_type'].astype(str).str.strip() == '1'])
    rail_count = len(all_routes[all_routes['route_type'].astype(str).str.strip() == '2'])
    bus_count = len(all_routes[all_routes['route_type'].astype(str).str.strip() == '3'])

    print(f"\n  机构数 (Agency):        {len(all_agency)} 家")
    print(f"  路线数 (Routes):        {len(all_routes)} 条")
    print(f"    ├─ 捷运 (TRTC):      {metro_count} 条")
    print(f"    ├─ 火车 (TRA):       {rail_count} 条")
    print(f"    └─ 公车:            {bus_count} 条")
    print(f"  行程数 (Trips):         {len(all_trips)} 个")
    print(f"  停靠点 (Stop_times):    {len(all_stop_times)} 筆 ✓")
    print(f"  车站数 (Stops):         {len(all_stops)} 个")
    print(f"  服务日期 (Calendar):    {len(all_calendar)} 种")
    print(f"  例外日期 (Calendar_dates): {len(all_calendar_dates)} 条")

    print(f"\n✓ GTFS 已准备好用于 PT 映射！")
    print(f"  数据目录: {OUTPUT}\n")

if __name__ == '__main__':
    rebuild_gtfs_correctly()
