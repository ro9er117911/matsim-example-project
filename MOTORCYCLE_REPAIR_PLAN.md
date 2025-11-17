# MATSim Motorcycle 模式修复计划

**创建时间**: 2025-11-17
**状态**: 执行中
**目标**: 修复 motorcycle agents 无法运行的问题

---

## ✅ 【完成】第1阶段 - 网络和配置修复

### 已完成的修改：
1. ✅ **Network 文件更新**
   - 62,948 条 links: `modes="bus,car"` → `modes="bus,car,motorcycle"`
   - 1,489 条 links: `modes="bus"` → `modes="bus,motorcycle"`
   - 文件重新压缩至 network-with-pt.xml.gz（15:37）

2. ✅ **Config.xml 配置验证**
   - `routing.networkModes = "car,motorcycle"` ✓
   - `qsim.mainMode = "car,motorcycle"` ✓
   - `subtourModeChoice.modes = "car,pt,motorcycle,walk"` ✓
   - `chainBasedModes = "car,motorcycle"` ✓
   - 评分参数：motorcycle modeParams 已配置 ✓
   - 无冲突的 teleportedModeParameters ✓

3. ✅ **Population 文件更新**
   - 20 个 motorcycle agents 已添加 ✓
   - 每个 agent 有 60 条 motorcycle legs ✓

4. ✅ **依赖问题解决**
   - pt2matsim-25.8-shaded.jar 已复制至正确位置 ✓

---

## 【待执行】第2阶段 - 手动编译和测试

### 步骤 2.1：编译项目（在终端手动执行）

```bash
cd /Users/ro9air/matsim-example-project

# 编译项目（生成 shaded JAR）
sh ./mvnw clean package -DskipTests

# 预期输出：
# [INFO] BUILD SUCCESS
# 生成文件: target/matsim-example-project-0.0.1-SNAPSHOT.jar (约 150MB)
```

**如果遇到问题**：
- 确保网络连接正常（需要下载依赖）
- 确保 Java 21 已安装
- 确保 pt2matsim/work/pt2matsim-25.8-shaded.jar 存在（已验证 ✓）

### 步骤 2.2：运行短期测试（5 iterations）

```bash
cd /Users/ro9air/matsim-example-project

# 首先修改配置使用 5 iterations
sed -i '' 's/<param name="lastIteration" value="15" \/>/<param name="lastIteration" value="5" \/>/' scenarios/equil/config.xml

# 运行模拟
java -Xmx4g -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml

# 预期：
# ✅ 5 次迭代完成，无 "Network does not contain" 错误
# ✅ 在 output/ITERS/it.0-4 中生成输出文件
# 耗时：约 5-10 分钟
```

### 步骤 2.3：检查输出（验证 motorcycle agents 工作）

```bash
# 检查是否有 motorcycle 事件
zcat output/ITERS/it.0/0.events.xml.gz | grep -c motorcycle_agent || echo "0"
# 预期：应该看到 > 0 的数字

# 检查模式统计
head output/modestats.csv
# 预期：看到 motorcycle 列和数值

# 查看 motorcycle 的链接选择
grep -c 'mode="motorcycle"' output/output_plans.xml.gz
# 预期：应该看到大于 0 的数字
```

### 步骤 2.4：运行完整模拟（15 iterations，如果短期测试成功）

```bash
# 恢复配置为 15 iterations
sed -i '' 's/<param name="lastIteration" value="5" \/>/<param name="lastIteration" value="15" \/>/' scenarios/equil/config.xml

# 运行完整模拟
java -Xmx4g -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml

# 预期：
# ✅ 15 次迭代完成
# ✅ 在 output/ 中生成完整统计数据
# ✅ output/modestats.csv 包含 motorcycle 模式数据
# 耗时：约 15-25 分钟
```

---

## 📋 问题分析（背景）

### 根本原因
网络文件 (`network-with-pt.xml`) 中**完全缺失** motorcycle 模式的 links：

```
配置要求:
  - routing.networkModes = "car,motorcycle"
  - qsim.mainMode = "car,motorcycle"

实际网络中的 modes:
  ✓ bus,car         (62,948 links)
  ✓ walk            (39,599 links)
  ✓ bus             (1,489 links)
  ✓ subway/pt/metro (232 + 241 links)
  ✗ motorcycle      (0 links) ❌ 完全缺失！
```

### 错误表现
```
java.lang.RuntimeException: Object is null
  at org.matsim.core.router.MultimodalLinkChooserDefaultImpl.decideOnLink()

原因: MATSim 无法为 "motorcycle" 模式找到可用的网络链接
```

---

## 🔧 修复方案：采用方案 A（快速稳定方案）

### 核心策略
1. **移除 motorcycle 从网络路由模式** → 从 `networkModes` 和 `mainMode` 中删除
2. **添加 motorcycle 为传送模式** → 使用 `teleportedModeParameters`
3. **保留 motorcycle 评分参数** → 保持 motorcycle 和 car 的行为差异
4. **彻底测试** → 确保没有其他隐藏问题

### 为什么选择方案A？
- ✅ 快速修复（5分钟内完成）
- ✅ 低风险（不需要修改网络文件）
- ✅ 可立即测试
- ✅ 后期可升级到完整的网络路由方案B
- ⚠️ motorcycle 使用直线传送（不走实际网络路由）

---

## 📊 修复步骤详解

### 【第1阶段】配置修改（config.xml）

#### Step 1.1: 从 networkModes 移除 motorcycle ⚙️
**文件**: `/Users/ro9air/matsim-example-project/scenarios/equil/config.xml`
**位置**: routing 模块，第55行
**当前**: `<param name="networkModes" value="car,motorcycle" />`
**修改为**: `<param name="networkModes" value="car" />`

**原因**: 网络中不存在 motorcycle 模式的 links，所以不能作为网络路由模式

---

#### Step 1.2: 从 qsim.mainMode 移除 motorcycle ⚙️
**文件**: `/Users/ro9air/matsim-example-project/scenarios/equil/config.xml`
**位置**: qsim 模块，第38行
**当前**: `<param name="mainMode" value="car,motorcycle" />`
**修改为**: `<param name="mainMode" value="car" />`

**原因**: 如果 motorcycle 不在 networkModes 中，就不应该在 mainMode 中

---

#### Step 1.3: 从 chainBasedModes 移除 motorcycle ⚙️
**文件**: `/Users/ro9air/matsim-example-project/scenarios/equil/config.xml`
**位置**: subtourModeChoice 模块，第134行
**当前**: `<param name="chainBasedModes" value="car,motorcycle" />`
**修改为**: `<param name="chainBasedModes" value="car" />`

**原因**: chainBasedModes 应该只包含网络模式，不包括传送模式

---

#### Step 1.4: 添加 motorcycle 为 teleportedModeParameters ⚙️
**文件**: `/Users/ro9air/matsim-example-project/scenarios/equil/config.xml`
**位置**: routing 模块，在现有 teleportedModeParameters 中添加新的 parameterset

**添加内容**:
```xml
<parameterset type="teleportedModeParameters">
  <param name="mode" value="motorcycle" />
  <param name="teleportedModeSpeed" value="12.0" />
  <param name="beelineDistanceFactor" value="1.3" />
</parameterset>
```

**参数说明**:
- `mode`: "motorcycle" - 运输模式名称
- `teleportedModeSpeed`: 12.0 m/s = 43.2 km/h（与计划保持一致）
- `beelineDistanceFactor`: 1.3（实际路线比直线远30%，模拟现实路网）

**原因**: 使 motorcycle 使用直线传送路由（快速方案），路由器会自动计算距离和时间

---

#### Step 1.5: 保留 motorcycle scoring 参数 ✅
**文件**: `/Users/ro9air/matsim-example-project/scenarios/equil/config.xml`
**位置**: scoring 模块，第164-170行

**现有参数保持不变**:
```xml
<parameterset type="modeParams">
  <param name="mode" value="motorcycle" />
  <param name="constant" value="-0.5" />
  <param name="marginalUtilityOfTraveling_util_hr" value="-6.0" />
  <param name="monetaryDistanceRate" value="-0.0002" />
</parameterset>
```

**用途**: 定义 motorcycle 的行为特性（吸引力比car低，但有成本优势）

---

### 【第2阶段】验证和短期测试

#### Step 2.1: 验证 config.xml 语法 ✓
```bash
cd /Users/ro9air/matsim-example-project

# 检查是否存在 motorcycle 在 networkModes（应该没有）
grep 'networkModes' scenarios/equil/config.xml
# 预期: <param name="networkModes" value="car" />

# 检查是否存在 motorcycle 在 mainMode（应该没有）
grep 'mainMode' scenarios/equil/config.xml
# 预期: <param name="mainMode" value="car" />

# 检查 motorcycle teleportedModeParameters 是否存在
grep -A 3 'mode" value="motorcycle"' scenarios/equil/config.xml
# 预期看到 teleportedModeSpeed 和 beelineDistanceFactor
```

---

#### Step 2.2: 运行短期模拟测试（5 iterations）🚀
```bash
cd /Users/ro9air/matsim-example-project

# 方式1: 使用 Maven 编译并运行
./mvnw clean package -q && \
java -jar target/matsim-example-project-*.jar scenarios/equil/config.xml

# 方式2: 直接修改临时配置运行5次迭代
# 编辑 config.xml，将 lastIteration 改为 5，运行后再改回 15
```

**预期输出**:
- ✅ 模拟启动成功
- ✅ 看到 "Iteration 0 finished" 这样的进度消息
- ✅ 在 `output/ITERS/` 中生成输出文件
- ❌ **不应该**看到 "Network does not contain any nodes" 错误

---

#### Step 2.3: 检查模拟日志和事件 🔍
```bash
# 检查是否有 motorcycle agents 的事件
zcat output/ITERS/it.0/0.events.xml.gz | \
  grep -E "motorcycle|motorcycle_agent" | head -20

# 预期：看到 motorcycle_agent_* 的 activity, leg 等事件
```

---

### 【第3阶段】完整模拟运行

#### Step 3.1: 如果短期测试成功 ✅
```bash
# 将 config.xml 中的 lastIteration 改为 15
# 运行完整模拟
java -jar target/matsim-example-project-*.jar scenarios/equil/config.xml
```

**预期**:
- 完成15次迭代（约5-10分钟）
- 生成 output_plans.xml, output_events.xml, 统计图表等

#### Step 3.2: 分析结果 📊
```bash
# 检查最终的模式选择统计
ls -lh output/*.csv
# 查看 modestats.csv 了解各模式的使用情况

# 统计 motorcycle 和 car 的使用比例
grep -c 'motorcycle' output/output_plans.xml.gz 2>/dev/null || echo "Check completed"
```

---

## 🛡️ 故障排查和错误应对

### 错误1: "Network does not contain any nodes!"
**症状**:
```
WARN SpeedyALTData:141 Network does not contain any nodes!
ERROR MultimodalLinkChooserDefaultImpl:54 Facility without link...
```

**原因**: 仍然在使用 networkModes 中的 motorcycle，但网络不支持

**解决**:
1. ✅ 检查 Step 1.1 是否完成：`grep networkModes config.xml` 应该显示 `value="car"`
2. ✅ 检查 Step 1.2 是否完成：`grep mainMode config.xml` 应该显示 `value="car"`
3. ✅ 重新构建：`./mvnw clean package`
4. ✅ 重新运行

---

### 错误2: "Object is null" - MultimodalLinkChooserDefaultImpl
**症状**:
```
java.lang.RuntimeException: Object is null
  at org.matsim.core.router.MultimodalLinkChooserDefaultImpl.decideOnLink()
```

**原因**: motorcycle 模式的子网络为空（与错误1相同根本原因）

**解决**:
- 这个错误必然随着错误1的修复而消失
- 按照上面"错误1"的解决步骤

---

### 错误3: 坐标超出网络范围
**症状**:
```
WARN NetworkUtils:457 nearestNode not found
```

**原因**: activity 的坐标不在网络覆盖范围内

**检查**:
```bash
# 检查 motorcycle agents 的坐标范围
python3 << 'EOF'
import xml.etree.ElementTree as ET
tree = ET.parse('scenarios/equil/population.xml')
root = tree.getroot()
coords = [(float(a.get('x')), float(a.get('y')))
          for p in root.findall('.//person')
          for a in p.findall('.//activity')]
print(f"X range: {min(c[0] for c in coords)} - {max(c[0] for c in coords)}")
print(f"Y range: {min(c[1] for c in coords)} - {max(c[1] for c in coords)}")
EOF
```

**预期结果** (应该已在范围内):
```
X range: 294035.05 - 308143.01
Y range: 2762173.24 - 2772105.34
```

**如果坐标超出范围**:
- 编辑 population.xml，调整 motorcycle agents 的活动坐标
- 或移除有问题的 agents

---

### 错误4: "Capacity too small" 或容量问题
**症状**:
```
WARN LinkImpl:104 capacity=0.0 of link id 101874 may cause problems
```

**解决**:
1. 这是网络数据问题，通常不致命
2. 如果影响模拟，运行 NetworkCleaner:
```bash
java -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckNetworkPlausibility \
  scenarios/equil/network-with-pt.xml
```

---

### 错误5: 模拟无限卡住
**症状**: 模拟运行超过30分钟仍未完成第一次迭代

**原因**: 可能是路由器性能问题

**解决**:
1. 检查日志：`tail -100 output/logfile.log | grep -E "ERROR|WARN"`
2. 尝试减少 agents 数量（临时调整 population.xml 测试）
3. 检查 routing 算法：确认使用了 SpeedyALT

---

## 📈 修复进度跟踪

- [ ] Step 1.1: 修改 networkModes
- [ ] Step 1.2: 修改 qsim.mainMode
- [ ] Step 1.3: 修改 chainBasedModes
- [ ] Step 1.4: 添加 motorcycle teleportedModeParameters
- [ ] Step 1.5: 验证 scoring 参数保留
- [ ] Step 2.1: 验证 config.xml 语法
- [ ] Step 2.2: 运行5次迭代测试
- [ ] Step 2.3: 检查事件日志
- [ ] Step 3.1: 运行完整15次迭代（如果测试成功）
- [ ] Step 3.2: 分析最终结果

---

## 🎯 预期的最终状态

### 修复成功标准
✅ 模拟能完整运行15次迭代，无错误
✅ output 目录中生成完整的输出文件
✅ motorcycle_agent_* 的事件在 output_events.xml.gz 中可见
✅ modestats.csv 中 motorcycle 模式有使用记录
✅ 没有 "Network does not contain nodes" 或类似的致命错误

### 预期输出文件（第一次迭代）
```
output/ITERS/it.0/
├── 0.events.xml.gz         ✓ 包含所有事件（活动、上车、下车等）
├── 0.plans.xml.gz          ✓ 包含修改后的计划
├── 0.activities.csv.gz     ✓ 活动统计
├── 0.legs.csv.gz           ✓ 旅程段统计
├── 0.trips.csv.gz          ✓ 出行统计
└── 0.legHistogram*.png     ✓ 可视化图表

output/
├── output_plans.xml.gz     ✓ 最终计划
├── output_events.xml.gz    ✓ 所有事件
├── modestats.csv           ✓ 模式统计
└── ... (其他统计文件)
```

---

## 🔄 回滚计划

如果修复失败且无法继续，回滚步骤：

1. 恢复网络文件：
```bash
cd scenarios/equil
cp network-with-pt.xml.gz.backup network-with-pt.xml.gz
```

2. 恢复 population.xml（移除 motorcycle agents）：
```bash
git checkout scenarios/equil/population.xml
```

3. 恢复 config.xml 到只支持 car 和 pt：
```bash
git checkout scenarios/equil/config.xml
```

---

## 📞 调试命令速查表

```bash
# 查看当前配置中的 networkModes
grep 'networkModes' scenarios/equil/config.xml

# 查看当前配置中的 mainMode
grep 'mainMode' scenarios/equil/config.xml

# 查看 motorcycle 的所有配置
grep -A 2 'mode" value="motorcycle"' scenarios/equil/config.xml

# 统计 population 中 motorcycle legs 数量
grep -c 'mode="motorcycle"' scenarios/equil/population.xml

# 检查最新错误日志
tail -50 output/logfile.log | grep ERROR

# 提取特定模式的事件
zcat output/ITERS/it.0/0.events.xml.gz | grep motorcycle | head -20
```

---

**最后更新**: 2025-11-17 | **状态**: 准备执行第1阶段修改
