# 给下一个 Agent 的指引

## 📋 当前项目状态

### 已完成的工作

✅ **GTFS 数据准备**
- 提取台北市范围内的公共运输数据（捷运、火车、公车）
- 生成包含 stop_times.txt 的完整 GTFS 数据集
- 创建映射指南和执行策略文档

✅ **关键文件生成**
- `pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/` - 台北市 GTFS 数据
- `../gtfs-mapping-guide.md` - GTFS 準備和验证指南
- `../pt-mapping-strategy.md` - PT 映射执行策略（待更新）
- `../../05-simulation/early-stop-strategy.md` - 资源管理和超时策略

---

## 🎯 你的任务

### 主要目标

**使用台北市 GTFS 数据进行 PT 映射，生成用于 MATSim 仿真的虚拟 PT 网络。**

### 任务步骤

#### Phase 1: GTFS 验证 (5-10 分钟)

**参考文档**: `../gtfs-mapping-guide.md` 第 4-5 节

验证 GTFS 数据的完整性：

```bash
# 检查所有必需文件是否存在
cd pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra/
ls -lh *.txt

# 运行验证脚本 (见 ../gtfs-mapping-guide.md 第 4.2 节)
python3 << 'EOF'
import pandas as pd
from pathlib import Path

gtfs_dir = Path('pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra')
routes = pd.read_csv(gtfs_dir / 'routes.txt', dtype=str)
trips = pd.read_csv(gtfs_dir / 'trips.txt', dtype=str)
stop_times = pd.read_csv(gtfs_dir / 'stop_times.txt', dtype=str)

print(f"✓ Routes: {len(routes)} 条")
print(f"✓ Trips: {len(trips)} 个")
print(f"✓ Stop_times: {len(stop_times)} 筆")

# 验证 trip_id 匹配度
matching = len(set(trips['trip_id']) & set(stop_times['trip_id'])) / len(trips) * 100
print(f"✓ Stop_times 匹配度: {matching:.1f}%")

if matching > 90:
    print("\n✓ GTFS 数据已准备好！")
else:
    print(f"\n❌ 警告：匹配度低于 90%，需要重新准备 GTFS")
EOF
```

**检查清单**:
- [ ] stop_times.txt 存在且 >100 KB
- [ ] stop_times.txt 与 trips.txt 的 trip_id 匹配度 >90%
- [ ] 没有非 TRTC 的其他捷运系统（KRTC、TMRT、NTMC）
- [ ] TRTC 路线数 24-31 条
- [ ] TRA 路线数 15 条
- [ ] 公车路线数 2,000+ 条

#### Phase 2: 准备 OSM 网络 (15-30 分钟)

**参考文档**: `../CLAUDE.md` 中的 PT Mapping 章节

需要：
1. 确保网络包含所有必要的模式：`car`, `pt`, `subway`, `bus`, `rail`
2. 运行网络清理以移除孤立的链接：
   ```bash
   java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
     org.matsim.pt2matsim.tools.NetworkUtils \
     <network.xml>
   ```

#### Phase 3: 创建 pt2matsim 配置 (10-20 分钟)

**参考文档**: `../CLAUDE.md` 中的"PT Mapping with pt2matsim"部分

创建 `pt2matsim-config-taipei.xml`，关键参数：

```xml
<!-- 输入文件 -->
<module name="publicTransitMapper">
  <param name="inputScheduleFile" value="pt2matsim/data/gtfs/gtfs_taipei_filtered_with_tra"/>
  <param name="inputNetworkFile" value="<your_network.xml>"/>
  <param name="outputScheduleFile" value="pt2matsim/output/transitSchedule.xml"/>
  <param name="outputVehiclesFile" value="pt2matsim/output/transitVehicles.xml"/>

  <!-- 映射参数（台北市网络优化） -->
  <param name="maxLinkCandidateDistance" value="300.0"/>  <!-- 对于地铁增加 -->
  <param name="nLinkThreshold" value="12"/>  <!-- 增加候选链接数 -->
  <param name="maxTravelCostFactor" value="15.0"/>  <!-- 增加容差 -->
  <param name="candidateDistanceMultiplier" value="3.0"/>  <!-- 扩大搜索范围 -->
  <param name="networkRouter" value="AStarLandmarks"/>  <!-- 对于断开的网络更可靠 -->

  <!-- 模式特定规则 -->
  <param name="useModeMappingForPassengers" value="false"/>
</module>
```

#### Phase 4: 执行 PT 映射 (2-4 小时)

**参考文档**: `../pt-mapping-strategy.md`

关键点：
- ⚠️ **分阶段执行** - 不要一次运行所有阶段
- 监控资源使用 (内存、磁盘、CPU)
- 每个阶段后验证输出

```bash
# 阶段 1: Maven 编译 (5 分钟)
./mvnw clean package

# 阶段 2: GTFS 解析 (10 分钟)
java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig \
  pt2matsim-config-taipei.xml

# 阶段 3: PT 映射 (1-2 小时)
java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim-config-taipei.xml

# 阶段 4: 映射验证 (10 分钟)
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  <your_network.xml> transitSchedule.xml.gz
```

#### Phase 5: 验证输出 (20-30 分钟)

**参考文档**: `../CLAUDE.md` 中的 PT 映射部分

检查：
- [ ] `transitSchedule.xml` 包含所有 PT 行程
- [ ] `transitVehicles.xml` 定义了足够的车辆
- [ ] 没有"无法映射"的路线警告（允许 <1%)
- [ ] 所有站点都能正确映射到网络链接

```bash
# 检查虚拟 PT 网络的连通性
gunzip -c transitSchedule.xml.gz | grep -c "stop"  # 应该有 1000+ 条
gunzip -c transitSchedule.xml.gz | grep -c "route"  # 应该有 2,000+ 条
```

---

## 📚 重要文档

### 必读文档（按优先级）

1. **`../gtfs-mapping-guide.md`** ⭐ **最重要**
   - GTFS 数据说明和验证方法
   - **重点：stop_times.txt 的重要性**
   - 常见问题解答

2. **`../CLAUDE.md`** - 项目总体架构
   - PT 映射工作流程
   - pt2matsim 参数说明
   - PT 配置清单

3. **`../../05-simulation/early-stop-strategy.md`** - 资源管理
   - 运行超时和内存监控
   - 分阶段执行策略
   - 故障诊断

4. **`../pt-mapping-strategy.md`** (待更新)
   - 映射执行的完整流程
   - 性能优化建议

---

## ⚙️ 关键技术细节

### GTFS 数据来源

```
原始数据流:
交通部公开 GTFS ↓
merged_gtfs.zip ↓
merged_gtfs_extracted/ ↓
gtfs_taipei_filtered_with_tra/  ← 你使用的
```

### stop_times.txt 的关键性

❌ **如果 stop_times.txt 缺失**：
- pt2matsim 无法确定停靠顺序
- 虚拟网络拓扑错误
- PT 代理无法正确路由

✅ **如果 stop_times.txt 完整**：
- 虚拟 PT 网络精确映射
- 正确的转乘时间计算
- 真实的 PT 行为模拟

---

## 🔧 如果遇到问题

### 问题 1: pt2matsim 报告"无法找到路线"

**检查步骤**（按顺序）:
1. GTFS 数据 → 运行 `../gtfs-mapping-guide.md` 第 4.2 节的验证脚本
2. network.xml → 确保包含 `pt`, `subway`, `bus` 等模式
3. 坐标系统 → 确保 GTFS 和 network 使用相同的 CRS

### 问题 2: 映射过程死机或超时

**参考**: `../../05-simulation/early-stop-strategy.md` 第 2-3 节
- 增加内存: `-Xmx16g` 或更多
- 减小问题规模: 先用子集测试
- 检查磁盘空间: 至少需要 20GB 可用空间

### 问题 3: 映射结果中有大量虚拟链接

**可能原因**:
1. `maxLinkCandidateDistance` 设置过小 - 增加至 300-500m
2. `maxTravelCostFactor` 太小 - 增加至 15-20
3. 网络中缺少关键链接 - 检查并补充 network.xml

---

## 📞 获取帮助

- **GTFS 问题** → 查看 `../gtfs-mapping-guide.md`
- **PT 映射流程** → 查看 `../CLAUDE.md` 中的 PT 章节
- **资源/超时问题** → 查看 `../../05-simulation/early-stop-strategy.md`
- **一般 MATSim 问题** → 查看 `../`  目录中的其他文档

---

## ✅ 成功标志

当你完成 PT 映射后，应该有：

```
pt2matsim/output/
├── transitSchedule.xml(.gz)      ← 虚拟 PT 网络
├── transitVehicles.xml(.gz)      ← PT 车辆定义
└── ... (其他日志和临时文件)
```

且能够：
- 在 MATSim 中加载 transitSchedule 和 transitVehicles
- PT 代理能够正确地计划和执行旅程
- SwissRailRaptor 路由器正常工作

---

**祝你成功！**

有任何问题，请参考上述文档或检查日志文件。

---

**准备者**: Claude Code
**日期**: 2025-11-17
**版本**: 1.0

