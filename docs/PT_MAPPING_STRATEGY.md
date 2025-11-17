# PT 映射执行策略 (PT Mapping Strategy)

## 概述

本文档说明如何使用 pt2matsim 工具将 GTFS 公共运输数据映射到 MATSim 网络，生成虚拟 PT 网络供仿真使用。

**关键要求**：必须完成 GTFS 验证前的所有检查清单（见 `docs/GTFS_MAPPING_GUIDE.md`）

---

## 0. 前置条件检查

在启动任何 PT 映射工作前，确保：

### 资源检查
```bash
# 检查可用内存（需要至少 12GB）
free -h

# 检查磁盘空间（需要至少 20GB）
df -h .

# 检查 CPU 核心数（用于并行配置）
nproc
```

### GTFS 数据检查
```bash
# 运行 GTFS_MAPPING_GUIDE.md 中的验证脚本
python3 << 'EOF'
import pandas as pd
from pathlib import Path

gtfs_dir = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')

# 加载数据
routes = pd.read_csv(gtfs_dir / 'routes.txt', dtype=str)
trips = pd.read_csv(gtfs_dir / 'trips.txt', dtype=str)
stop_times = pd.read_csv(gtfs_dir / 'stop_times.txt', dtype=str)

print("=== GTFS 数据验证 ===")
print(f"Routes: {len(routes)} 条")
print(f"Trips: {len(trips)} 个")
print(f"Stop_times: {len(stop_times)} 筆")

# 检查 stop_times 匹配度
trip_ids_trips = set(trips['trip_id'])
trip_ids_stop_times = set(stop_times['trip_id'])
matching = len(trip_ids_trips & trip_ids_stop_times) / len(trip_ids_trips) * 100

print(f"Stop_times 匹配度: {matching:.1f}%")

if matching > 90:
    print("✓ GTFS 已准备好！")
else:
    print("❌ GTFS 需要修复")
EOF
```

---

## 1. 准备 OSM 网络

### 1.1 网络覆盖范围检查

确保网络包含整个台北市区域：

```bash
# 检查网络边界
gunzip -c <network.xml.gz> | grep -E 'minx|miny|maxx|maxy'
```

预期范围（台北市 WGS84 坐标）：
- 纬度: 25.00 - 25.20
- 经度: 121.40 - 121.70

### 1.2 网络模式验证

确保网络包含所有必要的运输模式：

```bash
# 检查现有的链接模式
gunzip -c <network.xml.gz> | grep -o 'modes="[^"]*"' | sort | uniq -c
```

预期模式：`car`, `pt`, `subway`, `bus`, `rail`, `walk` 等

### 1.3 网络清理

使用 pt2matsim 内置工具移除孤立的链接和无效的拓扑：

```bash
# 清理网络（约 5-10 分钟）
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.tools.NetworkUtils \
  <input_network.xml> \
  <output_network_clean.xml>

# 验证清理结果
ls -lh <output_network_clean.xml>*
```

---

## 2. 创建 pt2matsim 配置文件

### 2.1 配置文件位置

```bash
# 创建配置目录
mkdir -p pt2matsim/work

# 配置文件路径
pt2matsim/work/ptmapper-config-taipei.xml
```

### 2.2 基础配置模板

创建 `pt2matsim/work/ptmapper-config-taipei.xml`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
<config>

  <!-- 公共运输映射器模块 -->
  <module name="publicTransitMapper">

    <!-- ===== 输入/输出文件 ===== -->
    <!-- GTFS 数据目录（包含 routes.txt, trips.txt, stops.txt, stop_times.txt 等） -->
    <param name="inputScheduleFile" value="pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra"/>

    <!-- 输入网络文件 -->
    <param name="inputNetworkFile" value="pt2matsim/output_v1/network-prepared.xml.gz"/>

    <!-- 输出虚拟 PT 网络 schedule -->
    <param name="outputScheduleFile" value="pt2matsim/output_v1/transitSchedule.xml"/>

    <!-- 输出车辆定义 -->
    <param name="outputVehiclesFile" value="pt2matsim/output_v1/transitVehicles.xml"/>

    <!-- ===== 核心映射参数 ===== -->
    <!-- 从停靠站到最近链接的最大距离（米） -->
    <!-- 默认: 90m，地铁: 300m，复杂网络: 500m -->
    <param name="maxLinkCandidateDistance" value="300.0"/>

    <!-- 每个停靠点考虑的候选链接数量 -->
    <!-- 默认: 6，复杂网络: 10-12 -->
    <param name="nLinkThreshold" value="12"/>

    <!-- 在创建虚拟链接前的最大成本因子 -->
    <!-- 默认: 5.0，台北市网络: 15.0-20.0 -->
    <param name="maxTravelCostFactor" value="15.0"/>

    <!-- 找不到足够候选链接后扩大搜索范围的倍数 -->
    <!-- 默认: 1.6，稀疏网络: 3.0-5.0 -->
    <param name="candidateDistanceMultiplier" value="3.0"/>

    <!-- ===== 路由和性能参数 ===== -->
    <!-- 路由算法：SpeedyALT（快）或 AStarLandmarks（稳健）-->
    <param name="networkRouter" value="AStarLandmarks"/>

    <!-- 并行处理线程数（根据 CPU 核心数调整）-->
    <param name="numOfThreads" value="8"/>

    <!-- 是否使用模式特定规则 -->
    <param name="useModeMappingForPassengers" value="false"/>

    <!-- ===== 输出选项 ===== -->
    <!-- 生成 schedule 的转换统计 -->
    <param name="scheduleTransitModes" value="pt"/>

  </module>

</config>
```

### 2.3 参数调优指南

根据具体情况调整以下参数：

| 参数 | 默认值 | 台北市推荐 | 说明 |
|-----|--------|-----------|------|
| maxLinkCandidateDistance | 90m | 300m | 增加以覆盖地下/高架站点 |
| nLinkThreshold | 6 | 12 | 增加以找到更多可能的链接 |
| maxTravelCostFactor | 5.0 | 15.0 | 增加以降低对人工链接的依赖 |
| candidateDistanceMultiplier | 1.6 | 3.0 | 增加以扩大搜索范围 |
| networkRouter | SpeedyALT | AStarLandmarks | 对于断开的网络更稳健 |

---

## 3. 执行 PT 映射

### 3.1 分阶段执行策略

**重要**: 不要一次运行所有阶段。分开运行并在每个阶段后验证。

详见: `docs/early-stop-strategy.md` 中的资源监控和超时管理

### 3.2 阶段 1: Maven 编译 (5-10 分钟)

```bash
# 清理和编译项目
./mvnw clean package

# 验证 JAR 生成
ls -lh target/matsim-example-project-0.0.1-SNAPSHOT.jar
```

**预期输出**:
- 构建成功（BUILD SUCCESS）
- JAR 文件大小 > 100MB

### 3.3 阶段 2: GTFS 解析 (10-20 分钟)

创建默认 pt2matsim 配置（如果还没有的话）：

```bash
# 如果没有现成配置，生成默认配置
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim/work/ptmapper-config-taipei.xml
```

### 3.4 阶段 3: PT 映射 (1-3 小时)

这是最耗时且最资源密集的阶段。**监控内存和CPU使用**。

```bash
# 基础命令（使用 timeout 保护）
timeout 3h java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-taipei.xml | tee pt2matsim/output_v1/ptmapper.log

# 如果有充足资源，可以增加并行度
timeout 3h java -Xmx16g \
  -Djava.util.concurrent.ForkJoinPool.common.parallelism=8 \
  -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-taipei.xml | tee pt2matsim/output_v1/ptmapper.log
```

**监控命令**（在另一个终端运行）：

```bash
# 实时监控内存
watch -n 5 'free -h'

# 实时监控 Java 进程
watch -n 5 'ps aux | grep "PublicTransitMapper"'

# 查看实时日志
tail -f pt2matsim/output_v1/ptmapper.log
```

**预期输出**:
- `transitSchedule.xml` (1-20MB)
- `transitVehicles.xml` (100KB-1MB)
- 日志中应该看到诸如 "Mapping route XXX..." 的进度信息

### 3.5 阶段 4: 映射验证 (10-20 分钟)

验证映射结果是否合理：

```bash
# 检查映射的 schedule
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  pt2matsim/output_v1/network-prepared.xml.gz \
  pt2matsim/output_v1/transitSchedule.xml.gz | tee pt2matsim/output_v1/check_plausibility.log
```

---

## 4. 输出验证

### 4.1 文件检查

```bash
# 检查所有输出文件
ls -lh pt2matsim/output_v1/ | grep -E "transitSchedule|transitVehicles"

# 预期输出
# -rw-r--r--  1 user  group   10M  transitSchedule.xml
# -rw-r--r--  1 user  group 500K  transitVehicles.xml
```

### 4.2 内容验证

```bash
# 统计 transitSchedule 中的路线和站点
gunzip -c pt2matsim/output_v1/transitSchedule.xml.gz | \
  grep -c '<transitRoute id='  # 应该有 2,000+ 条

# 统计 transitSchedule 中的停靠点
gunzip -c pt2matsim/output_v1/transitSchedule.xml.gz | \
  grep -c '<stop refId='  # 应该有 40,000+ 条

# 统计 transitVehicles 中的车辆
gunzip -c pt2matsim/output_v1/transitVehicles.xml.gz | \
  grep -c '<vehicle id='  # 应该有 2,000+ 个
```

### 4.3 质量检查

检查日志中是否有问题：

```bash
# 检查映射成功率
grep -i "routes mapped" pt2matsim/output_v1/ptmapper.log

# 检查警告
grep "WARN" pt2matsim/output_v1/ptmapper.log | head -20

# 检查错误
grep "ERROR" pt2matsim/output_v1/ptmapper.log
```

**预期结果**：
- 所有路线都应该成功映射（允许 <1% 失败）
- 人工创建的链接应该 <10%
- 没有致命错误

---

## 5. 常见问题排查

### 问题 1: "无法找到合适的链接"警告

**症状**: 日志中出现大量 "Could not find adequate link candidates" 警告

**解决方案**（按优先级）：
1. 增加 `maxLinkCandidateDistance`: 300 → 400 → 500
2. 增加 `nLinkThreshold`: 12 → 15 → 20
3. 增加 `maxTravelCostFactor`: 15 → 20 → 30
4. 检查网络覆盖范围是否包含所有站点

```bash
# 检查 GTFS 站点坐标范围
python3 << 'EOF'
import pandas as pd
gtfs_dir = 'pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra'
stops = pd.read_csv(f'{gtfs_dir}/stops.txt')
print(f"Lat: {stops['stop_lat'].min():.2f} - {stops['stop_lat'].max():.2f}")
print(f"Lon: {stops['stop_lon'].min():.2f} - {stops['stop_lon'].max():.2f}")
EOF
```

### 问题 2: OutOfMemoryError

**症状**: Java 进程突然终止，日志显示 `java.lang.OutOfMemoryError`

**解决方案**：
1. 增加堆内存: `-Xmx12g` → `-Xmx16g` → `-Xmx24g`
2. 使用 G1 垃圾回收器: `-XX:+UseG1GC`
3. 减少问题规模（使用 GTFS 子集测试）

```bash
# 使用更多内存的命令示例
java -Xms16g -Xmx16g -XX:+UseG1GC \
  -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-taipei.xml
```

### 问题 3: 映射超时

**症状**: 进程在 1-2 小时后仍未完成

**解决方案**（按优先级）：
1. 增加超时时间: `timeout 2h` → `timeout 4h`
2. 增加线程数: `numOfThreads` 参数从 4 → 8
3. 降低映射参数精度来加速：
   - `maxLinkCandidateDistance`: 300 → 200
   - `nLinkThreshold`: 12 → 8
4. 分割 GTFS 数据集（测试子集）

### 问题 4: 映射失败，错误率高

**症状**: 日志显示大量失败的路线或站点无法映射

**检查清单**:
- [ ] network.xml 和 GTFS 使用相同的坐标系统（EPSG:3826）
- [ ] network.xml 包含所有必要的模式（pt, subway, bus, rail）
- [ ] GTFS 数据有 stop_times.txt 且匹配度 >90%
- [ ] 网络覆盖 GTFS 站点坐标范围

---

## 6. 资源管理和监控

详细的资源管理策略见: `docs/early-stop-strategy.md`

### 快速参考

| 阶段 | 超时 | 内存 | CPU | 磁盘空间 |
|-----|------|------|-----|---------|
| Maven 打包 | 10m | 1-2G | 低 | 2GB |
| GTFS 解析 | 30m | 8-12G | 中 | 5GB |
| **PT 映射** | **2-3h** | **12-16G** | **高** | **10-20GB** |
| 验证 | 20m | 4G | 低 | 5GB |

---

## 7. 成功标志

当 PT 映射完成后，验证以下标志：

```bash
# 1. 输出文件存在且大小合理
ls -lh pt2matsim/output_v1/transitSchedule*.xml*
ls -lh pt2matsim/output_v1/transitVehicles*.xml*

# 2. 能在 MATSim 中加载
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar \
  --config scenarios/equil/config.xml

# 3. 虚拟 PT 网络包含足够的站点
gunzip -c pt2matsim/output_v1/transitSchedule.xml.gz | grep -c 'stop refId=' > 10000

# 4. PT 代理能够正确地规划和执行旅程
# (运行仿真并检查 events.xml 中的 PersonEntersVehicle 事件)
```

---

## 8. 后续步骤

PT 映射完成后：

1. **集成到 MATSim 配置**
   ```xml
   <module name="transit">
     <param name="transitScheduleFile" value="pt2matsim/output_v1/transitSchedule.xml"/>
     <param name="vehiclesFile" value="pt2matsim/output_v1/transitVehicles.xml"/>
   </module>
   ```

2. **测试仿真**
   - 使用小规模人口（10-50 agents）进行测试
   - 验证 PT 代理能够上下车
   - 检查转乘是否正确

3. **优化和验证**
   - 分析仿真日志
   - 如有问题，返回 Phase 2 调整映射参数

---

## 9. 参考文档

- **GTFS 数据验证**: `docs/GTFS_MAPPING_GUIDE.md`
- **资源管理和超时**: `docs/early-stop-strategy.md`
- **整体项目架构**: `CLAUDE.md`
- **下一个 agent 任务**: `NEXT_AGENT_INSTRUCTIONS.md`

---

**作者**: Claude Code
**版本**: 1.0
**最后更新**: 2025-11-17
