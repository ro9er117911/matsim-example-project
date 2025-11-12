# 工作日志索引 (Working Journal Index)

快速导航：找到你需要的文档

---

## 按日期

### 2025-11-11
- 🔧 **[2025-11-11-Summary.md](2025-11-11-Summary.md)** ← **从这里开始**
  - 本日工作完整总结（15分钟阅读）
  - 包含所有成果、文档、下一步建议

### 2025-11-11 详细分析文档

#### JAI 依赖问题
- 📖 [2025-11-11-Build-Fix-JAI-Dependencies-and-SwissRailRaptor-Research.md](2025-11-11-Build-Fix-JAI-Dependencies-and-SwissRailRaptor-Research.md)
  - Maven 构建修复（SafeDisplayNameGenerator、系统属性）
  - MATSim 安装指南
  - SwissRailRaptor 基础文档

#### PT 转乘问题
- 📖 [2025-11-11-PT-Transfer-Validation.md](2025-11-11-PT-Transfer-Validation.md)
  - 完整问题诊断和修复记录
  - 技术深度分析（新增部分）
  - 4 阶段实验过程

#### 快速参考指南（推荐收藏）
- 🚀 [2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md)
  - 快速诊断表
  - 参数选择流程图
  - 常见错误及解决方案
  - 验证转乘的命令

---

## 按主题

### 🚇 PT/转乘相关

| 文档 | 内容 | 推荐度 |
|------|------|--------|
| [2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md) | 快速参考指南（最常用） | ⭐⭐⭐⭐⭐ |
| [2025-11-11-PT-Transfer-Validation.md](2025-11-11-PT-Transfer-Validation.md) | 完整问题分析 | ⭐⭐⭐⭐ |
| [../CLAUDE.md (第433-485行)](../CLAUDE.md#L433) | SwissRailRaptor 标准配置 | ⭐⭐⭐⭐ |

### 🔧 构建/环境相关

| 文档 | 内容 | 推荐度 |
|------|------|--------|
| [2025-11-11-Build-Fix-JAI-Dependencies-and-SwissRailRaptor-Research.md](2025-11-11-Build-Fix-JAI-Dependencies-and-SwissRailRaptor-Research.md) | Maven JAI 依赖修复 | ⭐⭐⭐ |

---

## 核心问题速查

### ❓ "我的 agents 不转乘，怎么办？"

**按顺序检查**:
1. 打开 [快速参考指南](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md#快速诊断表)
2. 对照诊断表找到症状
3. 执行对应的验证命令
4. 不行？阅读 [技术深度分析](2025-11-11-PT-Transfer-Validation.md#技术深度分析为什么修复后能成功转乘)

### ❓ "我要修改 SwissRailRaptor 配置"

**按顺序进行**:
1. 查看 [CLAUDE.md 的参数说明](../CLAUDE.md#L433)
2. 对照 [快速参考指南的配置示例](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md#配置对照清单)
3. 使用 [验证命令](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md#验证转乘是否工作)
4. 查看 [常见错误](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md#常见错误及解决方案)

### ❓ "我想理解为什么修复能成功"

**深度阅读顺序**:
1. 先看 [修复前后对比](2025-11-11-PT-Transfer-Validation.md#配置修复-)
2. 再读 [技术深度分析](2025-11-11-PT-Transfer-Validation.md#技术深度分析为什么修复后能成功转乘)
3. 最后对照 [CLAUDE.md 详解](../CLAUDE.md#L433)

---

## 文档统计

| 文档类型 | 数量 | 总行数 |
|---------|------|--------|
| 工作日志 | 4 | 1,200+ |
| 快速参考 | 1 | 200+ |
| 代码注释 | 更新于 CLAUDE.md | 45+ |
| 配置文件 | 修改 config_pt_only.xml | -15 |

---

## 使用建议

### 🟢 新手用户（第一次遇到 PT 问题）
1. 阅读 [2025-11-11-Summary.md](2025-11-11-Summary.md)（5分钟）
2. 查看 [快速参考指南](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md)（10分钟）
3. 按诊断表找到症状，执行解决方案

### 🟡 进阶用户（需要深入理解）
1. 阅读 [完整问题分析](2025-11-11-PT-Transfer-Validation.md)（20分钟）
2. 查看 [技术深度分析](2025-11-11-PT-Transfer-Validation.md#技术深度分析为什么修复后能成功转乘)（15分钟）
3. 参考 CLAUDE.md 的标准配置进行修改

### 🔴 问题排查（出现新错误）
1. 在 [快速参考指南](2025-11-11-SwissRailRaptor-IntermodalParameter-Guide.md#常见错误及解决方案) 找症状
2. 执行对应的验证命令
3. 查看 [技术深度分析](2025-11-11-PT-Transfer-Validation.md) 理解原理

---

## 更新记录

| 日期 | 文档 | 变更 |
|------|------|------|
| 2025-11-11 | CLAUDE.md | +45 行（useIntermodalAccessEgress 详解） |
| 2025-11-11 | PT-Transfer-Validation.md | +160 行（技术深度分析） |
| 2025-11-11 | config_pt_only.xml | -15 行（移除 accessEgressSettings） |
| 2025-11-11 | 新建 3 份文档 | 900+ 行 |

---

## 快速命令

保存这些命令用于日常诊断：

```bash
# 检查 agents 转乘是否工作
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "PersonEntersVehicle" | wc -l

# 找出哪些 agents 进行了转乘（>1 次 boarding）
gunzip -c output/ITERS/it.0/0.events.xml.gz | \
  grep "PersonEntersVehicle.*pt_agent" | \
  sed 's/.*person="\([^"]*\)".*/\1/' | \
  sort | uniq -c | sort -rn | head -10

# 验证转乘站的 stopAreaId
gunzip -c scenarios/equil/transitSchedule-mapped.xml.gz | \
  grep 'stopFacility' | grep 'stopAreaId'
```

---

**Last Updated**: 2025-11-11
**Maintainer**: ro9air + Claude Code
