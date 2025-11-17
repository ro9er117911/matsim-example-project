# PT 映射快速开始指南 (Quick Start Guide)

**如果你是接手这个 PT 映射任务的 agent，请从这里开始！**

---

## 📋 你的任务是什么？

使用台北市 GTFS 数据，通过 pt2matsim 工具将公共运输路线映射到 MATSim 网络上，生成虚拟 PT 网络供仿真使用。

---

## 📚 按顺序阅读以下文档（必读！）

### 1️⃣ **第一步：了解 GTFS 数据准备** (15 分钟)
   📄 文件: [`docs/GTFS_MAPPING_GUIDE.md`](docs/GTFS_MAPPING_GUIDE.md)

   **你将学到**:
   - GTFS 数据的结构和内容
   - **为什么 stop_times.txt 对 PT 映射至关重要** ⭐
   - 如何验证 GTFS 数据完整性
   - 常见问题及解决方案

   **关键行动**:
   - 运行 GTFS 验证脚本（第 4 节）
   - 确认 stop_times.txt 存在且匹配度 > 90%
   - ✅ 验证清单（第 4 节）全部通过

---

### 2️⃣ **第二步：理解 PT 映射执行流程** (30 分钟)
   📄 文件: [`docs/PT_MAPPING_STRATEGY.md`](docs/PT_MAPPING_STRATEGY.md)

   **你将学到**:
   - 如何准备 OSM 网络
   - 如何创建 pt2matsim 配置文件
   - 分阶段执行 PT 映射（4 个阶段）
   - 如何验证映射输出
   - 常见问题排查

   **关键行动**:
   - 阶段 1: Maven 编译
   - 阶段 2: GTFS 解析
   - **阶段 3: PT 映射（最耗时，2-3 小时）**
   - 阶段 4: 验证输出

---

### 3️⃣ **第三步：资源管理和超时策略** (10 分钟)
   📄 文件: [`docs/early-stop-strategy.md`](docs/early-stop-strategy.md)

   **你将学到**:
   - 各阶段推荐的内存和 CPU 配置
   - 如何监控资源使用（内存、磁盘、CPU）
   - 超时和早停机制
   - 如果出错如何恢复

   **关键行动**:
   - 检查可用资源（至少 12GB 内存，20GB 磁盘）
   - 监控 Java 进程的内存使用
   - 如果超时，参考故障排除快速参考表

---

## 🚀 快速执行流程

### 前置条件检查 (5 分钟)
```bash
# 1. 验证 GTFS 数据
python3 << 'EOF'
import pandas as pd
from pathlib import Path

gtfs_dir = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')
routes = pd.read_csv(gtfs_dir / 'routes.txt', dtype=str)
trips = pd.read_csv(gtfs_dir / 'trips.txt', dtype=str)
stop_times = pd.read_csv(gtfs_dir / 'stop_times.txt', dtype=str)

print(f"Routes: {len(routes)}")
print(f"Trips: {len(trips)}")
print(f"Stop_times: {len(stop_times)}")

matching = len(set(trips['trip_id']) & set(stop_times['trip_id'])) / len(trips) * 100
print(f"Stop_times 匹配度: {matching:.1f}%")

if matching > 90:
    print("✓ GTFS 已准备好！")
else:
    print("❌ GTFS 需要修复")
EOF

# 2. 检查系统资源
free -h          # 应该有 > 12GB 内存
df -h .          # 应该有 > 20GB 磁盘空间
nproc            # 查看 CPU 核心数

# 3. 验证网络文件存在
ls -lh pt2matsim/output_v1/network-prepared.xml.gz
```

---

### 分阶段执行 (总计 2-4 小时)

#### 阶段 1: Maven 编译 (5-10 分钟)
```bash
./mvnw clean package
# ✓ 等待 BUILD SUCCESS
```

#### 阶段 2: GTFS 解析 (10-20 分钟)
```bash
# 创建配置文件（如果不存在）
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim/work/ptmapper-config-taipei.xml

# 或使用预配置的配置文件（参考 docs/PT_MAPPING_STRATEGY.md 第 2.2 节）
```

#### 阶段 3: PT 映射 (1-3 小时) ⚠️ 最耗资源
```bash
# 在另一个终端监控资源
watch -n 5 'free -h'       # 监控内存
tail -f pt2matsim/output_v1/ptmapper.log  # 查看进度

# 主命令
timeout 3h java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-taipei.xml | tee pt2matsim/output_v1/ptmapper.log

# ✓ 等待完成（应该看到 "...routes mapped successfully"）
```

#### 阶段 4: 验证输出 (10-20 分钟)
```bash
# 检查输出文件
ls -lh pt2matsim/output_v1/transitSchedule*.xml*
ls -lh pt2matsim/output_v1/transitVehicles*.xml*

# 验证内容
gunzip -c pt2matsim/output_v1/transitSchedule.xml.gz | grep -c '<transitRoute'
# 应该输出 > 2000

gunzip -c pt2matsim/output_v1/transitSchedule.xml.gz | grep -c '<stop refId='
# 应该输出 > 40000
```

---

## 🎯 成功标志

当你看到以下标志时，说明 PT 映射成功：

✅ `transitSchedule.xml` (10-20MB) 已生成
✅ `transitVehicles.xml` (500KB-1MB) 已生成
✅ 虚拟 PT 网络包含 2,000+ 条路线
✅ 虚拟 PT 网络包含 40,000+ 个停靠点
✅ 日志中显示大部分路线映射成功（允许 <1% 失败）

---

## ❌ 如果出错

### 常见问题快速索引

| 问题 | 查看文档 |
|------|--------|
| stop_times.txt 缺失或不匹配 | `docs/GTFS_MAPPING_GUIDE.md` 第 2 节 |
| 内存不足 (OutOfMemoryError) | `docs/PT_MAPPING_STRATEGY.md` 第 5.2 节 |
| 映射超时 | `docs/PT_MAPPING_STRATEGY.md` 第 5.3 节 |
| 大量警告 "无法找到链接" | `docs/PT_MAPPING_STRATEGY.md` 第 5.1 节 |
| 资源监控和管理 | `docs/early-stop-strategy.md` 第 3-4 节 |

---

## 📞 文档使用地图

```
GTFS 数据问题
    ↓
 docs/GTFS_MAPPING_GUIDE.md
    ↓
   ✓ 数据验证
   ✓ stop_times.txt 重要性
   ✓ 问题排查

PT 映射执行
    ↓
 docs/PT_MAPPING_STRATEGY.md
    ↓
   ✓ 网络准备
   ✓ 配置创建
   ✓ 4 个执行阶段
   ✓ 输出验证
   ✓ 问题排查

资源和超时管理
    ↓
 docs/early-stop-strategy.md
    ↓
   ✓ 资源监控
   ✓ 超时策略
   ✓ 故障恢复
```

---

## 📖 完整文档列表

| 文件 | 用途 | 何时阅读 |
|------|------|--------|
| **NEXT_AGENT_INSTRUCTIONS.md** | 完整任务说明（参考） | 开始前 |
| **docs/GTFS_MAPPING_GUIDE.md** | GTFS 数据准备和验证 | 开始前 |
| **docs/PT_MAPPING_STRATEGY.md** | PT 映射执行流程详解 | 执行 PT 映射时 |
| **docs/early-stop-strategy.md** | 资源管理和超时策略 | 执行过程中 |
| **CLAUDE.md** | 项目总体架构（参考） | 需要理解全貌时 |

---

## 🎓 关键概念

### GTFS (General Transit Feed Specification)
- 标准的公共运输数据格式
- 包含路线、班次、停靠站、停靠时间等信息
- **stop_times.txt** 定义每条路线在各站的停靠时间和顺序（必须存在！）

### pt2matsim
- 将 GTFS 映射到网络的工具
- 根据地理坐标和网络拓扑匹配停靠站
- 生成虚拟 PT 网络供 MATSim 仿真使用

### 虚拟 PT 网络 (Virtual Transit Network)
- pt2matsim 的输出
- 由虚拟链接组成（命名如 `pt_STATION_UP/DN`）
- 包含完整的路线定义、班次、停靠时间
- 供 MATSim 中的 PT 代理使用

---

## ⏱️ 时间预估

| 步骤 | 时间 |
|------|------|
| 阅读文档 | 1 小时 |
| 前置检查 | 10 分钟 |
| 阶段 1-2 | 30 分钟 |
| **阶段 3 (PT 映射)** | **1-3 小时** |
| 阶段 4 验证 | 20 分钟 |
| **总计** | **2-5 小时** |

---

## ✉️ 给下一个 agent 的消息

你好！这是 PT 映射任务。按照以下步骤进行：

1. **首先阅读**:
   - `docs/GTFS_MAPPING_GUIDE.md` (GTFS 数据验证)
   - `docs/PT_MAPPING_STRATEGY.md` (PT 映射执行)
   - `docs/early-stop-strategy.md` (资源管理)

2. **然后执行**: 分四个阶段运行 PT 映射（详见 PT_MAPPING_STRATEGY.md）

3. **重要**:
   - 不要一次运行所有阶段
   - 每个阶段后验证输出
   - 监控内存和 CPU 使用
   - 如果遇到问题，参考文档第 5 节的问题排查

4. **最终目标**:
   - 生成 `transitSchedule.xml` 和 `transitVehicles.xml`
   - 虚拟 PT 网络包含 2,000+ 条路线，40,000+ 个停靠点
   - 能在 MATSim 中正确加载和使用

祝你成功！有任何问题，参考相应的文档即可。

---

**准备者**: Claude Code
**日期**: 2025-11-17
**版本**: 1.0

希望你能顺利完成这个任务！加油！💪
