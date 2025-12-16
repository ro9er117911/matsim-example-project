# GTFS 映射指南 (GTFS Mapping Guide)

## 概述

本指南说明如何使用台北市 GTFS 数据进行 MATSim 公共运输 (PT) 映射。

**最重要的一点：stop_times.txt 对 PT 映射至关重要！**

---

## 1. GTFS 数据准备

### 1.1 推荐 GTFS 文件位置

**主要目录**：`pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/`

该目录包含：
- ✅ **routes.txt** - 路线定义（捷运、火车、公车）
- ✅ **trips.txt** - 班次/行程定义
- ✅ **stops.txt** - 停靠站定义
- **✅ stop_times.txt** - **停靠时间表（必须存在！）**
- ✅ **calendar.txt** - 服务日期定义
- ✅ **calendar_dates.txt** - 例外日期定义
- ✅ **agency.txt** - 运营机构定义

### 1.2 数据构成

| 运输系统 | 运营商 | 路线数 | 说明 |
|---------|--------|--------|------|
| **捷运** | TRTC | ~24-31 | 台北市捷运系统 (勿误用其他县市) |
| **火车** | TRA | 15 | 台北市内台铁短途区间车 |
| **公车** | TPE_*, NWT_* | ~2,614-8,329 | 台北市及新北公车 |

---

## 2. stop_times.txt 的重要性

### 2.1 为什么 stop_times.txt 必须存在？

**stop_times.txt 文件的作用**：
1. **定义 PT 路线在网络上的具体停靠顺序和停靠时间**
2. **使 pt2matsim 能够计算正确的路由和转乘时间**
3. **启用可靠的 PT 代理路由和行为模拟**

### 2.2 没有 stop_times.txt 的后果

❌ **映射失败**：pt2matsim 无法确定站点的先后顺序
❌ **路线混乱**：虚拟网络中可能产生不合理的拓扑
❌ **时间估计错误**：无法计算正确的 PT 行程时间
❌ **转乘失败**：SwissRailRaptor 无法找到合理的转乘方案

### 2.3 验证 stop_times.txt

在运行 PT 映射前，**必须**验证：

```bash
# 1. 检查 stop_times.txt 是否存在且非空
ls -lh pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/stop_times.txt

# 2. 验证行数（应该有 >1000 筆 stop_times）
wc -l pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/stop_times.txt

# 3. 检查 trip_ids 是否与 trips.txt 匹配
python3 << 'EOF'
import pandas as pd
trips = pd.read_csv('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/trips.txt', dtype=str)
stop_times = pd.read_csv('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/stop_times.txt', dtype=str)

trip_ids_in_trips = set(trips['trip_id'])
trip_ids_in_stop_times = set(stop_times['trip_id'])

print(f"Trips 中的 trip_id: {len(trip_ids_in_trips)}")
print(f"Stop_times 中的 trip_id: {len(trip_ids_in_stop_times)}")
print(f"匹配度: {len(trip_ids_in_trips & trip_ids_in_stop_times) / len(trip_ids_in_trips) * 100:.1f}%")

if len(trip_ids_in_trips & trip_ids_in_stop_times) == 0:
    print("❌ 警告：没有匹配的 trip_ids！")
else:
    print("✓ stop_times.txt 与 trips.txt 匹配")
EOF
```

---

## 3. 清理非台北系统的注意事项

### 3.1 需要清理的系统

在进行 PT 映射前，确保 GTFS 中**不包含**以下非台北系统：

| 系统 | Agency ID | 状态 |
|------|-----------|------|
| 高雄捷运 | KRTC | ❌ 应删除 |
| 新北捷运 | NTMC | ❌ 应删除 |
| 台中捷运 | TMRT | ❌ 应删除 |
| 桃园捷运 | TYMC | ⚠️ 台北车站连线可保留 |
| 台铁长途线 | TRA (非区间车) | ❌ 应删除 |

### 3.2 清理步骤

**关键：清理时必须同时清理 routes.txt、trips.txt 和 stop_times.txt，以保持数据一致性**

```bash
# 运行提供的清理脚本
python3 clean_non_taipei_metro.py
```

---

## 4. PT 映射前的检查清单

在启动 pt2matsim 前，请确认：

- [ ] stop_times.txt 存在且包含 >1,000 筆数据
- [ ] stop_times.txt 与 trips.txt 的 trip_ids 匹配度 >90%
- [ ] GTFS 中的捷运路线仅包含 TRTC（台北捷运）
- [ ] TRTC 路线数在 24-31 条之间
- [ ] TRA（台铁）路线数为 15 条（台北市内区间车）
- [ ] 公车路线数在 2,000-3,000 条之间（取决于是否包含新北部分)
- [ ] calendar_dates.txt 包含所有必要的服务日期

### 验证脚本

```bash
python3 << 'EOF'
import pandas as pd
from pathlib import Path

gtfs_dir = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')

# 加载数据
routes = pd.read_csv(gtfs_dir / 'routes.txt', dtype=str)
trips = pd.read_csv(gtfs_dir / 'trips.txt', dtype=str)
stop_times = pd.read_csv(gtfs_dir / 'stop_times.txt', dtype=str)

print("=" * 70)
print("GTFS 数据验证")
print("=" * 70)

# 检查 stop_times
trip_ids_trips = set(trips['trip_id'])
trip_ids_stop_times = set(stop_times['trip_id'])
matching = len(trip_ids_trips & trip_ids_stop_times)
matching_pct = matching / len(trip_ids_trips) * 100 if len(trip_ids_trips) > 0 else 0

print(f"\n✓ stop_times.txt 数据:")
print(f"    Records: {len(stop_times)}")
print(f"    Trip ID 匹配度: {matching_pct:.1f}%")

if matching_pct < 90:
    print(f"    ❌ 警告：匹配度低于 90%！")
else:
    print(f"    ✓ 匹配度良好")

# 检查路线类型
print(f"\n✓ 路线分布:")
for rt, name in [(1, '捷运'), (2, '火车'), (3, '公车')]:
    count = len(routes[routes['route_type'].astype(str).str.strip() == str(rt)])
    print(f"    {name}: {count} 条")

# 检查非 TRTC 捷运
non_trtc = routes[(routes['route_type'].astype(str).str.strip() == '1') & (routes['agency_id'] != 'TRTC')]
if len(non_trtc) > 0:
    print(f"\n❌ 警告：存在 {len(non_trtc)} 条非 TRTC 捷运路线")
    print(f"    需要运行 clean_non_taipei_metro.py 清理")
else:
    print(f"\n✓ 仅包含 TRTC 捷运路线")

# 检查 TRA 路线
tra_routes = routes[routes['agency_id'] == 'TRA']
print(f"    TRA 火车路线: {len(tra_routes)} 条")

print("\n" + "=" * 70)
if matching_pct >= 90 and len(non_trtc) == 0:
    print("✓ GTFS 已准备好进行 PT 映射！")
else:
    print("❌ GTFS 需要进一步处理")
print("=" * 70)
EOF
```

---

## 5. PT 映射执行指南

详见：`docs/PT_MAPPING_STRATEGY.md`

关键步骤：
1. **配置 pt2matsim 参数** - 根据台北市网络特性调整
2. **运行 PT 映射** - 参考 `docs/PT_MAPPING_STRATEGY.md` 中的分阶段执行
3. **验证输出** - 检查 `transitSchedule.xml` 和 `transitVehicles.xml`

---

## 6. 常见问题

### Q: 为什么 pt2matsim 报告"无法找到路线"？

**A**: 最可能的原因：
1. **stop_times.txt 缺失或为空** - 检查文件大小和记录数
2. **trip_ids 不匹配** - 运行上面的验证脚本检查 trip_id 一致性
3. **网络不连通** - 确保 network.xml 包含所有必要的模式（pt、subway、bus等）

### Q: 为什么有其他县市的捷运线？

**A**: 合并过程中可能包含了全台 GTFS 数据。需要运行：
```bash
python3 clean_non_taipei_metro.py
```

### Q: stop_times.txt 数据何时生成？

**A**: stop_times.txt 来自原始 `merged_gtfs.zip`（交通部公开数据），已包含所有台湾 GTFS 数据。在 MATSim 中不需要生成，只需提供。

### Q: 我可以跳过 stop_times.txt 吗？

**A**: ❌ **不可以**。没有 stop_times.txt，PT 映射会失败。这是 GTFS 标准的必需文件。

---

## 7. 文件大小参考

标准的台北市 GTFS 应该包含：

| 文件 | 预期大小 | 预期记录数 |
|------|---------|----------|
| routes.txt | ~500 KB | 2,000-3,000 条 |
| trips.txt | ~2-3 MB | 200,000-300,000 个 |
| stops.txt | ~5-10 MB | 40,000-50,000 个 |
| **stop_times.txt** | **~3-5 MB** | **100,000+ 筆** |
| calendar.txt | ~20-30 KB | ~200 种 |
| calendar_dates.txt | ~100-200 KB | ~1,000 条 |
| agency.txt | ~5 KB | 50-100 家 |

如果 stop_times.txt 小于 100 KB，说明数据不完整！

---

## 8. 后续步骤

1. **验证 GTFS** - 运行上面的检查清单和验证脚本
2. **清理非台北数据** - 如需要，运行 `clean_non_taipei_metro.py`
3. **准备 OSM 网络** - 确保 network.xml 覆盖台北市
4. **配置 pt2matsim** - 参考 `docs/PT_MAPPING_STRATEGY.md`
5. **执行 PT 映射** - 分阶段运行，监控进度和资源使用

---

**作者**: Claude Code
**版本**: 1.0
**最后更新**: 2025-11-17

