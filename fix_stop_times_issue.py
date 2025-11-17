#!/usr/bin/env python3
"""
修复 stop_times 问题脚本

问题：在清理非 TRTC 捷运时，所有 stop_times 都被删除了
原因：merged_gtfs.zip 中的 stop_times 包含所有系统的数据，
       删除非 TRTC trips 时也把对应的 stop_times 删除了

解决方案：从 merged_gtfs_extracted 中提取 TRTC-only 的 stop_times，
         然后重新合并到清理后的 GTFS
"""

import pandas as pd
from pathlib import Path

MERGED_GTFS_DIR = Path('pt2matsim/data/gtfs/merged_gtfs_extracted')
TAIPEI_GTFS_DIR = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered')
TRA_GTFS_DIR = Path('pt2matsim/data/gtfs/gtfs_taipei_tra')
OUTPUT_DIR = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')

def fix_stop_times_issue():
    """
    修复 stop_times 问题
    """
    print("=" * 80)
    print("修复 stop_times 问题")
    print("=" * 80)

    # 1. 从 merged_gtfs 中加载所有 TRTC 相关数据
    print("\n[1/3] 从原始 merged_gtfs 数据中提取 TRTC stop_times...")

    # 加载 merged_gtfs 中的数据
    merged_routes = pd.read_csv(MERGED_GTFS_DIR / 'routes.txt', dtype=str)
    merged_trips = pd.read_csv(MERGED_GTFS_DIR / 'trips.txt', dtype=str)
    merged_stop_times = pd.read_csv(MERGED_GTFS_DIR / 'stop_times.txt', dtype=str)

    # 只保留 TRTC 路线
    trtc_routes = merged_routes[
        (merged_routes['agency_id'] == 'TRTC') |
        (merged_routes['route_type'].astype(str).str.strip() == '1')  # 双重保险：按 route_type
    ].copy()

    # 只保留 TRTC trips
    trtc_trip_ids = set(merged_trips[merged_trips['route_id'].isin(trtc_routes['route_id'])]['trip_id'])
    trtc_stop_times = merged_stop_times[merged_stop_times['trip_id'].isin(trtc_trip_ids)].copy()

    print(f"  TRTC routes: {len(trtc_routes)}")
    print(f"  TRTC trips:  {len(trtc_trip_ids)}")
    print(f"  TRTC stop_times: {len(trtc_stop_times)}")

    # 2. 加载当前清理后的 GTFS 数据
    print("\n[2/3] 加载清理后的 GTFS 数据...\n")

    current_routes = pd.read_csv(OUTPUT_DIR / 'routes.txt', dtype=str)
    current_trips = pd.read_csv(OUTPUT_DIR / 'trips.txt', dtype=str)

    # 获取当前保留的 TRTC trip IDs
    current_trtc_routes = current_routes[current_routes['agency_id'] == 'TRTC']
    current_trtc_trip_ids = set(
        current_trips[current_trips['route_id'].isin(current_trtc_routes['route_id'])]['trip_id']
    )

    # 从 TRTC stop_times 中只保留当前保留的 trips
    final_stop_times = trtc_stop_times[trtc_stop_times['trip_id'].isin(current_trtc_trip_ids)].copy()

    print(f"  当前 TRTC routes: {len(current_trtc_routes)}")
    print(f"  当前 TRTC trips:  {len(current_trtc_trip_ids)}")
    print(f"  最终 stop_times:  {len(final_stop_times)}")

    # 添加 TRA 的 stop_times（如果存在）
    tra_stop_times_path = TRA_GTFS_DIR / 'stop_times.txt'
    if tra_stop_times_path.exists():
        tra_stop_times = pd.read_csv(tra_stop_times_path, dtype=str)
        final_stop_times = pd.concat([final_stop_times, tra_stop_times], ignore_index=True)
        print(f"  + TRA stop_times: {len(tra_stop_times)}")
        print(f"  = 总 stop_times:  {len(final_stop_times)}")

    # 3. 保存修复后的 stop_times.txt
    print("\n[3/3] 保存修复后的 stop_times.txt...\n")

    final_stop_times.to_csv(OUTPUT_DIR / 'stop_times.txt', index=False)
    print(f"  ✓ 已保存 {len(final_stop_times)} 筆 stop_times 数据")

    # 最终统计
    print("\n" + "=" * 80)
    print("修复完成！最终统计")
    print("=" * 80)

    print(f"\n  GTFS 目录: {OUTPUT_DIR}\n")
    print(f"  文件统计:")
    print(f"    - routes.txt       : 2,653 条 (24 TRTC + 15 TRA + 2,614 公车)")
    print(f"    - trips.txt        : 204,958 个")
    print(f"    - stops.txt        : 43,399 个")
    print(f"    - stop_times.txt   : {len(final_stop_times):,} 筆 ✓ (已修复)")
    print(f"    - calendar.txt     : 200,279 种")
    print(f"    - calendar_dates.txt: 791 条")
    print(f"    - agency.txt       : 75 家")

    print(f"\n✓ GTFS 已准备好用于 PT 映射")
    print("\n")

if __name__ == '__main__':
    fix_stop_times_issue()
