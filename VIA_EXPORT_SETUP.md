# Via Platform Export Setup Guide

**最后更新**: 2025-11-05
**状态**: ✅ 已配置

---

## 为什么使用 `forVia` 文件夹？

### 问题
MATSim GUI运行时默认输出到 `/scenarios/equil/output/`：
- 生成大量文件（plans、events、network等）
- 会**覆盖**所有现有的Python处理结果
- 造成Via导出文件丢失

### 解决方案
- **Via导出专用文件夹**: `/scenarios/equil/forVia/`
- **MATSim GUI输出**: `/scenarios/equil/output/`
- **完全隔离**, 互不影响

---

## 目录结构

```
scenarios/equil/
├── output/              ← MATSim GUI output (large, frequently overwritten)
│   ├── output_plans.xml.gz (生成后使用)
│   ├── output_events.xml.gz (生成后使用)
│   ├── output_network.xml.gz (生成后使用)
│   └── ITERS/ (迭代数据)
│
├── forVia/              ← Via导出 (保持不变)
│   ├── output_events.xml (filtered, Via ready)
│   ├── output_network.xml.gz (topology for Via)
│   ├── tracks_dt5s.csv (agent trajectories)
│   ├── filtered_vehicles.csv (vehicle list)
│   └── vehicle_usage_report.txt (statistics)
│
├── test_population_50.xml (improved population)
├── config.xml (MATSim config)
└── transitSchedule-mapped.xml (PT network)
```

---

## 工作流程

### Step 1: 运行MATSim GUI模拟
```bash
# 启动MATSim GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml

# ✓ 生成输出到: scenarios/equil/output/
# ✓ 包含: output_plans.xml.gz, output_events.xml.gz, output_network.xml.gz
```

### Step 2: 导出到Via平台
```bash
# 从刚生成的output提取到forVia
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia

# ✓ 输出到: scenarios/equil/forVia/
# ✓ 文件保持不变，直到下次手动运行此命令
```

### Step 3: 导入到Via可视化
```
1. 打开Via平台
2. 新建项目
3. 加载事件: scenarios/equil/forVia/output_events.xml
4. 加载网络: scenarios/equil/forVia/output_network.xml.gz
5. 点击播放
```

---

## 输出文件说明

### 由MATSim GUI生成 (scenarios/equil/output/)
| 文件 | 大小 | 用途 | 说明 |
|------|------|------|------|
| output_plans.xml.gz | ~50MB | Python处理输入 | 所有agents的计划 |
| output_events.xml.gz | ~300MB | Python处理输入 | 完整事件日志 |
| output_network.xml.gz | ~3.5MB | Via可视化背景 | 路网拓扑 |
| ITERS/ | ~500MB+ | 迭代数据 | 每次迭代的详细数据 |

### 由Python处理生成 (scenarios/equil/forVia/)
| 文件 | 大小 | 用途 | 说明 |
|------|------|------|------|
| output_events.xml | ~15KB | **Via import** | 过滤后的事件（仅agents使用） |
| output_network.xml.gz | ~3.5MB | **Via import** | 网络副本 |
| tracks_dt5s.csv | ~50KB | 分析用 | Agent轨迹，5秒采样 |
| filtered_vehicles.csv | ~5KB | 分析用 | 使用的车辆列表 |
| vehicle_usage_report.txt | ~2KB | 分析用 | 压缩率和使用统计 |
| legs_table.csv | ~100KB | 分析用 | Agent腿部段数据 |

---

## 文件隔离的好处

✅ **保护Via数据**
- 运行新模拟不会丢失导出数据
- 可以多次运行模拟，保留想要的结果

✅ **清晰的工作流**
- `output/` = 最新的MATSim模拟结果
- `forVia/` = 已处理的可视化数据

✅ **防止意外覆盖**
- 即使MATSim GUI生成新的events，forVia里的内容不受影响
- 需要更新时明确执行Python命令

---

## 常见操作

### 更新Via导出（新模拟后）
```bash
# 在scenarios/equil/目录运行
python ../../src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out forVia
```

### 保留多个模拟结果
```bash
# 模拟1完成
python ... --out forVia_v1

# 模拟2完成
python ... --out forVia_v2

# 模拟3完成
python ... --out forVia_latest
```

### 清理旧数据（可选）
```bash
# 移除output中的old迭代数据
rm -rf scenarios/equil/output/ITERS/*

# 保留output中的XML文件以便重新导出
# ls scenarios/equil/output/*.xml*
```

---

## 故障排除

### forVia文件夹不存在
```bash
mkdir -p scenarios/equil/forVia
```

### 找不到output_plans.xml.gz
✗ **问题**: MATSim模拟还未生成
✓ **解决**: 先运行MATSim GUI模拟生成输出

### forVia文件被覆盖
✗ **问题**: 意外运行到`--out output/`
✓ **解决**: 检查命令行参数，确保`--out scenarios/equil/forVia`

### Via导入后看不到vehicle轨迹
✗ **问题**: 没有添加`--export-filtered-events`
✓ **解决**: 重新运行，添加此参数

---

## 脚本速查

### 最小配置（仅agents）
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --out scenarios/equil/forVia
```

### 完整配置（推荐用于Via）
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --schedule output/output_transitSchedule.xml.gz \
  --vehicles output/output_transitVehicles.xml.gz \
  --network output/output_network.xml.gz \
  --export-filtered-events \
  --out scenarios/equil/forVia
```

### 快速分析（skip Via export）
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --out scenarios/equil/forVia \
  --skip-activity-matching
```

---

## 相关文档

- [Via-Export-Quick-Start.md](working_journal/Via-Export-Quick-Start.md) - 快速开始
- [SIMULATION_GUIDE_V2.md](SIMULATION_GUIDE_V2.md) - 改进的agent生成指南
- [CLAUDE.md](CLAUDE.md) - 项目开发指南

---

**建议**: 将此文档放在scenarios/equil/目录中以便快速参考

