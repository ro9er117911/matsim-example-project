#!/usr/bin/env python3
"""
清理脚本：删除非 TRTC 的捷运路线

目标：从合并后的 GTFS 中删除所有非台北捷运 (TRTC) 的路线
删除对象：
  - KRTC (高雄捷运) - 6 条
  - NTMC (新北捷运) - 10 条
  - TMRT (台中捷运) - 2 条
  - TYMC (桃园捷运) - 5 条
  总计：23 条非 TRTC 捷运路线
"""

import pandas as pd
from pathlib import Path

GTFS_DIR = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')

def clean_non_taipei_metro():
    """
    清理非 TRTC 的捷运路线
    """
    print("=" * 80)
    print("清理非 TRTC 捷运路线")
    print("=" * 80)

    # 1. 载入 routes.txt
    print("\n[1/4] 载入 routes.txt...", end=" ")
    routes = pd.read_csv(GTFS_DIR / 'routes.txt', dtype=str)
    print(f"✓ ({len(routes)} 条)")

    # 统计所有非 TRTC 的捷运路线
    print("\n[2/4] 识别非 TRTC 的捷运路线...\n")

    non_trtc_metro = routes[
        (routes['route_type'].astype(str).str.strip() == '1') &
        (routes['agency_id'] != 'TRTC')
    ].copy()

    # 按 agency 分组统计
    agency_counts = non_trtc_metro.groupby('agency_id').size().sort_values(ascending=False)

    for agency_id, count in agency_counts.items():
        print(f"  ❌ {agency_id:10} : {count:2} 条")

    print(f"\n  合计需删除: {len(non_trtc_metro)} 条非 TRTC 捷运路线")

    # 保留的捷运路线
    trtc_metro = routes[
        (routes['route_type'].astype(str).str.strip() == '1') &
        (routes['agency_id'] == 'TRTC')
    ]
    print(f"  保留 TRTC:   {len(trtc_metro)} 条")

    # 2. 过滤 routes.txt
    print("\n[3/4] 过滤 GTFS 文件...\n")

    # 过滤 routes.txt：保留所有非捷运路线 + 所有 TRTC 捷运路线
    routes_clean = routes[
        (routes['route_type'].astype(str).str.strip() != '1') |  # 所有非捷运路线
        (routes['agency_id'] == 'TRTC')  # 或者 TRTC 捷运
    ].copy()

    routes_deleted = len(routes) - len(routes_clean)
    print(f"  routes.txt   : {len(routes)} → {len(routes_clean)} ({routes_deleted} 条已删除)")

    # 更新 route_ids
    route_ids_clean = set(routes_clean['route_id'])
    routes_deleted_ids = set(routes[~routes['route_id'].isin(route_ids_clean)]['route_id'])

    # 过滤 trips.txt
    trips = pd.read_csv(GTFS_DIR / 'trips.txt', dtype=str)
    trips_clean = trips[trips['route_id'].isin(route_ids_clean)].copy()

    trips_deleted = len(trips) - len(trips_clean)
    print(f"  trips.txt    : {len(trips)} → {len(trips_clean)} ({trips_deleted} 个已删除)")

    # 获取保留的 trip_ids 用于过滤其他文件
    trip_ids_clean = set(trips_clean['trip_id'])

    # 过滤 stop_times.txt
    stop_times = pd.read_csv(GTFS_DIR / 'stop_times.txt', dtype=str)
    stop_times_clean = stop_times[stop_times['trip_id'].isin(trip_ids_clean)].copy()

    stop_times_deleted = len(stop_times) - len(stop_times_clean)
    print(f"  stop_times.txt: {len(stop_times)} → {len(stop_times_clean)} ({stop_times_deleted} 筆已删除)")

    # 过滤 calendar_dates.txt：只保留被使用的 service_id
    service_ids_clean = set(trips_clean['service_id'].unique())
    calendar_dates = pd.read_csv(GTFS_DIR / 'calendar_dates.txt', dtype=str)
    calendar_dates_clean = calendar_dates[calendar_dates['service_id'].isin(service_ids_clean)].copy()

    calendar_dates_deleted = len(calendar_dates) - len(calendar_dates_clean)
    print(f"  calendar_dates: {len(calendar_dates)} → {len(calendar_dates_clean)} ({calendar_dates_deleted} 条已删除)")

    # 过滤 agency.txt
    agency = pd.read_csv(GTFS_DIR / 'agency.txt', dtype=str)

    # 获取待删除的 agency
    agencies_to_delete = non_trtc_metro['agency_id'].unique()
    agency_clean = agency[~agency['agency_id'].isin(agencies_to_delete)].copy()

    agency_deleted = len(agency) - len(agency_clean)
    print(f"  agency.txt   : {len(agency)} → {len(agency_clean)} ({agency_deleted} 家已删除)")

    # 不过滤 stops.txt，因为可能被其他路线（如公车）使用

    # 3. 保存清理后的文件
    print("\n[4/4] 保存清理后的文件...\n")

    routes_clean.to_csv(GTFS_DIR / 'routes.txt', index=False)
    print(f"  ✓ routes.txt")

    trips_clean.to_csv(GTFS_DIR / 'trips.txt', index=False)
    print(f"  ✓ trips.txt")

    stop_times_clean.to_csv(GTFS_DIR / 'stop_times.txt', index=False)
    print(f"  ✓ stop_times.txt")

    calendar_dates_clean.to_csv(GTFS_DIR / 'calendar_dates.txt', index=False)
    print(f"  ✓ calendar_dates.txt")

    agency_clean.to_csv(GTFS_DIR / 'agency.txt', index=False)
    print(f"  ✓ agency.txt")

    # 统计报告
    print("\n" + "=" * 80)
    print("清理完成！统计报告")
    print("=" * 80)

    print(f"\n删除的非 TRTC 捷运路线 (共 23 条):\n")

    for agency_id, count in agency_counts.items():
        agency_name = {
            'KRTC': '高雄捷运',
            'NTMC': '新北捷运',
            'TMRT': '台中捷运',
            'TYMC': '桃园捷运'
        }.get(agency_id, agency_id)
        print(f"  ❌ {agency_id:10} ({agency_name:12}) : {count:2} 条路线已删除")

    print(f"\n保留的捷运系统:\n")
    print(f"  ✓ TRTC       (台北捷运)    : {len(trtc_metro):2} 条路线")

    print(f"\n最终 GTFS 统计:\n")
    print(f"  机构数 (Agency)       : {len(agency_clean)} 家")
    print(f"  总路线数 (Routes)     : {len(routes_clean)} 条")

    # 统计路线类型
    metro_final = len(routes_clean[routes_clean['route_type'].astype(str).str.strip() == '1'])
    rail_final = len(routes_clean[routes_clean['route_type'].astype(str).str.strip() == '2'])
    bus_final = len(routes_clean[routes_clean['route_type'].astype(str).str.strip() == '3'])

    print(f"    ├─ 捷运 (TRTC)     : {metro_final:4} 条 (删除前: 47)")
    print(f"    ├─ 火车 (TRA)      : {rail_final:4} 条 (保留)")
    print(f"    └─ 公车            : {bus_final:4} 条 (保留)")
    print(f"  总行程数 (Trips)      : {len(trips_clean):,} 个 (删除 {trips_deleted:,} 个)")
    print(f"  总停靠点 (Stop Times) : {len(stop_times_clean):,} 筆 (删除 {stop_times_deleted:,} 筆)")

    print(f"\n输出目录: {GTFS_DIR}")
    print("\n✓ 清理完成！GTFS 已准备好用于 PT 映射")
    print("\n")

if __name__ == '__main__':
    clean_non_taipei_metro()
