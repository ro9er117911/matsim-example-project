# Motorcycle 模式快速开始指南

## 📊 当前状态（✅ 已完成所有配置）

所有必要的修改已完成：

| 项目 | 状态 | 详情 |
|------|------|------|
| Network 文件 | ✅ | 62,948 + 1,489 条 links 已添加 motorcycle modes |
| Config.xml | ✅ | 已配置为网络路由模式（非传送） |
| Population.xml | ✅ | 添加 20 个 motorcycle agents（60 条 legs） |
| 依赖文件 | ✅ | pt2matsim JAR 已部署 |

---

## 🚀 手动运行指南（3步）

### 步骤 1: 编译项目
在终端执行：
```bash
cd /Users/ro9air/matsim-example-project
sh ./mvnw clean package -DskipTests
```
**耗时**：3-5 分钟
**输出**：`target/matsim-example-project-0.0.1-SNAPSHOT.jar` (~150MB)

### 步骤 2: 运行模拟
```bash
java -Xmx4g -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml
```
**耗时**：15-25 分钟（15 iterations）
**输出**：`output/` 目录中的模拟结果

### 步骤 3: 验证 Motorcycle Agents
```bash
# 检查是否成功运行
ls output/modestats.csv && echo "✅ 模拟成功"

# 查看 motorcycle 使用统计
head output/modestats.csv | grep motorcycle
```

---

## 🔍 验证成功的标志

**模拟完成后，检查以下内容：**

✅ **output 目录中存在**：
- `output_plans.xml.gz` - 所有 agents 的最终计划
- `output_events.xml.gz` - 所有事件日志
- `modestats.csv` - 模式统计

✅ **motorcycle 在统计中出现**：
```bash
grep motorcycle output/modestats.csv
```
应该看到 motorcycle 的使用数据

✅ **motorcycle_agent_* 在事件中出现**：
```bash
zcat output/ITERS/it.0/0.events.xml.gz | grep -c motorcycle_agent_
```
应该返回 > 0

✅ **没有网络错误**：
检查日志不包含 "Network does not contain any nodes"

---

## 🛠️ 如果遇到问题

| 错误 | 解决方案 |
|-----|--------|
| JAR 文件未生成 | 检查编译日志，确保网络连接 |
| "Network does not contain" | 网络文件可能未正确加载，检查 network-with-pt.xml.gz |
| 模拟运行缓慢 | 正常，15 iterations 需要 15-25 分钟 |
| 内存不足 | 增加 `-Xmx8g` 改为 `-Xmx8g` |

---

## 📁 文件位置速查表

```
/Users/ro9air/matsim-example-project/
├── scenarios/equil/
│   ├── config.xml ← 主配置文件
│   ├── network-with-pt.xml.gz ← 已更新的网络（包含 motorcycle）
│   ├── population.xml ← 已添加 20 个 motorcycle agents
│   └── output/ ← 模拟结果输出
├── target/
│   └── matsim-example-project-0.0.1-SNAPSHOT.jar ← 编译后的 JAR
└── MOTORCYCLE_REPAIR_PLAN.md ← 详细修复计划
```

---

## 📞 技术细节

### Motorcycle 参数设置
- **自由流速度**：12 m/s（43.2 km/h）
- **直线距离系数**：1.3（模拟现实路网）
- **路由方式**：真实网络路由（不是传送）
- **可用的 links**：所有允许 car 的 links

### Configuration 参数
```xml
<param name="networkModes" value="car,motorcycle" />
<param name="mainMode" value="car,motorcycle" />

<parameterset type="modeParams">
  <param name="mode" value="motorcycle" />
  <param name="constant" value="-0.5" />
  <param name="marginalUtilityOfTraveling_util_hr" value="-6.0" />
  <param name="monetaryDistanceRate" value="-0.0002" />
</parameterset>
```

---

## ✨ 预期结果

成功运行后，`output/modestats.csv` 应该包含类似的数据：

```
Iteration  car      motorcycle  pt    walk
0          45.32%   18.45%      24.21%  12.02%
1          44.98%   19.15%      24.32%  11.55%
...
15         43.12%   21.54%      25.34%  10.00%
```

（具体百分比取决于评分参数和模拟结果）

---

**创建于**：2025-11-17
**所有配置已完成** ✅
**等待手动编译和运行** ⏳
