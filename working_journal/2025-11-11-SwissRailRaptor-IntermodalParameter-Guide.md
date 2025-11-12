# SwissRailRaptor useIntermodalAccessEgress 参数速查指南

**Date**: 2025-11-11
**Issue**: PT agents 转乘失败
**Root Cause**: `useIntermodalAccessEgress = true` 与人口计划结构不匹配
**Status**: ✅ FIXED

---

## 快速诊断表

| 现象 | 原因 | 解决方案 |
|------|------|--------|
| Agents 不上车 (0 PersonEntersVehicle) | useIntermodalAccessEgress=true 但计划没有 access_walk legs | ✅ 改为 false |
| 错误的转乘站 | stopAreaId 不一致 | ✅ 检查 transitSchedule.xml |
| 转乘时间过长 | additionalTransferTime 设置过大 | ✅ 调整 transitRouter 参数 |

---

## useIntermodalAccessEgress 参数选择流程图

```
❓ 你的人口计划结构是什么？

A) 简单结构（推荐）
   home activity → <leg mode="pt"/> → work activity
   |
   └─→ 使用 useIntermodalAccessEgress = false ✅
       - 路由器自动处理 access/egress
       - 产生正确的转乘路线

B) 复杂结构（高级）
   home activity → <leg mode="access_walk"/> → <leg mode="pt"/>
                → <leg mode="transit_walk"/> → <leg mode="pt"/>
                → <leg mode="egress_walk"/> → work activity
   |
   └─→ 使用 useIntermodalAccessEgress = true ✅
       - 路由器遵循计划中的 leg 结构
       - 用于自定义 access/egress 路线
```

---

## 配置对照清单

### ❌ 错误配置示例
```xml
<!-- config_pt_only.xml 修复前 -->
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="true" />
  <parameterset type="accessEgressSettings">
    <param name="mode" value="walk" />
    <param name="radius" value="1000.0" />
  </parameterset>
</module>

<!-- 人口计划只有 -->
<leg mode="pt">...</leg>

<!-- 结果：❌ 路由失败，无转乘 -->
```

### ✅ 正确配置示例
```xml
<!-- config_pt_only.xml 修复后 -->
<module name="swissRailRaptor">
  <!-- 禁用 intermodal：人口计划中没有 access_walk/egress_walk legs -->
  <param name="useIntermodalAccessEgress" value="false" />

  <!-- 转乘成本参数 -->
  <param name="transferPenaltyBaseCost" value="0.0" />
  <param name="transferPenaltyCostPerTravelTimeHour" value="0.0" />

  <!-- 不使用模式映射 -->
  <param name="useModeMappingForPassengers" value="false" />
</module>

<!-- 人口计划可以很简单 -->
<leg mode="pt">...</leg>

<!-- 结果：✅ 正确路由，成功转乘 -->
```

---

## 技术原理速记

### 模式匹配原理

**useIntermodalAccessEgress = true 时**:
- SwissRailRaptor **期望** population plan 中有这样的 leg 序列：
  ```
  access_walk → pt → transit_walk → pt → egress_walk
  ```
- 如果 plan 中只有 `<leg mode="pt"/>`：
  - 路由器无法找到匹配的模式
  - 无法正确解析人口计划
  - 转乘规划失败

**useIntermodalAccessEgress = false 时**:
- SwissRailRaptor **不期望** access/egress legs
- 路由器处理简单的 `<leg mode="pt"/>`
- 在运行时自动：
  1. 从家活动坐标找最近的 PT 站（虚拟 access）
  2. 规划从该站到工作地附近站的 PT 路线
  3. 从该站走到工作活动坐标（虚拟 egress）
- 结果：正确的多段 PT legs + 转乘事件

### 转乘识别关键：stopAreaId

```
西门站（同一物理位置的不同线路）：

板南线 BL11 站:
  id="BL11_UP"
  stopAreaId="086"  ← 关键
  x=301278.15 y=2770528.60

松山新店线 G12 站:
  id="G12_UP"
  stopAreaId="086"  ← 相同！
  x=301278.15 y=2770528.60  ← 坐标也相同

结果：
- SwissRailRaptor 认识到 BL11 ↔ G12 可以转乘
- Agents 在这里进行转乘
```

---

## 验证转乘是否工作

### 命令 1：检查 PersonEntersVehicle 事件数
```bash
# Agent 应该产生多个 boarding 事件（>1 表示转乘）
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10

# 预期输出：每个转乘 agent 应该有 2+ 个 boarding
#    4 pt_agent_07
#    4 pt_agent_09
#    2 pt_agent_03
```

### 命令 2：检查具体的转乘序列
```bash
# 查看一个特定 agent 的转乘过程
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent_07" | \
  sed 's/.*person="\([^"]*\)".*vehicle="\([^"]*\)".*/\1 \2/' | \
  sort

# 预期输出：多个不同的 vehicle ID
# pt_agent_07 veh_1122_subway
# pt_agent_07 veh_1220_subway
# pt_agent_07 veh_2334_subway
# pt_agent_07 veh_2582_subway
```

### 命令 3：检查转乘站配置
```bash
# 验证转乘站有相同的 stopAreaId
gunzip -c scenarios/equil/transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | \
  grep -E 'BL11|G12' | \
  grep 'stopAreaId'

# 预期输出：所有转乘站对都有相同的 stopAreaId
# <stopFacility ... stopAreaId="086" ... name="西門-上行月臺(板南線)" />
# <stopFacility ... stopAreaId="086" ... name="西門-上行月臺(松山新店線)" />
```

---

## 常见错误及解决方案

### 错误 1：useIntermodalAccessEgress=true 但计划没有 legs
```
症状：
- WARNING: No suitable leg found
- Agents 产生 0 PersonEntersVehicle 事件

原因：
- 配置期望 access_walk/egress_walk
- 计划中没有这些 legs

修复：
改为 useIntermodalAccessEgress=false
```

### 错误 2：转乘站 stopAreaId 不一致
```
症状：
- Agents 无法在转乘站完成转乘
- 无论怎么改参数都不行

原因：
- BL11_UP 的 stopAreaId="086"
- G12_UP 的 stopAreaId="999"（不同！）

修复：
重新生成 transitSchedule，确保 stopAreaId 一致
或手动编辑 transitSchedule.xml 统一 stopAreaId
```

### 错误 3：转乘时间太长
```
症状：
- Agents 宁愿放弃转乘也要绕路
- 转乘的 agents 特别少

原因：
- additionalTransferTime 设置过大（如 3600s）
- transferPenaltyBaseCost 太高

修复：
减小参数值：
<param name="additionalTransferTime" value="300.0" /> <!-- 5分钟 -->
<param name="transferPenaltyBaseCost" value="0.0" />
```

---

## 文档交叉引用

| 文档位置 | 内容 |
|---------|------|
| [CLAUDE.md:433-469](../CLAUDE.md#L433) | useIntermodalAccessEgress 详细说明 |
| [CLAUDE.md:471-485](../CLAUDE.md#L471) | SwissRailRaptor 检查清单 |
| [2025-11-11-PT-Transfer-Validation.md](2025-11-11-PT-Transfer-Validation.md) | 完整的问题分析和修复记录 |
| [scenarios/equil/config_pt_only.xml](../scenarios/equil/config_pt_only.xml) | 修复后的配置示例 |

---

## 总结

### 记住这个简单规则
```
如果你的人口计划看起来是这样：
  <activity type="home" ... />
  <leg mode="pt" />
  <activity type="work" ... />

那就用这个配置：
  <param name="useIntermodalAccessEgress" value="false" />

Agent 会自动转乘，无需额外配置！ ✅
```

---

**下次遇到 PT 转乘问题时：**
1. 检查人口计划中是否有 access_walk/egress_walk legs
2. 如果没有 → 改为 `useIntermodalAccessEgress = false`
3. 如果有 → 保持 `useIntermodalAccessEgress = true` 并检查 leg 结构
4. 验证转乘站的 stopAreaId 一致性
5. 运行验证命令检查 PersonEntersVehicle 事件
