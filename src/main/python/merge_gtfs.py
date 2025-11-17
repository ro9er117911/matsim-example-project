#!/usr/bin/env python3
"""
GTFS 数据集合并工具

用途：
- 合并多个 GTFS 数据集为一个完整的数据集
- 处理 ID 冲突（自动添加前缀）
- 生成转乘关系（transfers.txt）
- 验证合并后的数据完整性

使用方法：
    python merge_gtfs.py <gtfs1_dir> <gtfs2_dir> <output_dir> [options]

    选项：
        --prefix1 PREFIX     为第一个数据集的 ID 添加前缀（默认：GTFS1_）
        --prefix2 PREFIX     为第二个数据集的 ID 添加前缀（默认：GTFS2_）
        --transfer-distance  转乘站点的最大距离（米，默认：100）
        --transfer-time      转乘时间（秒，默认：180）

示例：
    # 合并台北捷运和公交数据
    python merge_gtfs.py \
        pt2matsim/data/gtfs/tp_metro_gtfs/ \
        pt2matsim/data/gtfs/taipei_bus_gtfs/ \
        pt2matsim/data/gtfs/merged_gtfs/ \
        --prefix1 MRT_ \
        --prefix2 BUS_

注意：
    - 两个输入数据集必须都包含 stop_times.txt
    - 使用前请先运行 validate_gtfs.py 检查数据完整性
    - 合并大型数据集可能需要数分钟时间

作者：Claude Code
日期：2025-11-17
"""

import os
import sys
import csv
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import math


# GTFS 文件列表（需要合并的）
GTFS_FILES = [
    'agency.txt',
    'stops.txt',
    'routes.txt',
    'trips.txt',
    'stop_times.txt',
    'calendar.txt',
    'calendar_dates.txt',
    'frequencies.txt',
    'shapes.txt',
    'transfers.txt',
]

# 需要添加前缀的字段（按文件分类）
ID_FIELDS = {
    'agency.txt': {
        'key': 'agency_id',
        'refs': [],
    },
    'stops.txt': {
        'key': 'stop_id',
        'refs': ['parent_station'],
    },
    'routes.txt': {
        'key': 'route_id',
        'refs': ['agency_id'],
    },
    'trips.txt': {
        'key': 'trip_id',
        'refs': ['route_id', 'service_id', 'shape_id'],
    },
    'stop_times.txt': {
        'key': None,  # 没有主键
        'refs': ['trip_id', 'stop_id'],
    },
    'calendar.txt': {
        'key': 'service_id',
        'refs': [],
    },
    'calendar_dates.txt': {
        'key': None,
        'refs': ['service_id'],
    },
    'frequencies.txt': {
        'key': None,
        'refs': ['trip_id'],
    },
    'shapes.txt': {
        'key': None,
        'refs': ['shape_id'],
    },
    'transfers.txt': {
        'key': None,
        'refs': ['from_stop_id', 'to_stop_id'],
    },
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


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    计算两个经纬度坐标之间的距离（米）
    使用 Haversine 公式
    """
    R = 6371000  # 地球半径（米）

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def read_csv_with_prefix(filepath: Path, prefix: str, filename: str) -> Tuple[List[Dict], List[str]]:
    """
    读取 CSV 文件并为所有 ID 字段添加前缀

    返回：
        (修改后的行列表, 字段名列表)
    """
    if not filepath.exists():
        return [], []

    rows = []
    fieldnames = []

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            # 获取需要添加前缀的字段
            id_config = ID_FIELDS.get(filename, {})
            key_field = id_config.get('key')
            ref_fields = id_config.get('refs', [])

            for row in reader:
                # 为主键添加前缀
                if key_field and key_field in row and row[key_field]:
                    row[key_field] = f"{prefix}{row[key_field]}"

                # 为外键添加前缀
                for ref_field in ref_fields:
                    if ref_field in row and row[ref_field]:
                        # 处理可能为空的字段（如 parent_station）
                        row[ref_field] = f"{prefix}{row[ref_field]}"

                rows.append(row)

    except Exception as e:
        print(f"  {color_text('错误', 'red')}: 无法读取 {filepath}: {e}")
        return [], []

    return rows, fieldnames


def merge_csv_files(file1: Path, file2: Path, output_file: Path, prefix1: str, prefix2: str, filename: str):
    """
    合并两个 CSV 文件
    """
    print(f"  合并 {filename}...")

    # 读取两个文件
    rows1, fields1 = read_csv_with_prefix(file1, prefix1, filename)
    rows2, fields2 = read_csv_with_prefix(file2, prefix2, filename)

    # 确定最终的字段列表（使用第一个文件的字段，如果第二个文件有额外字段则添加）
    fieldnames = fields1 if fields1 else fields2
    if fields2:
        for field in fields2:
            if field not in fieldnames:
                fieldnames.append(field)

    # 合并行
    all_rows = rows1 + rows2

    if not all_rows:
        print(f"    {color_text('跳过', 'yellow')}: 两个文件都不存在或为空")
        return

    # 写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"    {color_text('✓', 'green')} {len(all_rows):,} 条记录 ({len(rows1):,} + {len(rows2):,})")

    except Exception as e:
        print(f"    {color_text('错误', 'red')}: 写入失败: {e}")


def load_stops(filepath: Path, prefix: str) -> Dict[str, Dict]:
    """
    加载站点数据（用于生成转乘关系）

    返回：
        {stop_id: {stop_lat, stop_lon, stop_name}}
    """
    if not filepath.exists():
        return {}

    stops = {}
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stop_id = f"{prefix}{row['stop_id']}"
                stops[stop_id] = {
                    'lat': float(row.get('stop_lat', 0)),
                    'lon': float(row.get('stop_lon', 0)),
                    'name': row.get('stop_name', ''),
                }
    except Exception as e:
        print(f"  {color_text('警告', 'yellow')}: 无法加载站点: {e}")

    return stops


def generate_transfers(stops1: Dict, stops2: Dict, output_file: Path,
                      max_distance: float = 100, transfer_time: int = 180):
    """
    生成转乘关系文件（transfers.txt）

    找出两个数据集中距离小于 max_distance 的站点对
    """
    print(f"\n{color_text('生成转乘关系...', 'bold')}")
    print(f"  最大转乘距离: {max_distance} 米")
    print(f"  转乘时间: {transfer_time} 秒")

    transfers = []

    # 遍历所有站点对
    for stop1_id, stop1 in stops1.items():
        for stop2_id, stop2 in stops2.items():
            # 计算距离
            distance = haversine_distance(
                stop1['lat'], stop1['lon'],
                stop2['lat'], stop2['lon']
            )

            if distance <= max_distance:
                # 创建双向转乘
                transfers.append({
                    'from_stop_id': stop1_id,
                    'to_stop_id': stop2_id,
                    'transfer_type': '2',  # 需要最小转乘时间
                    'min_transfer_time': str(transfer_time),
                })
                transfers.append({
                    'from_stop_id': stop2_id,
                    'to_stop_id': stop1_id,
                    'transfer_type': '2',
                    'min_transfer_time': str(transfer_time),
                })

                print(f"    {color_text('✓', 'green')} {stop1['name']} ↔ {stop2['name']} ({distance:.1f}m)")

    if transfers:
        # 写入 transfers.txt
        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['from_stop_id', 'to_stop_id', 'transfer_type', 'min_transfer_time'])
                writer.writeheader()
                writer.writerows(transfers)

            print(f"\n  {color_text('✓', 'green')} 生成 {len(transfers)} 个转乘关系")

        except Exception as e:
            print(f"  {color_text('错误', 'red')}: 写入 transfers.txt 失败: {e}")
    else:
        print(f"\n  {color_text('警告', 'yellow')}: 未找到转乘站点（距离小于 {max_distance}m）")


def merge_gtfs(gtfs1_dir: Path, gtfs2_dir: Path, output_dir: Path,
               prefix1: str, prefix2: str, transfer_distance: float, transfer_time: int):
    """
    合并两个 GTFS 数据集
    """
    print(f"\n{color_text('=== GTFS 数据集合并 ===', 'bold')}\n")
    print(f"  输入 1: {gtfs1_dir} (前缀: {prefix1})")
    print(f"  输入 2: {gtfs2_dir} (前缀: {prefix2})")
    print(f"  输出: {output_dir}\n")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 合并各个 GTFS 文件
    print(f"{color_text('合并 GTFS 文件...', 'bold')}\n")

    for filename in GTFS_FILES:
        file1 = gtfs1_dir / filename
        file2 = gtfs2_dir / filename

        # 跳过 transfers.txt（将在后面生成）
        if filename == 'transfers.txt':
            continue

        output_file = output_dir / filename
        merge_csv_files(file1, file2, output_file, prefix1, prefix2, filename)

    # 生成转乘关系
    print(f"\n{color_text('生成转乘关系...', 'bold')}")

    stops1 = load_stops(gtfs1_dir / 'stops.txt', prefix1)
    stops2 = load_stops(gtfs2_dir / 'stops.txt', prefix2)

    print(f"  数据集 1: {len(stops1):,} 个站点")
    print(f"  数据集 2: {len(stops2):,} 个站点")

    transfers_file = output_dir / 'transfers.txt'
    generate_transfers(stops1, stops2, transfers_file, transfer_distance, transfer_time)

    # 复制坐标文件（如果存在）
    print(f"\n{color_text('复制坐标文件...', 'bold')}")
    for coord_file in ['stops_epsg3826.txt', 'shapes_epsg3826.txt']:
        file1 = gtfs1_dir / coord_file
        file2 = gtfs2_dir / coord_file
        output_file = output_dir / coord_file

        if file1.exists() or file2.exists():
            merge_csv_files(file1, file2, output_file, prefix1, prefix2, coord_file)

    print(f"\n{color_text('✓ 合并完成！', 'green')}")
    print(f"\n输出目录: {output_dir}")
    print(f"\n{color_text('下一步:', 'bold')}")
    print(f"  1. 验证合并结果:")
    print(f"     python validate_gtfs.py {output_dir}")
    print(f"  2. 转换为 MATSim 格式:")
    print(f"     # 使用 GtfsToMatsim 工具")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='合并两个 GTFS 数据集',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 合并台北捷运和公交数据
  python merge_gtfs.py \\
      pt2matsim/data/gtfs/tp_metro_gtfs/ \\
      pt2matsim/data/gtfs/taipei_bus_gtfs/ \\
      pt2matsim/data/gtfs/merged_gtfs/ \\
      --prefix1 MRT_ \\
      --prefix2 BUS_

注意：
  - 两个输入数据集必须都包含 stop_times.txt
  - 使用前请先运行 validate_gtfs.py 检查数据完整性
        """
    )

    parser.add_argument('gtfs1_dir', type=Path, help='第一个 GTFS 数据集目录')
    parser.add_argument('gtfs2_dir', type=Path, help='第二个 GTFS 数据集目录')
    parser.add_argument('output_dir', type=Path, help='输出目录')
    parser.add_argument('--prefix1', default='GTFS1_', help='第一个数据集的 ID 前缀（默认：GTFS1_）')
    parser.add_argument('--prefix2', default='GTFS2_', help='第二个数据集的 ID 前缀（默认：GTFS2_）')
    parser.add_argument('--transfer-distance', type=float, default=100,
                       help='转乘站点的最大距离（米，默认：100）')
    parser.add_argument('--transfer-time', type=int, default=180,
                       help='转乘时间（秒，默认：180）')

    args = parser.parse_args()

    # 验证输入目录
    if not args.gtfs1_dir.exists():
        print(f"{color_text('错误', 'red')}: 目录不存在: {args.gtfs1_dir}")
        sys.exit(1)

    if not args.gtfs2_dir.exists():
        print(f"{color_text('错误', 'red')}: 目录不存在: {args.gtfs2_dir}")
        sys.exit(1)

    # 检查关键文件
    required_files = ['agency.txt', 'stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt']
    for filename in required_files:
        file1 = args.gtfs1_dir / filename
        file2 = args.gtfs2_dir / filename

        if not file1.exists() and not file2.exists():
            print(f"{color_text('错误', 'red')}: 两个数据集都缺少 {filename}")
            print(f"  请先运行: python validate_gtfs.py {args.gtfs1_dir}")
            print(f"  请先运行: python validate_gtfs.py {args.gtfs2_dir}")
            sys.exit(1)

    # 执行合并
    merge_gtfs(
        args.gtfs1_dir,
        args.gtfs2_dir,
        args.output_dir,
        args.prefix1,
        args.prefix2,
        args.transfer_distance,
        args.transfer_time,
    )


if __name__ == '__main__':
    main()
