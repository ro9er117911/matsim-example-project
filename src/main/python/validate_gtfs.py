#!/usr/bin/env python3
"""
GTFS 数据完整性验证工具

用途：
- 检查 GTFS 数据集是否包含所有必需文件
- 统计各文件的记录数
- 验证外键完整性
- 检查坐标系统
- 生成数据质量报告

使用方法：
    python validate_gtfs.py <gtfs_directory>
    python validate_gtfs.py pt2matsim/data/gtfs/tp_metro_gtfs/

作者：Claude Code
日期：2025-11-17
"""

import os
import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple


# GTFS 规范：必需和可选文件
REQUIRED_FILES = {
    'agency.txt': 'Agency (运营商信息)',
    'stops.txt': 'Stops (站点位置)',
    'routes.txt': 'Routes (路线定义)',
    'trips.txt': 'Trips (行程定义)',
    'stop_times.txt': 'Stop Times (时刻表) - 关键文件',
}

OPTIONAL_FILES = {
    'calendar.txt': 'Calendar (服务日历)',
    'calendar_dates.txt': 'Calendar Dates (日期例外)',
    'frequencies.txt': 'Frequencies (班次频率)',
    'transfers.txt': 'Transfers (转乘信息)',
    'shapes.txt': 'Shapes (路线形状)',
    'feed_info.txt': 'Feed Info (数据集信息)',
}

# 路线类型定义（GTFS 规范）
ROUTE_TYPES = {
    0: '电车/轻轨',
    1: '地铁/捷运',
    2: '铁路',
    3: '公交车',
    4: '渡轮',
    5: '缆车',
    6: '缆车/航空',
    7: '索道',
    11: '无轨电车',
    12: '单轨',
}


def color_text(text: str, color: str) -> str:
    """为终端输出添加颜色"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'bold': '\033[1m',
        'end': '\033[0m',
    }
    return f"{colors.get(color, '')}{text}{colors['end']}"


def check_file_exists(gtfs_dir: Path) -> Tuple[Dict, Dict]:
    """检查 GTFS 文件是否存在"""
    print(f"\n{color_text('=== 文件完整性检查 ===', 'bold')}\n")

    found_required = {}
    found_optional = {}

    print(f"{color_text('必需文件:', 'bold')}")
    for filename, description in REQUIRED_FILES.items():
        filepath = gtfs_dir / filename
        exists = filepath.exists()
        status = color_text('✓', 'green') if exists else color_text('✗ 缺失', 'red')
        print(f"  {status} {filename:20s} - {description}")
        if exists:
            found_required[filename] = filepath

    print(f"\n{color_text('可选文件:', 'bold')}")
    for filename, description in OPTIONAL_FILES.items():
        filepath = gtfs_dir / filename
        exists = filepath.exists()
        status = color_text('✓', 'green') if exists else color_text('-', 'yellow')
        print(f"  {status} {filename:20s} - {description}")
        if exists:
            found_optional[filename] = filepath

    return found_required, found_optional


def count_records(filepath: Path) -> int:
    """统计 CSV 文件的记录数（不含表头）"""
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            return sum(1 for _ in f) - 1  # 减去表头行
    except Exception as e:
        print(f"  {color_text('警告', 'yellow')}: 无法读取 {filepath.name}: {e}")
        return 0


def analyze_file_stats(files: Dict) -> Dict[str, int]:
    """统计各文件的记录数"""
    print(f"\n{color_text('=== 数据量统计 ===', 'bold')}\n")

    stats = {}
    for filename, filepath in files.items():
        count = count_records(filepath)
        stats[filename] = count
        print(f"  {filename:20s}: {count:>10,} 条记录")

    return stats


def analyze_route_types(gtfs_dir: Path) -> None:
    """分析路线类型分布"""
    routes_file = gtfs_dir / 'routes.txt'
    if not routes_file.exists():
        return

    print(f"\n{color_text('=== 路线类型分布 ===', 'bold')}\n")

    route_type_counts = Counter()
    route_names = defaultdict(list)

    try:
        with open(routes_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                route_type = int(row.get('route_type', -1))
                route_type_counts[route_type] += 1
                route_name = row.get('route_short_name', row.get('route_long_name', '未命名'))
                route_names[route_type].append(route_name)

        for route_type in sorted(route_type_counts.keys()):
            count = route_type_counts[route_type]
            type_name = ROUTE_TYPES.get(route_type, f'未知类型 ({route_type})')
            print(f"  {type_name:15s}: {count:>5} 条路线")

            # 显示前 3 条路线名称作为示例
            examples = route_names[route_type][:3]
            if examples:
                print(f"    {'示例:':<10s} {', '.join(examples)}")

    except Exception as e:
        print(f"  {color_text('警告', 'yellow')}: 无法分析路线类型: {e}")


def check_coordinate_system(gtfs_dir: Path) -> None:
    """检查坐标系统"""
    print(f"\n{color_text('=== 坐标系统检查 ===', 'bold')}\n")

    stops_file = gtfs_dir / 'stops.txt'
    stops_epsg3826 = gtfs_dir / 'stops_epsg3826.txt'

    if not stops_file.exists():
        print(f"  {color_text('✗', 'red')} stops.txt 不存在")
        return

    try:
        with open(stops_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            first_row = next(reader, None)
            if first_row:
                has_lat_lon = 'stop_lat' in first_row and 'stop_lon' in first_row
                has_epsg_in_main = 'stop_x_EPSG3826' in first_row and 'stop_y_EPSG3826' in first_row

                status_wgs84 = color_text('✓', 'green') if has_lat_lon else color_text('✗', 'red')
                status_epsg = color_text('✓', 'green') if has_epsg_in_main else color_text('-', 'yellow')

                print(f"  {status_wgs84} WGS84 (stop_lat, stop_lon)")
                print(f"  {status_epsg} EPSG:3826 在 stops.txt 中")
    except Exception as e:
        print(f"  {color_text('警告', 'yellow')}: 无法检查坐标: {e}")

    if stops_epsg3826.exists():
        print(f"  {color_text('✓', 'green')} 发现 stops_epsg3826.txt (TWD97/TM2)")
    else:
        print(f"  {color_text('-', 'yellow')} 未找到 stops_epsg3826.txt")


def check_foreign_keys(gtfs_dir: Path) -> None:
    """检查外键完整性（基础检查）"""
    print(f"\n{color_text('=== 外键完整性检查 ===', 'bold')}\n")

    # 检查 1: trips.txt 中的 route_id 是否都存在于 routes.txt
    routes_file = gtfs_dir / 'routes.txt'
    trips_file = gtfs_dir / 'trips.txt'

    if routes_file.exists() and trips_file.exists():
        try:
            # 读取所有 route_id
            route_ids = set()
            with open(routes_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                route_ids = {row['route_id'] for row in reader}

            # 检查 trips 中的 route_id
            invalid_routes = set()
            trip_count = 0
            with open(trips_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trip_count += 1
                    route_id = row.get('route_id', '')
                    if route_id and route_id not in route_ids:
                        invalid_routes.add(route_id)

            if invalid_routes:
                print(f"  {color_text('✗', 'red')} trips.txt → routes.txt: {len(invalid_routes)} 个无效 route_id")
                print(f"    示例: {list(invalid_routes)[:5]}")
            else:
                print(f"  {color_text('✓', 'green')} trips.txt → routes.txt: 所有 {trip_count:,} 个 trips 的 route_id 有效")

        except Exception as e:
            print(f"  {color_text('警告', 'yellow')}: 无法验证外键: {e}")

    # 检查 2: stop_times.txt 中的 trip_id 是否都存在于 trips.txt
    stop_times_file = gtfs_dir / 'stop_times.txt'

    if trips_file.exists() and stop_times_file.exists():
        try:
            # 读取所有 trip_id
            trip_ids = set()
            with open(trips_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                trip_ids = {row['trip_id'] for row in reader}

            # 检查 stop_times 中的 trip_id（仅采样前 10000 行）
            invalid_trips = set()
            sample_count = 0
            max_sample = 10000

            with open(stop_times_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sample_count += 1
                    if sample_count > max_sample:
                        break
                    trip_id = row.get('trip_id', '')
                    if trip_id and trip_id not in trip_ids:
                        invalid_trips.add(trip_id)

            if invalid_trips:
                print(f"  {color_text('✗', 'red')} stop_times.txt → trips.txt: {len(invalid_trips)} 个无效 trip_id (采样 {sample_count:,} 条)")
                print(f"    示例: {list(invalid_trips)[:5]}")
            else:
                print(f"  {color_text('✓', 'green')} stop_times.txt → trips.txt: 采样 {sample_count:,} 条记录，所有 trip_id 有效")

        except Exception as e:
            print(f"  {color_text('警告', 'yellow')}: 无法验证 stop_times 外键: {e}")


def check_agencies(gtfs_dir: Path) -> None:
    """分析运营商信息"""
    print(f"\n{color_text('=== 运营商信息 ===', 'bold')}\n")

    agency_file = gtfs_dir / 'agency.txt'
    if not agency_file.exists():
        print(f"  {color_text('✗', 'red')} agency.txt 不存在")
        return

    try:
        agencies = []
        with open(agency_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                agencies.append({
                    'id': row.get('agency_id', ''),
                    'name': row.get('agency_name', ''),
                    'timezone': row.get('agency_timezone', ''),
                })

        print(f"  共 {len(agencies)} 个运营商")
        print()

        # 显示前 5 个运营商
        for i, agency in enumerate(agencies[:5], 1):
            print(f"  {i}. {agency['name']}")
            print(f"     ID: {agency['id']}, 时区: {agency['timezone']}")

        if len(agencies) > 5:
            print(f"  ... 以及其他 {len(agencies) - 5} 个运营商")

    except Exception as e:
        print(f"  {color_text('警告', 'yellow')}: 无法读取运营商信息: {e}")


def generate_summary(gtfs_dir: Path, stats: Dict[str, int]) -> None:
    """生成总结报告"""
    print(f"\n{color_text('=== 数据集总结 ===', 'bold')}\n")

    # 检查数据集是否可用于 MATSim
    has_stop_times = 'stop_times.txt' in stats
    has_all_required = all(f in stats for f in REQUIRED_FILES.keys())

    print(f"  数据集目录: {gtfs_dir}")
    print()

    if has_all_required:
        print(f"  {color_text('✓ 数据集完整', 'green')} - 包含所有必需文件")
    else:
        print(f"  {color_text('✗ 数据集不完整', 'red')} - 缺少必需文件")
        missing = set(REQUIRED_FILES.keys()) - set(stats.keys())
        print(f"    缺少: {', '.join(missing)}")

    print()

    if not has_stop_times:
        print(f"  {color_text('⚠️  警告', 'yellow')}: 缺少 stop_times.txt")
        print(f"      这个文件对于 MATSim 模拟至关重要！")
        print(f"      没有它，无法生成 transitSchedule.xml")
    else:
        print(f"  {color_text('✓ MATSim 兼容性', 'green')} - 可用于 MATSim 转换")

    print()

    # 数据规模评估
    total_records = sum(stats.values())
    print(f"  总记录数: {total_records:,}")

    if stats.get('routes.txt', 0) > 1000:
        print(f"  {color_text('ℹ 大型数据集', 'blue')} - 包含大量路线，建议筛选后使用")
    elif stats.get('routes.txt', 0) < 10:
        print(f"  {color_text('ℹ 小型数据集', 'blue')} - 适合测试和原型开发")


def main():
    if len(sys.argv) != 2:
        print(f"使用方法: {sys.argv[0]} <gtfs_directory>")
        print(f"示例: {sys.argv[0]} pt2matsim/data/gtfs/tp_metro_gtfs/")
        sys.exit(1)

    gtfs_dir = Path(sys.argv[1])

    if not gtfs_dir.exists():
        print(f"{color_text('错误', 'red')}: 目录不存在: {gtfs_dir}")
        sys.exit(1)

    if not gtfs_dir.is_dir():
        print(f"{color_text('错误', 'red')}: 不是一个目录: {gtfs_dir}")
        sys.exit(1)

    print(f"\n{color_text('=' * 60, 'bold')}")
    print(f"{color_text('GTFS 数据完整性验证工具', 'bold')}")
    print(f"{color_text('=' * 60, 'bold')}")

    # 1. 检查文件存在性
    required_files, optional_files = check_file_exists(gtfs_dir)
    all_files = {**required_files, **optional_files}

    # 2. 统计记录数
    stats = analyze_file_stats(all_files)

    # 3. 分析运营商
    check_agencies(gtfs_dir)

    # 4. 分析路线类型
    analyze_route_types(gtfs_dir)

    # 5. 检查坐标系统
    check_coordinate_system(gtfs_dir)

    # 6. 检查外键完整性
    check_foreign_keys(gtfs_dir)

    # 7. 生成总结
    generate_summary(gtfs_dir, stats)

    print(f"\n{color_text('=' * 60, 'bold')}\n")


if __name__ == '__main__':
    main()
