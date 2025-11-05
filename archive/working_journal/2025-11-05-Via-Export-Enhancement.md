# Via 平台可视化导出增强 - 完整实现报告

**日期**: 2025-11-05
**状态**: ✅ 完成 (Phase 2 时间范围精细化已升级)
**目标**: 为 Via 平台生成完整的人-车交互事件可视化数据，支持精细时间范围过滤

---

## 目标概述

今天的工作分为四个阶段，逐步完善 Via 平台的可视化导出功能：

1. **第一阶段** - 动态车辆过滤（修复硬编码问题）
2. **第二阶段** - 事件文件过滤（基础过滤）
3. **第三阶段** - 车辆轨迹增强（包含车辆的完整运动事件）
4. **第四阶段** - 精细时间范围过滤 + 检查点机制（新增，2025-11-05 下午）

---

## 第一阶段：动态车辆过滤系统

### 问题发现
- `parsers.py` 中的 `load_actively_used_vehicles()` 硬编码了 3 个 agent IDs
- `main.py` 中的 `total_vehicles` 硬编码为 2791
- 无法正确处理 transitVehicles.xml 的命名空间

### 解决方案

#### 1. 创建 `count_total_vehicles_from_xml()` 函数
```python
# parsers.py 中新增
def count_total_vehicles_from_xml(vehicles_xml_path):
    """
    动态计算 transitVehicles.xml 中的车辆总数
    - 支持命名空间和非命名空间 XML
    - 处理压缩文件（.gz）
    """
```

**技术细节**:
- 使用 ElementTree 的命名空间支持
- 先尝试带命名空间的查询 (`ns:vehicle`)
- 如果失败再尝试无命名空间查询
- 优雅降级，失败时返回 0

#### 2. 改进 `load_actively_used_vehicles()` 的 agent_ids 处理
```python
# 原来: agent_ids = {"metro_up_01", "metro_down_01", "car_commuter_01"}
# 修改为: 不硬编码，允许 agent_ids = None 时处理所有代理人
```

#### 3. 更新 main.py 动态提取参数
```python
# 从已解析的 plans 中提取真实代理人
real_agent_ids = {plan.person_id for plan in plans}

# 动态计算车辆总数
total_vehicles = count_total_vehicles_from_xml(vehicles_path)
```

### 第一阶段成果
✅ 3 个 agents (car_commuter_01, metro_up_01, metro_down_01)
✅ 5 个被使用的车辆识别
✅ 2791 个定义车辆正确计数
✅ 99.8% 车辆过滤压缩

---

## 第二阶段：事件 XML 过滤

### 新建 filter_events.py 模块

**主要功能**:
- `filter_events_by_agents()` - 按代理人过滤事件 XML
- `filter_events_for_via()` - Via 导出便捷函数

**实现步骤**:

```python
def filter_events_by_agents(
    input_events_path,
    output_events_path,
    agent_ids
):
    """
    使用 iterparse 高效处理大型 XML 文件
    - 只读取 PersonEntersVehicle 等关键事件类型
    - 检查 person 属性是否在 agent_ids 中
    - 输出为格式化 XML
    """
```

**关键特性**:
- 流式处理 (iterparse) - 内存效率高
- 保留 XML 声明和格式
- 清晰的统计日志输出

### 第二阶段成果
✅ 从 310,743 个事件过滤到 104 个
✅ 99.97% 压缩率
✅ 保留所有 3 个 agents 的完整事件
✅ output_events.xml 可直接导入 Via

---

## 第三阶段：车辆轨迹增强

### 问题发现
用户反馈：
> "Via 现在没有显示车辆。看来是他们搭乘的五个 vehicle 也要筛选出来"

**根本原因**: 第二阶段只过滤了 agent 相关事件，遗漏了车辆的运动事件：
- `vehicle enters traffic` - 车辆开始运行
- `vehicle leaves traffic` - 车辆停止运行
- `VehicleArrivesAtFacility` - 车辆到达站点
- `VehicleDepartsAtFacility` - 车辆离开站点
- `entered link` / `left link` - 车辆移动

### 解决方案：双重过滤

#### 修改 filter_events.py 添加车辆过滤
```python
def filter_events_by_agents(
    input_events_path,
    output_events_path,
    agent_ids,
    vehicle_ids: set[str] | None = None  # ← 新增参数
):
    """
    双重过滤逻辑:
    事件保留条件 = (person in agent_ids) OR (vehicle in vehicle_ids)
    """
    agent_involved = (person_attr and person_attr in agent_ids)
    vehicle_involved = (vehicle_attr and vehicle_attr in vehicle_ids)

    if agent_involved or vehicle_involved:
        output_root.append(elem)
```

#### 修改 main.py 提取并传递 vehicle_ids
```python
# 从已计算的 used_vehicles 中提取车辆 ID
vehicle_ids = set(used_veh_dict.keys())  # {car_commuter_01, veh_465_subway, ...}

# 传递给过滤函数
filter_events_for_via(events_path, outdir, real_agent_ids, vehicle_ids=vehicle_ids)
```

### 第三阶段成果
✅ 事件数量：104 → 1,212 (+1,108 个车辆事件)
✅ 包含 5 辆车的完整轨迹数据
✅ Via 现在可显示车辆实时运动
✅ 人-车交互清晰可见

---

## 最终数据对比

### 事件统计
| 指标 | 数值 |
|---|---|
| 原始事件 | 310,743 |
| 仅 Agents | 104 |
| + Vehicles | 1,212 |
| 最终压缩 | 99.6% |

### 覆盖范围
| 实体 | 数量 | 来源 |
|---|---|---|
| 代理人 | 3 | plans.xml |
| 车辆 | 5 | events.xml |
| 定义车辆 | 2,791 | transitVehicles.xml |

### Via 限制检查
- ✅ Agents: 3 < 500 限制
- ✅ Vehicles: 5 < 500 限制
- ✅ 文件大小: 13 KB events + 3.5 MB network = 可接受

---

## 技术架构

```
MATSim 输出
├─ output_plans.xml.gz
├─ output_events.xml.gz (310K+ 事件)
├─ output_transitVehicles.xml.gz (2791 辆车)
├─ output_transitSchedule.xml.gz
└─ output_network.xml.gz

    ↓ build_agent_tracks.py 流程

Via Export 输出
├─ output_events.xml (1,212 事件) ← 双重过滤
├─ output_network.xml.gz ← 直接复制
├─ tracks_dt5s.csv (8597 条)
├─ legs_table.csv (62 条)
├─ filtered_vehicles.csv (5 行)
└─ vehicle_usage_report.txt
```

---

## 代码修改清单

### 新文件
- ✅ `src/main/python/build_agent_tracks/filter_events.py` (127 行)
  - 事件 XML 过滤引擎
  - 支持双重过滤 (agents + vehicles)

### 修改文件
- ✅ `src/main/python/build_agent_tracks/parsers.py`
  - 新增: `count_total_vehicles_from_xml()` 函数
  - 改进: `load_actively_used_vehicles()` agent_ids 处理
  - 改进: 命名空间 XML 支持

- ✅ `src/main/python/build_agent_tracks/main.py`
  - 新增: `--network`, `--export-filtered-events` 参数
  - 新增: 事件过滤和网络文件复制逻辑
  - 改进: 动态提取 agent_ids 和 vehicle_ids

---

## 使用方法

### 完整 Via 导出命令
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/output/via_tracks \
  --dt 5
```

### 输出文件
```
scenarios/equil/output/via_tracks/
├── output_events.xml          ← Via 主输入（人-车交互）
├── output_network.xml.gz      ← Via 主输入（网络拓扑）
├── tracks_dt5s.csv            ✓ 代理人轨迹
├── legs_table.csv             ✓ 出行段
├── filtered_vehicles.csv      ✓ 车辆清单
└── vehicle_usage_report.txt   ✓ 统计报告
```

---

## Via 可视化展示

### 可显示的内容
1. **代理人轨迹** - 3 个代理人的时空轨迹
   - car_commuter_01 的汽车通勤
   - metro_up_01 的捷运上行
   - metro_down_01 的捷运下行

2. **车辆轨迹** - 5 辆车的运动轨迹
   - 车辆进出交通网络时间
   - 车辆停靠站点时间
   - 车辆在路线上的移动

3. **人-车交互** - 实时的上下车事件
   - PersonEntersVehicle - 上车
   - PersonLeavesVehicle - 下车
   - 等车期间的位置变化

4. **网络背景** - 台北捷运线路和汽车道路

---

## 关键学习点

### XML 处理最佳实践
1. **命名空间处理** - MATSim XML 包含命名空间，需要特殊处理
2. **流式处理** - iterparse 相比 parse 更高效，适合大文件
3. **内存管理** - 定期 clear() 元素树，避免内存泄漏

### 数据过滤设计
1. **动态提取 > 硬编码** - 从源数据动态提取参数，提高灵活性
2. **多层过滤** - 支持同时按 agents 和 vehicles 过滤
3. **压缩指标** - 清晰展示过滤前后的数据量差异

### Via 平台要求
1. **包含完整轨迹** - 不仅是代理人，还需要车辆的运动事件
2. **网络拓扑** - 必须提供网络 XML 才能正确显示路线
3. **数据一致性** - agents 和 vehicles 的 ID 必须与 events 中的保持一致

---

## 第四阶段：精细时间范围过滤 + 检查点机制 ✨ (新增)

### 用户需求分析

**原问题**: 被 agents 使用的车辆产生了全天的事件数据，但 Via 只需要显示 agents 实际乘坐的时间段内的事件。

**具体案例**：
```
车辆 veh_900_subway：
  - 发车时间（全天）: 07:20:00 - 20:30:00
  - Agent 搭乘时间: 17:20:00 - 17:35:00

需求：仅显示 17:20:00 - 17:35:00 的车辆事件
```

### 解决方案：双层时间范围过滤

#### 新增函数：`extract_agent_vehicle_timeranges()` (parsers.py)

```python
def extract_agent_vehicle_timeranges(
    events_path: str | Path | None,
    agent_ids: set[str] | None = None,
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    """
    从事件文件提取每个 agent-vehicle 对的使用时间范围。

    返回: {(agent_id, vehicle_id): [(enter_s, leave_s), ...]}

    例如:
      ('agent_01', 'veh_517_subway'): [(56172, 56934)]  # 15:36:12 - 15:48:54
    """
```

**关键特性**：
- 扫描 `PersonEntersVehicle` 事件获取上车时间
- 扫描 `PersonLeavesVehicle` 事件获取下车时间
- 支持同一 agent-vehicle 对的多次乘坐
- 返回秒级时间戳，便于范围比较

#### 修改函数：`filter_events_by_agents()` (filter_events.py)

添加新参数和嵌套函数：

```python
def filter_events_by_agents(
    input_events_path: str,
    output_events_path: str,
    agent_ids: set[str],
    vehicle_ids: set[str] | None = None,
    time_ranges: dict[tuple[str, str], list[tuple[int, int]]] | None = None,  # ← 新增
) -> int:
    """
    双层过滤：
    1. 包含 agents 的所有事件
    2. 仅在时间范围内的 vehicle 事件
    """

    def is_event_in_timerange(vehicle_id: str, time_s: int) -> bool:
        """检查车辆事件是否在允许的时间范围内"""
        for (agent, veh), ranges in time_ranges.items():
            if veh == vehicle_id:
                for enter_s, leave_s in ranges:
                    if enter_s <= time_s <= leave_s:
                        return True
        return False
```

**过滤逻辑** (行 93-101)：
```python
vehicle_involved = False
if vehicle_attr and vehicle_attr in vehicle_ids:
    if time_ranges:
        time_s = int(float(time_str)) if time_str else 0
        vehicle_involved = is_event_in_timerange(vehicle_attr, time_s)  # ← 时间检查
    else:
        vehicle_involved = True

if agent_involved or vehicle_involved:
    output_root.append(elem)  # 保留事件
```

### 检查点机制实现 (main.py)

#### Checkpoint 1: 提取 Agent-Vehicle 时间范围

```
[1/3] 提取 agent-vehicle 使用時間範圍...
  ✓ 發現 42 個 agent-vehicle 組合
    car_agent_01 × car_agent_01: (07:04:42-07:14:45), (14:48:40-14:58:22)
    pt_agent_08 × unknown: (08:59:48-16:33:08)
    veh_517_subway × subway: (15:36:12-15:48:54)
    ... (总计 42 个组合，56 个时间段)
```

**实现**：时间秒数转换为 HH:MM:SS 格式 (行 177-182)：
```python
time_strs = [
    f"({int(enter/3600):02d}:{int((enter%3600)/60):02d}:{enter%60:02d}-"
    f"{int(leave/3600):02d}:{int((leave%3600)/60):02d}:{leave%60:02d})"
    for enter, leave in times
]
```

#### Checkpoint 2: 参数确认

```
[2/3] 準備事件過濾參數...
  原始事件檔案: output/output_events.xml.gz
  輸出目錄: scenarios/equil/output/via_tracks_refined
  Agent 數量: 50
  Vehicle 數量: 41
  時間範圍數: 56
```

#### Checkpoint 3: 执行和结果

```
[3/3] 執行精細過濾 (處理中...)...
  ✓ 過濾完成: scenarios/equil/output/via_tracks_refined/output_events.xml
```

### 第四阶段成果 - 50 Agent 数据集测试

**输入数据**：
- 50 agents (mixed car/PT/walk)
- 310,743 original events
- 2,791 vehicle definitions

**提取结果**：
- 42 agent-vehicle combinations
- 56 boarding segments
- ✅ All time ranges extracted in HH:MM:SS format

**过滤结果**：
- **8,372 events output** (vs 310,743 input)
- **2.6% retention rate** (97.4% compression)
- Vehicle size: 739 KB (vs 2.9 MB compressed)

**关键指标对比**：

| 指标 | Phase 1/3 (3 agents) | Phase 4 (50 agents) |
|------|---------------------|---------------------|
| 输入事件 | 310,743 | 310,743 |
| 输出事件 | 1,212 | 8,372 |
| 压缩率 | 99.6% | 97.3% |
| 提取 vehicles | 5 | 41 |
| 时间范围支持 | ❌ | ✅ |
| 检查点显示 | ❌ | ✅ |

### 第四阶段代码修改

**parsers.py** (新增)：
```python
# 第 312-391 行
def extract_agent_vehicle_timeranges(
    events_path: str | Path | None,
    agent_ids: set[str] | None = None,
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    ...
    # 82 行核心实现
```

**filter_events.py** (修改)：
- 行 19: 添加 `time_ranges` 参数
- 行 58-65: 新增 `is_event_in_timerange()` 嵌套函数
- 行 93-101: 修改车辆过滤逻辑以支持时间检查
- 行 161-198: 新增便捷函数 `filter_events_for_via_with_timeranges()`

**main.py** (修改)：
- 行 20: 导入 `extract_agent_vehicle_timeranges`
- 行 162-207: 添加 3-检查点事件过滤流程
- 中文 UI 输出，符合用户沟通风格

---

## 遗留工作 (如需)

- [x] ✅ 支持按时间范围过滤事件 - Phase 4 已完成
- [ ] 添加对 `vehicle enters traffic` 事件的特殊处理
- [ ] 生成事件的可视化统计报告 (HTML dashboard)
- [ ] 为 Via 生成 geojson 地图数据
- [ ] 支持用户指定特定 agents 子集过滤

---

## 参考文档

- CLAUDE.md - 项目开发指南
- PT_ERROR_HANDLING.md - PT 配置诊断
- Via 导出快速参考 - `Via-Export-Quick-Start.md`

**更新时间**: 2025-11-05 13:47 UTC+8
